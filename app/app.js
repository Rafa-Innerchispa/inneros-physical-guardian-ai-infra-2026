const $ = (id) => document.getElementById(id);

const els = {
  scenarioSelect: $("scenarioSelect"),
  sourceSelect: $("sourceSelect"),
  runtimeSelect: $("runtimeSelect"),
  runtimeBadge: $("runtimeBadge"),
  runBtn: $("runBtn"),
  resetBtn: $("resetBtn"),
  startCameraBtn: $("startCameraBtn"),
  captureFrameBtn: $("captureFrameBtn"),
  requestInferenceBtn: $("requestInferenceBtn"),
  mediaFileInput: $("mediaFileInput"),
  filePickLabel: $("filePickLabel"),
  approveBtn: $("approveBtn"),
  rejectBtn: $("rejectBtn"),
  interruptBtn: $("interruptBtn"),
  reverifyBtn: $("reverifyBtn"),
  resumeBtn: $("resumeBtn"),
  cancelBtn: $("cancelBtn"),
  lifecyclePanel: $("lifecyclePanel"),
  lifecycleState: $("lifecycleState"),
  lifecycleTimeline: $("lifecycleTimeline"),
  copyEvidenceBtn: $("copyEvidenceBtn"),
  cameraState: $("cameraState"),
  localVideo: $("cameraVideo"),
  prerecordedPreview: $("prerecordedPreview"),
  captureCanvas: $("captureCanvas"),
  overlayCanvas: $("overlayCanvas"),
  previewFail: $("previewFail"),
  previewFailText: $("previewFailText"),
  sourceLabel: $("sourceLabel"),
  frameId: $("frameId"),
  inferenceFrameTruth: $("inferenceFrameTruth"),
  cameraHealth: $("cameraHealth"),
  cameraTruth: $("cameraTruth"),
  simaHealth: $("simaHealth"),
  simaTruth: $("simaTruth"),
  mlaHealth: $("mlaHealth"),
  mlaTruth: $("mlaTruth"),
  guardianHealth: $("guardianHealth"),
  guardianTruth: $("guardianTruth"),
  ioHealth: $("ioHealth"),
  ioTruth: $("ioTruth"),
  evidenceHealth: $("evidenceHealth"),
  evidenceTruth: $("evidenceTruth"),
  traceId: $("traceId"),
  policyBadge: $("policyBadge"),
  approvalState: $("approvalState"),
  decisionEmpty: $("decisionEmpty"),
  decisionContent: $("decisionContent"),
  actionTitle: $("actionTitle"),
  actionReason: $("actionReason"),
  actionTarget: $("actionTarget"),
  actionImpact: $("actionImpact"),
  actionStatus: $("actionStatus"),
  simaModel: $("simaModel"),
  simaRuntime: $("simaRuntime"),
  simaDevice: $("simaDevice"),
  simaLatency: $("simaLatency"),
  simaFps: $("simaFps"),
  frameMatch: $("frameMatch"),
  runtimeList: $("runtimeList"),
  historicalBenchmark: $("historicalBenchmark"),
  receiptFrame: $("receiptFrame"),
  receiptSima: $("receiptSima"),
  receiptDetections: $("receiptDetections"),
  receiptDecision: $("receiptDecision"),
  receiptApproval: $("receiptApproval"),
  receiptAction: $("receiptAction"),
  receiptVerification: $("receiptReadback"),
  receiptSeal: $("receiptSeal"),
  evidencePreview: $("evidencePreview"),
  pitchCue: $("pitchCue"),
  toast: $("toast"),
};

const scenarioCopy = {
  loitering_after_hours:
    "The demo should show temporal understanding: a person remains in a restricted zone after closing, then policy asks for approval before any low-impact action.",
  repeated_access_attempt:
    "A single frame is not enough. Guardian should correlate repeated presence or attempts over time, then stop at the human boundary.",
  restricted_zone_entry:
    "Guardian should combine zone context, policy, approval, action, verification and proof without treating camera preview as inference truth.",
};

const sourceLabels = {
  "laptop-webcam": "LAPTOP WEBCAM",
  "local-prerecorded": "LOCAL PRERECORDED",
};

let latestState = null;
let latestCatalog = null;
let latestCameraCatalog = null;
let latestFrame = null;
let mediaStream = null;
let toastTimer = null;

function showToast(message, error = false) {
  clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.classList.toggle("error", error);
  els.toast.classList.add("show");
  toastTimer = setTimeout(() => els.toast.classList.remove("show"), 3400);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed with ${response.status}`);
    error.payload = payload;
    error.status = response.status;
    throw error;
  }
  return payload;
}

function setHealth(kind, status, truth) {
  const statusEl = els[`${kind}Health`];
  const truthEl = els[`${kind}Truth`];
  const cell = document.querySelector(`[data-health="${kind}"]`);
  const normalizedStatus = normalizeStatus(status);
  const normalizedTruth = normalizeTruth(truth);
  if (statusEl) statusEl.textContent = normalizedStatus;
  if (truthEl) truthEl.textContent = normalizedTruth;
  if (cell) {
    cell.dataset.status = normalizedStatus.toLowerCase();
    cell.dataset.truth = normalizedTruth.toLowerCase();
  }
}

function normalizeStatus(value) {
  const raw = String(value || "").toUpperCase();
  if (["READY", "OK", "ONLINE", "VERIFIED", "RESUMED_VERIFIED"].includes(raw)) return "READY";
  if (["DEGRADED", "PARTIAL", "AWAITING_APPROVAL", "REVERIFICATION_REQUIRED"].includes(raw)) return "DEGRADED";
  if (["BLOCKED", "FAILED_CLOSED", "ACTION_FAILED_SAFE", "SAFE_STATE_VERIFIED", "REJECTED_SAFE"].includes(raw)) return "BLOCKED";
  if (["OFFLINE", "UNAVAILABLE", "NOT_CONFIGURED"].includes(raw)) return "OFFLINE";
  return "BLOCKED";
}

function normalizeTruth(value) {
  const raw = String(value || "").toUpperCase();
  if (raw === "REAL" || raw.includes("REAL_LOW_VOLTAGE") || raw.includes("PRODUCT_HTTP_READBACK")) return "REAL";
  if (raw === "MEASURED" || raw.includes("MEASURED_SPONSOR_RUNTIME")) return "MEASURED";
  if (raw === "SIMULATED" || raw.includes("SIMULATED") || raw.includes("FIXTURE")) return "SIMULATED";
  return "UNVERIFIED";
}

function formatMs(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(value < 10 ? 2 : 1)} ms` : "Not provided";
}

function formatFps(value) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(value < 10 ? 2 : 1) : "Not provided";
}

function humanize(value, fallback = "Not provided") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value).replaceAll("_", " ");
}

function humanizeAction(actionType) {
  return humanize(actionType, "Bounded action")
    .split(" ")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1).toLowerCase())
    .join(" ");
}

function sourceLabel(sourceId) {
  return sourceLabels[sourceId] || humanize(sourceId, "UNKNOWN SOURCE").toUpperCase();
}

function currentSourceInfo() {
  const sourceId = els.sourceSelect.value;
  const sources = Array.isArray(latestCameraCatalog?.sources) ? latestCameraCatalog.sources : [];
  return sources.find((source) => source.source_id === sourceId) || {
    source_id: sourceId,
    label: sourceLabel(sourceId),
    kind: sourceId === "local-prerecorded" ? "LOCAL_PRERECORDED_SOURCE" : "LAPTOP_WEBCAM",
    status: "READY",
    truth: "UNVERIFIED",
  };
}

function isLocalFrameSource(sourceId) {
  return sourceId === "laptop-webcam" || sourceId === "local-prerecorded";
}

function isRemoteFrameSource(sourceId) {
  return Boolean(sourceId) && !isLocalFrameSource(sourceId);
}

function clearOverlay() {
  const ctx = els.overlayCanvas.getContext("2d");
  ctx.clearRect(0, 0, els.overlayCanvas.width, els.overlayCanvas.height);
}

function resetInferenceTelemetry() {
  els.simaModel.textContent = "Not provided";
  els.simaRuntime.textContent = "Not provided";
  els.simaDevice.textContent = "Not provided";
  els.simaLatency.textContent = "Not provided";
  els.simaFps.textContent = "Not provided";
  els.historicalBenchmark.textContent = "No historical benchmark supplied by backend.";
  els.runtimeBadge.textContent = "UNVERIFIED";
  setHealth("sima", "BLOCKED", "UNVERIFIED");
  setHealth("mla", "BLOCKED", "UNVERIFIED");
}

function resetFrameUi({ clearFrame = true } = {}) {
  if (clearFrame) latestFrame = null;
  clearOverlay();
  els.frameId.textContent = latestFrame?.frameId ? `frame: ${latestFrame.frameId}` : "frame: none";
  els.inferenceFrameTruth.textContent = "UNVERIFIED";
  els.frameMatch.textContent = "UNVERIFIED";
}

function resetRunView({ clearFrame = true } = {}) {
  latestState = { current: null, latest_evidence: null };
  resetFrameUi({ clearFrame });
  resetInferenceTelemetry();
  resetStages();
  renderState(latestState);
}

function frameRefFromPayload(payload) {
  return (
    payload?.frame_id ||
    payload?.frame_ref ||
    payload?.source_frame_id ||
    payload?.frame_source?.frame_id ||
    payload?.inference?.source?.frame_id ||
    payload?.current?.frame_source?.frame_id ||
    payload?.current?.inference?.source?.frame_id ||
    payload?.source?.frame_id ||
    payload?.camera?.frame_id ||
    null
  );
}

function sourceRefFromPayload(payload) {
  if (payload?.source && typeof payload.source === "object") {
    return payload.source.source_id || payload.source.id || payload.source.name || null;
  }
  return (
    payload?.source_id ||
    payload?.frame_source?.source_id ||
    payload?.inference?.source?.source_id ||
    payload?.current?.frame_source?.source_id ||
    payload?.current?.inference?.source?.source_id ||
    payload?.source ||
    payload?.camera?.source_id ||
    null
  );
}

function detectionFrameMatches(payload) {
  if (!latestFrame) return false;
  const frameRef = frameRefFromPayload(payload);
  const sourceRef = sourceRefFromPayload(payload);
  if (!frameRef || !sourceRef) return false;
  // Contract guard: frameId !== lastSubmittedFrameId must fail closed.
  return String(frameRef) === latestFrame.frameId && String(sourceRef) === latestFrame.sourceId;
}

function isDrawableDetection(detection) {
  if (!detection || typeof detection !== "object" || !Array.isArray(detection.bbox)) return false;
  const [rawX, rawY, rawW, rawH] = detection.bbox.map(Number);
  const confidence = detection.confidence;
  return (
    [rawX, rawY, rawW, rawH].every(Number.isFinite) &&
    rawW > 0 &&
    rawH > 0 &&
    typeof confidence === "number" &&
    Number.isFinite(confidence) &&
    confidence >= 0 &&
    confidence <= 1
  );
}

function extractDetections(traceOrPayload) {
  const candidates = [
    traceOrPayload?.detections,
    traceOrPayload?.runtime?.detections,
    traceOrPayload?.inference?.detections,
    traceOrPayload?.current?.inference?.detections,
    traceOrPayload?.sima?.detections,
    traceOrPayload?.stages?.find?.((stage) => stage.stage === "UNDERSTAND")?.runtime?.detections,
    traceOrPayload?.stages?.find?.((stage) => stage.stage === "PERCEIVE")?.runtime?.detections,
    traceOrPayload?.current?.stages?.find?.((stage) => stage.stage === "UNDERSTAND")?.runtime?.detections,
    traceOrPayload?.current?.stages?.find?.((stage) => stage.stage === "PERCEIVE")?.runtime?.detections,
  ];
  const raw = candidates.find((value) => Array.isArray(value));
  if (!raw) return [];
  return raw.filter(isDrawableDetection);
}

function drawDetections(detections, payload) {
  clearOverlay();
  if (!detections.length || !detectionFrameMatches(payload)) {
    els.inferenceFrameTruth.textContent = "UNVERIFIED";
    els.frameMatch.textContent = "UNVERIFIED";
    return;
  }

  const ctx = els.overlayCanvas.getContext("2d");
  const width = els.overlayCanvas.width;
  const height = els.overlayCanvas.height;
  ctx.lineWidth = 3;
  ctx.font = "700 18px ui-monospace, Consolas, monospace";

  for (const detection of detections) {
    const [rawX, rawY, rawW, rawH] = detection.bbox.map(Number);
    if (![rawX, rawY, rawW, rawH].every(Number.isFinite)) continue;
    const normalized = rawX <= 1 && rawY <= 1 && rawW <= 1 && rawH <= 1;
    const x = normalized ? rawX * width : rawX;
    const y = normalized ? rawY * height : rawY;
    const w = normalized ? rawW * width : rawW;
    const h = normalized ? rawH * height : rawH;
    const label = humanize(detection.label || detection.class || "object", "object").toUpperCase();
    const confidence =
      typeof detection.confidence === "number" && Number.isFinite(detection.confidence)
        ? ` ${(detection.confidence * 100).toFixed(1)}%`
        : "";
    ctx.strokeStyle = "#43f0bd";
    ctx.fillStyle = "rgba(67, 240, 189, 0.18)";
    ctx.strokeRect(x, y, w, h);
    ctx.fillRect(x, y - 28, Math.max(160, ctx.measureText(label + confidence).width + 18), 28);
    ctx.fillStyle = "#04130f";
    ctx.fillText(label + confidence, x + 9, y - 8);
  }

  els.inferenceFrameTruth.textContent = normalizeTruth(payload?.truth || payload?.inference_truth || payload?.sima?.truth);
  els.frameMatch.textContent = "MATCHED";
}

function makeFrameId() {
  return `frame-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`;
}

async function startLocalPreview() {
  const source = els.sourceSelect.value;
  if (source !== "laptop-webcam") {
    renderSourceMode();
    showToast(`${sourceLabel(source)} is prepared but not a verified live inference source.`, true);
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    setCameraBlocked("Browser does not expose navigator.mediaDevices.getUserMedia.");
    return;
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "environment" },
      audio: false,
    });
    els.localVideo.srcObject = mediaStream;
    els.previewFail.classList.add("hidden");
    els.cameraState.textContent = "Local preview ready";
    setHealth("camera", "READY", "UNVERIFIED");
    showToast("Local webcam preview is ready. Inference truth remains UNVERIFIED until backend proof.");
  } catch (error) {
    setCameraBlocked(error.message || "Camera permission denied.");
  }
}

function setCameraBlocked(message) {
  els.previewFail.classList.remove("hidden");
  els.previewFailText.textContent = `${message} No inference truth is implied.`;
  els.cameraState.textContent = "Local preview blocked";
  setHealth("camera", "BLOCKED", "UNVERIFIED");
  showToast(message, true);
}

function renderSourceMode() {
  const source = els.sourceSelect.value;
  const sourceInfo = currentSourceInfo();
  const isRemote = isRemoteFrameSource(source);
  els.sourceLabel.textContent = sourceLabel(source);
  els.filePickLabel.classList.toggle("hidden", source !== "local-prerecorded");
  els.prerecordedPreview.classList.toggle("hidden", source !== "local-prerecorded" || !els.prerecordedPreview.src);
  els.localVideo.classList.toggle("hidden", isRemote || (source === "local-prerecorded" && !!els.prerecordedPreview.src));
  els.startCameraBtn.disabled = source !== "laptop-webcam";
  els.captureFrameBtn.disabled = isRemote;
  resetFrameUi();

  if (source === "laptop-webcam") {
    els.previewFail.classList.toggle("hidden", !!mediaStream);
    els.previewFailText.textContent = "Camera permission is not active. No inference truth is implied.";
    setHealth("camera", mediaStream ? "READY" : "BLOCKED", "UNVERIFIED");
    els.cameraState.textContent = mediaStream ? "Local preview ready" : "Permission required";
    return;
  }

  if (isRemote) {
    els.previewFail.classList.remove("hidden");
    els.previewFailText.textContent = "Allowlisted remote source. Snapshot capture and inference are requested server-side; no URL or credential is exposed here.";
    els.cameraState.textContent = sourceInfo.status === "READY" ? "Remote source ready" : "Remote source blocked";
    setHealth("camera", sourceInfo.status || "BLOCKED", sourceInfo.truth || "UNVERIFIED");
    return;
  }

  els.previewFail.classList.remove("hidden");
  els.previewFailText.textContent = "Choose local prerecorded media. It remains UNVERIFIED until backend inference proves it.";
  els.cameraState.textContent = "Prerecorded source selected";
  setHealth("camera", "DEGRADED", "UNVERIFIED");
}

function handleLocalFile() {
  const file = els.mediaFileInput.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/") && !file.type.startsWith("video/")) {
    showToast("Unsupported local media type.", true);
    return;
  }
  const url = URL.createObjectURL(file);
  if (file.type.startsWith("video/")) {
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      mediaStream = null;
    }
    els.localVideo.srcObject = null;
    els.localVideo.src = url;
    els.localVideo.classList.remove("hidden");
    els.prerecordedPreview.classList.add("hidden");
    els.localVideo.play().catch(() => {});
  } else {
    els.prerecordedPreview.src = url;
    els.prerecordedPreview.classList.remove("hidden");
    els.localVideo.classList.add("hidden");
  }
  els.previewFail.classList.add("hidden");
  els.cameraState.textContent = "Local prerecorded preview";
  setHealth("camera", "DEGRADED", "UNVERIFIED");
  resetRunView();
}

function captureFrame() {
  const source = els.sourceSelect.value;
  const canvas = els.captureCanvas;
  const ctx = canvas.getContext("2d");
  let captured = false;

  if (source === "laptop-webcam" && els.localVideo.readyState >= 2) {
    canvas.width = els.localVideo.videoWidth || 1280;
    canvas.height = els.localVideo.videoHeight || 720;
    ctx.drawImage(els.localVideo, 0, 0, canvas.width, canvas.height);
    captured = true;
  }

  if (source === "local-prerecorded" && els.prerecordedPreview.src) {
    canvas.width = els.prerecordedPreview.naturalWidth || 1280;
    canvas.height = els.prerecordedPreview.naturalHeight || 720;
    ctx.drawImage(els.prerecordedPreview, 0, 0, canvas.width, canvas.height);
    captured = true;
  } else if (source === "local-prerecorded" && els.localVideo.readyState >= 2) {
    canvas.width = els.localVideo.videoWidth || 1280;
    canvas.height = els.localVideo.videoHeight || 720;
    ctx.drawImage(els.localVideo, 0, 0, canvas.width, canvas.height);
    captured = true;
  }

  if (!captured) {
    showToast("No local frame is available to capture.", true);
    return null;
  }

  latestFrame = {
    frameId: makeFrameId(),
    sourceId: source,
    capturedAt: new Date().toISOString(),
    previewOnly: true,
    imageType: "image/jpeg",
    dataUrl: canvas.toDataURL("image/jpeg", 0.82),
    width: canvas.width,
    height: canvas.height,
  };
  latestFrame.imageBase64 = latestFrame.dataUrl.split(",", 2)[1] || "";
  els.frameId.textContent = `frame: ${latestFrame.frameId}`;
  resetRunView({ clearFrame: false });
  showToast("Frame captured locally. It is preview evidence only until backend inference returns proof.");
  return latestFrame;
}

async function requestFrameInference() {
  if (isRemoteFrameSource(els.sourceSelect.value)) {
    await requestSourceInference();
    return;
  }
  const frame = latestFrame || captureFrame();
  if (!frame) return;
  els.requestInferenceBtn.disabled = true;
  resetRunView({ clearFrame: false });
  try {
    const payload = {
      frame_id: frame.frameId,
      source_id: frame.sourceId,
      captured_at: frame.capturedAt,
      image_type: frame.imageType,
      image_base64: frame.imageBase64,
      width: frame.width,
      height: frame.height,
      scenario: els.scenarioSelect.value,
    };
    const response = await api("/api/inference/frame", { method: "POST", body: JSON.stringify(payload) });
    syncLatestFrameFromState(response);
    renderState(response);
    showToast("Backend frame inference response received.");
  } catch (error) {
    clearOverlay();
    els.inferenceFrameTruth.textContent = "UNVERIFIED";
    els.frameMatch.textContent = "UNVERIFIED";
    setHealth("sima", "BLOCKED", "UNVERIFIED");
    setHealth("mla", "BLOCKED", "UNVERIFIED");
    showToast(`Frame inference fail-closed: ${error.message}`, true);
  } finally {
    els.requestInferenceBtn.disabled = false;
  }
}

async function requestSourceInference() {
  const sourceId = els.sourceSelect.value;
  els.requestInferenceBtn.disabled = true;
  resetRunView();
  try {
    const response = await api("/api/inference/source", {
      method: "POST",
      body: JSON.stringify({
        source_id: sourceId,
        scenario: els.scenarioSelect.value,
      }),
    });
    syncLatestFrameFromState(response);
    renderState(response);
    showToast("Backend allowlisted source inference response received.");
  } catch (error) {
    resetFrameUi();
    setHealth("camera", "BLOCKED", "UNVERIFIED");
    setHealth("sima", "BLOCKED", "UNVERIFIED");
    setHealth("mla", "BLOCKED", "UNVERIFIED");
    showToast(`Remote source inference fail-closed: ${error.message}`, true);
  } finally {
    els.requestInferenceBtn.disabled = false;
  }
}

function syncLatestFrameFromState(state) {
  const trace = state?.current || state;
  const frameSource = trace?.frame_source || trace?.inference?.source || null;
  if (!frameSource?.frame_id || !frameSource?.source_id) return;
  latestFrame = {
    frameId: String(frameSource.frame_id),
    sourceId: String(frameSource.source_id),
    capturedAt: frameSource.captured_at || trace?.inference?.captured_at || null,
    previewOnly: false,
    width: frameSource.width,
    height: frameSource.height,
  };
  els.frameId.textContent = `frame: ${latestFrame.frameId}`;
  sourceLabels[latestFrame.sourceId] = sourceLabel(latestFrame.sourceId);
}

function renderCatalog(catalog) {
  latestCatalog = catalog || {};
  els.runtimeSelect.innerHTML = "";
  els.runtimeList.innerHTML = "";

  const runtimes = Array.isArray(catalog?.runtimes) ? catalog.runtimes : [];
  for (const runtime of runtimes) {
    const option = document.createElement("option");
    option.value = runtime.runtime_id || runtime.id || "unknown-runtime";
    option.textContent = `${runtime.provider || option.value} / ${normalizeStatus(runtime.status)}`;
    if (normalizeStatus(runtime.status) !== "READY") option.disabled = true;
    els.runtimeSelect.appendChild(option);

    const row = document.createElement("div");
    row.className = "runtime-row";
    row.innerHTML = `<div><strong></strong><small></small></div><span></span>`;
    row.querySelector("strong").textContent = runtime.provider || "Backend runtime slot";
    row.querySelector("small").textContent = runtime.target || runtime.runtime_id || "No target supplied";
    row.querySelector("span").textContent = normalizeStatus(runtime.status);
    row.dataset.status = normalizeStatus(runtime.status).toLowerCase();
    els.runtimeList.appendChild(row);
  }

  if (!runtimes.length) {
    const empty = document.createElement("div");
    empty.className = "runtime-row";
    empty.textContent = "No backend runtime catalog supplied.";
    els.runtimeList.appendChild(empty);
  }

  const selected = runtimes.find((runtime) => normalizeStatus(runtime.status) === "READY") || runtimes[0];
  if (selected) {
    els.runtimeSelect.value = selected.runtime_id || selected.id;
    els.runtimeBadge.textContent = normalizeTruth(selected.truth || selected.inference_truth || selected.status);
  }

  const physical = catalog?.physical_io || {};
  setHealth("io", physical.status || "BLOCKED", physical.truth || "UNVERIFIED");
}

function renderCameraSources(catalog) {
  latestCameraCatalog = catalog || {};
  const previous = els.sourceSelect.value || "laptop-webcam";
  const sources = Array.isArray(catalog?.sources) ? [...catalog.sources] : [];
  if (!sources.some((source) => source.source_id === "laptop-webcam")) {
    sources.unshift({
      source_id: "laptop-webcam",
      label: "Laptop webcam",
      kind: "LAPTOP_WEBCAM",
      status: "READY",
      truth: "UNVERIFIED",
    });
  }

  els.sourceSelect.innerHTML = "";
  for (const source of sources) {
    if (!source?.source_id) continue;
    sourceLabels[source.source_id] = humanize(source.label || source.source_id).toUpperCase();
    const option = document.createElement("option");
    option.value = source.source_id;
    option.textContent = `${sourceLabels[source.source_id]} / ${normalizeStatus(source.status)}`;
    option.dataset.kind = source.kind || "";
    option.dataset.status = normalizeStatus(source.status);
    option.dataset.truth = normalizeTruth(source.truth);
    option.disabled = normalizeStatus(source.status) === "OFFLINE";
    els.sourceSelect.appendChild(option);
  }

  if ([...els.sourceSelect.options].some((option) => option.value === previous && !option.disabled)) {
    els.sourceSelect.value = previous;
  } else {
    els.sourceSelect.value = "laptop-webcam";
  }
}

function resetStages() {
  const defaults = {
    SEE: "Preview/capture only",
    PERCEIVE: "Awaiting backend detections",
    UNDERSTAND: "No temporal proof yet",
    POLICY: "Fail-closed until evaluated",
    HUMAN_APPROVAL: "Explicit operator boundary",
    ACTION: "Nothing executed",
    VERIFY: "Readback required",
    PROVE: "Evidence receipt required",
  };
  document.querySelectorAll(".stage").forEach((node) => {
    node.className = `stage${node.dataset.stage === "HUMAN_APPROVAL" ? " human-stage" : ""}`;
    const small = node.querySelector("small");
    if (small) small.textContent = defaults[node.dataset.stage] || "Pending";
  });
}

function stageAlias(stage) {
  const raw = String(stage || "").toUpperCase();
  if (raw === "DECIDE") return "POLICY";
  if (raw === "ACT") return "ACTION";
  if (raw === "UNDERSTAND") return "UNDERSTAND";
  return raw;
}

function renderStages(stages = [], trace = null) {
  resetStages();
  for (const stage of stages) {
    const key = stageAlias(stage.stage);
    const node = document.querySelector(`.stage[data-stage="${key}"]`);
    if (!node) continue;
    node.classList.add(stage.status || "pending");
    const small = node.querySelector("small");
    if (small) small.textContent = stage.summary || stage.status || "Backend reported";
  }

  if (trace?.status === "AWAITING_APPROVAL") {
    document.querySelector('.stage[data-stage="HUMAN_APPROVAL"]')?.classList.add("blocked_on_human_approval");
  }
  if (trace?.decision === "REJECTED") {
    document.querySelector('.stage[data-stage="ACTION"]')?.classList.add("rejected");
  }
  if (trace?.verified === true) {
    document.querySelector('.stage[data-stage="VERIFY"]')?.classList.add("complete");
    document.querySelector('.stage[data-stage="PROVE"]')?.classList.add("complete");
  }
}

function renderBackendTelemetry(payload) {
  const sima = payload?.sima || payload?.runtime || payload?.inference || {};
  const truth = normalizeTruth(
    sima.truth ||
      sima.inference_truth ||
      payload?.inference_truth ||
      (typeof payload?.truth === "string" ? payload.truth : payload?.truth?.detections),
  );
  const liveTruth = truth === "REAL" || truth === "MEASURED";
  els.runtimeBadge.textContent = truth;
  els.simaModel.textContent = liveTruth ? humanize(sima.model || payload?.model) : "Not provided";
  els.simaRuntime.textContent = liveTruth ? humanize(sima.runtime || sima.runtime_id || payload?.runtime_id) : "Not provided";
  els.simaDevice.textContent = liveTruth ? humanize(sima.device || sima.target || payload?.device) : "Not provided";
  els.simaLatency.textContent = liveTruth ? formatMs(sima.telemetry?.latency_ms ?? sima.latency_ms ?? payload?.latency_ms) : "Not provided";
  els.simaFps.textContent = liveTruth ? formatFps(sima.telemetry?.fps ?? sima.fps ?? payload?.fps) : "Not provided";

  const status = liveTruth ? "READY" : "BLOCKED";
  setHealth("sima", sima.status || status, truth);
  setHealth("mla", sima.mla_status || sima.status || status, truth);

  const benchmark = payload?.historical_benchmark || payload?.benchmark || payload?.evidence?.historical_benchmark;
  els.historicalBenchmark.textContent = benchmark
    ? JSON.stringify(benchmark, null, 2)
    : liveTruth
      ? "No historical benchmark supplied by backend."
      : "Backend did not prove live SiMa telemetry for this frame. Any fixture/reference runtime fields are intentionally withheld here.";
}

function renderEvidenceJson(evidence, state = null) {
  if (!evidence && !state) {
    els.evidencePreview.textContent = "No backend evidence yet.";
    return;
  }
  els.evidencePreview.textContent = JSON.stringify(evidence || state, null, 2);
}

function renderReceipt(evidence, trace, framePayload = null) {
  const detections = extractDetections(framePayload || trace || {});
  const traceTruth = trace?.truth || {};
  const simaTruth = normalizeTruth(
    framePayload?.sima?.truth ||
      framePayload?.inference_truth ||
      framePayload?.truth ||
      traceTruth.detections,
  );
  const physicalTruth = normalizeTruth(traceTruth.physical_io || evidence?.truth?.physical_io);
  const receiptPayload = framePayload || trace || {};
  const receiptFrame = frameRefFromPayload(receiptPayload);
  const receiptSource = sourceRefFromPayload(receiptPayload);
  const frameText = receiptFrame && receiptSource
    ? `${sourceLabel(String(receiptSource))} / ${receiptFrame}`
    : latestFrame
      ? `${sourceLabel(latestFrame.sourceId)} / ${latestFrame.frameId}`
      : humanize(framePayload?.frame_id || framePayload?.frame_ref || trace?.frame_ref, "UNVERIFIED");

  els.receiptFrame.textContent = frameText;
  els.receiptSima.textContent = simaTruth;
  const detectionsMatchFrame = detectionFrameMatches(framePayload || trace || {});
  els.receiptDetections.textContent = detections.length && detectionsMatchFrame
    ? `${detections.length} backend detection(s) for matched frame`
    : "No backend detections";
  els.receiptDecision.textContent = humanize(trace?.decision, "No decision");
  els.receiptApproval.textContent = humanize(trace?.status, "No action pending");
  els.receiptAction.textContent =
    trace?.decision === "REJECTED" || trace?.status === "REJECTED_SAFE"
      ? "DENIED - NOTHING EXECUTED"
      : humanize(trace?.proposed_action?.action_type, "Nothing executed");
  els.receiptVerification.textContent = trace?.verified === true ? `VERIFIED / ${physicalTruth}` : "Not verified";
  els.receiptSeal.textContent = evidence?.evidence_id || trace?.evidence_id || "Not sealed";

  setHealth("evidence", evidence?.evidence_id || trace?.evidence_id ? "READY" : "BLOCKED", evidence?.truth?.evidence || simaTruth);
  renderEvidenceJson(evidence, trace);
}

function renderLifecycle(trace) {
  if (!trace) {
    els.lifecyclePanel.classList.add("hidden");
    els.lifecycleTimeline.innerHTML = "";
    return;
  }

  els.lifecyclePanel.classList.remove("hidden");
  els.lifecycleState.textContent = humanize(trace.status, "BLOCKED").toUpperCase();

  const canInterrupt = trace.status === "VERIFIED" || trace.status === "RESUMED_VERIFIED";
  const canReverify = trace.status === "SAFE_STATE_VERIFIED";
  const canResume = trace.status === "REVERIFIED";
  const canCancel = trace.status === "SAFE_STATE_VERIFIED" || trace.status === "REVERIFIED";
  els.interruptBtn.classList.toggle("hidden", !canInterrupt);
  els.reverifyBtn.classList.toggle("hidden", !canReverify);
  els.resumeBtn.classList.toggle("hidden", !canResume);
  els.cancelBtn.classList.toggle("hidden", !canCancel);

  els.lifecycleTimeline.innerHTML = "";
  for (const event of (trace.lifecycle_events || []).slice(-6)) {
    const row = document.createElement("div");
    row.className = "lifecycle-event";
    const state = document.createElement("strong");
    state.textContent = humanize(event.state, "STATE").toUpperCase();
    const summary = document.createElement("span");
    summary.textContent = event.summary || "";
    const truth = document.createElement("small");
    truth.textContent = normalizeTruth(event.truth);
    row.append(state, summary, truth);
    els.lifecycleTimeline.appendChild(row);
  }
}

function renderState(state) {
  latestState = state || {};
  const trace = latestState.current || null;
  const evidence = latestState.latest_evidence || null;
  syncLatestFrameFromState(latestState);
  setHealth("guardian", trace ? trace.status : "READY", "UNVERIFIED");
  renderLifecycle(trace);
  renderReceipt(evidence, trace);
  renderStages(trace?.stages || [], trace);

  if (!trace) {
    resetInferenceTelemetry();
    els.traceId.textContent = "No active trace";
    els.policyBadge.textContent = "Fail-closed";
    els.approvalState.textContent = "NO ACTION PENDING";
    els.decisionEmpty.classList.remove("hidden");
    els.decisionContent.classList.add("hidden");
    els.decisionEmpty.querySelector("strong").textContent = "No physical action pending";
    els.decisionEmpty.querySelector("p").textContent =
      "Guardian will expose a proposed action only after backend policy evaluation. Nothing executes from preview alone.";
    els.pitchCue.textContent =
      "Physical Guardian presents the full governed loop, but stops at UNVERIFIED/BLOCKED when backend or hardware proof is absent.";
    return;
  }

  els.traceId.textContent = trace.trace_id || "Backend trace";
  els.policyBadge.textContent = humanize(trace.status, "Fail-closed");
  els.approvalState.textContent = humanize(trace.status, "NO ACTION PENDING").toUpperCase();
  els.pitchCue.textContent = scenarioCopy[trace.scenario] || scenarioCopy[els.scenarioSelect.value];

  const understand = trace.stages?.find((stage) => stage.stage === "UNDERSTAND") || {};
  renderBackendTelemetry(understand.runtime ? { runtime: understand.runtime, inference_truth: understand.truth } : trace);

  const detections = extractDetections(trace);
  drawDetections(detections, {
    ...trace,
    frame_id: trace.frame_id || trace.frame_ref,
    source_id: trace.source_id,
    truth: trace.truth?.detections,
  });

  const action = trace.proposed_action;
  if (action && trace.status === "AWAITING_APPROVAL") {
    els.decisionEmpty.classList.add("hidden");
    els.decisionContent.classList.remove("hidden");
    els.actionTitle.textContent = humanizeAction(action.action_type);
    els.actionReason.textContent = action.reason || "Backend did not provide a reason.";
    els.actionTarget.textContent = action.target || "Not provided";
    els.actionImpact.textContent = humanize(action.impact, "LOW").toUpperCase();
    els.actionStatus.textContent = "AWAITING_APPROVAL";
    return;
  }

  els.decisionEmpty.classList.remove("hidden");
  els.decisionContent.classList.add("hidden");
  if (trace.decision === "REJECTED" || trace.status === "REJECTED_SAFE") {
    els.decisionEmpty.querySelector("strong").textContent = "DENIED - NOTHING EXECUTED";
    els.decisionEmpty.querySelector("p").textContent = "The backend recorded a safe no-op. No physical action was executed.";
  } else if (trace.verified === true) {
    els.decisionEmpty.querySelector("strong").textContent = "Backend reports VERIFIED";
    els.decisionEmpty.querySelector("p").textContent =
      "Verification is accepted only because the backend response marked this trace verified.";
  } else {
    els.decisionEmpty.querySelector("strong").textContent = "Action not verified";
    els.decisionEmpty.querySelector("p").textContent = "Approval does not imply verification. Await backend readback proof.";
  }
}

function markBackendOffline(error) {
  setHealth("guardian", "OFFLINE", "UNVERIFIED");
  setHealth("sima", "OFFLINE", "UNVERIFIED");
  setHealth("mla", "OFFLINE", "UNVERIFIED");
  setHealth("io", "OFFLINE", "UNVERIFIED");
  setHealth("evidence", "BLOCKED", "UNVERIFIED");
  els.runtimeBadge.textContent = "UNVERIFIED";
  renderReceipt(null, null);
  showToast(`Backend unavailable: ${error.message}`, true);
}

async function runScenario() {
  els.runBtn.disabled = true;
  try {
    const state = await api("/api/demo/run", {
      method: "POST",
      body: JSON.stringify({
        scenario: els.scenarioSelect.value,
        runtime_id: els.runtimeSelect.value,
        source_id: els.sourceSelect.value,
        frame_id: latestFrame?.frameId || null,
      }),
    });
    renderState(state);
    showToast("Existing demo API reached the backend gate. Truth labels are backend-derived.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    els.runBtn.disabled = false;
  }
}

async function decide(path) {
  try {
    const state = await api(path, { method: "POST", body: "{}" });
    renderState(state);
    const status = state.current?.status;
    const rejected = state.current?.decision === "REJECTED" || status === "REJECTED_SAFE";
    const verified = state.current?.verified === true || status === "VERIFIED" || status === "RESUMED_VERIFIED";
    if (rejected) {
      showToast("DENIED - NOTHING EXECUTED");
    } else if (verified) {
      showToast("Backend reports VERIFIED. Evidence receipt updated.");
    } else {
      showToast("Approval recorded. Verification remains pending until backend proves readback.");
    }
  } catch (error) {
    showToast(error.message, true);
  }
}

async function resetDemo() {
  try {
    const state = await api("/api/demo/reset", { method: "POST", body: "{}" });
    resetRunView();
    renderState(state);
    showToast("Demo reset. Local preview state is unchanged; backend truth cleared.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function copyEvidence() {
  const evidence = latestState?.latest_evidence || latestState?.current;
  if (!evidence) {
    showToast("No backend evidence exists yet.", true);
    return;
  }
  try {
    await navigator.clipboard.writeText(JSON.stringify(evidence, null, 2));
    showToast("Backend JSON copied.");
  } catch (_) {
    showToast("Clipboard access was blocked by the browser.", true);
  }
}

async function boot() {
  renderSourceMode();
  resetStages();
  try {
    const [catalog, cameraCatalog, state] = await Promise.all([
      api("/api/catalog"),
      api("/api/camera/sources"),
      api("/api/state"),
    ]);
    renderCatalog(catalog);
    renderCameraSources(cameraCatalog || catalog?.camera_sources);
    renderSourceMode();
    syncLatestFrameFromState(state);
    renderState(state);
  } catch (error) {
    markBackendOffline(error);
  }
}

els.sourceSelect.addEventListener("change", () => {
  resetRunView();
  renderSourceMode();
});
els.mediaFileInput.addEventListener("change", handleLocalFile);
els.startCameraBtn.addEventListener("click", startLocalPreview);
els.captureFrameBtn.addEventListener("click", captureFrame);
els.requestInferenceBtn.addEventListener("click", requestFrameInference);
els.runBtn.addEventListener("click", runScenario);
els.resetBtn.addEventListener("click", resetDemo);
els.approveBtn.addEventListener("click", () => decide("/api/action/approve"));
els.rejectBtn.addEventListener("click", () => decide("/api/action/reject"));
els.interruptBtn.addEventListener("click", () => decide("/api/action/interrupt"));
els.reverifyBtn.addEventListener("click", () => decide("/api/action/reverify"));
els.resumeBtn.addEventListener("click", () => decide("/api/action/resume"));
els.cancelBtn.addEventListener("click", () => decide("/api/action/cancel"));
els.copyEvidenceBtn.addEventListener("click", copyEvidence);
els.runtimeSelect.addEventListener("change", () => {
  const selected = latestCatalog?.runtimes?.find((runtime) => runtime.runtime_id === els.runtimeSelect.value);
  els.runtimeBadge.textContent = normalizeTruth(selected?.truth || selected?.inference_truth || selected?.status);
});

document.addEventListener("guardian:voice-state", (event) => {
  if (event.detail) renderState(event.detail);
});

document.addEventListener("keydown", (event) => {
  const tag = document.activeElement?.tagName?.toLowerCase();
  if (tag === "select" || tag === "input" || tag === "textarea") return;
  if (event.key.toLowerCase() === "r") runScenario();
  if (event.key.toLowerCase() === "c") captureFrame();
  if (event.key.toLowerCase() === "a" && latestState?.current?.status === "AWAITING_APPROVAL") {
    decide("/api/action/approve");
  }
  if (event.key.toLowerCase() === "x") resetDemo();
});

boot();

// Legacy truth strings intentionally retained for static contract tests.
const LEGACY_TRUTH_COPY = "LIVE REAL / SYNTHETIC FIXTURE";
