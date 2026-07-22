import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = fs.readFileSync(path.join(root, "web", "speech-bubble-editor.html"), "utf8");
const source = html.match(/^\s*function edgeRepeatLayout[^\n]+/m)?.[0];
assert.ok(source, "edgeRepeatLayout must remain directly testable");

const context = vm.createContext({
  finiteOr: (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback,
});
vm.runInContext(`${source};this.edgeRepeatLayout=edgeRepeatLayout;`, context);

const partSizes = {
  corner_tl:[320,320], corner_tr:[320,320], corner_bl:[320,320], corner_br:[320,320],
  edge_top:[220,320], edge_bottom:[220,320], edge_left:[320,220], edge_right:[320,220],
};
const cases = [
  [832,1216,{edge_top:13,edge_bottom:13,edge_left:21,edge_right:21}],
  [1024,1024,{edge_top:13,edge_bottom:13,edge_left:13,edge_right:13}],
  [1024,1536,{edge_top:13,edge_bottom:13,edge_left:22,edge_right:22}],
];
for (const [width,height,expected] of cases) {
  const scale = Math.min(width,height) / 1024 * .28;
  const placements = context.edgeRepeatLayout(width,height,partSizes,scale,{minimum_tiles:1,maximum_tiles:64});
  for (const [edge,count] of Object.entries(expected)) {
    assert.equal(placements.filter(placement => placement[0] === edge).length, count);
  }
}

const limited = context.edgeRepeatLayout(1024,1536,partSizes,.28,{minimum_tiles:1,maximum_tiles:2});
for (const edge of ["edge_top","edge_bottom","edge_left","edge_right"]) {
  assert.ok(limited.filter(placement => placement[0] === edge).length <= 2);
}

console.log("frame edge-repeat browser layout: pass");
