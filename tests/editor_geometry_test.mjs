import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync(new URL("../web/speech-bubble-editor.html", import.meta.url), "utf8");
assert.ok(html.includes('id="quickStamps"'));
assert.ok(html.includes('id="openStampDrawer"'));
assert.ok(html.includes("function isComicStamp"));
assert.ok(html.includes("function insertBubbleBelowText"));
assert.ok(html.includes('state.elements.splice(firstTextIndex,0,item)'));
assert.ok(html.includes('function insertSfx(presetId,point=null)'));
assert.ok(html.includes("repeat(auto-fit,minmax(82px,1fr))"));
assert.ok(html.includes("aspect-ratio:1"));
for (const id of ["aha-small-tsu-mask", "hachun-small-tsu-mask", "n-small-tsu-ellipsis-mask", "u-small-tsu-ellipsis-mask", "iccha-mask", "ii-small-tsu-mask", "uwaaa-small-tsu-mask", "oo-dakuten-small-tsu-mask", "iguuu-mask", "gori-small-tsu-mask", "deru-small-tsu-mask", "uguuu-ellipsis-mask", "au-small-tsu-mask", "kaha-small-tsu-mask", "igu-small-tsu-mask", "tehepero-mask", "iee-small-tsu-mask", "oke-mask", "damee-mask", "u-dakuten-long-small-tsu-mask", "moo-long-small-tsu-mask", "e-small-tsu-question-mask", "yadaa-mask", "jaan-mask"]) {
  const marker = `id:"${id}",label:`;
  const start = html.indexOf(marker);
  const end = html.indexOf("\n", start);
  assert.ok(start >= 0 && end > start);
  assert.ok(html.slice(start, end).includes('fill:"#ffd42a"'));
}
const start = html.indexOf("function rotateAround");
const end = html.indexOf("function findHandle", start);
assert.ok(start >= 0 && end > start);
const context = vm.createContext({ state: { width: 1024, height: 768, zoom: 1 } });
vm.runInContext(`${html.slice(start, end)};this.geometry=rotationHandleGeometry;this.resizedEdges=resizedEdges;`, context);

const centered = context.geometry({ x: 300, y: 200, w: 240, h: 140, rotation: 0 });
assert.equal(centered.side, "top");
assert.ok(centered.handle.y > 0);

const topEdge = context.geometry({ x: 300, y: 0, w: 240, h: 140, rotation: 0 });
assert.equal(topEdge.side, "bottom");
assert.ok(topEdge.handle.y < context.state.height);

const bottomEdge = context.geometry({ x: 300, y: 650, w: 240, h: 118, rotation: 0 });
assert.equal(bottomEdge.side, "top");
assert.ok(bottomEdge.handle.y > 0);

const locked = context.resizedEdges({ handle:"se", left:100, right:300, top:50, bottom:150, originalW:200, originalH:100 }, { x:420, y:180 }, true);
assert.equal(Math.round(Math.abs(locked.right-locked.left) / Math.abs(locked.bottom-locked.top) * 1000), 2000);
assert.equal(locked.left, 100);
assert.equal(locked.top, 50);

const free = context.resizedEdges({ handle:"se", left:100, right:300, top:50, bottom:150, originalW:200, originalH:100 }, { x:420, y:180 }, false);
assert.equal(free.right, 420);
assert.equal(free.bottom, 180);

const crossed = context.resizedEdges({ handle:"nw", left:100, right:300, top:50, bottom:150, originalW:200, originalH:100 }, { x:380, y:190 }, true);
assert.ok(crossed.left > crossed.right);
assert.ok(crossed.top > crossed.bottom);
assert.equal(Math.round(Math.abs(crossed.right-crossed.left) / Math.abs(crossed.bottom-crossed.top) * 1000), 2000);

const numericStart = html.indexOf("const rangeSpecs");
const numericEnd = html.indexOf("function enhanceNumericInputs", numericStart);
const trackingValueStart = html.indexOf("function finiteOr");
const trackingValueEnd = html.indexOf("function storedStringList", trackingValueStart);
assert.ok(trackingValueStart >= 0 && trackingValueEnd > trackingValueStart);
assert.ok(numericStart >= 0 && numericEnd > numericStart);
const numericContext = vm.createContext({});
vm.runInContext(`${html.slice(trackingValueStart, trackingValueEnd)}${html.slice(numericStart, numericEnd)};this.normalizeNumericValue=normalizeNumericValue;this.numericDisplayValue=numericDisplayValue;this.numericPropertyValue=numericPropertyValue;this.normalizeItemNumericValues=normalizeItemNumericValues;`, numericContext);
assert.equal(numericContext.normalizeNumericValue("stroke_width", -29, 3), 0);
assert.equal(numericContext.normalizeNumericValue("stroke_width", 1.5500000000000005, 3), 1.5);
assert.equal(numericContext.numericDisplayValue("stroke_width", 1.5500000000000005, 3), "1.5");
assert.equal(numericContext.normalizeNumericValue("opacity", 1.55, 1), 1);
assert.equal(numericContext.normalizeNumericValue("x", -29, 0), -29);
assert.equal(numericContext.normalizeNumericValue("w", -29, 100), 1);
assert.equal(numericContext.numericPropertyValue("font_scale_y", "1", 100, false), 1);
assert.equal(numericContext.numericPropertyValue("font_scale_y", "10", 100, false), 10);
assert.equal(numericContext.numericPropertyValue("font_scale_y", "100", 100, false), 100);
assert.equal(numericContext.numericPropertyValue("font_scale_y", "100", 100, true), 100);
assert.equal(numericContext.numericPropertyValue("font_scale_y", "1000", 100, true), 500);
const legacyValues = numericContext.normalizeItemNumericValues({ x:-24, w:-90, stroke_width:-29, opacity:1.5500000000000005 });
assert.equal(legacyValues.x, -24);
assert.equal(legacyValues.w, 1);
assert.equal(legacyValues.stroke_width, 0);
assert.equal(legacyValues.opacity, 1);
assert.equal(numericContext.normalizeNumericValue("tracking", -250, 0), -200);
assert.equal(numericContext.normalizeNumericValue("tracking", 503, 0), 500);
assert.equal(numericContext.normalizeNumericValue("tracking", 12, 0), 12);
assert.ok(html.includes('文字間隔 (Tracking)'));
assert.ok(html.includes('1/1000 em'));
assert.ok(html.includes('delete item.letter_spacing'));
assert.ok(html.includes('properties.addEventListener("focusin"'));
const trackingStart = html.indexOf("function trackingPixels");
const trackingEnd = html.indexOf("function tailTip", trackingStart);
assert.ok(trackingStart >= 0 && trackingEnd > trackingStart);
const trackingContext = vm.createContext({
  ctx:{
    font:"",
    save(){},
    restore(){},
    measureText(text){return { width:text==="AV"?18:[...String(text)].length*10 };},
  },
  integerFontSize:value=>Math.max(1,Math.floor(Number(value)||48)),
  fontScaleFactor:(item,key)=>Math.max(.1,Math.min(5,(Number(item?.[key])||100)/100)),
  trackingValue:value=>Math.max(-200,Math.min(500,Math.round(Number(value)||0))),
  textPadding:()=>4,
});
vm.runInContext(`${html.slice(trackingStart, trackingEnd)};this.measureTrackedText=measureTrackedText;this.textContentSize=textContentSize;this.fitTextBox=fitTextBox;`, trackingContext);
assert.equal(trackingContext.measureTrackedText("AV", 0), 18);
assert.equal(trackingContext.measureTrackedText("AB", -5), 15);
assert.equal(trackingContext.measureTrackedText("AB", 5), 25);
assert.equal(trackingContext.measureTrackedText("A", 50), 10);
const horizontal = { type:"text", text:"AB", writing:"horizontal", font_size:100, tracking:100, font_scale_x:100, font_scale_y:100, x:100, y:80, w:80, h:40 };
const oldCenter = [horizontal.x+horizontal.w/2, horizontal.y+horizontal.h/2];
trackingContext.fitTextBox(horizontal, true);
assert.deepEqual([horizontal.x+horizontal.w/2, horizontal.y+horizontal.h/2], oldCenter);
assert.equal(horizontal.font_scale_x, 100);
assert.equal(horizontal.font_scale_y, 100);
const verticalBase = trackingContext.textContentSize({ ...horizontal, text:"ABC", writing:"vertical-rl", tracking:0 });
const verticalSpaced = trackingContext.textContentSize({ ...horizontal, text:"ABC", writing:"vertical-rl", tracking:100 });
assert.equal(verticalSpaced.w, verticalBase.w);
assert.ok(verticalSpaced.h > verticalBase.h);
assert.ok(!html.includes('id:"base-melting"'));
assert.ok(!html.includes('id:"base-hexagon"'));
assert.ok(html.includes('function meltingPath(intensity=0)'));
assert.ok(html.includes('"base-melting":{family:"special",intensity:0'));
assert.ok(html.includes('resizedEdges(d,local,isFixedPathItem(d.item)||!event.shiftKey)'));
assert.ok(html.includes('originalW:d.bounds.w,originalH:d.bounds.h},p,!event.shiftKey'));
assert.ok(html.includes('/speech_bubble/frame-assets'));
assert.ok(!html.includes('id:"pop-animal-parade-frame-v1"'));
assert.ok(html.includes('value.renderMode'));
assert.ok(html.includes('function edgeRepeatLayout'));
assert.ok(html.includes('function drawEdgeRepeatFrameAsset'));
assert.ok(html.includes('preset.frame_layout'));
assert.ok(!html.includes('id:"base-shoujo-aura"'));
assert.ok(html.includes('.drawer .palette { grid-template-columns:repeat(auto-fill,var(--drawer-card-width)); grid-auto-rows:var(--drawer-card-width);'));
assert.ok(html.includes('.drawer .sfx-card { min-height:0; gap:3px; padding:4px 6px;'));
assert.ok(html.includes('const probe=document.createElement("canvas"),probeSize=128'));
assert.ok(html.includes('#quickShapes,#quickSfx,#quickStamps,#quickFrames,#quickEmphasisLines { grid-template-columns:repeat(2,minmax(0,1fr)); }'));
assert.ok(html.includes('key==="t"'));
assert.ok(html.includes('const DRAWER_MIN_WIDTH = 224'));
assert.ok(html.includes('data-key="opacity"'));
assert.ok(html.includes('ctx.globalAlpha=Math.max(0,Math.min(1,finiteOr(item.opacity,1)))'));
assert.ok(html.includes('const COMIC_YELLOW = "#ffd42a"'));
assert.ok(html.includes('const SFX_ASSET_VERSION = "20260723-01"'));
assert.ok(html.includes('id="quickFrames"'));
assert.ok(html.includes('id="openFrameDrawer"'));
assert.ok(html.includes('id="frameDrawer"'));
assert.ok(html.includes('id="frameProps"'));
assert.ok(html.includes('data-key="border_width_x"'));
assert.ok(html.includes('data-key="border_width_y"'));
assert.ok(!html.includes('data-key="corner_radius"'));
assert.ok(!html.includes('id:"rounded-frame"'));
assert.ok(!html.includes('id:"rounded-black"'));
assert.ok(html.includes('function defaultFrame'));
assert.ok(html.includes('function insertFrame'));
assert.ok(html.includes('function drawFrame'));
assert.ok(html.includes('payload.kind==="frame"'));
assert.ok(html.includes('original.item.type==="frame"') && html.includes('fit_to_canvas=false'));
assert.ok(!html.includes('id="editFrame"'));
assert.ok(!html.includes('id="editFrameGlobal"'));
assert.ok(!html.includes('frameEditId'));
assert.ok(html.includes('function canvasItemEditable'));
assert.ok(html.includes('function canvasHitEnabled'));
assert.ok(html.includes('!canvasHitEnabled(e)'));
assert.ok(html.includes('function isFrameSelected'));
assert.ok(html.includes('function findFrameMoveHandle'));
assert.ok(html.includes('frameMoveHandleHit'));
assert.ok(html.includes('id="deleteFrameBtn"'));
assert.ok(html.includes('function deleteSelectedFrame'));
assert.ok(html.includes('deleteFrameBtn.disabled=!isFrameSelected(item)'));
assert.ok(html.includes('function canvasHitEnabled(item){return Boolean(item)&&item.type!=="frame"&&item.type!=="emphasis_lines";}'));
const frameStateStart = html.indexOf("function isFrameSelected");
const frameStateEnd = html.indexOf("function setSelection", frameStateStart);
assert.ok(frameStateStart >= 0 && frameStateEnd > frameStateStart);
const frameStateContext = vm.createContext({ state:{ selection:["frame-1"] } });
vm.runInContext(`${html.slice(frameStateStart, frameStateEnd)};this.isFrameSelected=isFrameSelected;this.canvasItemEditable=canvasItemEditable;this.canvasHitEnabled=canvasHitEnabled;`, frameStateContext);
const frameItem = { id:"frame-1", type:"frame", locked:false };
assert.equal(frameStateContext.isFrameSelected(frameItem), true);
assert.equal(frameStateContext.canvasItemEditable(frameItem), true);
assert.equal(frameStateContext.canvasHitEnabled(frameItem), false);
frameStateContext.state.selection = ["other"];
assert.equal(frameStateContext.isFrameSelected(frameItem), false);
assert.equal(frameStateContext.canvasItemEditable(frameItem), false);
frameStateContext.state.selection = ["frame-1"];
frameItem.locked = true;
assert.equal(frameStateContext.isFrameSelected(frameItem), false);
assert.equal(frameStateContext.canvasItemEditable(frameItem), false);
assert.equal(frameStateContext.canvasHitEnabled({ id:"text-1", type:"text", locked:false }), true);
assert.ok(html.includes('id="sfxSort"'));
for (const mode of ["recommended", "usage", "name"]) assert.ok(html.includes(`<option value="${mode}">`));
assert.ok(html.includes('const SFX_SORT_KEY = "speech_bubble:sfx_sort:v1"'));
assert.ok(html.includes("function sortedSfxPresets"));
assert.ok(html.includes('preset.id==="don-exclamation-mask"'));
assert.ok(html.includes("Number(preset.sortGroup)"));
assert.ok(html.includes("Number(preset.sortRank)"));
assert.ok(html.includes('id="sfxColorSwatches"'));
assert.ok(html.includes("const COMIC_SWATCHES"));
assert.ok(html.includes("function initializeSfxSwatches"));
assert.ok(html.includes("function updateSfxSwatches"));
assert.ok(html.includes("function sfxDefaultOutlineWidth"));
assert.ok(html.includes('id:"sweat-glossy"'));
assert.ok(html.includes('id:"sweat-flying"'));
for (const id of ["sweat-drop-mask", "sweat-drops-mask"]) {
  const marker = `id:"${id}",label:`;
  const start = html.indexOf(marker);
  const end = html.indexOf("\n", start);
  assert.ok(start >= 0 && html.slice(start, end).includes("hidden:true"));
}
assert.ok(html.includes('id:"giri-small-tsu-vertical-mask"'));
assert.ok(html.includes('id:"nuron-angular-vertical-mask"'));
assert.ok(html.includes('id:"dokun-hiragana-angular-vertical-mask"'));
assert.ok(html.includes('id:"dokun-hiragana-angular-horizontal-mask"'));
assert.ok(html.includes('id:"zubu-small-tsu-angular-vertical-mask"'));
assert.ok(html.includes('id:"handdrawn-filled-heart-mask"'));
assert.ok(!html.includes('<option value="dashed">'));
assert.ok(!html.includes('<option value="dotted">'));
assert.ok(html.includes("let hasElementList = false"));
assert.ok(html.includes("if (!hasElementList)"));
assert.ok(!html.includes("if (!state.elements.length)"));
assert.ok(html.includes('type:"speech_bubble:cancel_editor"'));
assert.ok(html.includes('window.addEventListener("pagehide"'));
assert.ok(html.includes('id="frameAttachedDecorationList"'));
assert.ok(html.includes("function drawAttachedFrameDecorations"));
assert.ok(html.includes("function syncFrameAttachedDecorationControls"));
const propertiesDockIndex = html.indexOf('id="propertiesDock"');
const dividerIndex = html.indexOf('id="rightDockDivider"');
const layersDockIndex = html.indexOf('id="layersDock"');
const layersIndex = html.indexOf('id="layers"');
assert.ok(propertiesDockIndex >= 0 && propertiesDockIndex < dividerIndex);
assert.ok(dividerIndex < layersDockIndex && layersDockIndex < layersIndex);
assert.ok(html.includes('const RIGHT_DOCK_SPLIT_KEY="speech_bubble:right_dock_split:v4"'));
assert.ok(html.includes('id="propertiesDockToggle"'));
assert.ok(html.includes('id="layersDockToggle"'));
assert.ok(html.includes('propertiesDockCollapsed'));
assert.ok(html.includes('layersDockCollapsed'));
assert.ok(html.includes('let ratio=.64'));
assert.ok(html.includes("function initializeRightDockResize"));
assert.ok(html.includes("initializeRightDockResize();enhanceNumericInputs()"));

console.log("editor geometry and numeric input constraints: pass");
