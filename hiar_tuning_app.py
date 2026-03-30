import streamlit as st
import numpy as np
import math
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. ADVANCED SOUND ENGINE (NSR Style) ---
def play_engine_sound(rpm, active=False):
    if not active: return ""
    # Logika frekuensi: Semakin tinggi RPM, semakin melengking
    freq = 40 + (rpm / 15)
    # Gain (Volume) sedikit bergetar untuk simulasi kompresi
    js_code = f"""
    <script>
    if (!window.audioCtx) {{
        window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        window.osc = window.audioCtx.createOscillator();
        window.gain = window.audioCtx.createGain();
        window.filter = window.audioCtx.createBiquadFilter();
        
        window.osc.type = 'sawtooth'; 
        window.filter.type = 'lowpass';
        
        window.osc.connect(window.filter);
        window.filter.connect(window.gain);
        window.gain.connect(window.audioCtx.destination);
        window.osc.start();
    }}
    // Update Frekuensi & Filter secara smooth (tanpa klik-klik)
    window.osc.frequency.setTargetAtTime({freq}, window.audioCtx.currentTime, 0.1);
    window.filter.frequency.setTargetAtTime({freq * 2}, window.audioCtx.currentTime, 0.1);
    
    if ({rpm} > 500) {{
        window.gain.gain.setTargetAtTime(0.2, window.audioCtx.currentTime, 0.1);
    }} else {{
        window.gain.gain.setTargetAtTime(0, window.audioCtx.currentTime, 0.2);
    }}
    </script>
    """
    return components.html(js_code, height=0)

# --- 3. DATABASE ---
DATABASE_MATIC = {
    "YAMAHA": {"NMAX 155": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "vva": True, "weight": 127}},
    "HONDA": {"Vario 150": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "vva": False, "weight": 112}}
}

# --- 4. GAUI LOGIC (NSR SP ANALOG STYLE) ---
def create_analog_gauge(value, title, max_val, steps):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title, 'font': {'size': 20, 'family': 'Orbitron'}},
        gauge = {
            'axis': {'range': [0, max_val], 'tickwidth': 2, 'tickcolor': "white", 
                     'tickmode': 'array', 'tickvals': list(range(0, max_val+1, steps))},
            'bar': {'color': "red" if value > max_val*0.85 else "white"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 4,
            'bordercolor': "#333",
            'steps': [
                {'range': [0, max_val*0.8], 'color': "rgba(255,255,255,0.1)"},
                {'range': [max_val*0.8, max_val], 'color': "rgba(255,0,0,0.3)"}
            ],
            'threshold': {
                'line': {'color': "yellow", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=350, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="black", font={'color': "white"})
    return fig

# --- 5. SIDEBAR & LOGIC ---
if 'history' not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.title("🏁 NSR SP COCKPIT")
    merk = st.selectbox("Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data = DATABASE_MATIC[merk][motor]
    
    bore_in = st.number_input("Bore (mm)", value=data['bore'], step=0.1)
    v_head_in = st.number_input("Vol Head (cc)", value=data['v_head'], step=0.1)
    rpm_limit = st.slider("Limit RPM", 5000, 15000, 10500)
    
    btn_run = st.button("🚀 PULL THE THROTTLE")

# --- 6. MAIN DISPLAY ---
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>DIGITAL INSTRUMENT</h1>", unsafe_allow_html=True)

if btn_run:
    cc = (math.pi * (bore_in**2) * data['stroke']) / 4000
    
    # Placeholders
    col_g1, col_g2 = st.columns(2)
    rpm_placeholder = col_g1.empty()
    spd_placeholder = col_g2.empty()
    chart_placeholder = st.empty()
    sound_placeholder = st.empty()

    list_rpm, list_hp = [], []

    # --- SIMULATION LOOP ---
    for r in range(0, rpm_limit + 250, 250):
        # Hitung Performa
        ve = 0.90 if data['vva'] and r > 6000 else 0.84
        hp = (10.2 * cc * r * ve * math.cos(math.radians((r-(rpm_limit*0.75))/(rpm_limit*0.5)*35))) / 900000
        speed = (r * 0.018) # Penyesuaian agar top speed ~200kmh di 11rb rpm
        
        list_rpm.append(r)
        list_hp.append(round(hp, 2))

        # Audio Update
        with sound_placeholder: play_engine_sound(r, active=True)

        # Gauge Update (NSR Style)
        rpm_placeholder.plotly_chart(create_analog_gauge(r, "RPM x1000", 15000, 1000), use_container_width=True)
        spd_placeholder.plotly_chart(create_analog_gauge(speed, "SPEED KM/H", 200, 20), use_container_width=True)

        # Live Graph Drawing
        fig_live = go.Figure(go.Scatter(x=list_rpm, y=list_hp, name="Power", line=dict(color='red', width=4)))
        fig_live.update_layout(template="plotly_dark", height=400, xaxis=dict(title="RPM", range=[0, 16000]), yaxis=dict(title="HP"))
        chart_placeholder.plotly_chart(fig_live, use_container_width=True)
        
        time.sleep(0.02)

    # Matikan Suara & Tampilkan Report
    with sound_placeholder: play_engine_sound(0, active=True)
    st.success("🏁 RUN FINISHED! Check the Expert Advisory below.")
    
    # Simpan History
    st.session_state.history.append({"Bore": bore_in, "CC": round(cc,1), "HP": max(list_hp), "RPM": r})

# --- 7. HISTORY & COMPARISON ---
if st.session_state.history:
    st.write("---")
    st.subheader("📊 Comparison Table (High-End Dyno)")
    st.table(st.session_state.history)
