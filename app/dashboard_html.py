from __future__ import annotations


def dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Store Intelligence Live Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef2f6;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #647181;
      --line: #dce3ea;
      --accent: #0f766e;
      --accent-2: #2563eb;
      --accent-soft: #d8f4ee;
      --stage: #0c1118;
      --warn: #b45309;
      --danger: #b91c1c;
      --shadow: 0 10px 30px rgba(20, 31, 46, 0.09);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 18px;
      padding: 16px 22px;
      background: rgba(255, 255, 255, 0.97);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(12px);
    }
    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
    }
    main {
      max-width: 1440px;
      margin: 0 auto;
      padding: 18px 22px 28px;
    }
    .sub {
      color: var(--muted);
      font-size: 13px;
      margin-top: 5px;
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    input, button {
      height: 36px;
      border-radius: 7px;
      border: 1px solid var(--line);
      padding: 0 10px;
      font: inherit;
      background: #fff;
      color: var(--ink);
    }
    button {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      cursor: pointer;
      font-weight: 700;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    .dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--warn);
    }
    .dot.live { background: var(--accent); }
    .top-grid {
      display: grid;
      grid-template-columns: minmax(600px, 1.52fr) minmax(320px, 0.72fr);
      gap: 14px;
      align-items: stretch;
    }
    .panel, .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .panel {
      padding: 14px;
      min-width: 0;
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .panel h2 {
      margin: 0;
      font-size: 15px;
    }
    .camera-tools {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
    }
    .camera-tabs {
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
    }
    .camera-tabs button {
      height: 30px;
      padding: 0 9px;
      background: #fff;
      color: var(--ink);
      border-color: var(--line);
      font-size: 12px;
    }
    .camera-tabs button.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .camera-tabs button.missing {
      color: #98a2b3;
      background: #f4f6f8;
    }
    .overlay-controls {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    select {
      height: 30px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      padding: 0 8px;
    }
    .video-shell {
      position: relative;
      background: var(--stage);
      border-radius: 10px;
      overflow: hidden;
      aspect-ratio: 16 / 9;
      border: 1px solid #111827;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
    }
    video {
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: var(--stage);
      display: block;
    }
    .overlay {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .box {
      position: absolute;
      border: 2px solid #10b981;
      background: rgba(16, 185, 129, 0.08);
      box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.22);
      border-radius: 3px;
      animation: breathe 1.4s ease-in-out infinite alternate;
    }
    .box.staff {
      border-color: #f59e0b;
      background: rgba(245, 158, 11, 0.12);
    }
    .box-label {
      position: absolute;
      left: -2px;
      top: -22px;
      min-width: 70px;
      padding: 2px 6px;
      border-radius: 5px 5px 5px 0;
      background: #10b981;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }
    .staff .box-label { background: #f59e0b; color: #1f2937; }
    @keyframes breathe {
      from { opacity: 0.72; }
      to { opacity: 1; }
    }
    .hud {
      position: absolute;
      left: 12px;
      bottom: 12px;
      display: grid;
      gap: 6px;
      color: #fff;
      font-size: 12px;
    }
    .hud span {
      display: inline-flex;
      width: fit-content;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.78);
    }
    .camera-note {
      position: absolute;
      right: 12px;
      top: 12px;
      max-width: min(420px, calc(100% - 24px));
      padding: 7px 10px;
      border-radius: 7px;
      background: rgba(15, 23, 42, 0.78);
      color: #dbeafe;
      font-size: 12px;
      line-height: 1.35;
    }
    .side-stack {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(130px, 1fr));
      align-content: start;
    }
    .metric {
      padding: 13px;
      min-height: 94px;
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }
    .metric.hot {
      border-color: rgba(15, 118, 110, 0.45);
      box-shadow: 0 14px 34px rgba(15, 118, 110, 0.16);
      transform: translateY(-1px);
    }
    .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 9px;
    }
    .value {
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
    }
    .wide { grid-column: span 2; }
    .lower-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 14px;
    }
    .funnel {
      display: grid;
      gap: 10px;
    }
    .stage {
      display: grid;
      grid-template-columns: 126px 1fr 72px;
      gap: 10px;
      align-items: center;
      font-size: 13px;
    }
    .bar {
      height: 12px;
      border-radius: 999px;
      overflow: hidden;
      background: #edf1f5;
    }
    .bar span {
      display: block;
      height: 100%;
      min-width: 2px;
      background: var(--accent);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 8px 6px;
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-weight: 700;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
    }
    .event-type {
      display: inline-block;
      padding: 3px 7px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: #075e55;
      font-size: 11px;
      font-weight: 800;
    }
    .quality {
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }
    .quality-row {
      display: grid;
      grid-template-columns: 92px 1fr 44px;
      gap: 8px;
      align-items: center;
      font-size: 12px;
      color: var(--muted);
    }
    .quality-track {
      height: 8px;
      background: #e5e7eb;
      border-radius: 999px;
      overflow: hidden;
    }
    .quality-track span {
      display: block;
      height: 100%;
      background: var(--accent);
    }
    .anomaly {
      padding: 10px 11px;
      background: #fff7ed;
      border: 1px solid #fed7aa;
      border-radius: 7px;
      margin-bottom: 9px;
      font-size: 13px;
    }
    .anomaly strong { color: var(--warn); }
    .empty {
      color: var(--muted);
      font-size: 13px;
      padding: 10px 0;
    }
    .heatmap {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 8px;
    }
    .heat-cell {
      border-radius: 7px;
      border: 1px solid var(--line);
      padding: 9px;
      background: #f8fafc;
      min-height: 74px;
    }
    .heat-score {
      margin-top: 8px;
      height: 8px;
      border-radius: 999px;
      background: #e5e7eb;
      overflow: hidden;
    }
    .heat-score span {
      display: block;
      height: 100%;
      background: var(--accent-2);
    }
    @media (max-width: 1100px) {
      .top-grid, .lower-grid { grid-template-columns: 1fr; }
      .side-stack { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
      .wide { grid-column: span 1; }
    }
    @media (max-width: 720px) {
      header { align-items: flex-start; flex-direction: column; }
      .side-stack { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .stage { grid-template-columns: 94px 1fr 54px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Store Intelligence Live Dashboard</h1>
      <div class="sub">YOLOE-26 CCTV detection, staff/customer role overlays, and metrics from API-ingested events.</div>
    </div>
    <div class="controls">
      <input id="storeId" value="ST1008" aria-label="Store ID">
      <button id="refresh">Refresh</button>
      <span class="status"><span id="dot" class="dot"></span><span id="statusText">Connecting</span></span>
    </div>
  </header>

  <main>
    <section class="top-grid">
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2>Live Detection Screen</h2>
            <div class="sub">Actual CCTV clip with latest high-confidence API event boxes for the selected camera.</div>
          </div>
          <div class="camera-tools">
            <label class="overlay-controls">
              <input id="showOverlay" type="checkbox" checked>
              Overlay
            </label>
            <label class="overlay-controls">
              Min conf
              <select id="minConfidence">
                <option value="0.25">0.25</option>
                <option value="0.50" selected>0.50</option>
                <option value="0.70">0.70</option>
              </select>
            </label>
            <div id="cameraTabs" class="camera-tabs"></div>
          </div>
        </div>
        <div class="video-shell">
          <video id="cctvVideo" autoplay muted loop playsinline controls></video>
          <div id="overlay" class="overlay"></div>
          <div class="camera-note">Overlay boxes are recent detections stored by the API. They are filtered and de-duplicated for demo readability.</div>
          <div class="hud">
            <span id="cameraHud">Camera loading</span>
            <span id="detectionHud">0 recent detections</span>
          </div>
        </div>
      </div>

      <div class="side-stack">
        <div class="metric"><div class="label">Unique Visitors</div><div id="uniqueVisitors" class="value">0</div><div class="sub">staff excluded</div></div>
        <div class="metric"><div class="label">Conversion Rate</div><div id="conversionRate" class="value">0%</div><div id="convertedVisitors" class="sub">0 converted</div></div>
        <div class="metric"><div class="label">Queue Depth</div><div id="queueDepth" class="value">0</div><div class="sub">latest billing event</div></div>
        <div id="eventMetric" class="metric"><div class="label">Stored Events</div><div id="eventCount" class="value">0</div><div id="lastEvent" class="sub">no events</div></div>
        <div id="pipelineMetric" class="metric wide"><div class="label">Active Pipeline Link</div><div id="pipelineLink" class="value">Idle</div><div class="sub">changes when live replay posts into ingest</div></div>
        <div class="metric wide">
          <div class="label">Model Signal Quality</div>
          <div id="qualitySummary" class="value">-</div>
          <div id="detectorModel" class="sub">waiting for YOLOE-26 events</div>
          <div class="quality">
            <div class="quality-row"><span>Avg conf</span><div class="quality-track"><span id="avgConfBar" style="width:0%"></span></div><strong id="avgConfText">0</strong></div>
            <div class="quality-row"><span>Staff roles</span><div class="quality-track"><span id="staffBar" style="width:0%"></span></div><strong id="staffText">0</strong></div>
          </div>
        </div>
      </div>
    </section>

    <section class="lower-grid">
      <div class="panel">
        <h2>Session Funnel</h2>
        <div id="funnel" class="funnel"></div>
      </div>
      <div class="panel">
        <h2>Anomalies</h2>
        <div id="anomalies"></div>
      </div>
      <div class="panel">
        <h2>Latest Events</h2>
        <table>
          <thead><tr><th>Time</th><th>Type</th><th>Camera</th><th>Visitor</th><th>Zone</th><th>Role</th></tr></thead>
          <tbody id="events"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Zone Heatmap</h2>
        <div id="heatmap" class="heatmap"></div>
      </div>
    </section>
  </main>

  <script>
    const state = {
      storeId: "ST1008",
      selectedCamera: "CAM_3",
      cameras: [],
      previousEventCount: null,
      pulseUntil: 0,
      lastEvents: []
    };

    function fmtPercent(value) {
      return `${((Number(value) || 0) * 100).toFixed(1)}%`;
    }

    function setText(id, value) {
      document.getElementById(id).textContent = value;
    }

    function eventSeconds(timestamp) {
      const d = new Date(timestamp);
      return d.toLocaleTimeString();
    }

    function personRole(event) {
      return (event.metadata && event.metadata.person_role) || (event.is_staff ? "staff" : "customer");
    }

    function detectorModel(events) {
      const event = events.find(item => item.metadata && item.metadata.detector_model);
      return event ? event.metadata.detector_model : "unknown detector";
    }

    async function loadCameras() {
      const response = await fetch("/media/cameras", { cache: "no-store" });
      const data = await response.json();
      state.cameras = data.cameras || [];
      if (!state.cameras.some(c => c.camera_id === state.selectedCamera && c.available)) {
        const firstAvailable = state.cameras.find(c => c.available);
        if (firstAvailable) state.selectedCamera = firstAvailable.camera_id;
      }
      renderCameraTabs();
      setVideoSource();
    }

    function renderCameraTabs() {
      const tabs = document.getElementById("cameraTabs");
      tabs.innerHTML = state.cameras.map(camera => {
        const active = camera.camera_id === state.selectedCamera ? "active" : "";
        const missing = camera.available ? "" : "missing";
        return `<button class="${active} ${missing}" data-camera="${camera.camera_id}" ${camera.available ? "" : "disabled"}>${camera.camera_id}</button>`;
      }).join("");
      tabs.querySelectorAll("button").forEach(button => {
        button.addEventListener("click", () => {
          state.selectedCamera = button.dataset.camera;
          renderCameraTabs();
          setVideoSource();
          loadDashboard();
        });
      });
    }

    function setVideoSource() {
      const camera = state.cameras.find(c => c.camera_id === state.selectedCamera);
      if (!camera || !camera.available) return;
      const video = document.getElementById("cctvVideo");
      if (!video.src.endsWith(camera.url)) {
        video.src = camera.url;
        video.play().catch(() => {});
      }
      setText("cameraHud", `${camera.camera_id} CCTV feed`);
    }

    function renderFunnel(stages) {
      const root = document.getElementById("funnel");
      const max = Math.max(1, ...stages.map(s => s.count || 0));
      root.innerHTML = stages.map(stage => {
        const width = Math.max(2, Math.round(((stage.count || 0) / max) * 100));
        return `<div class="stage">
          <strong>${stage.stage}</strong>
          <div class="bar"><span style="width:${width}%"></span></div>
          <span>${stage.count}</span>
        </div>`;
      }).join("");
    }

    function renderAnomalies(items) {
      const root = document.getElementById("anomalies");
      if (!items.length) {
        root.innerHTML = `<div class="empty">No active anomalies.</div>`;
        return;
      }
      root.innerHTML = items.map(item => `<div class="anomaly">
        <strong>${item.severity} ${item.type}</strong>
        <div>${item.suggested_action}</div>
      </div>`).join("");
    }

    function renderEvents(items) {
      const root = document.getElementById("events");
      root.innerHTML = items.map(event => `<tr>
        <td><code>${eventSeconds(event.timestamp)}</code></td>
        <td><span class="event-type">${event.event_type}</span></td>
        <td>${event.camera_id}</td>
        <td><code>${event.visitor_id}</code></td>
        <td>${event.zone_id || ""}</td>
        <td>${personRole(event)}</td>
      </tr>`).join("");
    }

    function renderHeatmap(items) {
      const root = document.getElementById("heatmap");
      if (!items.length) {
        root.innerHTML = `<div class="empty">No zone visits yet.</div>`;
        return;
      }
      root.innerHTML = items.map(item => `<div class="heat-cell">
        <strong>${item.zone_id}</strong>
        <div class="sub">${item.visit_frequency} visits</div>
        <div class="heat-score"><span style="width:${item.normalized_score}%"></span></div>
      </div>`).join("");
    }

    function renderQuality(events) {
      if (!events.length) {
        setText("qualitySummary", "-");
        setText("detectorModel", "waiting for YOLOE-26 events");
        setText("avgConfText", "0");
        setText("staffText", "0");
        document.getElementById("avgConfBar").style.width = "0%";
        document.getElementById("staffBar").style.width = "0%";
        return;
      }
      const avg = events.reduce((sum, event) => sum + (Number(event.confidence) || 0), 0) / events.length;
      const staff = events.filter(event => personRole(event) === "staff").length;
      const staffPct = staff / events.length;
      setText("qualitySummary", avg >= 0.65 ? "Good" : avg >= 0.45 ? "Watch" : "Low");
      setText("detectorModel", `detector: ${detectorModel(events)}`);
      setText("avgConfText", avg.toFixed(2));
      setText("staffText", staff);
      document.getElementById("avgConfBar").style.width = `${Math.round(avg * 100)}%`;
      document.getElementById("staffBar").style.width = `${Math.round(staffPct * 100)}%`;
    }

    function renderOverlay(events) {
      const overlay = document.getElementById("overlay");
      const showOverlay = document.getElementById("showOverlay").checked;
      const minConfidence = Number(document.getElementById("minConfidence").value) || 0;
      if (!showOverlay) {
        overlay.innerHTML = "";
        setText("detectionHud", "overlay hidden");
        return;
      }

      const latestByVisitor = new Map();
      events
        .filter(event => event.camera_id === state.selectedCamera)
        .filter(event => (Number(event.confidence) || 0) >= minConfidence)
        .filter(event => event.metadata && (event.metadata.bbox_xyxy || event.metadata.center_norm))
        .forEach(event => {
          const key = event.metadata.camera_visitor_id || event.visitor_id;
          if (!latestByVisitor.has(key)) latestByVisitor.set(key, event);
        });

      const cameraEvents = Array.from(latestByVisitor.values()).slice(0, 5);

      overlay.innerHTML = cameraEvents.map(event => {
        const bbox = event.metadata.bbox_xyxy;
        const role = personRole(event);
        const staff = role === "staff" ? "staff" : "";
        const label = `${role} ${Number(event.confidence || 0).toFixed(2)}`;
        if (Array.isArray(bbox) && bbox.length === 4) {
          const frameWidth = Number(event.metadata.frame_width) || 1920;
          const frameHeight = Number(event.metadata.frame_height) || 1080;
          const left = Math.max(0, Math.min(100, bbox[0] / frameWidth * 100));
          const top = Math.max(0, Math.min(100, bbox[1] / frameHeight * 100));
          const width = Math.max(3, Math.min(100 - left, (bbox[2] - bbox[0]) / frameWidth * 100));
          const height = Math.max(4, Math.min(100 - top, (bbox[3] - bbox[1]) / frameHeight * 100));
          return `<div class="box ${staff}" style="left:${left}%;top:${top}%;width:${width}%;height:${height}%"><span class="box-label">${label}</span></div>`;
        }
        const center = event.metadata.center_norm;
        if (Array.isArray(center) && center.length === 2) {
          return `<div class="box ${staff}" style="left:${center[0] * 100}%;top:${center[1] * 100}%;width:5%;height:8%"><span class="box-label">${label}</span></div>`;
        }
        return "";
      }).join("");
      setText("detectionHud", `${cameraEvents.length} boxes above ${minConfidence.toFixed(2)} confidence`);
    }

    async function loadDashboard() {
      state.storeId = document.getElementById("storeId").value.trim() || "ST1008";
      try {
        const response = await fetch(`/stores/${encodeURIComponent(state.storeId)}/live?limit=80`, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const metrics = data.metrics;

        setText("uniqueVisitors", metrics.unique_visitors);
        setText("conversionRate", fmtPercent(metrics.conversion_rate));
        setText("convertedVisitors", `${metrics.converted_visitors} converted`);
        setText("queueDepth", metrics.queue_depth);
        setText("eventCount", data.event_count);
        setText("lastEvent", data.last_event_timestamp || "no events");

        if (state.previousEventCount !== null && data.event_count > state.previousEventCount) {
          state.pulseUntil = Date.now() + 2500;
        }
        state.previousEventCount = data.event_count;
        const receiving = Date.now() < state.pulseUntil;
        setText("pipelineLink", receiving ? "Receiving" : "Idle");
        document.getElementById("pipelineMetric").classList.toggle("hot", receiving);
        document.getElementById("eventMetric").classList.toggle("hot", receiving);

        renderFunnel(data.funnel.stages || []);
        renderAnomalies(data.anomalies.active_anomalies || []);
        state.lastEvents = data.recent_events || [];
        renderEvents(state.lastEvents);
        renderHeatmap((data.heatmap && data.heatmap.zones) || []);
        renderQuality(state.lastEvents);
        renderOverlay(state.lastEvents);

        document.getElementById("dot").classList.add("live");
        setText("statusText", `Live ${new Date().toLocaleTimeString()}`);
      } catch (error) {
        document.getElementById("dot").classList.remove("live");
        setText("statusText", `Disconnected: ${error.message}`);
      }
    }

    document.getElementById("refresh").addEventListener("click", loadDashboard);
    document.getElementById("showOverlay").addEventListener("change", () => renderOverlay(state.lastEvents));
    document.getElementById("minConfidence").addEventListener("change", () => renderOverlay(state.lastEvents));
    loadCameras().then(loadDashboard).catch(loadDashboard);
    setInterval(loadDashboard, 1500);
  </script>
</body>
</html>"""
