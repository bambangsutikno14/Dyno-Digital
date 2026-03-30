import streamlit as st
import numpy as np
import math
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE (Memory for Comparison) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. SOUND ENGINE (Web Audio API) ---
def play_engine_sound(rpm, active=False):
    freq = 60 + (rpm / 18) # Pitch naik mengikuti RPM
    if not active: return ""
    js_code = f"""
    <script>
    if (!window.audioCtx) {{
        window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        window.oscillator = window.audioCtx.createOscillator();
        window.gainNode = window.audioCtx.createGain();
        window.oscillator.type = 'sawtooth'; 
        window.oscillator.connect(window.gainNode);
        window.gainNode.connect(window.audioCtx.destination);
        window.oscillator.start();
    }}
    window.oscillator.frequency.setTargetAtTime({freq}, window.audioCtx.currentTime, 0.05);
    window.gainNode.gain.setTargetAtTime(0.15, window.audioCtx.currentTime, 0.05);
    if ({rpm} == 0) {{ window.gainNode.gain.setTargetAtTime(0, window.audioCtx.currentTime, 0.1); }}
    </script>
    """
    return components.html(js_code, height=0)

# --- 4. DATABASE ---
DATABASE_MATIC = {
    "YAMAHA": {
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "vva": True, "weight": 127},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "vva": False, "weight": 94},
    },
    "HONDA": {
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "vva": False, "weight": 112},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head_std": 12.7, "vva": False, "weight": 90},
    }
}

# --- 5. LOGIKA ENGINE (SAE & Physics Based) ---
def get_dyno_point(r, cc, stroke, vva, rpm_limit, temp=25):
    cf = (1.18 * (((temp + 273) / 298) * math.sqrt(298 / (temp + 273)))) - 0.18
    cf = 1/cf
    ve = 0.92 if vva and r > 6000 else 0.86
    ve_curve = ve * math.cos(math.radians((r - (rpm_limit*0.75)) / (rpm_limit*0.5) * 35))
    hp = (10.5 * cc * r * ve_curve) / 900000 * cf
    torque = (hp * 7127) / r if r > 0 else 0
    speed = (r * 0.016) # KM/H Estimation
    return round(hp, 2), round(torque, 2), round(speed, 1)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("🏁 ULTIMATE TUNER")
    merk = st.selectbox("Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor]
    
    label_run = st.text_input("Run Name", value=f"Run {len(st.session_state.history)+1}")
    bore_in = st.number_input("Bore (mm)", value=data_std['bore'], step=0.1)
    v_head_in = st.number_input("Vol Head (cc)", value=data_std['v_head_std'], step=0.1)
    rpm_limit = st.slider("Limit RPM", 5000, 14000, 10000)
    
    with st.expander("🌡️ Weather & Rider"):
        amb_temp = st.slider("Ambient Temp (°C)", 15, 45, 25)
        rider_w = st.number_input("Rider Weight (kg)", value=65)

    btn_run = st.button("🚀 START CINEMATIC DYNO")
    if st.button("🗑️ RESET DATA"):
        st.session_state.history = []
        st.rerun()

# --- 7. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

if btn_run:
    cc = (math.pi * (bore_in**2) * data_std['stroke']) / 4000
    cr = (cc + v_head_in) / v_head_in
    
    # Placeholders for Animation
    g1, g2 = st.columns(2)
    rpm_gauge = g1.empty()
    spd_gauge = g2.empty()
    chart_area = st.empty()
    sound_area = st.empty()

    list_rpm, list_hp, list_torque = [], [], []

    # --- ANIMATION LOOP ---
    for r in range(0, rpm_limit + 200, 200):
        hp, trq, spd = get_dyno_point(r, cc, data_std['stroke'], data_std['vva'], rpm_limit, amb_temp)
        list_rpm.append(r); list_hp.append(hp); list_torque.append(trq)

        with sound_area: play_engine_sound(r, active=True)

        # Gauges Update
        fig_r = go.Figure(go.Indicator(mode="gauge+number", value=r, title={'text':"RPM"}, gauge={'axis':{'range':[0,14000]}, 'bar':{'color':"red" if r >= rpm_limit else "blue"}}))
        rpm_gauge.plotly_chart(fig_r, use_container_width=True)

        fig_s = go.Figure(go.Indicator(mode="gauge+number", value=spd, title={'text':"KM/H"}, gauge={'axis':{'range':[0,200]}, 'bar':{'color':"green"}}))
        spd_gauge.plotly_chart(fig_s, use_container_width=True)

        # Live Graph Drawing
        fig_g = go.Figure()
        fig_g.add_trace(go.Scatter(x=list_rpm, y=list_hp, name="HP", line=dict(color='#ff4b4b', width=4)))
        fig_g.add_trace(go.Scatter(x=list_rpm, y=list_torque, name="Nm", line=dict(color='#00d4ff', dash='dot'), yaxis="y2"))
        fig_g.update_layout(template="plotly_dark", height=400, yaxis2=dict(overlaying="y", side="right"))
        chart_area.plotly_chart(fig_g, use_container_width=True)
        time.sleep(0.01)

    # Save to History after Run
    max_hp = max(list_hp)
    t_w = data_std['weight'] + rider_w
    st.session_state.history.append({
        "Label": label_run, "CC": round(cc,1), "CR": round(cr,1), "HP": max_hp, "Nm": max(list_torque),
        "100m": round(((4.5*t_w*(100**2))/(max_hp*746*0.8))**(1/3), 2),
        "201m": round(((4.5*t_w*(201**2))/(max_hp*746*0.8))**(1/3), 2),
        "402m": round(((4.5*t_w*(402**2))/(max_hp*746*0.8))**(1/3), 2),
        "rpms": list_rpm, "hps": list_hp, "torques": list_torque
    })
    with sound_area: play_engine_sound(0, active=True)

# --- 8. HIGH-END REPORT (Always Show if History Exists) ---
if st.session_state.history:
    st.write("---")
    st.subheader("📊 High-End Comparison Report")
    
    # Drag Table
    st.table([{k: v for k, v in r.items() if k not in ['rpms', 'hps', 'torques']} for r in st.session_state.history])

    # Overlay Graph
    fig_comp = go.Figure()
    colors = ['#ff4b4b', '#00d4ff', '#00ff00', '#ffcc00']
    for i, run in enumerate(st.session_state.history):
        c = colors[i % len(colors)]
        fig_comp.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Label']} HP", line=dict(color=c, width=3)))
        fig_comp.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Label']} Nm", line=dict(color=c, dash='dot'), yaxis="y2"))
    
    fig_comp.update_layout(template="plotly_dark", height=500, yaxis2=dict(overlaying="y", side="right"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_comp, use_container_width=True)

    # Tuner Advisory (Graham Bell Style)
    latest = st.session_state.history[-1]
    st.subheader("🧠 Tuner's Expert Advisory")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**Induction System:**\n\n* Klep In Ideal: {round(latest['CC']*0.2,1)} mm\n* Intake Velocity: Optimal at {latest['Label']}")
    with c2:
        st.warning(f"**Thermal Analysis:**\n\n* BBM: {'Wajib Turbo' if latest['CR'] > 12.2 else 'Pertamax Aman'}\n* SAE Correction Applied: {amb_temp}°C")
