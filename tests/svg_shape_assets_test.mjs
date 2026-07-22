import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = fs.readFileSync(path.join(root,"web","speech-bubble-editor.html"),"utf8");
const start = html.indexOf("function svgPathTokens");
const end = html.indexOf("async function loadBubbleShapeManifest", start);
assert.ok(start >= 0 && end > start);

class FakeNode {
  constructor(name, attrs) { this.nodeName = name; this.attrs = attrs; }
  getAttribute(name) { return this.attrs[name] ?? null; }
}
class DOMParser {
  parseFromString(source) {
    const svgTag = source.match(/<svg\b([^>]*)>/i)?.[1] || "";
    const pathTag = source.match(/<path\b([^>]*)>/i)?.[1] || "";
    const attrs = (tag) => Object.fromEntries([...tag.matchAll(/([:\w-]+)="([^"]*)"/g)].map(match => [match[1],match[2]]));
    const svg = new FakeNode("svg", attrs(svgTag));
    const pathNode = new FakeNode("path", attrs(pathTag));
    return { documentElement: svg, querySelector(selector) { return selector === "#bubble-shape" || selector === "path" ? pathNode : null; } };
  }
}
const context = vm.createContext({ DOMParser, Error, Math, Number, String, RegExp });
vm.runInContext(`${html.slice(start,end)};this.parseSvgBubblePath=parseSvgBubblePath;`, context);

const manifest = JSON.parse(fs.readFileSync(path.join(root,"web","assets","shapes","manifest.json"),"utf8"));
assert.equal(manifest.schemaVersion, 1);
assert.ok(manifest.presets.some(p => p.id === "base-oval-alt" && p.label === "Classic Oval 2"));
assert.equal(new Set(manifest.presets.map(p => p.id)).size, manifest.presets.length);
for (const preset of manifest.presets) {
  if (!preset.svg) continue;
  const svg = fs.readFileSync(path.join(root,"web","assets","shapes",preset.svg),"utf8");
  const points = context.parseSvgBubblePath(svg);
  assert.ok(points.length >= 3, preset.id);
  for (const point of points) for (const key of ["x","y","in_x","in_y","out_x","out_y"]) assert.ok(Number.isFinite(point[key]));
}
assert.ok(html.includes('family==="jagged"'));
assert.ok(html.includes('family==="heart"'));
assert.ok(html.includes('never collapses to an oval'));
console.log("SVG bubble shape assets: pass");
