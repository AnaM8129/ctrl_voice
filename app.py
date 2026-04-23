import os
import json
import time
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho

# ── MQTT ──
broker = "broker.mqttdashboard.com"
port   = 1883

def on_publish(client, userdata, result):
    print("dato publicado")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

client1 = paho.Client("ANA_8129")
client1.on_message = on_message

# ── PAGE ──
st.set_page_config(page_title="Control por Voz", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');

:root {
    --bg:       #fef9ee;
    --card:     #ffffff;
    --yellow:   #f9c74f;
    --yellow2:  #fde68a;
    --peach:    #fca5a5;
    --green:    #86efac;
    --lavender: #c4b5fd;
    --blue:     #93c5fd;
    --text:     #3d2c1e;
    --muted:    #a8906f;
    --pill:     #f3e8d0;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    font-family: 'Quicksand', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    max-width: 420px;
    padding: 1.2rem 1rem 3rem;
    margin: 0 auto;
}

/* ── Top bar ── */
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.2rem 1rem;
}
.topbar-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
}
.topbar-icons { font-size: 1.2rem; display: flex; gap: 0.6rem; }

/* ── Hero illustration card ── */
.hero-card {
    background: linear-gradient(145deg, #fde68a 0%, #fef3c7 60%, #fce7f3 100%);
    border-radius: 28px;
    padding: 1.8rem 1.5rem 1.4rem;
    text-align: center;
    position: relative;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 16px rgba(249,199,79,0.18);
    overflow: hidden;
}
.hero-card::before {
    content: '✦';
    position: absolute; top: 14px; left: 18px;
    color: var(--yellow); font-size: 0.9rem; opacity: 0.7;
}
.hero-card::after {
    content: '✦';
    position: absolute; bottom: 18px; right: 22px;
    color: var(--peach); font-size: 0.7rem; opacity: 0.7;
}
.companion-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.05em;
    margin-bottom: 0.1rem;
}
.companion-name {
    font-size: 2rem;
    font-weight: 700;
    color: #b45309;
    font-style: italic;
    margin-bottom: 0.6rem;
}
.hero-emoji-big {
    font-size: 5rem;
    display: block;
    animation: float 3s ease-in-out infinite;
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.08));
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-8px); }
}

/* ── Section label ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 1.2rem 0 0.6rem 0.2rem;
}

/* ── Info card ── */
.info-card {
    background: var(--card);
    border-radius: 20px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.info-card-row {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
}
.info-icon { font-size: 1.5rem; flex-shrink: 0; margin-top: 0.1rem; }
.info-body {}
.info-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--muted);
    margin-bottom: 0.15rem;
}
.info-value {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
}
.info-sub {
    font-size: 0.8rem;
    color: var(--muted);
    font-weight: 500;
    margin-top: 0.1rem;
}

/* ── Command chips ── */
.chips-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.chip {
    background: var(--card);
    border-radius: 16px;
    padding: 0.7rem 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text);
}
.chip-icon { font-size: 1.3rem; }

/* ── Voice button ── */
.bk-btn, .bk-btn-default {
    font-family: 'Quicksand', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    background: var(--yellow) !important;
    color: var(--text) !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.55rem 2rem !important;
    box-shadow: 0 4px 14px rgba(249,199,79,0.45) !important;
    cursor: pointer !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.bk-btn:hover, .bk-btn-default:hover {
    transform: scale(1.03) !important;
    box-shadow: 0 6px 20px rgba(249,199,79,0.55) !important;
}

/* ── Result pill ── */
.result-pill {
    background: var(--pill);
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    margin-top: 0.8rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}
.sent-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: var(--green);
    color: #14532d;
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 0.5rem;
}
.error-tag {
    background: var(--peach);
    color: #7f1d1d;
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 0.5rem;
    display: inline-block;
}

/* ── Bottom nav ── */
.bottom-nav {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: white;
    display: flex;
    justify-content: space-around;
    padding: 0.8rem 0 1rem;
    box-shadow: 0 -2px 16px rgba(0,0,0,0.07);
    font-size: 1.4rem;
    z-index: 999;
}
.nav-item { cursor: pointer; opacity: 0.45; }
.nav-item.active { opacity: 1; }
</style>
""", unsafe_allow_html=True)

# ── TOP BAR ──
st.markdown("""
<div class="topbar">
    <div class="topbar-title">Interfaces Multimodales</div>
    <div class="topbar-icons">⚙️ 🔔</div>
</div>
""", unsafe_allow_html=True)

# ── HERO CARD ──
st.markdown("""
<div class="hero-card">
    <div class="companion-label">Tu asistente es...</div>
    <div class="companion-name">Micrófono 🎙️</div>
    <span class="hero-emoji-big">🤖</span>
</div>
""", unsafe_allow_html=True)

# ── VOICE SECTION ──
st.markdown('<div class="section-label">🎤 Control por voz</div>', unsafe_allow_html=True)

st.markdown('<div class="info-card">', unsafe_allow_html=True)
st.markdown("""
<div class="info-card-row">
    <span class="info-icon">💬</span>
    <div class="info-body">
        <div class="info-title">Instrucción</div>
        <div class="info-value">Toca el botón y habla</div>
        <div class="info-sub">Di uno de los comandos disponibles abajo</div>
    </div>
</div>
""", unsafe_allow_html=True)

stt_button = Button(label="🎙  Iniciar escucha", width=220)
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
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
    override_height=65,
    debounce_time=0,
)

if result:
    if "GET_TEXT" in result:
        texto = result.get("GET_TEXT")
        st.markdown(f"""
        <div class="result-pill">
            <span>🗣️</span>
            <div>
                <div style="color:#a8906f;font-size:0.72rem;font-weight:600;margin-bottom:0.2rem">ESCUCHÉ</div>
                "{texto}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            client1.on_publish = on_publish
            client1.connect(broker, port)
            message = json.dumps({"Act1": texto.strip()})
            client1.publish("voice_ctrl_ana", message)
            st.markdown('<div class="sent-tag">✔ Enviado al dispositivo</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-tag">⚠️ Error: {e}</div>', unsafe_allow_html=True)

        try:
            os.mkdir("temp")
        except:
            pass

st.markdown('</div>', unsafe_allow_html=True)

# ── COMMANDS GRID ──
st.markdown('<div class="section-label">📋 Comandos disponibles</div>', unsafe_allow_html=True)
st.markdown("""
<div class="chips-grid">
    <div class="chip"><span class="chip-icon">🔓</span> Abre la puerta</div>
    <div class="chip"><span class="chip-icon">🔒</span> Cierra la puerta</div>
    <div class="chip"><span class="chip-icon">💡</span> Enciende las luces</div>
    <div class="chip"><span class="chip-icon">🌑</span> Apaga las luces</div>
</div>
""", unsafe_allow_html=True)

# ── BOTTOM NAV ──
st.markdown("""
<div class="bottom-nav">
    <span class="nav-item active">🏠</span>
    <span class="nav-item">👥</span>
    <span class="nav-item">⏺️</span>
    <span class="nav-item">👤</span>
    <span class="nav-item">📊</span>
</div>
""", unsafe_allow_html=True)
