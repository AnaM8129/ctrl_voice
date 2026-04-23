import os
import json
import time
import datetime
import pandas as pd
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS · Control de Acceso",
    page_icon="🔐",
    layout="wide",
)

# ─────────────────────────────────────────────
#  MQTT CONFIG
# ─────────────────────────────────────────────
BROKER   = "broker.mqttdashboard.com"
PORT     = 1883
TOPIC    = "voice_ctrl"

# ─────────────────────────────────────────────
#  COMMAND MAP  (exact strings the Arduino uses)
# ─────────────────────────────────────────────
COMMANDS = {
    "abre la puerta":    {"action": "PUERTA ABIERTA",   "icon": "🔓", "type": "access",  "arduino": "abre la puerta"},
    "cierra la puerta":  {"action": "PUERTA CERRADA",   "icon": "🔒", "type": "lock",    "arduino": "Cierra la puerta"},
    "enciende las luces":{"action": "LUCES ENCENDIDAS", "icon": "💡", "type": "light",   "arduino": "enciende las luces"},
    "apaga las luces":   {"action": "LUCES APAGADAS",   "icon": "🌑", "type": "light",   "arduino": "apaga las luces"},
}

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "bitacora" not in st.session_state:
    st.session_state.bitacora = []   # list of dicts
if "door_open" not in st.session_state:
    st.session_state.door_open = False
if "lights_on" not in st.session_state:
    st.session_state.lights_on = False
if "last_cmd" not in st.session_state:
    st.session_state.last_cmd = None

# ─────────────────────────────────────────────
#  GLOBAL CSS  — Tactical / Security Terminal
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@300;400;600;700;900&display=swap');

:root {
    --bg:        #0a0d0f;
    --panel:     #0f1417;
    --border:    #1e2c35;
    --border2:   #243340;
    --cyan:      #00d4ff;
    --cyan-dim:  #007a99;
    --green:     #00ff88;
    --green-dim: #007a40;
    --red:       #ff3d3d;
    --red-dim:   #7a1a1a;
    --amber:     #ffb700;
    --text:      #c8dde8;
    --text-dim:  #4a6a7a;
    --mono:      'Share Tech Mono', monospace;
    --sans:      'Barlow Condensed', sans-serif;
}

/* ── Base ── */
.stApp {
    background-color: var(--bg);
    background-image:
        linear-gradient(rgba(0,212,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
}
* { box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

/* ── Top bar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border2);
    padding-bottom: 1rem;
    margin-bottom: 1.8rem;
}
.topbar-brand {
    font-family: var(--sans);
    font-weight: 900;
    font-size: 1.9rem;
    letter-spacing: 0.22em;
    color: var(--cyan);
    text-shadow: 0 0 20px rgba(0,212,255,0.5);
    text-transform: uppercase;
}
.topbar-brand span { color: var(--text-dim); font-weight: 300; }
.topbar-time {
    font-family: var(--mono);
    font-size: 0.85rem;
    color: var(--text-dim);
    text-align: right;
    line-height: 1.6;
}
.topbar-status {
    display: flex;
    gap: 1.2rem;
    align-items: center;
}
.status-pill {
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    padding: 0.25rem 0.75rem;
    border-radius: 2px;
    border: 1px solid;
    text-transform: uppercase;
}
.pill-online  { color: var(--green); border-color: var(--green-dim); background: rgba(0,255,136,0.06); }
.pill-offline { color: var(--red);   border-color: var(--red-dim);   background: rgba(255,61,61,0.06); }
.pill-locked  { color: var(--amber); border-color: #7a5500;          background: rgba(255,183,0,0.06); }

/* ── Cards ── */
.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--cyan);
}
.card-accent-green::before { background: var(--green); }
.card-accent-red::before   { background: var(--red); }
.card-accent-amber::before { background: var(--amber); }

.card-title {
    font-family: var(--sans);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.5rem;
}
.card-value {
    font-family: var(--sans);
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: 0.05em;
}
.card-icon {
    position: absolute;
    right: 1.2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 2rem;
    opacity: 0.18;
}

/* ── Section headers ── */
.sec-header {
    font-family: var(--sans);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--cyan-dim);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.sec-header::before {
    content: '▶';
    font-size: 0.5rem;
    color: var(--cyan);
}

/* ── Voice button ── */
.bk-btn {
    font-family: var(--sans) !important;
    background: transparent !important;
    border: 1px solid var(--cyan) !important;
    color: var(--cyan) !important;
    letter-spacing: 0.15em !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: #060a0c;
    border: 1px solid var(--border2);
    border-radius: 3px;
    padding: 1rem 1.2rem;
    font-family: var(--mono);
    font-size: 0.9rem;
    color: var(--green);
    min-height: 60px;
    margin: 0.8rem 0;
    position: relative;
}
.transcript-box::before {
    content: '> ';
    color: var(--cyan-dim);
}
.transcript-label {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}

/* ── Log table ── */
.log-row {
    display: grid;
    grid-template-columns: 140px 50px 1fr 120px;
    gap: 1rem;
    align-items: center;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--text);
    transition: background 0.15s;
}
.log-row:hover { background: rgba(0,212,255,0.03); }
.log-row-header {
    color: var(--text-dim) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border2) !important;
    padding-bottom: 0.5rem !important;
}
.log-type-access { color: var(--green); }
.log-type-lock   { color: var(--red); }
.log-type-light  { color: var(--amber); }

.badge-access { background: rgba(0,255,136,0.1); color: var(--green); border: 1px solid var(--green-dim); padding: 2px 8px; border-radius: 2px; font-size: 0.65rem; letter-spacing: 0.1em; }
.badge-lock   { background: rgba(255,61,61,0.1);  color: var(--red);   border: 1px solid var(--red-dim);   padding: 2px 8px; border-radius: 2px; font-size: 0.65rem; letter-spacing: 0.1em; }
.badge-light  { background: rgba(255,183,0,0.1);  color: var(--amber); border: 1px solid #7a5500;           padding: 2px 8px; border-radius: 2px; font-size: 0.65rem; letter-spacing: 0.1em; }

/* ── Device display ── */
.device-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.device-name {
    font-family: var(--sans);
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.device-state {
    font-family: var(--sans);
    font-size: 2.8rem;
    font-weight: 900;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.state-open   { color: var(--green); text-shadow: 0 0 20px rgba(0,255,136,0.4); }
.state-closed { color: var(--red);   text-shadow: 0 0 20px rgba(255,61,61,0.4); }
.state-on     { color: var(--amber); text-shadow: 0 0 20px rgba(255,183,0,0.4); }
.state-off    { color: var(--text-dim); }

.device-icon  { font-size: 3rem; margin-bottom: 0.5rem; display: block; }
.pulse-ring {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 80px; height: 80px;
    border-radius: 50%;
    border: 1px solid var(--green);
    animation: pulse 2s infinite;
    pointer-events: none;
}
@keyframes pulse {
    0%   { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
    100% { transform: translate(-50%, -50%) scale(2.0); opacity: 0; }
}

/* ── Command feedback ── */
.cmd-feedback {
    background: rgba(0,255,136,0.05);
    border: 1px solid var(--green-dim);
    border-radius: 3px;
    padding: 0.8rem 1rem;
    font-family: var(--mono);
    font-size: 0.82rem;
    color: var(--green);
    animation: fadeIn 0.4s ease;
    margin-top: 0.6rem;
}
.cmd-feedback-warn {
    background: rgba(255,61,61,0.05);
    border-color: var(--red-dim);
    color: var(--red);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Streamlit overrides ── */
.stButton > button {
    font-family: var(--sans) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border: 1px solid var(--border2) !important;
    color: var(--text-dim) !important;
    border-radius: 2px !important;
    padding: 0.4rem 1rem !important;
}
.stButton > button:hover {
    border-color: var(--red) !important;
    color: var(--red) !important;
}
.stTextInput > div > div > input {
    background: #060a0c !important;
    border: 1px solid var(--border2) !important;
    color: var(--cyan) !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
    border-radius: 2px !important;
}
.stTextInput label {
    font-family: var(--sans) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
}
[data-testid="stSidebar"] {
    background: #080b0d !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-dim) !important; }
.stSlider > div > div > div > div { background: var(--cyan) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def publish_command(arduino_cmd: str) -> bool:
    try:
        c = paho.Client("streamlit_nexus_01")
        c.connect(BROKER, PORT, keepalive=10)
        payload = json.dumps({"Act1": arduino_cmd})
        c.publish(TOPIC, payload)
        c.disconnect()
        return True
    except Exception as e:
        st.error(f"MQTT error: {e}")
        return False


def log_event(raw_text: str, matched: bool, cmd_info: dict | None, user: str):
    now = datetime.datetime.now()
    st.session_state.bitacora.insert(0, {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "time_only": now.strftime("%H:%M:%S"),
        "user":      user,
        "raw":       raw_text,
        "action":    cmd_info["action"] if matched else "SIN COINCIDENCIA",
        "icon":      cmd_info["icon"]   if matched else "⚠️",
        "type":      cmd_info["type"]   if matched else "unknown",
        "status":    "OK" if matched else "FAIL",
    })


def match_command(text: str):
    t = text.lower().strip()
    for key, info in COMMANDS.items():
        if key in t:
            return key, info
    return None, None


def render_log_table():
    if not st.session_state.bitacora:
        st.markdown(
            "<div style='font-family:var(--mono);font-size:0.78rem;color:var(--text-dim);"
            "padding:1.5rem;text-align:center;border:1px dashed #1e2c35;border-radius:3px;'>"
            "— Sin registros aún —</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown("""
    <div class="log-row log-row-header">
        <span>TIMESTAMP</span><span>ST</span><span>ACCIÓN / VOZ</span><span>TIPO</span>
    </div>""", unsafe_allow_html=True)

    for entry in st.session_state.bitacora[:50]:
        type_cls   = f"log-type-{entry['type']}"
        badge_cls  = f"badge-{entry['type']}" if entry["type"] in ("access","lock","light") else ""
        status_sym = "✔" if entry["status"] == "OK" else "✘"
        status_col = "#00ff88" if entry["status"] == "OK" else "#ff3d3d"
        st.markdown(f"""
        <div class="log-row">
            <span style="color:var(--text-dim)">{entry['time_only']}</span>
            <span style="color:{status_col};font-size:1rem">{status_sym}</span>
            <span>
                <span style="margin-right:0.4rem">{entry['icon']}</span>
                <span class="{type_cls}">{entry['action']}</span>
                <span style="color:var(--text-dim);font-size:0.7rem;margin-left:0.6rem">
                    [{entry['raw'][:40]}]
                </span>
            </span>
            <span><span class="{badge_cls}">{entry['type'].upper()}</span></span>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ CONFIG")
    st.markdown("---")
    operator_name = st.text_input("Operador", value="Operador 1",
                                  help="Nombre que se registra en la bitácora")
    st.markdown("---")
    st.markdown("**Comandos reconocidos:**")
    for k, v in COMMANDS.items():
        st.markdown(
            f"<span style='font-family:monospace;font-size:0.8rem;color:#4a6a7a'>"
            f"{v['icon']} <em>{k}</em></span>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    if st.button("🗑 Limpiar bitácora"):
        st.session_state.bitacora = []
        st.rerun()
    st.markdown("---")
    total   = len(st.session_state.bitacora)
    success = sum(1 for e in st.session_state.bitacora if e["status"] == "OK")
    fail    = total - success
    st.markdown(f"<span style='font-size:0.75rem;color:#4a6a7a'>Total: {total} · OK: {success} · FAIL: {fail}</span>",
                unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TOP BAR
# ─────────────────────────────────────────────
now_str = datetime.datetime.now().strftime("%A, %d %b %Y · %H:%M")
door_pill = '<span class="status-pill pill-online">PUERTA ABIERTA</span>' if st.session_state.door_open \
            else '<span class="status-pill pill-locked">PUERTA CERRADA</span>'
lights_pill = '<span class="status-pill pill-online">LUCES ON</span>' if st.session_state.lights_on \
              else '<span class="status-pill pill-offline">LUCES OFF</span>'

st.markdown(f"""
<div class="topbar">
    <div class="topbar-brand">NEXUS <span>// CONTROL DE ACCESO</span></div>
    <div class="topbar-status">{door_pill} {lights_pill}</div>
    <div class="topbar-time">🟢 MQTT CONECTADO<br>{now_str}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MAIN LAYOUT
# ─────────────────────────────────────────────
left_col, right_col = st.columns([1.1, 1.9], gap="large")

# ══════════════════════════════════════════════
#  LEFT — Voice Control + Device State
# ══════════════════════════════════════════════
with left_col:

    # ── Stat cards ──
    total   = len(st.session_state.bitacora)
    success = sum(1 for e in st.session_state.bitacora if e["status"] == "OK")
    fail    = total - success

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="card">
            <div class="card-title">Total</div>
            <div class="card-value">{total}</div>
            <div class="card-icon">📋</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card card-accent-green">
            <div class="card-title">Exitosos</div>
            <div class="card-value" style="color:var(--green)">{success}</div>
            <div class="card-icon">✔</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card card-accent-red">
            <div class="card-title">Fallidos</div>
            <div class="card-value" style="color:var(--red)">{fail}</div>
            <div class="card-icon">✘</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='sec-header'>Control por voz</div>", unsafe_allow_html=True)

    # ── Voice button ──
    stt_button = Button(label="🎙  INICIAR ESCUCHA", width=300,
                        styles={"font-family": "Barlow Condensed", "font-size": "14px",
                                "letter-spacing": "2px", "background": "#0f1417",
                                "color": "#00d4ff", "border": "1px solid #00d4ff"})
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';
        recognition.onresult = function(e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) { value += e.results[i][0].transcript; }
            }
            if (value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=60,
        debounce_time=0,
    )

    # ── Process voice result ──
    if result and "GET_TEXT" in result:
        raw_text = result["GET_TEXT"].strip()
        matched_key, cmd_info = match_command(raw_text)

        # Show transcript
        st.markdown(f"""
        <div class="transcript-label">TRANSCRIPCIÓN RECIBIDA</div>
        <div class="transcript-box">{raw_text}</div>
        """, unsafe_allow_html=True)

        if matched_key and cmd_info:
            ok = publish_command(cmd_info["arduino"])
            log_event(raw_text, True, cmd_info, operator_name)

            # Update device state
            if matched_key == "abre la puerta":
                st.session_state.door_open = True
            elif matched_key == "cierra la puerta":
                st.session_state.door_open = False
            elif matched_key == "enciende las luces":
                st.session_state.lights_on = True
            elif matched_key == "apaga las luces":
                st.session_state.lights_on = False

            st.session_state.last_cmd = cmd_info
            st.markdown(f"""<div class="cmd-feedback">
                ✔ COMANDO ENVIADO · {cmd_info['icon']} {cmd_info['action']}
            </div>""", unsafe_allow_html=True)
            st.rerun()
        else:
            log_event(raw_text, False, None, operator_name)
            st.markdown(f"""<div class="cmd-feedback cmd-feedback-warn">
                ✘ COMANDO NO RECONOCIDO · "{raw_text}"
            </div>""", unsafe_allow_html=True)

    # ── Device state display ──
    st.markdown("<br><div class='sec-header'>Estado de dispositivos</div>", unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        door_icon  = "🔓" if st.session_state.door_open else "🔒"
        door_state = "ABIERTA" if st.session_state.door_open else "CERRADA"
        door_cls   = "state-open" if st.session_state.door_open else "state-closed"
        pulse      = '<div class="pulse-ring"></div>' if st.session_state.door_open else ""
        st.markdown(f"""<div class="device-card">
            {pulse}
            <div class="device-name">Puerta principal</div>
            <span class="device-icon">{door_icon}</span>
            <div class="device-state {door_cls}">{door_state}</div>
        </div>""", unsafe_allow_html=True)

    with d2:
        light_icon  = "💡" if st.session_state.lights_on else "🌑"
        light_state = "ON" if st.session_state.lights_on else "OFF"
        light_cls   = "state-on" if st.session_state.lights_on else "state-off"
        pulse2      = '<div class="pulse-ring" style="border-color:var(--amber)"></div>' \
                      if st.session_state.lights_on else ""
        st.markdown(f"""<div class="device-card">
            {pulse2}
            <div class="device-name">Iluminación</div>
            <span class="device-icon">{light_icon}</span>
            <div class="device-state {light_cls}">{light_state}</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  RIGHT — Access Log
# ══════════════════════════════════════════════
with right_col:
    st.markdown("<div class='sec-header'>Bitácora de accesos en tiempo real</div>",
                unsafe_allow_html=True)

    render_log_table()

    # ── Export ──
    if st.session_state.bitacora:
        st.markdown("<br>", unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.bitacora)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Exportar CSV",
            data=csv,
            file_name=f"bitacora_{datetime.date.today()}.csv",
            mime="text/csv",
        )
