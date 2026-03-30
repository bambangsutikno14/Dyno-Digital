import streamlit as st
import numpy as np
import math
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="RX-King Dyno Station", layout="wide")

# --- 2. ADVANCED SOUND ENGINE (Triple Layer Engine) ---
def play_rx_king_sound(rpm, active=False):
    if not active: return ""
    # Frekuensi dasar untuk suara 2-tak/bore-up yang lebih serak
    f1 = 40 + (rpm / 20)
    f2 = f1 * 1.5
    f3 = f1 * 2.1
    js_code = f"""
    <script>
    if (!window.audioCtx) {{
        window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        function createOsc(freq, type, vol) {{
            let osc = window.audioCtx.createOscillator();
            let g = window.audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, window.audioCtx.currentTime);
            osc.connect(g); g.connect(window.audioCtx.destination);
            osc.start();
            return {{osc: osc, g: g}};
        }}
        window.layer1 = createOsc({f1}, 'sawtooth', 0.1);
        window.layer2 = createOsc({f2}, 'square', 0.05);
        window.layer3 = createOsc({f3}, 'triangle', 0.05);
    }}
    let t = window.audioCtx.currentTime;
    window.layer1.osc.frequency.setTargetAtTime({f1}, t, 0.1);
    window.layer2.osc.frequency.setTargetAtTime({f2}, t, 0.1);
    window.layer3.osc.frequency.setTargetAtTime({f3}, t, 0.1);
    
    let vol = {rpm} > 500 ? 0.15 : 0;
    window.layer1.g.gain.setTargetAtTime(vol, t, 0.1);
    window.layer2.g.gain.setTargetAtTime(vol * 0.5, t, 0.1);
    window.layer3.g.gain.setTargetAtTime(vol * 0.3, t, 0.1);
    </script>
    """
    return components.html(js_code, height=0)

# --- 3. ANALOG RX-KING GAUGE DESIGN ---
def draw_rx_gauge(value, label, max_val, steps, color="white"):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': label, 'font': {'size': 24, 'color': 'gold', 'family': 'Courier New'}},
        gauge = {
            'axis': {'range': [0, max_val], 'tickvals': list(range(0, max_val+1, steps)), 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "black",
            'borderwidth': 3,
            'bordercolor': "#555",
            'steps': [{'range': [max_val*0.85, max_val], 'color': "red"}],
        }
    ))
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=60, b=40), paper_bgcolor="black", font={'color': "white"})
    return fig

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("👑 RX-KING COCKPIT")
    bore = st.number_input("Piston (mm)", value=58.0)
    stroke = st.number_input("Stroke (mm)", value=58.7)
    rpm_limit = st.slider("Limit RPM", 8000, 15000, 12000)
    btn_start = st.button("🏁 GAS POLLLL!")

# --- 5. MAIN PANEL ---
st.markdown("<h2 style='text-align: center; color: gold;'>👑 RAJA JALANAN DYNO TEST 👑</h2>", unsafe_allow_html=True)

if btn_start:
    cc = (math.pi * (bore**2) * stroke) / 4000
    
    c1, c2 = st.columns(2)
    rpm_ph = c1.empty()
    spd_ph = c2.empty()
    chart_ph = st.empty()
    sound_ph = st.empty()
    
    # Logika Penarikan Gas Manusiawi (Non-Linear)
    # Kita bagi jadi 60 langkah, tapi pakai fungsi power agar awalnya pelan
    steps = 80
    list_rpm, list_hp = [], []
    
    for i in range(steps + 1):
        # Progress non-linear (i/steps)^1.5 membuat percepatan lebih halus di awal
        progress = (i / steps)**1.4
        curr_rpm = progress * rpm_limit
        
        # Efek "Blayer" dikit di awal (RPM naik turun dikit)
        if i < 15: curr_rpm += math.sin(i) * 100 
        
        # Hitung HP & Speed
        hp = (11.0 * cc * curr_rpm * 0.85) / 950000 
        speed = (curr_rpm * 0.018)
        
        list_rpm.append(curr_rpm)
        list_hp.append(round(hp, 2))
        
        # Visual Update
        rpm_ph.plotly_chart(draw_rx_gauge(curr_rpm, "RPM x1000", 15000, 1000, "cyan"), use_container_width=True)
        spd_ph.plotly_chart(draw_rx_gauge(speed, "KM/H", 200, 20, "lime"), use_container_width=True)
        
        # Graph Update
        fig_g = go.Figure(go.Scatter(x=list_rpm, y=list_hp, line=dict(color='gold', width=4)))
        fig_g.update_layout(template="plotly_dark", height=350, xaxis=dict(range=[0, 16000]), yaxis=dict(range=[0, 30]))
        chart_ph.plotly_chart(fig_g, use_container_width=True)
        
        # Sound Update
        with sound_ph: play_rx_king_sound(curr_rpm, active=True)
        
        # Kecepatan tarikan gas (semakin tinggi semakin cepat)
        time.sleep(0.04 - (progress * 0.02))

    # Finish
    with sound_ph: play_rx_king_sound(0, active=True)
    st.success(f"🔥 Selesai! Power: {max(list_hp)} HP pada {int(curr_rpm)} RPM")
else:
    st.info("Atur Piston & Stroke di kiri, lalu tarik gasnya!")
