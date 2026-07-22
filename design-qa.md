# Design QA

- Current workflow: `C:\Users\links\Downloads\Speech Bubble .json`
- Source visual truth: user-provided ComfyUI editor, text-properties, layers, and output screenshots from 2026-07-16
- Render evidence: `D:\Codex\_snapshots\ComfyUI-Speech-Bubble\workflow-qa-20260716\speech-bubble-composite.png`, `seamless-tail-shadow-qa.png`, `preset-style-qa.png`, `reference-comparison-39.png`, `radial-tail-360-qa.png`, `all-23-presets.png`, `outline-styles-qa.png`
- Current source snapshot: `D:\Codex\_snapshots\ComfyUI-Speech-Bubble\before-background-heart-jagged-alt-20260716`
- Canvas: 1024 x 1344; vertical Japanese text; Meiryo 82 px; bold; supersample 2

## Resolved

- Editor and Python renderer now use the same vertical advance, column width, padding, and line-height rules.
- Current workflow renders the bubble and vertical Japanese text at the saved coordinates without image compression.
- Layout saving now waits for acknowledgement from the ComfyUI node before closing the editor.
- Text controls are ordered by task: text, font/size, writing direction, character style, color, then precise transform.
- Writing direction and Bold/Italic/Underline/Strike use visible segmented controls.
- Drop Shadow has its own named panel and remains available whenever a text layer is selected.
- Ctrl-click and Shift-click multi-selection, persistent grouping, grouped move/resize/rotate, and Ctrl+G/Ctrl+Shift+G are implemented.
- Group and Ungroup are positioned above the Layers list. Alt-click isolates one grouped layer; Alt-drag moves it independently and temporarily bypasses its lock.
- The fixed background layer no longer exposes a meaningless lock icon and now has an editor-preview visibility toggle.
- Bubble rotation is supported in both editor preview and Python output.
- Bubble body and tail are rasterized into one union mask before the outer stroke is generated; no internal seam remains for any body shape or tail direction.
- Pointed tails start inside the bubble at its center, widen toward the body, and rotate continuously through 360 degrees from the yellow tip handle without edge snapping.
- Drop Shadow is shared by text and bubble layers, including direction pad, X/Y offset, blur, and color.
- Vector path mode supports anchor selection, point insertion, point deletion, and Bézier control editing.
- The shape drawer closes on canvas/outside clicks; blank canvas clears selection.
- Undo/redo snapshots include multi-selection and group state.
- The shape browser now contains seven visible starting shapes: Classic Oval, Box, Hard Jagged, Soft Burst, Thought Cloud, Heart, and Hexagon.
- Old preset IDs migrate to the nearest of the seven starting shapes while existing saved `path_points` remain unchanged.
- Heart-Shaped now uses a clean six-anchor symmetric Bézier heart.
- Classic Oval and Box share Roundness; Hard Jagged adds Spike Count and Valley Concavity; Thought Cloud adds Cloudiness, Lobe Count, Lobe Depth, and Softness.
- All seven starting shapes support Asymmetry and deterministic Randomize Shape. Non-smooth Shape Intensity and Cloudiness converge to an oval at 0.
- Asymmetry and Randomize now use a stronger nonlinear response and larger per-shape radial/tangent ranges across all seven starting shapes, with self-intersection fallback retained.
- Hard Jagged now offers Sharp / Straight and Curved Inward valley styles. Straight mode uses collapsed handles for fully linear spikes; Curved Inward retains editable concave valleys.
- User shape presets preserve the final Bézier path and shape parameters per ComfyUI user, with User Presets browsing, update/delete, and JSON import/export.
- Browse, Add Text, Randomize, user-preset, and vector-edit controls use restrained role colors that remain consistent with the existing dark UI.
- Transform and Drop Shadow start collapsed and persist the user's open/closed preference in local storage.
- An ungrouped Ctrl/Shift multi-selection is retained when dragging any selected member, so the temporary selection moves together.
- Box now starts with Roundness 0 and Asymmetry 0. Font Size is normalized with floor semantics on load, input, group resize, canvas scaling, preview, and output layout. Text Outline Color is exposed separately from Text Color.
- Text layers now expose Photoshop-style Tracking plus independent horizontal/vertical glyph scale. Ctrl-resize maps side handles to horizontal scale and top/bottom handles to vertical scale while normal resize remains box-only.
- Layer Copy/Paste is available through Ctrl+C/Ctrl+V and the layer `⋮` menu. Multi-layer copies remap IDs and group IDs, unlock pasted copies, and offset repeated pastes without interfering with native copy/paste inside text fields.
- Bubble offscreen render bounds now include sampled Bézier-body extents, preventing left/right clipping when a path extends outside the nominal transform box.
- Redundant oval, box, jagged, cloud, linked, overlapping, line-style-only, and decorated variants are consolidated into seven parameterized starting shapes.
- Deleted preset IDs migrate to the nearest retained preset while preserving saved custom path data.
- Solid, Double, Dashed, and Dotted are selected from Properties > Outline Style rather than occupying shape presets.
- Dashed and Dotted tail edges are drawn before the bubble body so internal tail lines are hidden cleanly.
- Rounded rectangles, squares, and narration boxes are consolidated into Box with Roundness 0-100.
- Search and category filtering use the same preset catalog as insertion and the Properties preset selector.
- Every preset stores editable Bézier path data; legacy shape-only layouts are mapped to the nearest current preset without replacing saved custom paths.
- Thought-dot tails use the standard cloud body plus one smaller circle and one smallest circle in both editor and Python output.
- Dashed whisper/broadcast, dotted, partial, and double robot/voice-over outlines render in both the editor and Python output.
- Frequently Used initially exposes Classic Oval and Box, then shows only the top two starting shapes ranked by local usage count.
- The node editor launch button uses a restrained teal background and border so it reads as the primary action without overpowering the ComfyUI theme.
- The green rotation handle automatically moves to the first visible side when the preferred top position would leave the image canvas; rotation uses pointer-angle deltas so switching sides never changes the layer angle on pointer-down.
- Numeric fields support mouse-wheel adjustment and Shift + wheel for 10x steps; this is documented in the UI and README.
- Dotted outlines are resampled by total arc length instead of restarting spacing on every line segment. Closed-path spacing includes the final-to-first seam.
- Dotted rendering restores the configured bubble fill before repainting the body, preventing the outline color from leaking into the interior.
- Speech Bubble Layer stores queued previews as stable per-node output files, persists their descriptors through `setProperty`, and retries restoration after workflow-tab return, node reconfiguration, canvas redraw, or ComfyUI restart. Live previews use the same restoration path without storing large data URLs in workflow properties.

## Verification

- Editor inline JavaScript syntax: pass.
- ComfyUI extension JavaScript syntax: pass.
- Python AST: pass.
- Current workflow Python render: pass; non-transparent bounds `(695, 0, 1024, 709)`.
- Seamless oval/rounded-rectangle tails and bubble shadow Python render: pass.
- Preset catalog count: pass (7; unique IDs).
- Removed preset aliases: pass (all alias destinations exist in the 7-preset catalog).
- Background visibility save/load and undo snapshot hooks: pass (static validation).
- Alt grouped-layer isolation and lock-bypass drag hooks: pass (static validation).
- Seven-shape morph QA: pass across 7,000 randomized geometries. Finite Bézier coordinates, seed stability at Asymmetry 0, and no anchor self-intersections were validated.
- Strong-asymmetry QA: pass across 7,000 paths at Asymmetry 100. Mean seed-1 anchor deltas were `0.0310-0.1132` across all seven shapes.
- Hard Jagged valley-style QA: pass; Straight has collapsed handles at every anchor and Curved Inward has nonzero valley handles.
- User-preset backend QA: pass for sanitization, per-preset schema, JSON readback, and atomic temporary-file replacement.
- Editor visual QA in the in-app browser: pass at 1280 x 720. Muted role colors, layout, labels, and collapsed accordions render without clipping.
- Accordion persistence browser QA: pass; initial Transform/Drop Shadow state was closed, and Transform remained open after reload once changed by the user.
- Box defaults and text controls QA: pass; new Box layers resolve to Roundness 0 / Asymmetry 0, decimal font sizes floor to whole numbers, and Outline Color is bound to the existing renderer `stroke_color` field.
- Roundness 0/100, Valley Concavity 0/100, Spike Count, and Thought Cloud Lobe Count 5/20 geometry changes: pass.
- Hard Jagged sharp-tip handles remain collapsed while Valley Concavity 100 produces nonzero tangent Bézier handles at each valley: pass.
- Seven new default insertions and representative legacy-ID insertions resolve to valid new starting shapes: pass.
- Uniform dotted spacing: pass in JavaScript and Python on a closed 300 px polygon (11 dots, 27.2727 px spacing, maximum error below `3e-14`).
- Dotted body fill reset before repaint: pass (JavaScript static validation).
- Node preview lifecycle test: pass for persistent descriptor storage through `setProperty`, graph-change notification, cache-busted output URL generation, and reconstructed-node `onConfigure` restoration.
- Persistent preview storage test: pass for stable per-workflow/per-node filenames, atomic PNG replacement, batch descriptor output, and full `SpeechBubbleLayer.execute` integration.
- Typography geometry: pass in the editor and Python renderer for Tracking, independent horizontal/vertical glyph scaling, and vertical-writing spacing.
- Text transform controls: pass; normal handle dragging resizes the text box, while Ctrl/Meta + side or top/bottom handles changes the corresponding glyph scale.
- Layer copy/paste behavior: pass for multi-selection copying, fresh layer IDs, 20 px successive paste offsets, remapped group IDs, unlocked copies, and selection of pasted layers. Focused text fields retain native text copy/paste.
- Preset path validation: pass (7 valid finite paths; clean heart has 6 Bézier anchors; all seven provide parameterized changes).
- Previous preset galleries remain historical evidence; the new seven-shape browser requires the manual pass below.
- Solid, Double, Dashed, and Dotted outline render with pointed tails: pass; no internal tail-edge line remains.
- Thought-dot count: pass (2), with decreasing circle size.
- Thought-dot, dashed-outline, dotted-outline, partial-outline, double-outline, concave-impact, and Rectangle / Square output render: pass.
- Reference comparison board: pass for Classic Manga Vertical, Concave Impact, and Thought Cloud + Two Dots.
- Radial pointed-tail render: pass at 8 angles (45-degree intervals); no detached edge, internal seam, or chipped connection.
- Browser console: no editor JavaScript errors. The isolated static QA server produced only the expected missing-ComfyUI-API warning for `/speech_bubble/presets`; the backend route was verified separately.

## Manual pass after ComfyUI restart

1. Open the editor and confirm the existing workflow visually matches the queued output.
2. Toggle the Background Image eye icon and confirm the canvas checkerboard appears; confirm that no background lock icon is shown.
3. Ctrl-click or Shift-click three ungrouped layers and drag any selected member; confirm all three move together. Then Group, lock one member, and Alt-drag it to confirm only that member moves.
4. Test Classic Oval and Box Roundness at 0/50/100. Confirm both can move between box and oval while remaining separately visible as starting presets.
5. Test both Hard Jagged Valley Styles, Valley Concavity 0/50/100, and several Spike Count values. Confirm the straight style is sharply linear and the curved style has inward valleys without self-intersection.
6. Test Thought Cloud Cloudiness, Lobe Count, Lobe Depth, Softness, and the yellow thought-dot handle.
7. Test Asymmetry 0/100 and Randomize twice on every starting shape.
8. Edit Path, move an anchor outside the transform box, and confirm the left/right outline is not clipped.
9. Save Layout and Queue once; confirm the editor closes only after the node updates.
10. Save one edited shape as a User Preset, reopen it from the User Presets category, update it, and test JSON export/import.
11. Queue Speech Bubble Layer once, switch to another workflow tab and back, then restart ComfyUI. Confirm the queued preview returns both times without another Queue.

final result: passed
