const $ = (id) => document.getElementById(id);

const els = {
  scenarioSelect: $("scenarioSelect"),
  runtimeSelect: $("runtimeSelect"),
  runtimeBadge: $("runtimeBadge"),
  ioBadge: $("ioBadge"),
  truthBadge: $("truthBadge"),
  runBtn: $("runBtn"),
  resetBtn: $("resetBtn"),
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
  cameraClock: $("cameraClock"),
  subjectBox: $("subjectBox"),
  subjectLabel: $("subjectLabel"),
  zoneLabel: $("zoneLabel"),
  severityBadge: $("severityBadge"),
  eventTitle: $("eventTitle"),
  eventText: $("eventText"),
  traceId: $("traceId"),
  policyBadge: $("policyBadge"),
  decisionEmpty: $("decisionEmpty"),
  decisionContent: $("decisionContent"),
  actionTitle: $("actionTitle"),
  actionReason: $("actionReason"),
  actionTarget: $("actionTarget"),
  actionImpact: $("actionImpact"),
  proposalMetric: $("proposalMetric"),
  verifyMetric: $("verifyMetric"),
  inferenceMetric: $("inferenceMetric"),
  inferenceTruth: $("inferenceTruth"),
  evidenceMetric: $("evidenceMetric"),
  runtimeList: $("runtimeList"),
  evidencePreview: $("evidencePreview"),
  pitchCue: $("pitchCue"),
  toast: $("toast"),
};

const scenarioCopy = {
  loitering_after_hours: {
    title: "After-hours loitering",
    cue: "The camera sees one frame. Guardian understands the behavior over time: the same tracked person has remained in a restricted zone after closing, so a bounded warning action is proposed instead of an accusation.",
  },
  repeated_access_attempt: {
    title: "Repeated access attempt",
    cue: "A single detection is not enough. Guardian correlates repeated presence inside a policy window, then asks a human before taking even a low-impact action.",
  },
  restricted_zone_entry: {
    title: "Restricted equipment zone",
    cue: "Guardian combines tracking and zone context. The important part is not merely detecting a person, but converting a verified transition into a governed, auditable physical response.",
  },
};

let latestState = null;
let physicalIoCatalog = null;
let toastTimer = null;

function showToast(message, error = false) {
  clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.classList.toggle("error", error);
  els.toast.classList.add("show");
  toastTimer = setTimeout(() => els.toast.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {
    payload = { error: `HTTP ${response.status}` };
  }
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

function humanizeAction(actionType) {
  return actionType
    .split("_")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

function humanizeZone(zone) {
  return String(zone || "restricted-zone")
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .toUpperCase();
}

function formatMs(value) {
  return typeof value === "number" ? `${value.toFixed(Math.min(value < 1 ? 3 : 2, 3))} ms` : "—";
}

function renderTruthBadge(trace = null) {
  const inference = trace?.truth?.detections;
  const physical = trace?.truth?.physical_io;

  if (
    inference === "MEASURED_SPONSOR_RUNTIME"
    && (physical === "REAL_LOW_VOLTAGE_HARDWARE" || physical === "PRODUCT_HTTP_READBACK")
  ) {
    els.truthBadge.textContent = "LIVE REAL";
    return;
  }
  if (inference === "MEASURED_SPONSOR_RUNTIME") {
    els.truthBadge.textContent = "LIVE SPONSOR INFERENCE";
  } else if (inference === "SIMULATED_SPONSOR_SDK") {
    els.truthBadge.textContent = "SIMULATED SPONSOR SDK";
  } else {
    els.truthBadge.textContent = "SYNTHETIC FIXTURE";
  }
}

function renderIoBadge(trace = null) {
  const truth = trace?.truth?.physical_io;
  if (truth === "REAL_LOW_VOLTAGE_HARDWARE") {
    els.ioBadge.textContent = "Hardware readback verified";
    return;
  }
  if (truth === "PRODUCT_HTTP_READBACK") {
    els.ioBadge.textContent = "Product I/O readback verified";
    return;
  }
  if (truth === "FAILED_CLOSED") {
    els.ioBadge.textContent = "Physical I/O failed closed";
    return;
  }
  if (physicalIoCatalog?.status === "READY_CONFIGURED") {
    els.ioBadge.textContent = "Physical I/O bridge ready";
    return;
  }
  if (physicalIoCatalog?.status === "INVALID_LOCAL_BRIDGE_CONFIG") {
    els.ioBadge.textContent = "Physical I/O config invalid";
    return;
  }
  els.ioBadge.textContent = "Physical I/O fallback";
}

function renderCatalog(catalog) {
  els.runtimeSelect.innerHTML = "";
  els.runtimeList.innerHTML = "";
  physicalIoCatalog = catalog.physical_io || null;
  renderIoBadge();

  for (const runtime of catalog.runtimes || []) {
    const option = document.createElement("option");
    option.value = runtime.runtime_id;
    option.textContent = `${runtime.provider} · ${runtime.status === "READY" ? "ready" : "awaiting hardware"}`;
    if (runtime.status !== "READY") option.disabled = true;
    els.runtimeSelect.appendChild(option);

    const row = document.createElement("div");
    row.className = "runtime-row";
    const info = document.createElement("div");
    const strong = document.createElement("strong");
    strong.textContent = runtime.provider;
    const small = document.createElement("small");
    small.textContent = runtime.target || runtime.runtime_id;
    info.append(strong, small);

    const state = document.createElement("span");
    state.className = `runtime-state ${runtime.status === "READY" ? "ready" : ""}`;
    state.textContent = runtime.status === "READY" ? "READY" : "SLOT";
    row.append(info, state);
    els.runtimeList.appendChild(row);
  }

  const selected = catalog.runtimes?.find((r) => r.status === "READY");
  if (selected) {
    els.runtimeSelect.value = selected.runtime_id;
    els.runtimeBadge.textContent = `${selected.provider} ready`;
  }
}

function resetStages() {
  document.querySelectorAll(".stage").forEach((node) => {
    node.className = "stage";
    const small = node.querySelector("small");
    const stage = node.dataset.stage;
    const defaults = {
      SEE: "Awaiting event",
      UNDERSTAND: "Normalize perception",
      DECIDE: "Policy + temporal context",
      ACT: "Bounded action only",
      VERIFY: "Readback / expected state",
      PROVE: "Seal evidence",
    };
    if (small) small.textContent = defaults[stage] || "Pending";
  });
}

function renderStages(stages = []) {
  resetStages();
  for (const stage of stages) {
    const node = document.querySelector(`.stage[data-stage="${stage.stage}"]`);
    if (!node) continue;
    node.classList.add(stage.status || "pending");
    const small = node.querySelector("small");
    if (small) small.textContent = stage.summary || stage.status;
  }
}

function renderEvidence(evidence) {
  if (!evidence) {
    els.evidencePreview.textContent = "Run a scenario to generate evidence.";
    els.evidenceMetric.textContent = "Pending";
    return;
  }
  const concise = {
    evidence_id: evidence.evidence_id,
    trace_id: evidence.trace_id,
    status: evidence.status,
    decision: evidence.decision,
    verified: evidence.verified,
    runtime_id: evidence.runtime_id,
    physical_io_bridge: evidence.physical_io_bridge,
    physical_io_failure: evidence.physical_io_failure,
    truth: evidence.truth,
    metrics: evidence.metrics,
  };
  els.evidencePreview.textContent = JSON.stringify(concise, null, 2);
  els.evidenceMetric.textContent = evidence.evidence_id ? evidence.evidence_id.slice(0, 10) + "…" : "Draft";
}

function renderLifecycle(trace) {
  if (!trace) {
    els.lifecyclePanel.classList.add("hidden");
    els.lifecycleTimeline.innerHTML = "";
    return;
  }

  els.lifecyclePanel.classList.remove("hidden");
  els.lifecycleState.textContent = String(trace.status || "UNKNOWN").replaceAll("_", " ");

  const canInterrupt = trace.status === "VERIFIED" || trace.status === "RESUMED_VERIFIED";
  const canReverify = trace.status === "SAFE_STATE_VERIFIED";
  const canResume = trace.status === "REVERIFIED";
  const canCancel = trace.status === "SAFE_STATE_VERIFIED" || trace.status === "REVERIFIED";
  els.interruptBtn.classList.toggle("hidden", !canInterrupt);
  els.reverifyBtn.classList.toggle("hidden", !canReverify);
  els.resumeBtn.classList.toggle("hidden", !canResume);
  els.cancelBtn.classList.toggle("hidden", !canCancel);

  const events = trace.lifecycle_events || [];
  els.lifecycleTimeline.innerHTML = "";
  for (const event of events.slice(-7)) {
    const row = document.createElement("div");
    row.className = "lifecycle-event";
    const state = document.createElement("strong");
    state.textContent = String(event.state || "STATE").replaceAll("_", " ");
    const summary = document.createElement("span");
    summary.textContent = event.summary || "";
    const truth = document.createElement("small");
    truth.textContent = event.truth || "";
    row.append(state, summary, truth);
    els.lifecycleTimeline.appendChild(row);
  }
}

function renderState(state) {
  latestState = state;
  const trace = state.current;
  renderEvidence(state.latest_evidence);
  renderLifecycle(trace);
  renderTruthBadge(trace);

  if (!trace) {
    renderIoBadge();
    els.cameraState.textContent = "Fixture standby";
    els.subjectBox.classList.remove("active");
    els.subjectLabel.textContent = "PERSON · --";
    els.zoneLabel.textContent = "RESTRICTED ZONE";
    els.severityBadge.className = "severity-badge";
    els.severityBadge.textContent = "STANDBY";
    els.eventTitle.textContent = "Ready for deterministic judge scenario";
    els.eventText.textContent = "No customer footage or private camera topology is required for this fallback demo.";
    els.traceId.textContent = "No active trace";
    els.decisionEmpty.classList.remove("hidden");
    els.decisionContent.classList.add("hidden");
    els.decisionEmpty.querySelector("strong").textContent = "No physical action pending";
    els.decisionEmpty.querySelector("p").textContent = "Guardian will propose only an allowlisted low-impact action. Human approval remains explicit.";
    els.policyBadge.textContent = "Fail-closed";
    els.proposalMetric.textContent = "—";
    els.verifyMetric.textContent = "—";
    els.inferenceMetric.textContent = "Fixture";
    els.inferenceTruth.textContent = "not benchmarked";
    els.pitchCue.innerHTML = "<strong>Physical Guardian does not replace your cameras.</strong> It adds a governed intelligence layer that observes, reasons over time, acts safely, verifies the result, and preserves proof.";
    resetStages();
    return;
  }

  renderIoBadge(trace);
  if (trace.status === "VERIFIED" || trace.status === "RESUMED_VERIFIED") {
    els.cameraState.textContent = "Verified event";
  } else if (trace.status === "SAFE_STATE_VERIFIED") {
    els.cameraState.textContent = "Interrupted · safe state";
  } else if (trace.status === "REVERIFIED") {
    els.cameraState.textContent = "Safe state re-verified";
  } else if (trace.status === "CANCELLED_SAFE") {
    els.cameraState.textContent = "Cancelled safely";
  } else if (trace.status === "REJECTED_SAFE") {
    els.cameraState.textContent = "Safe no-op";
  } else if (trace.status === "ACTION_FAILED_SAFE") {
    els.cameraState.textContent = "Action failed safe";
  } else {
    els.cameraState.textContent = "Event active";
  }
  els.subjectBox.classList.add("active");
  const scenario = scenarioCopy[trace.scenario] || {};
  const decideStage = trace.stages?.find((s) => s.stage === "DECIDE") || {};
  const see = trace.stages?.find((s) => s.stage === "SEE") || {};
  const understand = trace.stages?.find((s) => s.stage === "UNDERSTAND");
  const detection = understand?.runtime?.detections?.[0];
  if (detection) {
    const confidence = typeof detection.confidence === "number" ? detection.confidence.toFixed(2) : "--";
    els.subjectLabel.textContent = `${String(detection.label || "object").toUpperCase()} · ${confidence}`;
    els.zoneLabel.textContent = humanizeZone(detection.zone);
  } else {
    els.subjectLabel.textContent = "OBJECT · --";
    els.zoneLabel.textContent = "ACTIVE ZONE";
  }
  els.severityBadge.className = `severity-badge ${(decideStage.severity || "").toLowerCase()}`;
  els.severityBadge.textContent = (decideStage.severity || "EVENT").toUpperCase();
  els.eventTitle.textContent = scenario.title || trace.scenario;
  els.eventText.textContent = see.summary || "Guardian event received";
  els.traceId.textContent = trace.trace_id;
  renderStages(trace.stages || []);

  const action = trace.proposed_action;
  if (action && trace.status === "AWAITING_APPROVAL") {
    els.decisionEmpty.classList.add("hidden");
    els.decisionContent.classList.remove("hidden");
    els.actionTitle.textContent = humanizeAction(action.action_type);
    els.actionReason.textContent = action.reason;
    els.actionTarget.textContent = action.target;
    els.actionImpact.textContent = (action.impact || "low").toUpperCase();
    els.policyBadge.textContent = "Human approval required";
  } else {
    els.decisionEmpty.classList.remove("hidden");
    els.decisionContent.classList.add("hidden");
    const decisionText = trace.status === "ACTION_FAILED_SAFE"
      ? "Action failed closed. No verified output accepted."
      : trace.decision === "APPROVED"
        ? "Action verified and evidence sealed."
        : trace.decision === "REJECTED"
          ? "Operator rejected action. Safe no-op verified."
          : "No physical action pending.";
    els.decisionEmpty.querySelector("strong").textContent = decisionText;
    els.decisionEmpty.querySelector("p").textContent = trace.evidence_id
      ? `Evidence ${trace.evidence_id} preserves the decision, truth labels, and measured composition timings.`
      : "Guardian remains fail-closed until an explicit decision is recorded.";
    els.policyBadge.textContent = trace.status === "VERIFIED" ? "Verified" : trace.status.replaceAll("_", " ");
  }

  els.proposalMetric.textContent = formatMs(trace.metrics?.composition_to_proposal_ms);
  els.verifyMetric.textContent = formatMs(
    trace.metrics?.approval_to_verification_ms ?? trace.metrics?.approval_to_failure_ms,
  );
  els.inferenceMetric.textContent = understand?.runtime?.model || "Fixture";
  els.inferenceTruth.textContent = (understand?.truth || "unknown").replaceAll("_", " ").toLowerCase();
  els.pitchCue.textContent = scenario.cue || "Guardian converts perception into policy-governed physical action with verification and evidence.";
}

async function runScenario() {
  els.runBtn.disabled = true;
  try {
    const state = await api("/api/demo/run", {
      method: "POST",
      body: JSON.stringify({
        scenario: els.scenarioSelect.value,
        runtime_id: els.runtimeSelect.value,
      }),
    });
    renderState(state);
    showToast("Guardian reached the human approval gate.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    els.runBtn.disabled = false;
  }
}

async function decide(path, successText) {
  try {
    const state = await api(path, { method: "POST", body: "{}" });
    renderState(state);
    if (state.current?.status === "ACTION_FAILED_SAFE") {
      showToast("Physical I/O failed closed; evidence was preserved.", true);
    } else {
      showToast(successText);
    }
  } catch (error) {
    showToast(error.message, true);
  }
}

async function resetDemo() {
  try {
    const state = await api("/api/demo/reset", { method: "POST", body: "{}" });
    renderState(state);
    showToast("Demo reset. Ready for the next judge.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function copyEvidence() {
  const evidence = latestState?.latest_evidence;
  if (!evidence) {
    showToast("No evidence exists yet.", true);
    return;
  }
  try {
    await navigator.clipboard.writeText(JSON.stringify(evidence, null, 2));
    showToast("Evidence JSON copied.");
  } catch (_) {
    showToast("Clipboard access was blocked by the browser.", true);
  }
}

function updateClock() {
  els.cameraClock.textContent = new Date().toISOString().slice(11, 19) + " UTC";
}

async function boot() {
  updateClock();
  setInterval(updateClock, 1000);
  try {
    const [catalog, state] = await Promise.all([api("/api/catalog"), api("/api/state")]);
    renderCatalog(catalog);
    renderState(state);
  } catch (error) {
    showToast(`Backend unavailable: ${error.message}`, true);
    els.runtimeBadge.textContent = "Backend unavailable";
    els.ioBadge.textContent = "Backend unavailable";
  }
}

els.runBtn.addEventListener("click", runScenario);
els.resetBtn.addEventListener("click", resetDemo);
els.approveBtn.addEventListener("click", () => decide("/api/action/approve", "Action verified. Evidence sealed."));
els.rejectBtn.addEventListener("click", () => decide("/api/action/reject", "Action rejected. Safe no-op recorded."));
els.interruptBtn.addEventListener("click", () => decide("/api/action/interrupt", "Interrupt verified. Safe state active."));
els.reverifyBtn.addEventListener("click", () => decide("/api/action/reverify", "Safe state re-verified. Resume unlocked."));
els.resumeBtn.addEventListener("click", () => decide("/api/action/resume", "Action resumed only after re-verification."));
els.cancelBtn.addEventListener("click", () => decide("/api/action/cancel", "Interrupted action cancelled safely."));
els.copyEvidenceBtn.addEventListener("click", copyEvidence);
els.runtimeSelect.addEventListener("change", () => {
  const text = els.runtimeSelect.options[els.runtimeSelect.selectedIndex]?.textContent || "runtime";
  els.runtimeBadge.textContent = text;
});

document.addEventListener("guardian:voice-state", (event) => {
  if (event.detail) renderState(event.detail);
});

document.addEventListener("keydown", (event) => {
  const tag = document.activeElement?.tagName?.toLowerCase();
  if (tag === "select" || tag === "input" || tag === "textarea") return;
  if (event.key.toLowerCase() === "r") runScenario();
  if (event.key.toLowerCase() === "a" && latestState?.current?.status === "AWAITING_APPROVAL") {
    decide("/api/action/approve", "Action verified. Evidence sealed.");
  }
  if (event.key.toLowerCase() === "x") resetDemo();
});

boot();
