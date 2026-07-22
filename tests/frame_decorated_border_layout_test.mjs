import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync(new URL("../web/speech-bubble-editor.html", import.meta.url), "utf8");
const start = html.indexOf("function decoratedBorderLayout");
const end = html.indexOf("function drawPatternedRoundedRect", start);
assert.ok(start >= 0 && end > start);
const source = html.slice(start, end);
const context = vm.createContext({
  finiteOr: (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback,
});
vm.runInContext(`${source};this.decoratedBorderLayout=decoratedBorderLayout;`, context);

const sizes = {
  corner_tl:[420,420], corner_tr:[420,420], corner_bl:[420,420], corner_br:[420,420],
  bunny:[320,320], cat:[320,320], bear:[320,320], mouse:[320,320], dog:[320,320],
  flowers:[300,260], stars:[300,260],
};
const sequences = {
  top:["bunny","flowers","cat","stars","bear"],
  bottom:["mouse","stars","dog","flowers","bunny"],
  left:["cat","flowers","bunny","stars","mouse"],
  right:["dog","stars","mouse","flowers","cat"],
};
for (const [width,height] of [[832,1216],[1024,1024],[1024,1536]]) {
  const placements = context.decoratedBorderLayout(width,height,sizes,sequences,Math.min(width,height)/1024*.28,{corner_scale:1,edge_scale:.72});
  assert.equal(placements.filter(p => p[0].startsWith("corner_")).length, 4);
  assert.ok(placements.length > 8);
  for (const [key,x,y,w,h] of placements) {
    assert.ok(x >= -1e-6 && y >= -1e-6);
    assert.ok(x+w <= width+1e-6 && y+h <= height+1e-6);
    assert.ok(Math.abs(w/h - sizes[key][0]/sizes[key][1]) < 1e-9);
  }
}
assert.ok(html.includes('mode==="decorated-border"'));
assert.ok(html.includes("drawDecoratedBorderFrameAsset"));
assert.ok(html.includes("drawProceduralBaseBorder"));
console.log("frame decorated-border browser layout: pass");
