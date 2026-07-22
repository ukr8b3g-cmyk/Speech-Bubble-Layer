# Speech-bubble shape packages

Put one shape pack under `web/assets/shapes/<pack-id>/`:

```text
my-dialogue-shapes/
├─ manifest.json
├─ preview.webp
└─ cloud.svg
```

```json
{
  "schemaVersion": 1,
  "id": "my-dialogue-shapes",
  "label": "My Dialogue Shapes",
  "presets": [
    {
      "id": "my-cloud",
      "label": "My Cloud",
      "category": "dialogue",
      "shape": "custom",
      "w": 380,
      "h": 245,
      "svg": "cloud.svg",
      "preview": "preview.webp"
    }
  ]
}
```

`svg`, `preview`, `thumbnail`, and `asset` paths are relative to the pack folder.
Do not use absolute paths or `..`. A preset ID must be unique; duplicate IDs
replace the earlier definition and emit a catalog warning. Restart ComfyUI after
copying a package, or call the asset reload endpoint when integrating it from a
custom workflow.

## Built-in layout

Built-in assets are grouped by role:

- `basic/` — circle, triangle, square, and trapezoid
- `bubbles/` — speech and thought bubbles
- `dialogue/` — dialogue-box raster assets

The root `manifest.json` remains the built-in registry. Its `svg`, `asset`, and
optional `preview` paths are relative to `web/assets/shapes/`.

## Static image shapes

Symbols and color image shapes that do not need editable bubble geometry may be
registered as static Shape presets in `web/speech-bubble-editor.html`. Store
their runtime image as lossless WebP in `web/assets/shapes/<asset-id>/`; these
items appear in the same unified Speech Bubbles & Shapes browser.
