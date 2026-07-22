# Asset packages

Extension assets use the same folder-per-pack rule:

```text
web/assets/
├─ sfx/<pack-id>/manifest.json
├─ shapes/<pack-id>/manifest.json
└─ frames/<pack-id>/manifest.json
```

Copy one complete pack folder into its matching category, then restart ComfyUI.
The editor discovers SFX, comic stamps, speech-bubble shapes, and frames from
their manifests. Keep IDs stable: a later pack with the same asset ID overrides
the earlier definition and is reported as a catalog warning.

All referenced files must stay inside the pack folder. Use relative paths only.
Built-in root manifests remain supported for compatibility, but new packages
should always use their own folder.

Static image shapes that do not need editable bubble geometry may instead be
registered as built-in Shape presets and reference a lossless WebP under
`shapes/<asset-id>/`. This is the intended route for symbols and color image
shapes such as Mission Complete.

## User Presets are separate

The editor's **User Presets** save bubble geometry in the ComfyUI user settings.
They do not install image files and do not replace extension asset packs. Use an
asset package when distributing reusable SFX, stamps, frames, or shapes.
