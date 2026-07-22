# SFX packages

Put an onomatopoeia package under `web/assets/sfx/<pack-id>/`:

```text
my-comic-pack/
├─ manifest.json
└─ assets/
   └─ impact.webp
```

Put comic stamps and symbols under `web/assets/stamps/<pack-id>/` with the
same package structure. Use `category: "symbols"` or `category: "effects"`
for stamps; use `category: "japanese"` or another SFX category for
onomatopoeia. Existing item IDs are stable references in saved layouts; do not
reuse an ID for unrelated artwork.

All paths in `manifest.json` are relative to the package directory. A preview
file is optional and should be kept only when the manifest actually references
it. Copy the whole folder and restart ComfyUI to register it.
