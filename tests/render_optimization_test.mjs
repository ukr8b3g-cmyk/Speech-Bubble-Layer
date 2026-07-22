import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync(new URL("../web/speech-bubble-editor.html", import.meta.url), "utf8");
const functionBody = (name, nextName) => {
  const start = html.indexOf(`function ${name}`);
  const end = html.indexOf(`function ${nextName}`, start + 1);
  assert.ok(start >= 0 && end > start, `${name} must exist before ${nextName}`);
  return html.slice(start, end);
};

const bitmap = functionBody("ensureCanvasBitmapSize", "updateCanvasViewportSize");
assert.match(bitmap, /canvas\.width!==state\.width/);
assert.match(bitmap, /canvas\.height!==state\.height/);

assert.match(html, /function requestRender\(options=\{canvas:true,layers:false,preview:false\}\)/);
assert.match(html, /requestAnimationFrame/);
assert.match(html, /MAX_FRAME_SURFACE_CACHE = 32/);
assert.match(html, /MAX_TINTED_FRAME_CACHE = 24/);
assert.match(html, /const livePreviewCanvas = document\.createElement\("canvas"\)/);
const livePreview = functionBody("scheduleLivePreview", "drawSelection");
assert.match(livePreview, /revision!==renderRevision/);
assert.match(livePreview, /updateLivePreviewCanvas\(\)/);
assert.match(livePreview, /\},280\)/);

const pointerMoveStart = html.indexOf('canvas.addEventListener("pointermove"');
const pointerMoveEnd = html.indexOf("function endPointer", pointerMoveStart);
const pointerMove = html.slice(pointerMoveStart, pointerMoveEnd);
assert.match(pointerMove, /requestRender\(\{canvas:true\}\)/);
assert.doesNotMatch(pointerMove, /refreshLayers\(/);
assert.doesNotMatch(pointerMove, /preview:true/);

const endPointerStart = html.indexOf("function endPointer");
const endPointer = html.slice(endPointerStart, html.indexOf('canvas.addEventListener("pointerup"', endPointerStart));
assert.match(endPointer, /layers:true,preview:true/);

const propertiesInputStart = html.indexOf('properties.addEventListener("input"');
const propertiesInput = html.slice(propertiesInputStart, html.indexOf('document.getElementById("copyLayer")', propertiesInputStart));
assert.match(propertiesInput, /requestRender\(\{canvas:true\}\)/);
assert.doesNotMatch(propertiesInput, /preview:true/);

const frameKey = functionBody("frameSurfaceCacheKey", "buildFrameSurface");
assert.doesNotMatch(frameKey, /item\.x|item\.y|item\.rotation|item\.opacity/);

const openFrameBrowser = functionBody("openFrameBrowser", "filterSfxCards");
assert.doesNotMatch(openFrameBrowser, /requestRender\(|render\(\)/);

console.log("Speech Bubble render optimization tests passed.");
