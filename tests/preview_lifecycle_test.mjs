import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

let extension;
const windowListeners = new Map();
const popup = { closed: false };
const mockWindow = {
  addEventListener(type, callback) { windowListeners.set(type, callback); },
  setTimeout(callback) { callback(); },
  setInterval() { return 1; },
  clearInterval() {},
  open(url) { this.lastOpen = url; return popup; },
};
const app = {
  graph: { setDirtyCanvas() {}, links: {}, getNodeById() {} },
  registerExtension(value) { extension = value; },
};
const api = { apiURL: (path) => `/base${path}` };
class MockImage {
  set src(value) {
    this._src = value;
    queueMicrotask(() => this.onload?.());
  }
  get src() { return this._src; }
}
const context = vm.createContext({
  app,
  api,
  Image: MockImage,
  URLSearchParams,
  console,
  localStorage: { getItem: () => null, setItem() {} },
  queueMicrotask,
  window: mockWindow,
});
const sourcePath = new URL("../web/js/speech_bubble.js", import.meta.url);
const source = fs.readFileSync(sourcePath, "utf8").replace(/^import .*;\r?\n/gm, "");
vm.runInContext(source, context, { filename: "speech_bubble.js" });
assert.match(source, /function clearPreview\(node, options = \{\}\)/);
assert.match(source, /clearPreview\(node, \{ clearPersistent: true \}\)/);
assert.match(source, /applyLayout\(node, data\.layout_json \|\| \"\{\}\", data\.preview_data_url \|\| \"\"\s*,\s*data\.revision\)/);
assert.match(source, /else if \(inputSource\) showCurrentInputPreview\(this, inputSource\)/);
assert.match(source, /speech_bubble:cancel_editor/);
assert.match(source, /PREVIEW_DATA_PROPERTY/);
assert.match(source, /PREVIEW_LAYOUT_PROPERTY/);
assert.match(source, /PREVIEW_REVISION_PROPERTY/);
assert.match(source, /acceptPreviewRevision/);
assert.match(source, /data\.revision/);
assert.match(source, /revisionBase/);
assert.match(source, /_speechBubblePreviewLoadGeneration/);
assert.doesNotMatch(source, /live_preview" && data\.preview_data_url\) \{\s*restorePreview\(node, setPreviewSources/);

function NodeType() {
  this.widgets = [];
  this.properties = {};
  this.graph = {
    changes: 0,
    change() { this.changes += 1; },
    setDirtyCanvas() {},
  };
  this.size = [470, 500];
}
NodeType.prototype.addWidget = function (type, name, value, callback, options = {}) {
  const widget = { type, name, value, callback, options };
  this.widgets.push(widget);
  if (name === "Open Speech Bubble Editor") this.editorButton = widget;
  return widget;
};
NodeType.prototype.setSize = function () {};
NodeType.prototype.setDirtyCanvas = function () {};
NodeType.prototype.setProperty = function (name, value) { this.properties[name] = value; };

await extension.beforeRegisterNodeDef(NodeType, { name: "SpeechBubbleLayer" });
const preview = {
  filename: "speech_bubble_2_0.png",
  subfolder: "speech_bubble_preview",
  type: "output",
  cache_key: "123",
};
const original = new NodeType();
original.onNodeCreated();
const buttonDraws = [];
original.editorButton.draw({
  save() {}, beginPath() {}, roundRect() {}, restore() {},
  fill() { buttonDraws.push(["fill", this.fillStyle]); },
  stroke() { buttonDraws.push(["stroke", this.strokeStyle]); },
  fillText(text) { buttonDraws.push(["text", text, this.fillStyle]); },
}, original, 470, 90, 24);
assert.deepEqual(buttonDraws[0], ["fill", "#244b49"]);
assert.deepEqual(buttonDraws[1], ["stroke", "#5f8b86"]);
assert.deepEqual(buttonDraws[2], ["text", "Open Speech Bubble Editor", "#e5f4f1"]);
original.onExecuted({ images: [preview] });
await new Promise((resolve) => setImmediate(resolve));

assert.equal(
  JSON.stringify(original.properties.speech_bubble_preview_images),
  JSON.stringify([preview]),
);
assert.equal(original.graph.changes, 1);
assert.equal(original.properties.speech_bubble_preview_layout, "{}");
assert.equal(original.imgs.length, 1);
assert.match(original.imgs[0].src, /type=output/);
assert.match(original.imgs[0].src, /speech_bubble_cache=123/);

const serialized = JSON.parse(JSON.stringify({ properties: original.properties }));
const restored = new NodeType();
restored.onNodeCreated();
restored.onConfigure(serialized);
await new Promise((resolve) => setImmediate(resolve));

assert.equal(restored.imgs.length, 1);
assert.equal(restored.images[0].type, "output");
assert.equal(restored.properties.speech_bubble_preview_images[0].filename, preview.filename);
assert.match(restored.imgs[0].src, /speech_bubble_cache=restore-/);
assert.doesNotMatch(restored.imgs[0].src, /speech_bubble_cache=123/);

const loadImage = { id: "load-image", type: "LoadImage", widgets: [{ name: "image", value: "current.png" }] };
app.graph.links[1] = { origin_id: "load-image" };
app.graph.getNodeById = (id) => id === "load-image" ? loadImage : undefined;
const currentInputNode = new NodeType();
currentInputNode.id = 2;
currentInputNode.inputs = [{ name: "image", link: 1 }];
currentInputNode.onNodeCreated();
currentInputNode.onConfigure({
  properties: {
    speech_bubble_preview_images: [preview],
    speech_bubble_preview_input: "/base/view?filename=old.png&type=input",
  },
});
await new Promise((resolve) => setImmediate(resolve));
assert.match(currentInputNode.imgs[0].src, /filename=current.png/);
assert.match(currentInputNode.imgs[0].src, /speech_bubble_input_cache=/);
assert.doesNotMatch(currentInputNode.imgs[0].src, /speech_bubble_cache=restore-/);

const editable = new NodeType();
editable.id = 7;
editable.widgets.push({ name: "layout_json", value: '{"version":1,"elements":[{"id":"saved"}]}' });
editable.widgets.push({ name: "preview_key", value: "sb-test" });
editable.onNodeCreated();
editable.onExecuted({ images: [preview] });
await new Promise((resolve) => setImmediate(resolve));
editable.editorButton.callback();
const editorUrl = new URL(mockWindow.lastOpen, "http://localhost");
const editorKey = editorUrl.searchParams.get("jsonKey");
assert.ok(Number(editorUrl.searchParams.get("revisionBase")) >= 1);
const messageHandler = windowListeners.get("message");
messageHandler({ data: { type: "speech_bubble:live_preview", key: editorKey, revision: 2, preview_data_url: "data:image/png;base64,LIVE-2" } });
messageHandler({ data: { type: "speech_bubble:live_preview", key: editorKey, revision: 1, preview_data_url: "data:image/png;base64,LIVE-1" } });
await new Promise((resolve) => setImmediate(resolve));
assert.equal(editable.imgs[0].src, "data:image/png;base64,LIVE-2");
messageHandler({ data: { type: "speech_bubble:cancel_editor", key: editorKey } });
await new Promise((resolve) => setImmediate(resolve));
assert.match(editable.imgs[0].src, /speech_bubble_2_0\.png/);

editable.editorButton.callback();
const saveKey = new URL(mockWindow.lastOpen, "http://localhost").searchParams.get("jsonKey");
const emptyLayout = '{"version":1,"elements":[]}';
messageHandler({
  data: { type: "speech_bubble:set_layout_json", key: saveKey, revision: 6, layout_json: emptyLayout, preview_data_url: "data:image/png;base64,SAVED" },
  source: { postMessage() {} },
  origin: "http://localhost",
});
await new Promise((resolve) => setImmediate(resolve));
assert.equal(editable.widgets.find((widget) => widget.name === "layout_json").value, emptyLayout);
assert.equal(editable.properties.speech_bubble_saved_preview, "data:image/png;base64,SAVED");
assert.equal(editable.properties.speech_bubble_preview_layout, emptyLayout);
assert.equal(JSON.stringify(editable.properties.speech_bubble_preview_images), "[]");
assert.equal(editable.properties.speech_bubble_preview_revision, 6);

editable.editorButton.callback();
const staleSaveKey = new URL(mockWindow.lastOpen, "http://localhost").searchParams.get("jsonKey");
messageHandler({
  data: { type: "speech_bubble:set_layout_json", key: staleSaveKey, revision: 5, layout_json: '{"version":1,"elements":[{"id":"stale"}]}', preview_data_url: "data:image/png;base64,STALE" },
  source: { postMessage() {} },
  origin: "http://localhost",
});
assert.equal(editable.widgets.find((widget) => widget.name === "layout_json").value, emptyLayout);
assert.equal(editable.properties.speech_bubble_saved_preview, "data:image/png;base64,SAVED");
assert.equal(editable.properties.speech_bubble_preview_revision, 6);

const savedProperties = JSON.parse(JSON.stringify(editable.properties));
const savedRestored = new NodeType();
savedRestored.widgets.push({ name: "layout_json", value: emptyLayout });
savedRestored.widgets.push({ name: "preview_key", value: "sb-test-restored" });
savedRestored.onNodeCreated();
savedRestored.onConfigure({ properties: savedProperties });
await new Promise((resolve) => setImmediate(resolve));
assert.equal(savedRestored.imgs[0].src, "data:image/png;base64,SAVED");

const stale = new NodeType();
stale.widgets.push({ name: "layout_json", value: emptyLayout });
stale.widgets.push({ name: "preview_key", value: "sb-test-stale" });
stale.onNodeCreated();
stale.onConfigure({ properties: {
  speech_bubble_preview_images: [preview],
  speech_bubble_preview_layout: '{"version":1,"elements":[{"id":"old"}]}',
} });
await new Promise((resolve) => setImmediate(resolve));
assert.ok(!stale.imgs?.length);

console.log("preview lifecycle: pass");
