import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const extensionSource = fs.readFileSync(new URL("../web/js/speech_bubble.js", import.meta.url), "utf8").replace(/^import .*;\r?\n/gm, "");
const editorHtml = fs.readFileSync(new URL("../web/speech-bubble-editor.html", import.meta.url), "utf8");
const start = editorHtml.indexOf("// BEGIN EDITOR SAVE PROTOCOL");
const end = editorHtml.indexOf("// END EDITOR SAVE PROTOCOL", start);
assert.ok(start >= 0 && end > start);
const editorSource = editorHtml.slice(start, end);
const serializer = editorHtml.split("\n").find(line => line.includes("function currentLayoutJson()"));
assert.match(editorHtml, /renderRevision\+=1;scheduleEditorDraft\(\)/);
assert.match(editorHtml, /!editorConnected \|\| pendingSave/);
new Function(editorHtml.split("<script>")[1].split("</script>")[0]);

const results = [];
function test(name, run) {
  const env = environment();
  try { run(env); assert.equal(env.errors.length, 0, JSON.stringify(env.errors)); results.push(name); }
  catch (error) { throw new Error(name + ": " + error.message, { cause: error }); }
}
function environment() {
  let now = 1000, nextTimer = 1, uuid = 1, parent;
  const timers = new Map(), store = new Map(), errors = [], alerts = [], outbound = [];
  const clock = {
    setTimeout(fn, delay = 0) { const id = nextTimer++; timers.set(id, { fn, due: now + delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
    setInterval(fn, delay) { const id = nextTimer++; timers.set(id, { fn, due: now + delay, interval: delay }); return id; },
    clearInterval(id) { timers.delete(id); },
    tick(ms = 0) {
      const end = now + ms;
      for (let i = 0; i < 10000; i++) {
        const entry = [...timers].filter(([, t]) => t.due <= end).sort((a,b) => a[1].due - b[1].due || a[0] - b[0])[0];
        if (!entry) { now = end; return; }
        const [id, t] = entry; timers.delete(id); now = t.due;
        if (t.interval) timers.set(id, { ...t, due: now + t.interval });
        try { t.fn(); } catch (error) { errors.push(error.message); }
      }
      throw new Error("Timer loop did not settle");
    },
    skip(ms) { now += ms; for (const t of timers.values()) if (t.due < now) t.due = now + (t.interval || 0); },
  };
  const storage = {
    failSet: false, failGet: false,
    get length() { return store.size; }, key(i) { return [...store.keys()][i] ?? null; },
    getItem(k) { if (this.failGet) throw new Error("SecurityError"); return store.get(String(k)) ?? null; },
    setItem(k,v) { if (this.failSet) throw new Error("QuotaExceededError"); store.set(String(k), String(v)); },
    removeItem(k) { store.delete(String(k)); },
  };
  const fakeDate = class extends Date { static now() { return now; } };
  const crypto = { randomUUID() { return "verification-" + uuid++; } };
  class MockImage { set src(v) { this._src=v; Promise.resolve().then(() => this.onload?.()); } get src() { return this._src; } }
  const origin = "http://verification.invalid";
  const parentProxy = { closed: false, postMessage(data) {
    const popup = data.__source;
    throw new Error("Use the editor's bound opener");
  } };
  function makeParent() {
    const listeners = new Map(), nodes = new Map(), popups = [];
    const graph = { changes:0, links:{}, getNodeById(id) { return nodes.get(String(id)); }, setDirtyCanvas() {}, change() { this.changes++; } };
    const app = { graph, registerExtension(value) { this.extension=value; } };
    const win = { location:{origin}, addEventListener(t,cb) { listeners.set(t,cb); },
      setTimeout:clock.setTimeout, setInterval:clock.setInterval, clearInterval:clock.clearInterval,
      alert(message) { alerts.push(message); },
      open(url,name) {
        const popup = { closed:false, focusCount:0, focus() { this.focusCount++; }, name };
        popups.push(popup); this.lastOpen = url; return popup;
      },
    };
    const context = vm.createContext({ app, api:{apiURL:p=>p}, window:win, localStorage:storage,
      Image:MockImage, URLSearchParams, console, Date:fakeDate, crypto });
    vm.runInContext(extensionSource + "\nglobalThis.testApi={editorTargets,editorSessions,readEditorRecord,storedEditorRecords,pruneEditorRecords};", context);
    function NodeType(id) {
      this.id=id;this.properties={};this.size=[470,500];this.graph=graph;
      this.widgets=[{name:"layout_json",value:'{"version":1,"canvas":{"width":1024,"height":1024},"background_visible":true,"elements":[]}'},{name:"preview_key",value:"sb-test"}];
    }
    NodeType.prototype.addWidget=function(type,name,value,callback,options={}) {
      const w={type,name,value,callback,options};this.widgets.push(w);
      if(name==="Open Speech Bubble Editor")this.editorButton=w;return w;
    };
    NodeType.prototype.setSize=function(){};
    NodeType.prototype.setDirtyCanvas=function(){};
    NodeType.prototype.setProperty=function(name,value){this.properties[name]=value;};
    app.extension.beforeRegisterNodeDef(NodeType,{name:"SpeechBubbleLayer"});
    return {
      ...context.testApi, app, win, listeners, nodes, popups,
      node(id=7, saved) {
        const n=new NodeType(id);
        if(saved){n.widgets[0].value=saved.layout;n.properties=JSON.parse(JSON.stringify(saved.properties));}
        nodes.set(String(id),n);n.onNodeCreated();
        if(saved)n.onConfigure({properties:saved.properties});
        return n;
      },
      launch(node) {
        node.editorButton.callback();
        if(!popups.length)return null;
        const params=new URL(win.lastOpen,origin).searchParams;
        return {key:params.get("jsonKey"),revision:Number(params.get("revisionBase")),popup:popups.at(-1)};
      },
      receive(data,source,from=origin) { listeners.get("message")({data,source,origin:from}); },
    };
  }
  parent=makeParent();
  function editor(launch, options={}) {
    const listeners=new Map(), elements=new Map();
    for(const id of ["save","saveStatus","cancel","downloadLayout"])elements.set(id,{textContent:id==="save"?"Save Layout":"",disabled:false,isConnected:true});
    const document={getElementById:id=>elements.get(id),createElement(){return {click(){},href:"",download:""};}};
    const popup=launch.popup, opener={closed:false,postMessage(data) {
      outbound.push(data);
      clock.setTimeout(() => parent.receive(data,popup), options.requestDelay || 0);
    }};
    const win={opener,addEventListener(t,cb){listeners.set(t,cb);},close(){popup.closed=true;listeners.get("pagehide")?.();}};
    if(options.noOpener)win.opener=null;
    popup.postMessage=(data)=>{
      if(options.throwAck)throw new Error("postMessage failed");
      if(!options.dropAck)clock.setTimeout(()=>listeners.get("message")?.({data,source:opener,origin}),options.ackDelay || 0);
    };
    const context=vm.createContext({window:win,document,localStorage:storage,location:{origin},crypto,Date:fakeDate,console,
      setTimeout:clock.setTimeout,clearTimeout:clock.clearTimeout,
      URL:{createObjectURL(){return "blob:verification";},revokeObjectURL(){}},Blob:class{},
      initialKey:launch.key,initialRevision:launch.revision,
      flushThrows:options.flushThrows || false,
    });
    vm.runInContext("const jsonKey=initialKey;let renderRevision=initialRevision,editorClosed=false,editorCommitted=false,editorStateLoaded=true,livePreviewTimer=null;\n"+
      "const state=JSON.parse(localStorage.getItem(jsonKey)||'{\"canvas\":{\"width\":1024,\"height\":1024},\"elements\":[]}');state.width=state.canvas?.width||1024;state.height=state.canvas?.height||1024;state.backgroundVisible=state.background_visible!==false;\n"+
      "function flushPendingEmphasisRegeneration(){}function flushLivePreview(){if(flushThrows)throw new Error('Render failed');return 'data:image/png;base64,TEST';}\n"+
      serializer+"\n"+editorSource+"\nglobalThis.testApi={state,flags:()=>({editorClosed,editorCommitted,editorConnected}),pending:()=>pendingSave,edit:()=>{state.elements.push({id:'edited-'+state.elements.length,type:'text',text:'test'});renderRevision++;scheduleEditorDraft();},connectToOpener,persistEditorDraft,scheduleEditorDraft,setRevision:v=>renderRevision=v,setLoaded:v=>editorStateLoaded=v};",context);
    return { ...context.testApi, popup, options, listeners, elements, opener,
      save(){elements.get("save").onclick();},cancel(){elements.get("cancel").onclick();},
      pagehide(){listeners.get("pagehide")();},
      pageshow(){listeners.get("pageshow")({persisted:true});},
      status(){return elements.get("saveStatus").textContent;},
    };
  }
  return {
    clock,storage,store,errors,alerts,outbound,editor,get p(){return parent;},
    reloadParent() {
      const saved=[...parent.nodes.values()].map(n=>({id:n.id,layout:n.widgets[0].value,properties:n.properties}));
      for(const session of parent.editorSessions.values())clock.clearInterval(session.watcher);
      parent=makeParent();for(const n of saved)parent.node(n.id,n);return parent;
    },
    open(id=7,options={}) { const node=parent.node(id),launch=parent.launch(node),ed=editor(launch,options);clock.tick();return {node,launch,ed}; },
    json(node){return JSON.parse(node.widgets[0].value);},
  };
}

test("normal save confirms once and discards committed draft",e=>{
  const {node,launch,ed}=e.open();ed.edit();e.clock.tick(500);ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
  assert.equal(e.p.editorTargets.size,0);assert.equal(e.store.has(launch.key),false);
  assert.equal(e.store.has("speech_bubble:editor_session:v2:"+launch.key),false);
});
test("same node opens once and focuses the existing editor",e=>{
  const {node,ed}=e.open();node.editorButton.callback();
  assert.equal(e.p.popups.length,1);assert.equal(ed.popup.focusCount,1);
});
test("two nodes route independently",e=>{
  const a=e.open(7),b=e.open(8);a.ed.edit();b.ed.edit();b.ed.edit();a.ed.save();b.ed.save();e.clock.tick(1500);
  assert.notEqual(a.launch.key,b.launch.key);assert.equal(e.json(a.node).elements.length,1);assert.equal(e.json(b.node).elements.length,2);
});
test("parent reload reconnects automatically on save",e=>{
  const {ed}=e.open();ed.edit();e.reloadParent();ed.save();e.clock.tick(1500);
  assert.equal(e.json(e.p.nodes.get("7")).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("editor reload keeps draft and reconnects same key",e=>{
  const {node,launch,ed}=e.open();ed.edit();ed.pagehide();e.clock.tick();
  assert.equal(e.p.editorTargets.size,1);assert.equal(JSON.parse(e.store.get(launch.key)).elements.length,1);
  const second=e.editor(launch);e.clock.tick();second.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(second.popup.closed,true);
});
test("bfcache pagehide and pageshow reconnect",e=>{
  const {node,ed}=e.open();ed.edit();ed.pagehide();e.clock.tick();ed.pageshow();e.clock.tick();ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("delayed acknowledgement reports unconfirmed then accepts same request",e=>{
  const {node,ed}=e.open();ed.options.ackDelay=2000;ed.edit();const changes=e.p.app.graph.changes;ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/not yet confirmed/);assert.equal(e.json(node).elements.length,1);
  e.clock.tick(500);assert.equal(ed.popup.closed,true);assert.equal(e.p.app.graph.changes,changes+1);
});
test("delayed request saves without premature close",e=>{
  const {node,ed}=e.open();ed.options.requestDelay=2000;ed.edit();ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,0);assert.match(ed.status(),/not yet confirmed/);
  e.clock.tick(500);assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("lost acknowledgement retries immutable request without reapplication",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.dropAck=true;const changes=e.p.app.graph.changes;
  ed.save();const request=ed.pending().requestId;e.clock.tick(1500);ed.options.dropAck=false;ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(e.p.app.graph.changes,changes+1);assert.equal(ed.popup.closed,true);
  assert.ok(e.outbound.filter(d=>d.type==="speech_bubble:set_layout_json").every(d=>d.requestId===request));
});
test("reply send exception remains retryable",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.throwAck=true;ed.save();e.clock.tick(1500);ed.options.throwAck=false;ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("lost ack then parent reload reacknowledges restored applied layout",e=>{
  const {ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();e.clock.tick(1500);
  e.reloadParent();const changes=e.p.app.graph.changes;ed.options.dropAck=false;ed.save();e.clock.tick(1500);
  assert.equal(e.json(e.p.nodes.get("7")).elements.length,1);assert.equal(e.p.app.graph.changes,changes);assert.equal(ed.popup.closed,true);
});
test("pending immutable request survives editor reload",e=>{
  const {node,launch,ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();const request=ed.pending().requestId;e.clock.tick(1500);ed.pagehide();e.clock.tick();
  const second=e.editor(launch);e.clock.tick();assert.equal(second.pending().requestId,request);
  const changes=e.p.app.graph.changes;second.save();e.clock.tick(1500);
  assert.equal(e.p.app.graph.changes,changes);assert.equal(e.json(node).elements.length,1);assert.equal(second.popup.closed,true);
});
test("newer edits survive late acknowledgement and can be saved separately",e=>{
  const {node,ed}=e.open();ed.options.ackDelay=2000;ed.edit();ed.save();e.clock.tick(0);ed.edit();e.clock.tick(2000);
  assert.equal(ed.popup.closed,false);assert.match(ed.status(),/newer changes/);assert.equal(e.json(node).elements.length,1);
  ed.options.ackDelay=0;ed.save();e.clock.tick(1500);assert.equal(e.json(node).elements.length,2);assert.equal(ed.popup.closed,true);
});
test("retry timer is scoped to current request",e=>{
  const {ed,node}=e.open();node._speechBubbleLatestPreviewRevision=20;ed.save();e.clock.tick(100);
  assert.match(ed.status(),/newer preview/);ed.edit();ed.options.dropAck=true;ed.save();e.clock.tick(1400);
  assert.equal(ed.elements.get("save").disabled,true);e.clock.tick(100);assert.equal(ed.elements.get("save").disabled,false);
});
test("stale revision is rejected and explicit current save succeeds",e=>{
  const {node,ed}=e.open();node._speechBubbleLatestPreviewRevision=10;ed.edit();ed.setRevision(2);ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,0);assert.match(ed.status(),/newer preview/);
  ed.save();e.clock.tick(1500);assert.equal(e.json(node).elements.length,1);
});
test("missing layout widget gives a failure response",e=>{
  const {node,ed}=e.open();node.widgets=node.widgets.filter(w=>w.name!=="layout_json");ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/rejected/);assert.equal(ed.popup.closed,false);
});
for(const where of ["widget.callback","node.onWidgetChanged","node.setProperty","node.graph.change","app.graph.setDirtyCanvas"]){
  test("application exception rolls back and retry succeeds: "+where,e=>{
    const {node,ed}=e.open();ed.edit();const originalLayout=node.widgets[0].value;
    const fail=()=>{throw new Error("injected "+where);};let restore;
    if(where==="widget.callback"){node.widgets[0].callback=fail;restore=()=>delete node.widgets[0].callback;}
    if(where==="node.onWidgetChanged"){node.onWidgetChanged=fail;restore=()=>delete node.onWidgetChanged;}
    if(where==="node.setProperty"){const previous=node.setProperty;node.setProperty=fail;restore=()=>node.setProperty=previous;}
    if(where==="node.graph.change"){const previous=node.graph.change;node.graph.change=fail;restore=()=>node.graph.change=previous;}
    if(where==="app.graph.setDirtyCanvas"){const previous=e.p.app.graph.setDirtyCanvas;e.p.app.graph.setDirtyCanvas=fail;restore=()=>e.p.app.graph.setDirtyCanvas=previous;}
    ed.save();const request=ed.pending().requestId;e.clock.tick(1500);
    assert.equal(node.widgets[0].value,originalLayout);assert.match(ed.status(),/could not apply/);
    restore();ed.save();e.clock.tick(1500);assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
    assert.ok(e.outbound.filter(d=>d.type==="speech_bubble:set_layout_json").every(d=>d.requestId===request));
  });
}
test("storage write failure does not prevent live save",e=>{
  const {node,ed}=e.open();e.storage.failSet=true;ed.edit();ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("storage unavailable from launch still saves through memory session",e=>{
  e.storage.failSet=true;const {node,ed}=e.open();ed.edit();ed.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(ed.popup.closed,true);
});
test("missing session returns an actionable connection failure",e=>{
  const popup={closed:false},ed=e.editor({key:"speech_bubble_7_unknown",revision:1,popup});e.clock.tick();
  assert.match(ed.status(),/recovery session is unavailable/);assert.equal(ed.popup.closed,false);
});
test("missing opener preserves downloadable draft",e=>{
  const {launch,ed}=e.open(7,{noOpener:true});ed.edit();ed.pagehide();e.clock.tick();
  assert.match(ed.status(),/original ComfyUI tab is unavailable/);assert.equal(JSON.parse(e.store.get(launch.key)).elements.length,1);
});
test("explicit cancel discards session and draft",e=>{
  const {node,launch,ed}=e.open();ed.edit();ed.cancel();e.clock.tick();
  assert.equal(ed.popup.closed,true);assert.equal(e.p.editorTargets.size,0);assert.equal(e.store.has(launch.key),false);assert.equal(e.json(node).elements.length,0);
});
test("closing popup keeps recovery draft and releases watcher",e=>{
  const {launch,ed}=e.open();ed.edit();ed.pagehide();ed.popup.closed=true;e.clock.tick(250);
  assert.equal(e.p.editorTargets.size,0);assert.ok(e.store.has(launch.key));assert.ok(e.store.has("speech_bubble:editor_session:v2:"+launch.key));
});
test("reopening the node recovers the closed draft",e=>{
  const {node,launch,ed}=e.open();ed.edit();ed.pagehide();ed.popup.closed=true;e.clock.tick(250);
  const recovered=e.p.launch(node);assert.equal(recovered.key,launch.key);const second=e.editor(recovered);e.clock.tick();second.save();e.clock.tick(1500);
  assert.equal(e.json(node).elements.length,1);assert.equal(second.popup.closed,true);
});
test("node id reused for another node refuses reconnect",e=>{
  const {ed}=e.open();ed.edit();e.reloadParent();const replacement=e.p.node(7);ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/original node is no longer/);assert.equal(e.json(replacement).elements.length,0);
});
test("external layout change refuses reconnect and keeps draft",e=>{
  const {node,ed,launch}=e.open();ed.edit();e.reloadParent();e.p.nodes.get("7").widgets[0].value='{"elements":[{"id":"external"}]}';ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/node layout changed/);assert.equal(e.json(e.p.nodes.get("7")).elements[0].id,"external");assert.ok(e.store.has(launch.key));
});
test("duplicate request cannot change its immutable payload",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();const request={...ed.pending()};e.clock.tick();
  const session=[...e.p.editorSessions.values()][0],changes=e.p.app.graph.changes;
  e.p.receive({...request,connectionId:session.connectionId,layout_json:'{"elements":[{"id":"tampered"}]}'},ed.popup);
  assert.equal(e.p.app.graph.changes,changes);assert.equal(e.json(node).elements.length,1);
});
test("unknown document acknowledgement cannot close editor",e=>{
  const {ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();
  const request=ed.pending();ed.listeners.get("message")({data:{type:"speech_bubble:layout_applied",key:request.key,connectionId:"old-document",requestId:request.requestId,applied:true},source:ed.opener,origin:"http://verification.invalid"});
  assert.equal(ed.popup.closed,false);
});
test("foreign origin and source cannot apply or acknowledge",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();const request={...ed.pending()},session=[...e.p.editorSessions.values()][0];
  e.p.receive({...request,connectionId:session.connectionId},{closed:false},"http://other.invalid");
  e.p.receive({...request,connectionId:session.connectionId},{closed:false});
  ed.listeners.get("message")({data:{type:"speech_bubble:layout_applied",key:request.key,connectionId:session.connectionId,requestId:request.requestId,applied:true},source:{},origin:"http://verification.invalid"});
  assert.equal(e.json(node).elements.length,0);assert.equal(ed.popup.closed,false);
});
test("expiry refuses reconnect without deleting an open draft",e=>{
  const {ed,launch}=e.open();ed.edit();e.clock.tick(500);ed.pagehide();e.clock.tick();e.clock.skip(24*60*60*1000+1);e.p.pruneEditorRecords();ed.pageshow();e.clock.tick();
  assert.match(ed.status(),/session expired/);assert.ok(e.store.has(launch.key));
});
test("expired closed recovery records are pruned",e=>{
  const {ed,launch}=e.open();ed.edit();ed.pagehide();ed.popup.closed=true;e.clock.tick(250);e.clock.skip(24*60*60*1000+1);e.p.pruneEditorRecords();
  assert.equal(e.store.has(launch.key),false);assert.equal(e.p.storedEditorRecords().length,0);
});
test("recovery records are capped and open sessions are not evicted",e=>{
  for(let i=0;i<18;i++){const {ed}=e.open(i+1);ed.edit();ed.pagehide();ed.popup.closed=true;e.clock.tick(250);}
  assert.ok(e.p.storedEditorRecords().length<=16);
});
test("simultaneous editor limit refuses a seventeenth editor",e=>{
  for(let i=0;i<16;i++)e.open(i+1);
  const node=e.p.node(17);node.editorButton.callback();assert.equal(e.p.editorTargets.size,16);assert.equal(e.p.popups.length,16);assert.equal(e.alerts.length,1);
});
test("reconnection to an already applied request does not overwrite changed node",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();e.clock.tick(1500);node.widgets[0].value='{"elements":[{"id":"external"}]}';ed.options.dropAck=false;ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/node layout changed/);assert.equal(e.json(node).elements[0].id,"external");
});
test("preview failure is visible and retains draft",e=>{
  const {node,ed}=e.open(7,{flushThrows:true});ed.edit();ed.save();e.clock.tick(1500);
  assert.match(ed.status(),/Could not prepare/);assert.equal(e.json(node).elements.length,0);assert.equal(ed.popup.closed,false);
});


test("startup does not overwrite an existing draft before loadState",e=>{
  const {launch,ed}=e.open();e.store.set(launch.key,'{"elements":[{"id":"recovery"}]}');ed.setLoaded(false);
  ed.edit();e.clock.tick(500);ed.save();e.clock.tick();
  assert.equal(JSON.parse(e.store.get(launch.key)).elements[0].id,"recovery");
  assert.match(ed.status(),/not finished loading/);
});


test("late connection reply cannot replace the current saving state",e=>{
  const {ed}=e.open();const oldConnect=e.outbound.find(d=>d.type==="speech_bubble:connect_editor");
  ed.edit();ed.options.dropAck=true;ed.save();e.clock.tick();
  ed.listeners.get("message")({data:{type:"speech_bubble:editor_connected",key:oldConnect.key,connectionId:oldConnect.connectionId,attemptId:oldConnect.attemptId,connected:true,revision:0},source:ed.opener,origin:"http://verification.invalid"});
  assert.equal(ed.elements.get("save").textContent,"Saving…");assert.equal(ed.elements.get("save").disabled,true);
});
test("equal applied revision with another payload is rejected",e=>{
  const {node,ed}=e.open();ed.edit();ed.options.dropAck=true;ed.save();const request={...ed.pending()};e.clock.tick();
  const session=[...e.p.editorSessions.values()][0],changes=e.p.app.graph.changes;
  e.p.receive({...request,connectionId:session.connectionId,requestId:"another-request",layout_json:'{"elements":[{"id":"old"}]}'},ed.popup);
  assert.equal(e.p.app.graph.changes,changes);assert.equal(e.json(node).elements[0].id,"edited-0");
});

console.log("editor save protocol: " + results.length + " cases passed");
