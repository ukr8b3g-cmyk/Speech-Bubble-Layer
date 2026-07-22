# Future Ideas (Not Committed)

This file records optional directions for later exploration. Items here are not implemented features or guaranteed commitments.

## User assets and stamps

- Allow PNG, transparent WebP, and JPEG assets to be registered by drag-and-drop or an **Import User Asset** action.
- Store imported files locally per ComfyUI user, not on an external internet service.
- Keep user assets separate from built-in SFX and comic-stamp assets.
- Support two asset types: full-color images and recolorable mask stamps.
- Use a small manifest with stable fields such as `id`, `name`, `category`, `keywords`, `sortGroup`, and `sortRank` so future assets can participate in search and sorting without changing the built-in list.
- Generate compact thumbnails for the browser while retaining the original file for final compositing.
- Consider ZIP import/export later; JSON alone cannot carry image files.

## Editor dock layout

- Keep the left side focused on asset entry points: speech-bubble shapes, SFX, comic stamps, and future asset categories.
- Reserve the lower-right dock for the Layers panel because layer visibility, order, grouping, and selection are core operations.
- Use the upper-right dock as a tabbed workspace. Candidate tabs are **Properties**, **Swatches**, **History**, and **Styles**.
- Keep Transform and Drop Shadow inside Properties/Appearance for the first dock iteration. They remain collapsed and should not consume permanent layer space.
- Add a draggable horizontal divider between the upper dock and Layers. Remember the divider position per user.
- On narrow windows, switch the right dock to tabs rather than compressing Layers into an unusable height.
- New asset categories should open in the left drawer and must not reduce the persistent Layers area.

## Near-term editor cleanup

- Add SFX ordering choices: fixed Recommended/Related order, explicit Usage Count order, and Name order. The default order is not automatically changed by usage.
- Add a compact shared color-swatch palette while retaining the free color picker.
- Use common default colors across built-in assets.
- Disable the default outline for assets such as hearts and arrows where an added border harms the original shape.
- Explore two glossy sweat stamps later: one normal blue drop and one diagonally flying drop, both with a fixed white highlight.

