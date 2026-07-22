# ComfyUI Speech Bubble — Complete Fixed Build

This build is based on `ComfyUI-Speech-Bubble(5).zip` and includes the requested frame, preview, and speech-bubble shape updates.

## Installation

1. Stop ComfyUI.
2. Back up the existing `custom_nodes/ComfyUI-Speech-Bubble` folder.
3. Replace it with this folder.
4. Start ComfyUI and perform a browser hard refresh.

## Implemented

- `edge-repeat` rendering in both the browser editor and Python/Pillow output.
- `decorated-border` rendering with one continuous procedural border and independent corner/edge decorations.
- Automatic frame discovery from `web/assets/frames/*/manifest.json`.
- Part-only frame assets; `runtimeAsset` is optional for `edge-repeat` and `decorated-border`.
- `preview` / `preview.webp` support for frame cards.
- SVG-backed built-in speech-bubble shapes.
- Added `Classic Oval 2`.
- Thinking Cloud and other manifest-defined speech-bubble shapes.
- Heart tuning remains within the heart family instead of morphing to a circle/oval.
- Preview generation ordering and stale asynchronous preview-load protection.
- Editor revision numbers continue across reopened editor sessions.
- Included `Pop Animal Decorated Border` sample asset.

## Add a frame asset

Place a folder containing `manifest.json` under:

```text
web/assets/frames/<frame_id>/
```

Restart ComfyUI. No JavaScript or Python registration is required for supported render modes:

- `nine-slice`
- `full-overlay`
- `edge-repeat`
- `decorated-border`

See `web/assets/frames/README.md` and the included sample manifest.
