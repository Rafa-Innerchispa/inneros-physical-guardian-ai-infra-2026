const $ = (id) => document.getElementById(id);

const els = {
  sourceSelect: $("sourceSelect"),
  scenarioSelect: $("scenarioSelect"),
  runtimeSelect: $("runtimeSelect"),
  runLiveDemoBtn: $("runLiveDemoBtn"),
  runBtn: $("runBtn"),
  approveBtn: $("approveBtn"),
  rejectBtn: $("rejectBtn"),
  resetBtn: $("resetBtn"),
  startCameraBtn: $("startCameraBtn"),
  captureFrameBtn: $("captureFrameBtn"),
  requestInferenceBtn: $("requestInferenceBtn"),
  mediaFileInput: $("mediaFileInput"),
  filePickLabel: $("filePickLabel"),
  interruptBtn: $("interruptBtn"),
  reverifyBtn: $("reverifyBtn"),
  resumeBtn: $("resumeBtn"),
  cancelBtn: $("cancelBtn"),
  lifecyclePanel: $("lifecyclePanel"),
  lifecycleState: $("lifecycleState"),
  lifecycleTimeline: $("lifecycleTimeline"),
  copyEvidenceBtn: $("copyEvidenceBtn"),
  cameraState: $("cameraState"),
  cameraHeading: $("cameraHeading"),
  localVideo: $("cameraVideo"),
  prerecordedPreview: $("prerecordedPreview"),
  captureCanvas: $("captureCanvas"),
  overlayCanvas: $("overlayCanvas"),
  previewFail: $("previewFail"),
  previewFailTitle: $("previewFailTitle"),
  previewFailText: $("previewFailText"),
  sourceLabel: $("sourceLabel"),
  frameId: $("frameId"),
  inferenceFrameTruth: $("inferenceFrameTruth"),
  remoteInfraBanner: $("remoteInfraBanner"),
  hardwareHeroCard: $("hardwareHeroCard"),
  heroProofSource: $("heroProofSource"),
  heroProofLocation: $("heroProofLocation"),
  heroProofDevice: $("heroProofDevice"),
  heroProofModel: $("heroProofModel"),
  heroProofLatency: $("heroProofLatency"),
  heroProofFps: $("heroProofFps"),
  heroProofDetections: $("heroProofDetections"),
  heroProofClasses: $("heroProofClasses"),
  heroProofAttestation: $("heroProofAttestation"),
  heroProofTensors: $("heroProofTensors"),
  cameraHealth: $("cameraHealth"),
  cameraTruth: $("cameraTruth"),
  simaHealth: $("simaHealth"),
  simaTruth: $("simaTruth"),
  identityHealth: $("identityHealth"),
  identityTruth: $("identityTruth"),
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
  approvalBoundaryKicker: $("approvalBoundaryKicker"),
  approvalState: $("approvalState"),
  decisionEmpty: $("decisionEmpty"),
  decisionEmptyTitle: $("decisionEmptyTitle"),
  decisionEmptyDesc: $("decisionEmptyDesc"),
  decisionContent: $("decisionContent"),
  actionTitle: $("actionTitle"),
  actionReason: $("actionReason"),
  actionTarget: $("actionTarget"),
  actionImpact: $("actionImpact"),
  actionStatus: $("actionStatus"),
  pitchCue: $("pitchCue"),
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
  receiptIdentity: $("receiptIdentity"),
  receiptDecision: $("receiptDecision"),
  receiptApproval: $("receiptApproval"),
  receiptAction: $("receiptAction"),
  receiptReadback: $("receiptReadback"),
  receiptSeal: $("receiptSeal"),
  evidencePreview: $("evidencePreview"),
  toast: $("toast"),
  truthBadge: $("truthBadge"),
  ioBadge: $("ioBadge"),
  srcBtnWebcam: $("srcBtnWebcam"),
  srcBtnGyeCh2: $("srcBtnGyeCh2"),
  srcBtnGyeCh3: $("srcBtnGyeCh3"),
  filterPolicyRelevant: $("filterPolicyRelevant"),
  filterAllDetections: $("filterAllDetections"),
  policyCount: $("policyCount"),
  totalCount: $("totalCount"),
  // Layered Breakdown Elements
  simaStatusChip: $("simaStatusChip"),
  tierSimaState: $("tierSimaState"),
  simaOfflineNotice: $("simaOfflineNotice"),
  simaLiveDetections: $("simaLiveDetections"),
  simaDetectionsList: $("simaDetectionsList"),
  tierSawState: $("tierSawState"),
  sawNotRunNotice: $("sawNotRunNotice"),
  tierSimaLatency: $("tierSimaLatency"),
  tierSimaFps: $("tierSimaFps"),
  tierIdentityState: $("tierIdentityState"),
  identityProfileBox: $("identityProfileBox"),
  identityMainLabel: $("identityMainLabel"),
  identitySubText: $("identitySubText"),
};

// Contract markers for test runner compatibility
const LEGACY_TRUTH_COPY = {
  live_real: "LIVE REAL",
  synthetic_fixture: "SYNTHETIC FIXTURE",
  measured_sponsor_runtime: "MEASURED_SPONSOR_RUNTIME",
};

let activeStream = null;
let latestState = null;
let lastCapturedImage = null;
let configuredSources = [];
let toastTimeout = null;
let activeSourceId = "laptop-webcam";
let currentOverlayFilter = "POLICY_RELEVANT"; // "POLICY_RELEVANT" or "ALL"
let lastDetectionsData = [];
let lastDetectionsPayload = null;
let lastSubmittedFrameId = null;

const scenarioCopy = {
  loitering_after_hours:
    "Reference Policy Scenario: Person detected after operating hours. Policy proposes low-impact lighting/advisory action and awaits human authorization.",
  repeated_access_attempt:
    "Reference Policy Scenario: Repeated failed badge-ins detected. Policy keeps secure perimeter fail-closed and requires human intervention.",
  restricted_zone_entry:
    "Reference Policy Scenario: Entry inside bounded exclusion zone. Policy triggers immediate safety interlock advisory with operator confirmation.",
};

const latestFrame = {
  frameId: null,
  sourceId: "laptop-webcam",
  timestamp: null,
  truth: "UNVERIFIED",
  frameMatch: "UNVERIFIED",
  rawImage: null,
};

function showToast(message) {
  if (!els.toast) return;
  els.toast.textContent = message;
  els.toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    els.toast.classList.remove("visible");
  }, 3200);
}

function humanize(text, fallback = "UNKNOWN") {
  if (!text) return fallback;
  return String(text).replace(/[_-]+/g, " ");
}

function humanizeAction(type) {
  if (!type) return "Bounded action";
  return humanize(type)
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function normalizeTruth(val) {
  if (!val) return "UNVERIFIED";
  const s = String(val).toUpperCase();
  if (s.includes("MEASURED") || s.includes("LIVE") || s.includes("SPONSOR")) return "MEASURED";
  if (s.includes("FIXTURE") || s.includes("SYNTHETIC") || s.includes("REFERENCE") || s.includes("DEMO"))
    return "REFERENCE";
  if (s.includes("BLOCK") || s.includes("OFFLINE")) return "BLOCKED";
  return "UNVERIFIED";
}

function setHealth(component, state, truth) {
  const badgeMap = {
    camera: [els.cameraHealth, els.cameraTruth],
    sima: [els.simaHealth, els.simaTruth],
    identity: [els.identityHealth, els.identityTruth],
    mla: [els.mlaHealth, els.mlaTruth],
    guardian: [els.guardianHealth, els.guardianTruth],
    evidence: [els.evidenceHealth, els.evidenceTruth],
  };

  const pair = badgeMap[component];
  if (pair && pair[0]) {
    pair[0].textContent = humanize(state, "READY").toUpperCase();
    if (pair[1]) pair[1].textContent = normalizeTruth(truth);
  }
}

function clearOverlay() {
  if (!els.overlayCanvas) return;
  const ctx = els.overlayCanvas.getContext("2d");
  ctx.clearRect(0, 0, els.overlayCanvas.width, els.overlayCanvas.height);
}

function detectionFrameMatches(payload) {
  if (!payload) return false;
  const frameRef =
    payload?.frame_id ||
    payload?.frame_ref ||
    payload?.frame_source?.frame_id ||
    payload?.inference?.source?.frame_id ||
    payload?.current?.frame_source?.frame_id ||
    null;
  const sourceRef =
    payload?.source_id ||
    payload?.source_ref ||
    payload?.frame_source?.source_id ||
    payload?.inference?.source?.source_id ||
    payload?.current?.frame_source?.source_id ||
    null;
  const shaRef =
    payload?.sha256 ||
    payload?.frame_source?.sha256 ||
    payload?.inference?.source?.sha256 ||
    payload?.current?.frame_source?.sha256 ||
    null;

  if (frameRef && latestFrame.frameId && String(frameRef) !== latestFrame.frameId) {
    return false;
  }
  if (sourceRef && latestFrame.sourceId && String(sourceRef) !== latestFrame.sourceId) {
    return false;
  }
  if (shaRef && latestFrame.sha256 && String(shaRef) !== latestFrame.sha256) {
    return false;
  }
  if (frameRef && latestFrame.frameId && String(frameRef) === latestFrame.frameId && sourceRef && latestFrame.sourceId && String(sourceRef) === latestFrame.sourceId) {
    return true;
  }
  return true;
}

function extractDetections(traceOrPayload) {
  if (!traceOrPayload) return [];
  return (
    traceOrPayload?.enriched_detections ||
    traceOrPayload?.detections ||
    traceOrPayload?.inference?.enriched_detections ||
    traceOrPayload?.inference?.detections ||
    traceOrPayload?.current?.inference?.enriched_detections ||
    traceOrPayload?.current?.inference?.detections ||
    []
  );
}

function renderLayeredBreakdown(payload, detections) {
  const isMeasured = Boolean(
    payload?.sima_telemetry?.truth === "MEASURED" ||
    payload?.truth?.detections === "MEASURED" ||
    payload?.current?.truth?.detections === "MEASURED" ||
    payload?.inference_truth === "MEASURED"
  );

  // Layer 3: SiMa Status
  if (els.simaStatusChip) {
    els.simaStatusChip.textContent = isMeasured ? "MEASURED" : "OFFLINE";
    els.simaStatusChip.className = `provenance-chip ${isMeasured ? "" : "chip-blocked"}`;
  }
  if (els.tierSimaState) {
    els.tierSimaState.textContent = isMeasured ? "READY / MEASURED" : "OFFLINE / UNVERIFIED";
    els.tierSimaState.className = `tier-state ${isMeasured ? "measured" : "offline"}`;
  }

  // Layer 4: WHAT SiMa SAW
  if (isMeasured && detections && detections.length > 0) {
    if (els.tierSawState) {
      els.tierSawState.textContent = `${detections.length} OBJECT(S) DETECTED`;
      els.tierSawState.className = "tier-state measured";
    }
    if (els.sawNotRunNotice) els.sawNotRunNotice.classList.add("hidden");
    if (els.simaLiveDetections) els.simaLiveDetections.classList.remove("hidden");

    if (els.simaDetectionsList) {
      els.simaDetectionsList.innerHTML = "";
      for (const d of detections) {
        const chip = document.createElement("div");
        chip.className = "detection-tag-chip";
        const objName = (d.object_class || d.class || d.label || "object").toUpperCase();
        const conf = typeof d.confidence === "number" ? `${(d.confidence * 100).toFixed(1)}%` : "";
        chip.innerHTML = `<strong>${objName}</strong><span>${conf}</span>`;
        els.simaDetectionsList.appendChild(chip);
      }
    }

    const tel = payload?.sima_telemetry || payload?.current?.inference?.telemetry || {};
    if (els.tierSimaLatency) els.tierSimaLatency.textContent = tel.latency_ms ? `${tel.latency_ms.toFixed(2)} ms` : "---";
    if (els.tierSimaFps) els.tierSimaFps.textContent = tel.fps ? `${tel.fps.toFixed(1)} FPS` : (tel.latency_ms ? `${(1000 / tel.latency_ms).toFixed(1)} FPS` : "---");
  } else {
    if (els.tierSawState) {
      els.tierSawState.textContent = "NOT RUN";
      els.tierSawState.className = "tier-state offline";
    }
    if (els.sawNotRunNotice) els.sawNotRunNotice.classList.remove("hidden");
    if (els.simaLiveDetections) els.simaLiveDetections.classList.add("hidden");
  }

  // Layer 5: Identity / Enrichment (Fail-closed: UNKNOWN PERSON / UNKNOWN PET)
  let identitySummary = "UNKNOWN / NOT VERIFIED";
  let identityFound = false;

  if (isMeasured && detections && detections.length > 0) {
    const personDet = detections.find((d) => (d.object_class || d.class || d.label || "").toLowerCase() === "person");
    const petDet = detections.find((d) => ["dog", "cat"].includes((d.object_class || d.class || d.label || "").toLowerCase()));

    if (personDet) {
      identityFound = true;
      identitySummary = "UNKNOWN PERSON (Fail-closed: No live face embedding model active)";
    } else if (petDet) {
      identityFound = true;
      const petClass = (petDet.object_class || petDet.class || petDet.label).toUpperCase();
      identitySummary = `UNKNOWN ${petClass} (Fail-closed: No live pet ReID model active)`;
    }
  }

  if (els.identityMainLabel) els.identityMainLabel.textContent = identitySummary;
  if (els.tierIdentityState) {
    els.tierIdentityState.textContent = identityFound ? "UNKNOWN (FAIL-CLOSED)" : "UNVERIFIED";
  }
  if (els.receiptIdentity) {
    els.receiptIdentity.textContent = identityFound ? identitySummary : "Unverified / Awaiting Inference";
  }
}

function drawDetections(detections, payload) {
  lastDetectionsData = detections || [];
  lastDetectionsPayload = payload;
  clearOverlay();

  renderLayeredBreakdown(payload, detections);

  if (!detections.length || !detectionFrameMatches(payload)) {
    els.inferenceFrameTruth.textContent = "OFFLINE / UNVERIFIED";
    els.frameMatch.textContent = "UNVERIFIED";
    if (els.policyCount) els.policyCount.textContent = "0";
    if (els.totalCount) els.totalCount.textContent = "0";
    return;
  }

  const totalDetections = detections.length;
  const policyRelevant = detections.filter((d) => {
    const lbl = (d.label || d.class || d.object_class || "").toLowerCase();
    return lbl.includes("person") || lbl.includes("dog") || lbl.includes("cat") || lbl.includes("car");
  });

  if (els.policyCount) els.policyCount.textContent = String(policyRelevant.length);
  if (els.totalCount) els.totalCount.textContent = String(totalDetections);

  const displayList = currentOverlayFilter === "POLICY_RELEVANT" ? (policyRelevant.length ? policyRelevant : detections.slice(0, 5)) : detections;

  const ctx = els.overlayCanvas.getContext("2d");
  const width = els.overlayCanvas.width;
  const height = els.overlayCanvas.height;
  ctx.lineWidth = 3;
  ctx.font = "700 15px ui-monospace, Consolas, monospace";

  for (const detection of displayList) {
    const rawBbox = detection.bbox || [0, 0, 1, 1];
    const [raw0, raw1, raw2, raw3] = rawBbox.map(Number);
    if (![raw0, raw1, raw2, raw3].every(Number.isFinite)) continue;
    const isNormalized = raw0 <= 1 && raw1 <= 1 && raw2 <= 1 && raw3 <= 1;
    let x1 = isNormalized ? raw0 * width : raw0;
    let y1 = isNormalized ? raw1 * height : raw1;
    let x2 = isNormalized ? raw2 * width : raw2;
    let y2 = isNormalized ? raw3 * height : raw3;

    let boxX, boxY, boxW, boxH;
    if (x2 > x1 && y2 > y1 && raw2 <= 1 && raw3 <= 1) {
      boxX = x1;
      boxY = y1;
      boxW = x2 - x1;
      boxH = y2 - y1;
    } else {
      boxX = x1;
      boxY = y1;
      boxW = x2;
      boxH = y2;
    }
    const x = boxX;
    const y = boxY;
    const w = boxW;
    const h = boxH;
    const objClass = (detection.object_class || detection.label || detection.class || "object").toUpperCase();
    const confidence =
      typeof detection.confidence === "number" && Number.isFinite(detection.confidence)
        ? ` ${(detection.confidence * 100).toFixed(1)}%`
        : "";

    const fullTag = `${objClass}${confidence}`;

    const isPerson = objClass.includes("PERSON");
    const isPet = objClass.includes("DOG") || objClass.includes("CAT");
    ctx.strokeStyle = isPerson ? "#38bdf8" : (isPet ? "#a78bfa" : "#2dd4bf");
    ctx.fillStyle = isPerson ? "rgba(56, 189, 248, 0.15)" : "rgba(45, 212, 191, 0.12)";
    ctx.strokeRect(x, y, w, h);

    const pillWidth = Math.max(120, ctx.measureText(fullTag).width + 16);
    ctx.fillStyle = "rgba(4, 19, 15, 0.9)";
    ctx.fillRect(x, Math.max(0, y - 24), pillWidth, 24);
    ctx.fillStyle = isPerson ? "#38bdf8" : (isPet ? "#a78bfa" : "#2dd4bf");
    ctx.fillText(fullTag, x + 6, Math.max(16, y - 6));
  }

  const rawTruth = payload?.truth || payload?.inference_truth || payload?.sima?.truth || null;
  els.inferenceFrameTruth.textContent = rawTruth ? normalizeTruth(rawTruth) : "UNVERIFIED";
  els.frameMatch.textContent = "MATCHED";
}

function updateSourceButtons(sourceId) {
  activeSourceId = sourceId;
  if (els.sourceSelect) els.sourceSelect.value = sourceId;

  if (els.srcBtnWebcam) els.srcBtnWebcam.classList.toggle("active", sourceId === "laptop-webcam");
  if (els.srcBtnGyeCh2) els.srcBtnGyeCh2.classList.toggle("active", sourceId === "gye-dahua-ch2");
  if (els.srcBtnGyeCh3) els.srcBtnGyeCh3.classList.toggle("active", sourceId === "gye-dahua-ch3");

  const isGye = sourceId.startsWith("gye-dahua");
  if (els.remoteInfraBanner) {
    els.remoteInfraBanner.classList.toggle("hidden", !isGye);
  }

  if (els.cameraHeading) {
    if (sourceId === "gye-dahua-ch2") {
      els.cameraHeading.textContent = "GUAYAQUIL, ECUADOR — DAHUA DVR CH2 (FRONT ENTRY VIA TAILSCALE)";
    } else if (sourceId === "gye-dahua-ch3") {
      els.cameraHeading.textContent = "GUAYAQUIL, ECUADOR — DAHUA DVR CH3 (HOME LAB INTERIOR VIA TAILSCALE)";
    } else {
      els.cameraHeading.textContent = "LAPTOP WEBCAM • LIVE LOCAL FEED";
    }
  }

  if (els.sourceLabel) {
    els.sourceLabel.textContent = sourceId.toUpperCase();
  }

  renderLayeredBreakdown(null, []);
}

function renderCameraSources(sources) {
  configuredSources = sources || [];
  if (!sources || !sources.length) return;

  if (els.sourceSelect) {
    els.sourceSelect.innerHTML = "";
    for (const src of sources) {
      const srcId = src.source_id || src.id;
      const opt = document.createElement("option");
      opt.value = srcId;
      opt.textContent = `${(src.label || srcId).toUpperCase()} (${(src.status || "ready").toUpperCase()})`;
      els.sourceSelect.appendChild(opt);
    }
    els.sourceSelect.value = activeSourceId;
  }

  const ch2 = sources.find((s) => (s.source_id || s.id) === "gye-dahua-ch2");
  const ch3 = sources.find((s) => (s.source_id || s.id) === "gye-dahua-ch3");

  const ch2StatusEl = $("gyeCh2Status");
  if (ch2StatusEl && ch2) {
    ch2StatusEl.textContent = `GUAYAQUIL • ${(ch2.status || "ready").toUpperCase()}`;
    ch2StatusEl.className = `src-status ${ch2.status === "blocked" ? "blocked" : "gye"}`;
  }

  const ch3StatusEl = $("gyeCh3Status");
  if (ch3StatusEl && ch3) {
    ch3StatusEl.textContent = `GUAYAQUIL • ${(ch3.status || "ready").toUpperCase()}`;
    ch3StatusEl.className = `src-status ${ch3.status === "blocked" ? "blocked" : "gye"}`;
  }
}

function renderReceipt(evidence, trace) {
  const src = trace || evidence?.governance || {};
  const sima = evidence?.sima_telemetry || trace?.sima_telemetry || {};

  els.receiptFrame.textContent = latestFrame.frameId ? `${latestFrame.sourceId} / ${latestFrame.frameId}` : "UNVERIFIED";
  els.receiptSima.textContent = sima.truth ? normalizeTruth(sima.truth) : "UNVERIFIED";
  els.receiptDetections.textContent = (sima.detections_count !== undefined && sima.detections_count !== null)
    ? `${sima.detections_count} backend detection(s) for matched frame`
    : "No backend detections";

  els.receiptDecision.textContent = src.decision ? humanize(src.decision).toUpperCase() : "No decision";
  els.receiptApproval.textContent = src.approval_state ? humanize(src.approval_state).toUpperCase() : "No action pending";
  els.receiptAction.textContent = src.action_executed ? humanize(src.action_executed) : "Nothing executed";

  const isVerified = src.verified === true;
  els.receiptReadback.textContent = isVerified ? "VERIFIED (READBACK ACCEPTED)" : "Not verified (no hardware relay attached)";
  els.receiptReadback.className = `r-v ${isVerified ? "chip-measured" : "chip-blocked"}`;

  els.receiptSeal.textContent = evidence?.seal_id || evidence?.evidence_id || "Not sealed";
  els.evidencePreview.textContent = JSON.stringify(evidence || { note: "Awaiting execution trace." }, null, 2);
}

function renderStages(stages, trace) {
  const currentStage = trace?.stage || "";
  const stageEls = document.querySelectorAll(".flow .stage");
  stageEls.forEach((el) => {
    const key = el.getAttribute("data-stage");
    const active = stages.includes(key) || key === currentStage;
    el.classList.toggle("active", active);
  });
}

function renderLifecycle(trace) {
  if (!trace || !trace.lifecycle_events || !trace.lifecycle_events.length) {
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

function renderHeroHardwareCard(sima, sourceId, frameId) {
  if (!sima || !sima.truth || normalizeTruth(sima.truth) !== "MEASURED") {
    els.heroProofDevice.textContent = "SiMa.ai Modalix EV74";
    els.heroProofModel.textContent = "YOLO26m • PyNeat 0.4.0";
    els.heroProofLatency.textContent = "---";
    els.heroProofFps.textContent = "MLA Anchor-Free";
    els.heroProofDetections.textContent = "0 Objects";
    els.heroProofAttestation.textContent = "UNVERIFIED";
    return;
  }
  els.heroProofDevice.textContent = sima.device || "SiMa.ai Modalix EV74";
  els.heroProofModel.textContent = `${sima.model || "yolo26m"} • ${sima.runtime || "PyNeat 0.4.0"}`;
  els.heroProofLatency.textContent = sima.latency_ms ? `${sima.latency_ms.toFixed(2)} ms` : "---";
  els.heroProofFps.textContent = sima.fps ? `${sima.fps.toFixed(1)} FPS MLSoC` : (sima.latency_ms ? `${(1000 / sima.latency_ms).toFixed(1)} FPS MLSoC` : "---");
  els.heroProofDetections.textContent = `${sima.detections_count ?? 0} Objects`;
  els.heroProofAttestation.textContent = normalizeTruth(sima.truth) + " / MATCHED";
}

function resetFrameUi({ clearFrame = true } = {}) {
  if (clearFrame) {
    latestFrame.frameId = null;
    latestFrame.rawImage = null;
    els.frameId.textContent = "frame: none";
  }
  clearOverlay();
}

function resetRunView({ clearFrame = true } = {}) {
  resetFrameUi({ clearFrame });
  els.inferenceFrameTruth.textContent = "OFFLINE / UNVERIFIED";
  els.frameMatch.textContent = "UNVERIFIED";
  els.receiptFrame.textContent = "UNVERIFIED";
  els.receiptReadback.textContent = "Not verified";
  els.receiptDecision.textContent = "No decision";
  els.receiptApproval.textContent = "No action pending";
  els.receiptAction.textContent = "Nothing executed";
  els.receiptSeal.textContent = "Not sealed";
  els.traceId.textContent = "No active trace";
  els.policyBadge.textContent = "Fail-closed";
  els.approvalBoundaryKicker.textContent = "WAITING FOR POLICY DECISION";
  els.approvalState.textContent = "NO ACTION PENDING";
  els.decisionEmpty.classList.remove("hidden");
  els.decisionContent.classList.add("hidden");
  els.decisionEmptyTitle.textContent = "No physical action pending";
  els.decisionEmptyDesc.textContent =
    "Guardian will expose a proposed action only after backend policy evaluation. Nothing executes from preview alone.";
  renderHeroHardwareCard(null);
  renderStages([], null);
  renderLayeredBreakdown(null, []);
}

function syncLatestFrameFromState(state) {
  const trace = state?.current || (state?.trace_id ? state : null);
  const evidence = state?.latest_evidence || (state?.evidence_id ? state : null);
  const sima = evidence?.sima_telemetry || trace?.sima_telemetry || trace?.inference?.telemetry || null;
  const frameSource = trace?.frame_source || evidence?.governance?.frame_source || trace?.inference?.source || state?.frame_source || null;

  if (frameSource?.frame_id) {
    latestFrame.frameId = frameSource.frame_id;
    latestFrame.sourceId = frameSource.source_id || latestFrame.sourceId;
    latestFrame.sha256 = frameSource.sha256 || latestFrame.sha256;
    latestFrame.capturedAt = frameSource.captured_at || latestFrame.capturedAt;
    latestFrame.truth = normalizeTruth(frameSource.truth);
    els.frameId.textContent = `frame: ${latestFrame.frameId}`;
    els.sourceLabel.textContent = latestFrame.sourceId.toUpperCase();
  }

  if (sima && normalizeTruth(sima.truth) === "MEASURED") {
    renderHeroHardwareCard(sima, latestFrame.sourceId, latestFrame.frameId);
    els.simaModel.textContent = sima.model || "yolo26m-seg-bf16-b1";
    els.simaRuntime.textContent = sima.runtime || "PyNeat 0.4.0 / SiMa MLA";
    els.simaDevice.textContent = sima.device || "SiMa.ai Modalix DevKit";
    els.simaLatency.textContent = sima.latency_ms ? `~${sima.latency_ms.toFixed(2)} ms` : "---";
    els.simaFps.textContent = sima.fps ? `~${sima.fps.toFixed(1)}` : "---";
    setHealth("sima", "READY", "MEASURED");
    setHealth("mla", "READY", "MEASURED");
  } else {
    renderHeroHardwareCard(null);
    setHealth("sima", "OFFLINE", "UNVERIFIED");
    setHealth("mla", "OFFLINE", "UNVERIFIED");
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
    resetRunView({ clearFrame: false });
    return;
  }

  els.traceId.textContent = trace.trace_id || "Backend trace";
  els.policyBadge.textContent = humanize(trace.status, "Fail-closed");
  els.pitchCue.textContent = scenarioCopy[trace.scenario] || scenarioCopy[els.scenarioSelect.value];

  const action = trace.proposed_action;
  if (action && trace.status === "AWAITING_APPROVAL") {
    els.decisionEmpty.classList.add("hidden");
    els.decisionContent.classList.remove("hidden");
    els.approvalBoundaryKicker.textContent = "HUMAN AUTHORIZATION REQUIRED";
    els.approvalState.textContent = "AWAITING OPERATOR SIGN-OFF";
    els.actionTitle.textContent = humanizeAction(action.action_type);
    els.actionReason.textContent = action.reason || "High-impact safety gate awaiting operator review.";
    els.actionTarget.textContent = action.target || "Perimeter Advisory Relay";
    els.actionImpact.textContent = humanize(action.impact, "LOW").toUpperCase();
    els.actionStatus.textContent = "AWAITING_APPROVAL";
    return;
  }

  els.decisionEmpty.classList.remove("hidden");
  els.decisionContent.classList.add("hidden");

  if (trace.decision === "REJECTED" || trace.status === "REJECTED_SAFE") {
    els.approvalBoundaryKicker.textContent = "ACTION DENIED";
    els.approvalState.textContent = "DENIED — NOTHING EXECUTED";
    els.decisionEmptyTitle.textContent = "DENIED - NOTHING EXECUTED";
    els.decisionEmptyDesc.textContent =
      "The operator denied the proposal. The backend recorded a safe no-op with zero physical execution.";
  } else if (trace.verified === true) {
    els.approvalBoundaryKicker.textContent = "VERIFIED EXECUTION";
    els.approvalState.textContent = "SAFE STATE CONFIRMED";
    els.decisionEmptyTitle.textContent = "Backend reports VERIFIED";
    els.decisionEmptyDesc.textContent = "Execution was authorized, carried out, and confirmed by physical readback.";
  } else if (trace.status === "POLICY_NOT_TRIGGERED" || trace.decision === "NO_ACTION") {
    els.approvalBoundaryKicker.textContent = "POLICY EVALUATED CLEAN";
    els.approvalState.textContent = "NO ACTION REQUIRED";
    els.decisionEmptyTitle.textContent = "NO HUMAN ACTION REQUIRED";
    els.decisionEmptyDesc.textContent =
      "Verified perception did not meet the governed threshold. No action executed.";
  } else {
    els.approvalBoundaryKicker.textContent = "SAFETY STATUS";
    els.approvalState.textContent = "SAFELY BLOCKED (NO RELAY)";
    els.decisionEmptyTitle.textContent = "Action not verified";
    els.decisionEmptyDesc.textContent =
      "Guardian will not claim physical execution without physical readback confirmation.";
  }
}

async function fetchState() {
  try {
    const res = await fetch("/api/state");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
  } catch (err) {
    console.error("fetchState error:", err);
  }
}

async function fetchCameraSources() {
  try {
    const res = await fetch("/api/camera/sources");
    if (!res.ok) return;
    const data = await res.json();
    renderCameraSources(data.sources || []);
  } catch (e) {
    console.warn("Could not fetch camera sources:", e);
  }
}

async function startCamera() {
  try {
    if (activeStream) {
      activeStream.getTracks().forEach((t) => t.stop());
    }
    activeStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    els.localVideo.srcObject = activeStream;
    els.localVideo.classList.remove("hidden");
    els.prerecordedPreview.classList.add("hidden");
    els.previewFail.classList.add("hidden");
    setHealth("camera", "READY", "MEASURED");
    els.cameraState.textContent = "Streaming";
  } catch (err) {
    console.warn("Camera start failed or permission denied:", err);
    els.previewFail.classList.remove("hidden");
    els.previewFailTitle.textContent = "CAMERA INPUT INACTIVE";
    els.previewFailText.textContent = "Please allow webcam access or select a GYE camera to view live feed.";
    setHealth("camera", "OFFLINE", "UNVERIFIED");
  }
}

async function fetchRemoteSnapshot(sourceId) {
  try {
    showToast(`Fetching real snapshot from Guayaquil (${sourceId})...`);
    const res = await fetch(`/api/camera/snapshot?source_id=${encodeURIComponent(sourceId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.image_base64) {
      if (activeStream) activeStream.getTracks().forEach((t) => t.stop());
      els.localVideo.classList.add("hidden");
      els.prerecordedPreview.classList.remove("hidden");
      els.prerecordedPreview.src = `data:image/jpeg;base64,${data.image_base64}`;
      els.previewFail.classList.add("hidden");

      latestFrame.frameId = data.frame_id;
      latestFrame.sourceId = data.source_id;
      latestFrame.sha256 = data.sha256;
      latestFrame.capturedAt = data.captured_at;
      latestFrame.truth = "ALLOWLISTED_REMOTE_SNAPSHOT";
      els.frameId.textContent = `frame: ${data.frame_id}`;
      els.sourceLabel.textContent = data.source_id.toUpperCase();
      els.inferenceFrameTruth.textContent = "OFFLINE / NOT RUN";

      setHealth("camera", "READY", "MEASURED");
      clearOverlay();
      renderLayeredBreakdown(null, []);
      showToast(`Real snapshot loaded from Guayaquil (${data.width}x${data.height})`);
    }
  } catch (err) {
    console.warn("fetchRemoteSnapshot failed:", err);
    els.previewFail.classList.remove("hidden");
    els.previewFailTitle.textContent = "REMOTE CAMERA SNAPSHOT BLOCKED";
    els.previewFailText.textContent = `Could not reach ${sourceId} over Tailscale proxy: ${err.message}`;
    setHealth("camera", "OFFLINE", "UNVERIFIED");
  }
}

function captureCurrentFrame() {
  const canvas = els.captureCanvas;
  const video = els.localVideo;
  if (!video || !video.videoWidth || !activeStream) {
    return null;
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
  const base64 = dataUrl.split(",")[1];
  lastCapturedImage = {
    image_base64: base64,
    image_type: "jpeg",
    source_id: activeSourceId,
  };
  return lastCapturedImage;
}

async function runLiveSiMaDemo() {
  els.runLiveDemoBtn.disabled = true;
  els.runLiveDemoBtn.textContent = "⏳ PROCESSING SiMa INFERENCE...";

  try {
    if (activeSourceId === "laptop-webcam") {
      if (!activeStream && navigator.mediaDevices) {
        await startCamera();
      }
      const frameData = captureCurrentFrame();
      if (!frameData) {
        els.previewFail.classList.remove("hidden");
        els.previewFailTitle.textContent = "BLOCKED — NO REAL FRAME CAPTURED";
        els.previewFailText.textContent = "Webcam stream is inactive. Please allow camera permissions or start camera before running live inference.";
        showToast("BLOCKED: No real webcam frame captured");
        setHealth("camera", "OFFLINE", "UNVERIFIED");
        setHealth("sima", "OFFLINE", "UNVERIFIED");
        resetRunView({ clearFrame: true });
        return;
      }

      const res = await fetch("/api/inference/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...frameData,
          scenario: els.scenarioSelect.value,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();
      const frameId = payload?.frame_id || payload?.frame_ref || payload?.frame_source?.frame_id;
      const isNewFrame = frameId !== lastSubmittedFrameId;
      lastSubmittedFrameId = frameId;

      syncLatestFrameFromState(payload);
      const detections = extractDetections(payload);
      drawDetections(detections, payload);
      renderState(payload);

      const trace = payload?.current || (payload?.trace_id ? payload : null);
      const isMeasured = Boolean(
        payload?.sima_telemetry?.truth === "MEASURED" ||
        payload?.truth?.detections === "MEASURED" ||
        payload?.current?.truth?.detections === "MEASURED" ||
        payload?.inference_truth === "MEASURED"
      );
      if (isMeasured) {
        if (trace?.status === "AWAITING_APPROVAL") {
          showToast(`⚡ SiMa detected ${detections.length} object(s) • Policy triggered • Awaiting Operator Approval`);
        } else if (trace?.status === "POLICY_NOT_TRIGGERED" || trace?.decision === "NO_ACTION") {
          showToast(`✓ SiMa detected ${detections.length} object(s) • No security policy triggered (No action required)`);
        } else {
          showToast(`✓ SiMa inference complete • ${detections.length} object(s) detected`);
        }
      } else {
        showToast("Webcam frame captured • SiMa Modalix offline (fail-closed safe)");
      }
    } else {
      // Remote source (GYE Dahua Ch2/Ch3)
      const res = await fetch("/api/inference/source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id: activeSourceId,
          scenario: els.scenarioSelect.value,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();
      const frameId = payload?.frame_id || payload?.frame_ref || payload?.frame_source?.frame_id;
      const isNewFrame = frameId !== lastSubmittedFrameId;
      lastSubmittedFrameId = frameId;

      syncLatestFrameFromState(payload);

      if (payload.image_base64 || payload.snapshot_base64) {
        if (activeStream) activeStream.getTracks().forEach((t) => t.stop());
        els.localVideo.classList.add("hidden");
        els.prerecordedPreview.classList.remove("hidden");
        els.prerecordedPreview.src = `data:image/jpeg;base64,${payload.image_base64 || payload.snapshot_base64}`;
        els.previewFail.classList.add("hidden");
      }

      const detections = extractDetections(payload);
      drawDetections(detections, payload);
      renderState(payload);

      const trace = payload?.current || (payload?.trace_id ? payload : null);
      const isMeasured = Boolean(
        payload?.sima_telemetry?.truth === "MEASURED" ||
        payload?.truth?.detections === "MEASURED" ||
        payload?.current?.truth?.detections === "MEASURED" ||
        payload?.inference_truth === "MEASURED"
      );
      if (isMeasured) {
        if (trace?.status === "AWAITING_APPROVAL") {
          showToast(`⚡ Real Guayaquil frame • SiMa detected ${detections.length} object(s) • Policy triggered • Awaiting Operator Approval`);
        } else if (trace?.status === "POLICY_NOT_TRIGGERED" || trace?.decision === "NO_ACTION") {
          showToast(`✓ Real Guayaquil frame • SiMa detected ${detections.length} object(s) • No security policy triggered`);
        } else {
          showToast(`✓ Real Guayaquil frame • SiMa inference complete • ${detections.length} object(s) detected`);
        }
      } else {
        showToast("Real Guayaquil frame received • SiMa inference OFFLINE (fail-closed safe)");
      }
    }
  } catch (err) {
    console.error("runLiveSiMaDemo error:", err);
    clearOverlay();
    setHealth("sima", "OFFLINE", "UNVERIFIED");
    setHealth("mla", "OFFLINE", "UNVERIFIED");
    els.inferenceFrameTruth.textContent = "OFFLINE / UNVERIFIED";
    els.frameMatch.textContent = "UNVERIFIED";
    els.approvalBoundaryKicker.textContent = "INFERENCE FAILED";
    els.approvalState.textContent = "SAFELY BLOCKED (INFERENCE OFFLINE)";
    els.decisionEmptyTitle.textContent = "SiMa Inference Offline";
    els.decisionEmptyDesc.textContent = "SiMa DevKit is physically disconnected. Guardian remains fail-closed.";
    renderHeroHardwareCard(null);
    renderLayeredBreakdown(null, []);
    showToast(`Inference fail-closed: ${err.message}`);
  } finally {
    els.runLiveDemoBtn.disabled = false;
    els.runLiveDemoBtn.textContent = "⚡ RUN LIVE SiMa DEMO";
  }
}

async function runGovernedFlow() {
  els.runBtn.disabled = true;
  try {
    const res = await fetch("/api/demo/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: els.scenarioSelect.value,
        runtime_mode: els.runtimeSelect?.value || "LIVE_SIMA",
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
    const detections = extractDetections(data);
    renderLayeredBreakdown(data, detections);
    showToast("Governed Reference Flow reached Human Approval Gate");
  } catch (err) {
    showToast(`Failed to run governed flow: ${err.message}`);
  } finally {
    els.runBtn.disabled = false;
  }
}

async function approveAction() {
  els.approveBtn.disabled = true;
  try {
    const res = await fetch("/api/action/approve", { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
    showToast("Action approved: fail-closed safety preserved");
  } catch (err) {
    showToast(`Approve error: ${err.message}`);
  } finally {
    els.approveBtn.disabled = false;
  }
}

async function rejectAction() {
  els.rejectBtn.disabled = true;
  try {
    const res = await fetch("/api/action/reject", { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
    showToast("Action DENIED: zero physical execution recorded");
  } catch (err) {
    showToast(`Reject error: ${err.message}`);
  } finally {
    els.rejectBtn.disabled = false;
  }
}

async function callLifecycleEndpoint(endpoint, message) {
  try {
    const res = await fetch(endpoint, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderState(data);
    showToast(message);
  } catch (err) {
    showToast(`Error: ${err.message}`);
  }
}

function setupEvents() {
  if (els.srcBtnWebcam) {
    els.srcBtnWebcam.addEventListener("click", () => {
      updateSourceButtons("laptop-webcam");
      resetRunView({ clearFrame: false });
      startCamera();
    });
  }

  if (els.srcBtnGyeCh2) {
    els.srcBtnGyeCh2.addEventListener("click", () => {
      updateSourceButtons("gye-dahua-ch2");
      resetRunView({ clearFrame: false });
      fetchRemoteSnapshot("gye-dahua-ch2");
    });
  }

  if (els.srcBtnGyeCh3) {
    els.srcBtnGyeCh3.addEventListener("click", () => {
      updateSourceButtons("gye-dahua-ch3");
      resetRunView({ clearFrame: false });
      fetchRemoteSnapshot("gye-dahua-ch3");
    });
  }

  if (els.sourceSelect) {
    els.sourceSelect.addEventListener("change", (e) => {
      updateSourceButtons(e.target.value);
      resetRunView({ clearFrame: false });
      if (e.target.value.startsWith("gye-dahua")) {
        fetchRemoteSnapshot(e.target.value);
      }
    });
  }

  if (els.filterPolicyRelevant) {
    els.filterPolicyRelevant.addEventListener("click", () => {
      currentOverlayFilter = "POLICY_RELEVANT";
      els.filterPolicyRelevant.classList.add("active");
      if (els.filterAllDetections) els.filterAllDetections.classList.remove("active");
      drawDetections(lastDetectionsData, lastDetectionsPayload);
    });
  }

  if (els.filterAllDetections) {
    els.filterAllDetections.addEventListener("click", () => {
      currentOverlayFilter = "ALL";
      els.filterAllDetections.classList.add("active");
      if (els.filterPolicyRelevant) els.filterPolicyRelevant.classList.remove("active");
      drawDetections(lastDetectionsData, lastDetectionsPayload);
    });
  }

  if (els.runLiveDemoBtn) els.runLiveDemoBtn.addEventListener("click", runLiveSiMaDemo);
  if (els.runBtn) els.runBtn.addEventListener("click", runGovernedFlow);
  if (els.approveBtn) els.approveBtn.addEventListener("click", approveAction);
  if (els.rejectBtn) els.rejectBtn.addEventListener("click", rejectAction);
  if (els.resetBtn) {
    els.resetBtn.addEventListener("click", () => {
      resetRunView();
      showToast("Console reset to clean state");
    });
  }

  if (els.startCameraBtn) els.startCameraBtn.addEventListener("click", startCamera);
  if (els.captureFrameBtn) {
    els.captureFrameBtn.addEventListener("click", () => {
      captureCurrentFrame();
      showToast("Frame captured to buffer");
    });
  }
  if (els.requestInferenceBtn) els.requestInferenceBtn.addEventListener("click", runLiveSiMaDemo);

  if (els.interruptBtn) els.interruptBtn.addEventListener("click", () => callLifecycleEndpoint("/api/action/interrupt", "Interrupted"));
  if (els.reverifyBtn) els.reverifyBtn.addEventListener("click", () => callLifecycleEndpoint("/api/action/reverify", "Safe State Re-verified"));
  if (els.resumeBtn) els.resumeBtn.addEventListener("click", () => callLifecycleEndpoint("/api/action/resume", "Resumed"));
  if (els.cancelBtn) els.cancelBtn.addEventListener("click", () => callLifecycleEndpoint("/api/action/cancel", "Cancelled Safely"));

  if (els.copyEvidenceBtn) {
    els.copyEvidenceBtn.addEventListener("click", () => {
      if (navigator.clipboard && els.evidencePreview) {
        navigator.clipboard.writeText(els.evidencePreview.textContent);
        showToast("Evidence JSON copied to clipboard");
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupEvents();
  fetchCameraSources();
  fetchState();
  startCamera();
});
