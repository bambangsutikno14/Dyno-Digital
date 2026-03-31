import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
    }
}

# --- 3. SESSION STATE (FIXED SYNC) ---
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. CORE ENGINE LOGIC ---
def calculate_axis_v14(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    adj_peak = std['peak_rpm'] + (( (dur_in + dur_out)/2 - 240) * 55)
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    afr_mod = 1.0 - abs(afr - 13.0) * 0.035
    bmep_lock = (std['hp_std'] * 950000) / (cc * adj_peak * eff)
    
    for r in rpms:
        ve = math.exp(-((r - adj_peak) / 4500)**2) if r <= adj_peak else math.exp(-((r - adj_peak) / 1600)**2)
        ps_speed = (2 * stroke * r) / 60000
        gs_in = ((bore / valve_in)**2) * ps_speed
        gs_out = ((bore / valve_out)**2) * ps_speed
        if gs_in > 105: ve *= (105 / gs_in)
        if gs_out > 115: ve *= (115 / gs_out)
        hp_val = (bmep_lock * cc * r * ve * eff * afr_mod) / 950000
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.022)
        hps.append(round(hp_val, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
    return rpms, hps, torques, gs_in, gs_out

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]

    # Initialize current values for the specific model
    if 'current_bore' not in st.session_state or st.session_state.get('last_model') != model_name:
        st.session_state.current_bore = std['bore']
        st.session_state.current_cc = (math.pi * (std['bore']**2) * std['stroke']) / 4000
        st.session_state.last_model = model_name

    st.divider()
    st.header("2️⃣ ENGINE SIMULATION")
    
    with st.expander("🛠️ Perimeter 1 (Auto-Sync)", expanded=True):
        def on_bore_change():
            st.session_state.current_cc = (math.pi * (st.session_state.sb_bore**2) * std['stroke']) / 4000
        def on_cc_change():
            st.session_state.current_bore = math.sqrt((st.session_state.sb_cc * 4000) / (math.pi * std['stroke']))

        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        
        in_bore = st.number_input(f"Bore (std: {std['bore']})", key="sb_bore", 
                                 value=st.session_state.current_bore, step=0.1, on_change=on_bore_change)
        in_cc = st.number_input(f"CC Real (std: {(math.pi*(std['bore']**2)*std['stroke'])/4000:.1f})", 
                               key="sb_cc", value=st.session_state.current_cc, step=0.1, on_change=on_cc_change)
        
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=std['v_head'], step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Perimeter Expert", value=True)
    if expert_on:
        with st.expander("🧪 Expert Details (Graham Bell)", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=std['stroke'], step=0.1)
            in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=std['valve_in'], step=0.1)
            in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=std['valve_out'], step=0.1)
            in_venturi = st.number_input(f"Venturi (std: {std['venturi']})", value=std['venturi'], step=1.0)
            in_dur_in = st.slider("Durasi In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Out", 200, 320, 240)
            in_afr = st.slider("Target AFR", 11.5, 14.7, 13.0, step=0.1)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60)
    
    run_btn = st.button("🔥 ANALYZE & RUN AXIS DYNO")

# --- 6. MAIN PANEL FLOWBENCH ANALYSIS ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    # Use the session state values to ensure the calc matches the visual inputs
    cc_final = st.session_state.sb_cc
    bore_final = st.session_state.sb_bore
    cr_final = (cc_final + in_vhead) / in_vhead
    
    rpms, hps, torques, gsin, gsout = calculate_axis_v14(cc_final, bore_final, in_stroke, cr_final, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    
    # Save to History
    max_hp = max(hps)
    pwr = max_hp / (std['weight_std'] + in_joki)
    st.session_state.history.append({
        "Run": f"{label_run} {model_name.split(' ')[0]}", "CC": round(cc_final, 2), "CR": round(cr_final, 2),
        "Max_HP": max_hp, "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
        "T201": round(10.2/math.pow(pwr, 0.45), 2), "rpms": rpms, "hps": hps, "torques": torques, 
        "gsin": gsin, "gsout": gsout, "v_in": in_v_in, "v_out": in_v_out, "afr": in_afr, "bore": bore_final
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 7. AXIS HIGH-END FLOWBENCH PANEL ---
    st.header("🌪️ Axis Expert Flowbench Analysis")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Flow In (CFM)", f"{round((latest['v_in'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with col2:
        st.metric("Flow Out (CFM)", f"{round((latest['v_out'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with col3:
        st.metric("Mean Gas Speed In", f"{latest['gsin']:.1f} m/s")
    with col4:
        st.metric("Mean Gas Speed Out", f"{latest['gsout']:.1f} m/s")

    # --- 8. GRAPH & RESULTS ---
    st.write("---")
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF"]
    for i, run in enumerate(st.session_state.history):
        clr = colors[i % 3]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)", line=dict(color=clr, width=4)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], line=dict(color=clr, dash='dot'), yaxis="y2", showlegend=False))

    fig.update_layout(template="plotly_dark", height=500, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="RPM", gridcolor="#1a1a1a"), yaxis=dict(title="Power (HP)"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"))
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. DYNAMIC EXPERT SOLUTIONS ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    st.info(f"**1. Analisa Performa:** Kapasitas {latest['CC']}cc pada AFR {latest['afr']}. Gas Speed In: {latest['gsin']:.1f} m/s. {'⚠️ Choke Flow Terdeteksi!' if latest['gsin'] > 105 else '✅ Aliran udara harmonis.'}")
    
    vhead_ideal = round(latest['CC'] / (12.5 - 1), 2)
    st.warning(f"**2. Rekomendasi:** Untuk {latest['CC']}cc, Vol Head ideal CR 12.5:1 adalah **{vhead_ideal} cc**. Rasio Klep Out/In: { (latest['v_out']/latest['v_in'])*100 :.1f}%")
    
    st.success(f"**3. Solusi:** Bubut kubah head ke {vhead_ideal} cc. {'Ganti Klep In minimal ' + str(round(latest['bore']*0.52, 1)) + 'mm.' if latest['gsin'] > 105 else 'Optimalkan timing pengapian.'}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Aplikasi ini adalah simulator berbasis rumus. Hasil nyata bergantung pada kualitas pengerjaan dan kondisi lingkungan.")
