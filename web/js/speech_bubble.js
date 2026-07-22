import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const editorTargets = new Map();
const editorSessions = new Map();
const PREVIEW_PROPERTY = "speech_bubble_preview_images";
const PREVIEW_INPUT_PROPERTY = "speech_bubble_preview_input";
const PREVIEW_DATA_PROPERTY = "speech_bubble_saved_preview";
const PREVIEW_LAYOUT_PROPERTY = "speech_bubble_preview_layout";
const PREVIEW_REVISION_PROPERTY = "speech_bubble_preview_revision";
const PREVIEW_DEBUG_KEY = "speech_bubble_preview_debug";
const RESTORE_DELAYS = [0, 80, 300];

function debugPreview(message, detail) {
  try {
    if (localStorage.getItem(PREVIEW_DEBUG_KEY) !== "1") return;
  } catch {
    return;
  }
  console.debug(`[Speech Bubble Preview] ${message}`, detail || "");
}

function getWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function ensurePreviewKey(node) {
  const widget = getWidget(node, "preview_key");
  if (!widget) return;
  const current = String(widget.value || "").trim();
  if (current && current !== "open") return;
  const randomPart = globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  widget.value = `sb-${randomPart}`;
  node.graph?.change?.();
}

function isLoadImageNode(node) {
  const names = [node?.type, node?.title, node?.comfyClass, node?.constructor?.type]
    .map((name) => String(name || "").replace(/\s+/g, ""));
  return names.includes("LoadImage");
}

function findConnectedLoadImageNode(node, visited = new Set()) {
  if (!node || visited.has(node.id)) return null;
  visited.add(node.id);
  if (isLoadImageNode(node)) return node;
  const input = node.inputs?.find((slot) => slot.name === "image");
  const linkId = input?.link;
  if (!linkId) return null;
  const link = app.graph.links?.[linkId];
  const originId = Array.isArray(link) ? link[1] : link?.origin_id;
  const origin = originId ? app.graph.getNodeById(originId) : null;
  return findConnectedLoadImageNode(origin, visited);
}

function getLoadImageUrl(node) {
  if (!isLoadImageNode(node)) return null;
  const widget = getWidget(node, "image");
  const value = widget?.value;
  if (!value) return node.imgs?.[0]?.src || null;
  const normalized = String(value).replaceAll("\\", "/");
  const parts = normalized.split("/");
  const filename = parts.pop();
  const subfolder = parts.join("/");
  const params = new URLSearchParams({ filename, type: "input" });
  if (subfolder) params.set("subfolder", subfolder);
  return api.apiURL(`/view?${params.toString()}`);
}

function currentInputSource(node) {
  return getLoadImageUrl(findConnectedLoadImageNode(node));
}

function cacheBustedInputUrl(url, node) {
  if (!url) return null;
  const token = `${node?.id || "node"}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${url}${String(url).includes("?") ? "&" : "?"}speech_bubble_input_cache=${encodeURIComponent(token)}`;
}

function setNodeProperty(node, name, value) {
  node.properties ||= {};
  if (typeof node.setProperty === "function") node.setProperty(name, value);
  else node.properties[name] = value;
}

function clearPreview(node, options = {}) {
  node.imgs = null;
  node.images = [];
  node.imageIndex = null;
  node._speechBubblePreviewUrls = [];
  node._speechBubblePreviewRefs = [];
  node._speechBubbleLoadingPreviewKey = null;
  node._speechBubbleRenderedPreviewKey = null;
  node._speechBubblePreviewLoadGeneration = (Number(node._speechBubblePreviewLoadGeneration) || 0) + 1;
  if (options.clearPersistent) setNodeProperty(node, PREVIEW_PROPERTY, []);
  node.setDirtyCanvas?.(true, true);
  node.graph?.setDirtyCanvas?.(true, true);
}

function currentLayout(node) {
  return String(getWidget(node, "layout_json")?.value || "{}");
}

function editorBaselineSources(node) {
  if (Array.isArray(node?._speechBubblePreviewUrls) && node._speechBubblePreviewUrls.length) {
    return [...node._speechBubblePreviewUrls];
  }
  return (Array.isArray(node?.imgs) ? node.imgs : []).map((image) => image?.src).filter(Boolean);
}

function finishEditorSession(key, restore = false) {
  const session = editorSessions.get(key);
  const node = editorTargets.get(key);
  if (session?.watcher) window.clearInterval?.(session.watcher);
  if (node?._speechBubbleEditorWindow === session?.popup) node._speechBubbleEditorWindow = null;
  editorSessions.delete(key);
  editorTargets.delete(key);
  if (!restore || !node) return;
  clearPreview(node);
  node._speechBubblePreviewUrls = [...session.sources];
  if (session.sources.length) restorePreview(node, session.sources);
  else if (session.inputSource) showCurrentInputPreview(node, session.inputSource);
}

function beginEditorSession(key, node, popup) {
  const session = {
    sources: editorBaselineSources(node),
    inputSource: currentInputSource(node),
    popup,
    watcher: null,
  };
  editorTargets.set(key, node);
  editorSessions.set(key, session);
  if (popup && window.setInterval) {
    session.watcher = window.setInterval(() => {
      if (popup.closed) finishEditorSession(key, true);
    }, 250);
  }
}

function showCurrentInputPreview(node, source) {
  if (!node || !source) return;
  clearPreview(node);
  node._speechBubbleExecutedInputSource = null;
  const freshSource = cacheBustedInputUrl(source, node);
  restorePreview(node, setPreviewSources(node, [freshSource]));
}

function previewRefToUrl(ref, cacheOverride = null) {
  if (!ref) return null;
  if (typeof ref === "string") return ref;
  if (ref.url) return String(ref.url);
  if (!ref.filename) return null;
  const params = new URLSearchParams({
    filename: String(ref.filename),
    type: String(ref.type || "temp"),
  });
  if (ref.subfolder) params.set("subfolder", String(ref.subfolder));
  if (ref.preview) params.set("preview", String(ref.preview));
  if (ref.channel) params.set("channel", String(ref.channel));
  const cacheKey = cacheOverride || ref.cache_key;
  if (cacheKey) params.set("speech_bubble_cache", String(cacheKey));
  return api.apiURL(`/view?${params.toString()}`);
}

function serializablePreviewRefs(refs) {
  return (Array.isArray(refs) ? refs : [])
    .filter((ref) => ref && typeof ref === "object" && ref.filename)
    .map((ref) => {
      const copy = {};
      for (const key of ["filename", "subfolder", "type", "preview", "channel", "cache_key"]) {
        if (ref[key] !== undefined && ref[key] !== null) copy[key] = ref[key];
      }
      return copy;
    });
}

function setPreviewSources(node, refs, persist = false, cacheOverride = null) {
  const urls = (Array.isArray(refs) ? refs : []).map((ref) => previewRefToUrl(ref, cacheOverride)).filter(Boolean);
  if (!urls.length) return [];
  node._speechBubblePreviewUrls = urls;
  const stored = serializablePreviewRefs(refs);
  if (stored.length) {
    node._speechBubblePreviewRefs = stored;
    node.images = stored;
    if (persist) {
      node.properties ||= {};
      if (typeof node.setProperty === "function") node.setProperty(PREVIEW_PROPERTY, stored);
      else node.properties[PREVIEW_PROPERTY] = stored;
      node.graph?.change?.();
      debugPreview("stored persistent preview references", stored);
    } else {
      node.properties ||= {};
      node.properties[PREVIEW_PROPERTY] = stored;
    }
  }
  return urls;
}

function previewRevision(value) {
  const revision = Number(value);
  return Number.isFinite(revision) && revision >= 0 ? revision : 0;
}

function latestPreviewRevision(node) {
  const revision = Number(node?._speechBubbleLatestPreviewRevision);
  return Number.isFinite(revision) ? revision : -1;
}

function acceptPreviewRevision(node, revision) {
  const next = previewRevision(revision);
  if (next < latestPreviewRevision(node)) return false;
  node._speechBubbleLatestPreviewRevision = next;
  return true;
}

function schedulePreviewRestore(node) {
  for (const delay of RESTORE_DELAYS) {
    window.setTimeout(() => {
      if (!node?.imgs?.length) restorePreview(node);
    }, delay);
  }
}

function restorePreview(node, sources = node?._speechBubblePreviewUrls) {
  if (!node || !Array.isArray(sources) || !sources.length) return;
  const key = sources.join("\n");
  if (node.imgs?.length && node._speechBubbleRenderedPreviewKey === key) return;
  if (node._speechBubbleLoadingPreviewKey === key) return;
  const generation = (Number(node._speechBubblePreviewLoadGeneration) || 0) + 1;
  node._speechBubblePreviewLoadGeneration = generation;
  node._speechBubbleLoadingPreviewKey = key;
  Promise.all(
    sources.map(
      (source) =>
        new Promise((resolve) => {
          const preview = new Image();
          preview.onload = () => resolve(preview);
          preview.onerror = () => {
            debugPreview("preview image failed to load", source);
            resolve(null);
          };
          preview.src = source;
        }),
    ),
  ).then((loaded) => {
    if (node._speechBubblePreviewLoadGeneration !== generation) return;
    if (node._speechBubbleLoadingPreviewKey !== key) return;
    const images = loaded.filter(Boolean);
    node._speechBubbleLoadingPreviewKey = null;
    if (!images.length) {
      debugPreview("no preview image could be restored", sources);
      return;
    }
    node.imgs = images;
    node.imageIndex = images.length === 1 ? 0 : null;
    node._speechBubbleRenderedPreviewKey = key;
    node.setDirtyCanvas?.(true, true);
    node.graph?.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    debugPreview("preview restored", sources);
  });
}

function applyLayout(node, layoutJson, previewDataUrl = "", revision = 0) {
  const widget = getWidget(node, "layout_json");
  if (!widget) return false;
  const acceptedRevision = previewRevision(revision);
  if (acceptedRevision < latestPreviewRevision(node)) return false;
  node._speechBubbleLatestPreviewRevision = acceptedRevision;
  const oldValue = widget.value;
  widget.value = layoutJson;
  widget.callback?.(layoutJson);
  node.onWidgetChanged?.("layout_json", layoutJson, oldValue, widget);
  const inputSource = currentInputSource(node);
  clearPreview(node, { clearPersistent: true });
  setNodeProperty(node, PREVIEW_INPUT_PROPERTY, inputSource || "");
  setNodeProperty(node, PREVIEW_LAYOUT_PROPERTY, layoutJson);
  setNodeProperty(node, PREVIEW_DATA_PROPERTY, previewDataUrl || "");
  setNodeProperty(node, PREVIEW_REVISION_PROPERTY, node._speechBubbleLatestPreviewRevision);
  node._speechBubbleExecutedInputSource = null;
  if (previewDataUrl) {
    restorePreview(node, setPreviewSources(node, [previewDataUrl]));
  } else if (inputSource) {
    showCurrentInputPreview(node, inputSource);
  }
  node._speechBubbleExecutedInputSource = inputSource || null;
  node.graph?.change?.();
  node.setDirtyCanvas?.(true, true);
  app.graph.setDirtyCanvas(true, true);
  return widget.value === layoutJson;
}

window.addEventListener("message", (event) => {
  const data = event.data;
  if (!data || !data.type?.startsWith("speech_bubble:")) return;
  const node = editorTargets.get(data.key);
  if (!node) return;
  if (data.type === "speech_bubble:set_layout_json") {
    const applied = applyLayout(node, data.layout_json || "{}", data.preview_data_url || "", data.revision);
    if (applied) finishEditorSession(data.key, false);
    event.source?.postMessage(
      { type: "speech_bubble:layout_applied", key: data.key, applied },
      event.origin || "*",
    );
    return;
  }
  if (data.type === "speech_bubble:cancel_editor") {
    finishEditorSession(data.key, true);
    return;
  }
  if (data.type === "speech_bubble:live_preview" && data.preview_data_url) {
    const revision = previewRevision(data.revision);
    if (acceptPreviewRevision(node, revision)) restorePreview(node, [data.preview_data_url]);
  }
});

app.registerExtension({
  name: "speech_bubble.editor_button",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "SpeechBubbleLayer") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    const onExecuted = nodeType.prototype.onExecuted;
    const onConfigure = nodeType.prototype.onConfigure;
    const onDrawBackground = nodeType.prototype.onDrawBackground;

    nodeType.prototype.onExecuted = function (output) {
      const result = onExecuted?.apply(this, arguments);
      const refs = output?.images;
      if (Array.isArray(refs) && refs.length) {
        setNodeProperty(this, PREVIEW_INPUT_PROPERTY, currentInputSource(this) || "");
        setNodeProperty(this, PREVIEW_LAYOUT_PROPERTY, currentLayout(this));
        setNodeProperty(this, PREVIEW_DATA_PROPERTY, "");
        this._speechBubbleExecutedInputSource = currentInputSource(this);
        restorePreview(this, setPreviewSources(this, refs, true));
      }
      return result;
    };

    nodeType.prototype.onConfigure = function (info) {
      const result = onConfigure?.apply(this, arguments);
      ensurePreviewKey(this);
      const refs = info?.properties?.[PREVIEW_PROPERTY] || this.properties?.[PREVIEW_PROPERTY];
      const layoutJson = currentLayout(this);
      const storedLayout = info?.properties?.[PREVIEW_LAYOUT_PROPERTY]
        ?? this.properties?.[PREVIEW_LAYOUT_PROPERTY]
        ?? "";
      const savedPreview = info?.properties?.[PREVIEW_DATA_PROPERTY]
        ?? this.properties?.[PREVIEW_DATA_PROPERTY]
        ?? "";
      this._speechBubbleLatestPreviewRevision = previewRevision(
        info?.properties?.[PREVIEW_REVISION_PROPERTY]
          ?? this.properties?.[PREVIEW_REVISION_PROPERTY]
          ?? -1,
      );
      const inputSource = currentInputSource(this);
      const storedInputSource = info?.properties?.[PREVIEW_INPUT_PROPERTY]
        ?? this.properties?.[PREVIEW_INPUT_PROPERTY]
        ?? "";
      if (inputSource && inputSource !== storedInputSource) {
        showCurrentInputPreview(this, inputSource);
      } else if (storedLayout === layoutJson && savedPreview) {
        clearPreview(this);
        this._speechBubbleExecutedInputSource = inputSource || null;
        restorePreview(this, setPreviewSources(this, [savedPreview]));
      } else if (storedLayout === layoutJson && Array.isArray(refs) && refs.length) {
        const restoreKey = `restore-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const sources = setPreviewSources(this, refs, false, restoreKey);
        this.imgs = null;
        this.imageIndex = null;
        this._speechBubbleRenderedPreviewKey = null;
        this._speechBubbleExecutedInputSource = inputSource || null;
        restorePreview(this, sources);
      } else if (inputSource) showCurrentInputPreview(this, inputSource);
      else clearPreview(this);
      schedulePreviewRestore(this);
      return result;
    };

    nodeType.prototype.onDrawBackground = function () {
      const result = onDrawBackground?.apply(this, arguments);
      const inputSource = currentInputSource(this);
      if (inputSource && this._speechBubbleExecutedInputSource && inputSource !== this._speechBubbleExecutedInputSource) {
        showCurrentInputPreview(this, inputSource);
      }
      if (!this.imgs?.length) restorePreview(this);
      return result;
    };

    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);

      const layoutWidget = getWidget(this, "layout_json");
      const fontWidget = getWidget(this, "font_path");
      const supersampleWidget = getWidget(this, "supersample");
      const previewKeyWidget = getWidget(this, "preview_key");
      ensurePreviewKey(this);
      // Remove only a stale legacy output socket. The serialized layout widget
      // remains the internal save/load channel for this node.
      const legacyLayoutOutputIndex = this.outputs?.findIndex(output => output?.name === "layout_json") ?? -1;
      if (legacyLayoutOutputIndex >= 0) this.removeOutput?.(legacyLayoutOutputIndex);
      for (const widget of [layoutWidget, fontWidget, supersampleWidget, previewKeyWidget]) {
        if (!widget) continue;
        widget.hidden = true;
        widget.serialize = true;
        widget.options ||= {};
        widget.options.serialize = true;
        widget.computeSize = () => [0, -4];
        widget.type = "hidden";
        if (widget.element) widget.element.style.display = "none";
        if (widget.inputEl) widget.inputEl.style.display = "none";
      }

      const editorButton = this.addWidget("button", "Open Speech Bubble Editor", "open", () => {
        const existingPopup = this._speechBubbleEditorWindow;
        if (existingPopup && !existingPopup.closed) {
          existingPopup.focus?.();
          return;
        }
        this._speechBubbleEditorWindow = null;
        const randomPart = globalThis.crypto?.randomUUID?.()
          || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
        const key = `speech_bubble_${this.id || "node"}_${randomPart}`;
        const loadImageNode = findConnectedLoadImageNode(this);
        const imageUrl = getLoadImageUrl(loadImageNode);
        try {
          localStorage.setItem(key, layoutWidget?.value || "{}");
        } catch {
          // The editor can still open without localStorage.
        }
        const revisionBase = Math.max(
          0,
          latestPreviewRevision(this) + 1,
          previewRevision(this.properties?.[PREVIEW_REVISION_PROPERTY]) + 1,
        );
        const params = new URLSearchParams({ jsonKey: key, v: "20260720-03", revisionBase: String(revisionBase) });
        if (imageUrl) params.set("imageUrl", cacheBustedInputUrl(imageUrl, this));
        const popup = window.open(`/extensions/ComfyUI-Speech-Bubble/speech-bubble-editor.html?${params.toString()}`, `speech_bubble_editor_${this.id}`);
        if (!popup) return;
        this._speechBubbleEditorWindow = popup;
        beginEditorSession(key, this, popup);
      });
      if (editorButton) {
        editorButton.serialize = false;
        editorButton.options ||= {};
        editorButton.options.serialize = false;
        editorButton.draw = function (ctx, _node, width, y, height) {
          const margin = 10;
          ctx.save();
          ctx.beginPath();
          if (typeof ctx.roundRect === "function") ctx.roundRect(margin, y, width - margin * 2, height, 4);
          else ctx.rect(margin, y, width - margin * 2, height);
          ctx.fillStyle = "#244b49";
          ctx.fill();
          ctx.strokeStyle = "#5f8b86";
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.fillStyle = "#e5f4f1";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = `${Math.max(12, Math.min(15, height * 0.58))}px Arial, sans-serif`;
          ctx.fillText(this.label || this.name, width / 2, y + height / 2);
          ctx.restore();
        };
      }
      this.setSize([Math.max(320, this.size?.[0] || 0), 112]);
    };
  },
});
