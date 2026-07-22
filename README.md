# ComfyUI Speech Bubble

A lightweight speech-bubble and text editor for ComfyUI. Open the editor from the node, arrange bubble and text layers, save the layout, and queue the workflow to render the final image.

A distinctive feature is the direct **360-degree tail (pointer) handle**: the speaker pointer is not locked to a left/right preset and can be aimed freely at any character or off-canvas position.

## Built-in shapes and shape morphing

Speech and thought bubbles are loaded from the built-in shape manifest. Basic geometric shapes and color image shapes are registered as static Shape presets; both appear in the unified Speech Bubbles & Shapes browser. Retired jagged/burst entries are not registered as built-in presets.

- Classic Oval and Box share a Roundness control: 0 is a box and 100 is an oval. Box starts at Roundness 0 and Asymmetry 0.
- Thought Cloud provides Cloudiness, Lobe Count, Lobe Depth, and Softness. Double and fuzzy clouds are created from this one starting shape.
- Tunable shapes support deliberate asymmetry and deterministic Randomize Shape, followed by direct Bézier editing when needed.

Changing these parameters creates a custom vector shape while retaining the selected preset as its understandable starting point. Additional unusual shapes can be added later as new starting presets without changing the renderer or layer workflow.

## User shape presets

Select a bubble and use **Save as User Preset…** to preserve its final Bézier outline and shape parameters. User presets appear in **Browse All Shapes > User Presets** and can be updated or deleted. Import and Export use a portable JSON file.

Only the reusable shape is stored; dialogue text, position, colors, canvas size, and other scene layout data are not included. Presets are isolated per ComfyUI user. The default single-user file is `ComfyUI/user/default/speech-bubble/presets.json`.

## Tail handle

The pointed part of a speech bubble is generally called its **tail** or **pointer**. Speech bubbles use a yellow handle to control its direction and length. Drag it freely around the bubble for 360-degree placement. If a tail is not needed, drag the yellow handle inside the bubble; the tail is then hidden inside the bubble body.

Thought bubbles use the same handle concept for their thought dots. Narration and explanation boxes have no speaker, so they do not require a tail handle.

## Outline styles

Outline appearance is selected in **Properties > Outline Style** instead of using separate shape presets. Available styles are Solid, Double, Dashed, and Dotted.

Dotted outlines are distributed by distance along the complete outline. Dot spacing stays uniform across horizontal, vertical, diagonal, curved, and closing segments.

## Editor controls

- The background layer is fixed, so it has no lock control. Use its eye icon to show or hide it in the editor preview.
- Group and Ungroup are located above the Layers list. Alt-click selects one layer inside a group. Alt-drag moves that layer independently and temporarily bypasses its lock.
- Ctrl/Shift-click selects multiple ungrouped layers. Drag any selected layer to move the entire temporary selection together.
- Hover a numeric field and use the mouse wheel to adjust it. Hold Shift while scrolling for 10x steps.
- Transform and Drop Shadow start collapsed. Their open/closed state is remembered after the user changes it.
- Font Size is always stored and displayed as a whole number; decimal input is truncated. Text Color and Outline Color can be selected independently.
- The font browser shows a live sample for each installed family and separates Japanese, Simplified Chinese, Traditional Chinese, Korean, Latin, and other scripts. Families stay collapsed to one row; additional installed styles expand only when requested. Search, Favorites, Recent, and Recommended keep the default list short.
- Character Spacing uses Photoshop-style Tracking values (`-200` to `500`). Horizontal Scale and Vertical Scale independently stretch the glyphs from `10%` to `500%`.
- With one text layer selected, Ctrl-drag a left/right handle to stretch glyphs horizontally, or Ctrl-drag a top/bottom handle to stretch them vertically. Dragging without Ctrl continues to resize only the text box.
- Ctrl+C copies the selected bubble/text layers to the editor clipboard and Ctrl+V pastes them with a small offset. Multi-selections are copied together, including their group relationship. Copy and Paste are also available from each layer's `⋮` menu. Text fields keep normal text copy/paste behavior while focused.
- All seven starting shapes provide shape-changing controls appropriate to their geometry, plus **Asymmetry** and **Randomize Shape**.
- Shape Intensity or Cloudiness 0 produces a smooth oval; increasing it restores the selected starting shape.
- Existing layouts that used the older Jagged Intensity setting are migrated automatically.

## Node preview persistence

The Speech Bubble Layer keeps the most recent queued preview in `output/speech_bubble_preview` and restores it when returning from another workflow tab or after restarting ComfyUI. The file is overwritten per node and batch instead of creating a new preview on every queue. Live editor previews remain session-only until the workflow is queued.

For preview diagnostics, set `localStorage.speech_bubble_preview_debug = "1"` in the browser console and reload. Remove that key after checking to disable the debug messages.

## Minimal edge-repeat frame assets

An `edge-repeat` frame is auto-registered from `web/assets/frames/<frame_id>/manifest.json`. Its runtime package may contain only `manifest.json`, `preview.webp`, and the eight corner/edge WebP files under `parts/`. `runtimeAsset` and `runtimeAsset2x` are optional for this render mode; `nine-slice` and `full-overlay` still require `runtimeAsset`.

---

# ComfyUI スピーチバブル

ComfyUI上で吹き出しと文字レイヤーを配置する軽量エディターです。ノードからエディターを開き、配置を保存してワークフローを実行すると最終画像へ反映されます。

特徴的な機能として、発話者を指す**尻尾（tail / pointer）を360度自由に動かせるハンドル**があります。左右などの固定プリセットに制限されず、任意の人物や画像枠外へ直接向けられます。

## ビルトイン形状と形状変化

発話・思考バブルはビルトインShapeマニフェストから読み込みます。基本図形とカラー画像のShapeは静的プリセットとして登録し、どちらも統合されたSpeech Bubbles & Shapes一覧に表示します。廃止したギザギザ／バースト形状はビルトイン登録していません。

- Classic OvalとBoxはRoundnessを共有します。0で四角、100で楕円になります。Boxの初期値はRoundness 0、Asymmetry 0です。
- Thought Cloudでは、Cloudiness、Lobe Count、Lobe Depth、Softnessを変更できます。Double CloudやFuzzy Thoughtも、この1種類から作成できます。
- 調整対応の形状では、再現可能なRandomize Shapeとベジェパスの直接編集を使用できます。

パラメータを変更すると、選択した開始形状を基準にしたカスタムベクター形状になります。将来、変わった形を追加する場合も、レンダラーやレイヤー構成を増やさず、新しい開始プリセットとして追加できます。

## ユーザー形状プリセット

吹き出しを選択して**Save as User Preset…**を押すと、最終的なベジェ外形と形状パラメータを保存できます。保存した形状は**Browse All Shapes > User Presets**に表示され、更新・削除が可能です。Import / Exportでは持ち運び可能なJSONを使用します。

保存対象は再利用する形状だけです。セリフ文字、位置、色、キャンバスサイズなどのシーン配置情報は含みません。プリセットはComfyUIユーザーごとに分離されます。通常の単一ユーザー環境では`ComfyUI/user/default/speech-bubble/presets.json`に保存されます。

## 尻尾ハンドル

吹き出しから話者へ伸びる尖った部分は、一般に**尻尾**または**ポインター**（tail / pointer）と呼ばれます。発話用の吹き出しでは、黄色いハンドルで尻尾の方向と長さを調整します。吹き出しの周囲を自由にドラッグでき、360度どの方向にも配置できます。尻尾が不要な場合は、黄色いハンドルを吹き出し内部へ移動してください。尻尾が本体の内側へ収納され、見えなくなります。

思考バブルでは、同じハンドル操作で思考点の位置を変更します。第三者による説明・解説などのナレーション枠には話者がいないため、尻尾ハンドルは使用しません。

## 枠線スタイル

線種ごとの形状プリセットは使用せず、**Properties > Outline Style**から枠線を選択します。Solid、Double、Dashed、Dottedに対応します。

Dottedは外周全体の実距離を基準に配置します。横・縦・斜め・曲線・一周した継ぎ目でも、ドット間隔が均等になります。

## エディター操作

- 背景レイヤーは固定のため鍵はありません。目のアイコンでエディター上の表示・非表示を切り替えられます。
- Group / UngroupはLayers一覧の上にあります。Altクリックでグループ内の1レイヤーだけを選択し、Altドラッグでロックを一時的に迂回して単独移動できます。
- Ctrl / Shiftクリックで、グループ化していない複数レイヤーを一時選択できます。選択中のどれかをドラッグすると、選択した全レイヤーを一緒に移動できます。
- 数値入力欄にマウスを重ねてホイールを回すと値を変更できます。Shiftを押しながら回すと10倍刻みです。
- TransformとDrop Shadowは初期状態では閉じています。ユーザーが変更した後は、開閉状態を次回も保持します。
- Font Sizeは常に整数で保存・表示され、小数入力は切り捨てられます。Text ColorとOutline Colorは別々に選択できます。
- フォントブラウザーは、OSにインストールされた各ファミリーを実際の書体サンプルで表示し、日本語・簡体字・繁体字・韓国語・Latin・その他の文字体系に分けます。通常はファミリーを1行にまとめ、追加スタイルは必要なときだけ展開します。Search、Favorites、Recent、Recommendedにより初期一覧を短く保ちます。
- Character SpacingはPhotoshopに近いTracking値（`-200`〜`500`）です。Horizontal Scale / Vertical Scaleで文字自体を`10%`〜`500%`まで個別に伸縮できます。
- テキストを1つ選択し、Ctrlを押しながら左右ハンドルをドラッグすると文字を横方向へ、上下ハンドルでは縦方向へ伸縮します。Ctrlなしのドラッグは従来どおりテキスト枠だけを変更します。
- Ctrl+Cで選択中の吹き出し・テキストレイヤーを内部クリップボードへコピーし、Ctrl+Vで少しずらして貼り付けます。複数選択とグループ関係もまとめて複製されます。各レイヤーの`⋮`メニューにもCopy / Pasteがあります。文字入力欄の編集中は通常の文字コピー・貼り付けが優先されます。
- 7つの開始形状すべてに、形状に適した変形設定と**Asymmetry**、**Randomize Shape**があります。
- Shape IntensityまたはCloudinessを0にすると滑らかな楕円になり、値を上げると選択した開始形状の特徴が強くなります。
- 旧Jagged Intensityを保存した既存レイアウトは自動移行します。

## ノードプレビューの保持

Speech Bubble Layerは、最後に実行したプレビューを`output/speech_bubble_preview`へ保持し、別のワークフロータブから戻った場合やComfyUI再起動後にも自動復元します。プレビューはノード・バッチ単位で同じファイルへ上書きするため、Queueのたびに増えません。エディターのライブプレビューは、ワークフローをQueueするまでは現在のセッション内だけで保持されます。

プレビュー復元を診断する場合は、ブラウザーコンソールで`localStorage.speech_bubble_preview_debug = "1"`を設定して再読み込みします。確認後にこのキーを削除するとデバッグ表示を停止できます。

## edge-repeatフレームの最小アセット

`edge-repeat`フレームは`web/assets/frames/<frame_id>/manifest.json`から自動登録されます。実行用パッケージは`manifest.json`、`preview.webp`、`parts/`内の四隅・四辺WebPだけで構成できます。この描画モードでは`runtimeAsset`と`runtimeAsset2x`を省略できます。`nine-slice`と`full-overlay`では引き続き`runtimeAsset`が必要です。
