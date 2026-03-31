import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    th, td { text-align: center !important; vertical-align: middle !important; }
    div[data-testid="stDataFrame"] { display: flex; justify-content: center; }
    .main { background-color: #050505; }
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

# --- 3. SESSION STATE FOR SYNC ---
if 'history' not in st.session_state: st.session_state.history = []
if 'bore' not in st.session_state: st.session_state.bore = 50.0
if 'cc' not in st.session_state: st.session_state.cc = 113.7

# --- 4. CORE LOGIC (HP, CFM, & DURATION) ---
def calculate_ultimate(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    avg_dur = (dur_in + dur_out) / 2
    peak_shift = (avg_dur - 240) * 55 
    adjusted_peak = std['peak_rpm'] + peak_shift
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    afr_mod = 1.0 - abs(afr - 13.0) * 0.035
    bmep_lock = (std['hp_std'] * 950000) / (cc * adjusted_peak * eff)
    
    for r in rpms:
        ve = math.exp(-((r - adjusted_peak) / 4500)**2) if r <= adjusted_peak else math.exp(-((r - adjusted_peak) / 1600)**2)
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
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]

    if st.button("Reset ke Standar"):
        st.session_state.bore = std['bore']
        st.session_state.cc = (math.pi * (std['bore']**2) * std['stroke']) / 4000

    st.divider()
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Auto-Sync Bore & CC)", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        
        # Callback Functions
        def on_bore_change():
            st.session_state.cc = (math.pi * (st.session_state.bore_input**2) * std['stroke']) / 4000
        def on_cc_change():
            st.session_state.bore = math.sqrt((st.session_state.cc_input * 4000) / (math.pi * std['stroke']))

        st.number_input("Bore (mm)", step=0.1, key="bore_input", value=st.session_state.bore, on_change=on_bore_change)
        st.number_input("CC Motor Real", step=0.1, key="cc_input", value=st.session_state.cc, on_change=on_cc_change)
        
        in_vhead = st.number_input(f"Vol Head (cc)", value=std['v_head'], step=0.1)
        in_rpm = st.number_input(f"Limit RPM", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Perimeter Expert", value=True)
    if expert_on:
        with st.expander("🧪 Expert Details", expanded=True):
            in_stroke = st.number_input("Stroke", value=std['stroke'], step=0.1)
            in_valve_in = st.number_input("Klep In", value=std['valve_in'], step=0.1)
            in_valve_out = st.number_input("Klep Out", value=std['valve_out'], step=0.1)
            in_dur_in = st.slider("Durasi In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Out", 200, 320, 240)
            in_afr = st.slider("Target AFR", 11.5, 14.7, 13.0, step=0.1)
            in_fratio = st.number_input("Final Ratio", value=std['f_ratio'], step=0.01)
    else:
        in_stroke, in_valve_in, in_valve_out, in_dur_in, in_dur_out, in_afr, in_fratio = std['stroke'], std['valve_in'], std['valve_out'], 240, 240, 13.0, std['f_ratio']

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60)

    if st.button("🔥 ANALYZE & RUN"):
        cc_f = (math.pi * (st.session_state.bore_input**2) * in_stroke) / 4000
        cr_f = (cc_f + in_vhead) / in_vhead
        rpms, hps, torques, gsin, gsout = calculate_ultimate(cc_f, st.session_state.bore_input, in_stroke, cr_f, in_rpm, in_valve_in, in_valve_out, std['venturi'], in_dur_in, in_dur_out, in_afr, std)
        
        # Simpan ke history
        max_hp = max(hps)
        pwr = max_hp / (std['weight_std'] + in_joki)
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", "CC": round(cc_f, 2), "CR": round(cr_f, 2),
            "Max_HP": max_hp, "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
            "Joki": in_joki, "T100": round(6.5/math.pow(pwr, 0.45), 2), "T201": round(10.2/math.pow(pwr, 0.45), 2),
            "rpms": rpms, "hps": hps, "torques": torques, "gsin": gsin, "gsout": gsout, "afr": in_afr,
            "valve_in": in_valve_in, "valve_out": in_valve_out, "bore": st.session_state.bore_input
        })

    with st.expander("🌪️ CFM Flow Bench Calc", expanded=False):
        cfm_in = round((in_valve_in / 25.4)**2 * math.sqrt(28) * 128, 1)
        cfm_out = round((in_valve_out / 25.4)**2 * math.sqrt(28) * 128, 1)
        st.metric("Flow In", f"{cfm_in} CFM")
        st.metric("Flow Out", f"{cfm_out} CFM")

# --- 6. MAIN DISPLAY (AXIS STYLE) ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- PERFORMANCE TABLES ---
    st.write("### 📊 Engine & Drag Data")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)
    st.dataframe(df[["Run", "Joki", "T100", "T201", "afr"]], hide_index=True, use_container_width=True)

    # --- GRAPH AXIS VX5 ---
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF"]
    for i, run in enumerate(st.session_state.history):
        clr = colors[i % 3]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)", line=dict(color=clr, width=4)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], line=dict(color=clr, dash='dot'), yaxis="y2", showlegend=False))
        fig.add_annotation(x=run['RPM_HP'], y=run['Max_HP'], text=f"{run['Max_HP']} HP", showarrow=True)

    fig.update_layout(template="plotly_dark", height=550, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="RPM", gridcolor="#1a1a1a"), yaxis=dict(title="HP", gridcolor="#1a1a1a"),
                      yaxis2=dict(overlaying="y", side="right", title="Nm"))
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ANALYSIS (3 BARIS DINAMIS) ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    
    # 1. Analisa
    st.write("**1. Analisa Performa Mesin:**")
    analisa = f"Kapasitas {latest['CC']}cc pada AFR {latest['afr']}. Gas Speed In: {latest['gsin']:.1f} m/s, Out: {latest['gsout']:.1f} m/s. "
    if latest['gsin'] > 105: analisa += "Mesin mengalami hambatan aliran udara masuk (choke) yang signifikan di RPM atas."
    st.info(analisa)

    # 2. Rekomendasi
    st.write("**2. Rekomendasi Expert:**")
    # Hitung v_head ideal untuk CR 12.5:1
    vhead_ideal = round(latest['CC'] / (12.5 - 1), 2)
    rekomendasi = f"Untuk kapasitas {latest['CC']}cc, volume head ideal untuk mengejar kompresi 12.5:1 adalah **{vhead_ideal} cc**. "
    if latest['CR'] > 13.5: rekomendasi += "Kompresi saat ini terlalu padat, risiko knocking sangat tinggi."
    st.warning(rekomendasi)

    # 3. Solusi
    st.write("**3. Solusi Setingan & Part:**")
    if latest['CR'] != 12.5:
        solusi = f"Sesuaikan Vol Head ke {vhead_ideal} cc dengan cara bubut kubah atau ubah mendem piston. "
    else: solusi = "Kompresi sudah ideal. "
    
    if latest['gsin'] > 105:
        solusi += f"Ganti klep In ke ukuran minimal {round(latest['bore']*0.52, 1)} mm untuk melayani CC besar."
    else:
        solusi += "Fokus pada optimalisasi kurva pengapian lewat ECU Juken/Aracer."
    st.success(solusi)
