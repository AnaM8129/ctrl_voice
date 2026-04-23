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
    pass

# ── PAGE ──
st.set_page_config(page_title="Control por Voz 🎀", page_icon="🎀", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

:root {
    --pink:   #f9a8d4;
    --pink2:  #fce7f3;
    --purple: #c084fc;
    --soft:   #fdf4ff;
    --text:   #6b21a8;
    --muted:  #a78bca;
}

.stApp {
    background: linear-gradient(160deg, #fdf4ff 0%, #fce7f3 50%, #ede9fe 100%);
    font-family: 'Nunito', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 540px; padding-top: 2rem; }

h1 {
    font-family: 'Nunito', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    text-align: center;
}

.hero {
    text-align: center;
    padding: 2rem 1rem 1rem;
}
.hero-emoji { font-size: 5rem; animation: bounce 2s infinite; display: block; }
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-10px); }
}
.hero-title {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--text);
    margin: 0.5rem 0 0.2rem;
}
.hero-sub {
    font-size: 0.95rem;
    color: var(--muted);
    font-weight: 600;
}

.card {
    background: white;
    border-radius: 20px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 4px 20px rgba(192,132,252,0.15);
    margin: 1rem 0;
    text-align: center;
}
.hint {
    font-size: 0.92rem;
    color: var(--muted);
    font-weight: 600;
    margin-bottom: 0.8rem;
}

/* Bokeh button */
.bk-btn, .bk-btn-default {
    font-family: 'Nunito', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #f9a8d4, #c084fc) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.6rem 2rem !important;
    cursor: pointer !important;
    box-shadow: 0 4px 14px rgba(192,132,252,0.4) !important;
    transition: transform 0.15s !important;
}
.bk-btn:hover, .bk-btn-default:hover {
    transform: scale(1.04) !important;
}

.result-box {
    background: var(--pink2);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    margin-top: 1rem;
    border: 2px dashed var(--pink);
}
.sent-badge {
    display: inline-block;
    background: #d1fae5;
    color: #065f46;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.82rem;
    font-weight: 700;
    margin-top: 0.6rem;
}

.commands {
    background: white;
    border-radius: 20px;
    padding: 1.2rem 1.8rem;
    box-shadow: 0 4px 20px rgba(192,132,252,0.1);
    margin-top: 1rem;
}
.cmd-title {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.cmd-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
    padding: 0.3rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── HERO ──
st.markdown("""
<div class="hero">
    <span class="hero-emoji">🎙️</span>
    <div class="hero-title">Control por Voz 🎀</div>
    <div class="hero-sub">Habla y tu dispositivo te escucha ✨</div>
</div>
""", unsafe_allow_html=True)

# ── VOICE CARD ──
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="hint">🌸 Toca el botón y di tu comando</div>', unsafe_allow_html=True)

stt_button = Button(label="🎀  ¡Habla aquí!  🎀", width=220)
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
    override_height=65,
    debounce_time=0,
)

if result and "GET_TEXT" in result:
    text = result["GET_TEXT"].strip()
    st.markdown(f"""
    <div class="result-box">🗣️ &nbsp;"{text}"</div>
    """, unsafe_allow_html=True)

    try:
        client1 = paho.Client("ANA_8129")
        client1.on_publish = on_publish
        client1.connect(broker, port)
        payload = json.dumps({"Act1": text})
        client1.publish("voice_ctrl_ana", payload)
        client1.disconnect()
        st.markdown('<div class="sent-badge">✔ Enviado al dispositivo</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div style="color:#dc2626;font-size:0.85rem;margin-top:0.5rem">⚠️ Error MQTT: {e}</div>',
                    unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── COMMANDS HINT ──
st.markdown("""
<div class="commands">
    <div class="cmd-title">💬 Comandos disponibles</div>
    <div class="cmd-item">🔓 "abre la puerta"</div>
    <div class="cmd-item">🔒 "Cierra la puerta"</div>
    <div class="cmd-item">💡 "enciende las luces"</div>
    <div class="cmd-item">🌑 "apaga las luces"</div>
</div>
""", unsafe_allow_html=True)
