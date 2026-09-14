(() => {
  const root = document.querySelector(".lower-grid");
  if (!root) return;

  const card = document.createElement("article");
  card.className = "panel";
  card.id = "voice-section";

  const head = document.createElement("div");
  head.className = "panel-head compact";
  const titleWrap = document.createElement("div");
  const kicker = document.createElement("span");
  kicker.className = "section-kicker";
  kicker.textContent = "SPEECHMATICS BONUS";
  const title = document.createElement("h3");
  title.textContent = "Bounded voice control";
  titleWrap.append(kicker, title);
  const status = document.createElement("span");
  status.className = "status-pill";
  status.id = "voiceStatusBadge";
  status.textContent = "Checking voice lane";
  head.append(titleWrap, status);

  const safety = document.createElement("p");
  safety.className = "hero-copy";
  safety.textContent = "Voice can explain, interrupt, re-verify, resume or cancel. Voice can never approve or directly execute a physical action.";

  const form = document.createElement("div");
  form.className = "control-strip";
  const label = document.createElement("label");
  const labelText = document.createElement("span");
  labelText.textContent = "Transcript test fallback";
  const input = document.createElement("input");
  input.id = "voiceTranscriptInput";
  input.type = "text";
  input.autocomplete = "off";
  input.placeholder = "e.g. interrupt the action";
  input.maxLength = 2000;
  label.append(labelText, input);
  const button = document.createElement("button");
  button.className = "primary-btn";
  button.type = "button";
  button.textContent = "Route bounded intent";
  form.append(label, button);

  const result = document.createElement("pre");
  result.id = "voiceResult";
  result.textContent = "Typed transcripts are a fallback test, not proof of live Speechmatics audio.";

  card.append(head, safety, form, result);
  root.appendChild(card);

  async function fetchJson(path, options = {}) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }

  async function refreshStatus() {
    try {
      const voice = await fetchJson("/api/voice/status");
      if (voice.credential_configured && voice.sdk_installed) {
        status.textContent = "Speechmatics runtime ready";
      } else if (voice.credential_configured) {
        status.textContent = "Credential ready · SDK optional";
      } else if (voice.sdk_installed) {
        status.textContent = "SDK ready · credential not bound";
      } else {
        status.textContent = "Manual fallback ready";
      }
    } catch (error) {
      status.textContent = "Voice status unavailable";
    }
  }

  async function routeTranscript() {
    const transcript = input.value.trim();
    if (!transcript) {
      result.textContent = "Enter a bounded test transcript.";
      return;
    }
    button.disabled = true;
    try {
      const response = await fetchJson("/api/voice/intent", {
        method: "POST",
        body: JSON.stringify({ transcript, provider: "speechmatics" }),
      });
      const current = response.state?.current || {};
      result.textContent = JSON.stringify(
        {
          intent: response.intent,
          allowed: response.allowed,
          truth: response.truth,
          guardian_state: current.status || null,
          transcript_sha256: response.transcript_sha256,
          voice_can_approve: response.voice_can_approve,
        },
        null,
        2,
      );
      document.dispatchEvent(new CustomEvent("guardian:voice-state", { detail: response.state }));
    } catch (error) {
      result.textContent = `Fail-closed: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", routeTranscript);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") routeTranscript();
  });
  refreshStatus();
})();
