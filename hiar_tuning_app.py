import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    th, td { text-align: center !important; vertical-align: middle !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION ---
def calculate_axis_v10(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    
    # Graham Bell Calculation Logic
    adj_peak = std['peak_rpm'] + (((dur_in + dur_out)/2 - 240) * 55)
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    afr_mod = 1.0 - abs(afr - 13.0) * 0.04
    bmep = (std['hp_std'] * 950000) / (cc * adj_peak * eff)
    
    for r in rpms:
        ve = math.exp(-((r - adj_peak) / 4500)**2) if r <= adj_peak else math.exp(-((r - adj_peak) / 1600)**2)
        ps_speed = (2 * stroke * r) / 60000
        gs_in = ((bore / v_in)**2) * ps_speed
        gs_out = ((bore / v_out)**2) * ps_speed
        
        # Choke Flow Factor
        if gs_in > 105: ve *= (105 / gs_in)
        if gs_out > 115: ve *= (115 / gs_out)
        
        hp = (bmep * cc * r * ve * eff * afr_mod) / 950000
        if bore > std['bore']: hp *= (1 + (cr - 9.5) * 0.025)
        if venturi > std['venturi']: hp *= (1 + (venturi - std['venturi']) * 0.012)
        
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques, ps_speed, gs_in, gs_out

# --- 4. SIDEBAR (V10 STYLE) ---
with st.sidebar:
    st.header("1️⃣ PILIH MOTOR")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]

    st.divider()
    st.header("2️⃣ ENGINE CONFIG")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    
    # BORE DAN STROKE INPUT
    in_bore = st.number_input(f"Bore (std: {std['bore']})", value=std['bore'], step=0.1)
    in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=std['stroke'], step=0.1)
    
    # CC ADALAH HASIL KALKULASI SATU ARAH (Paham: User tidak input CC)
    cc_calc = (0.785 * in_bore * in_bore * in_stroke) / 1000
    st.success(f"CC Motor Real: {cc_calc:.2f} cc")
    
    in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=std['v_head'], step=0.1)
    in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    st.header("3️⃣ EXPERT PARAMETER")
    expert_on = st.toggle("Aktifkan Expert (Dyno High-End)", value=True)
    if expert_on:
        with st.expander("🧪 Detail Tuning", expanded=True):
            in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
            in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
            in_venturi = st.number_input(f"Venturi (std: {float(std['venturi'])})", value=float(std['venturi']), step=0.5)
            in_dur_in = st.slider("Durasi In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Out", 200, 320, 240)
            in_afr = st.slider("Target AFR (Injeksi)", 11.5, 14.7, 13.0, step=0.1)
            in_joki = st.number_input("Berat Joki (kg)", value=60)
    else:
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, in_joki = std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0, 60

    run_btn = st.button("🚀 ANALYZE & RUN AXIS DYNO")

# --- 5. MAIN PANEL DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")
st.caption("GassPoll")

if run_btn:
    cr_calc = (cc_calc + in_vhead) / in_vhead
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v10(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, 
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std
    )
    
    # Simulasi Drag T201
    pwr = max(hps) / (std['weight_std'] + in_joki)
    t201_pred = 10.2 / math.pow(pwr, 0.45)
    
    # Save History
    st.session_state.history.append({
        "Run": label_run, "CC": round(cc_calc, 2), "CR": round(cr_calc, 2), "AFR": in_afr,
        "Max_HP": max(hps), "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques),
        "T201": round(t201_pred, 2), "rpms": rpms, "hps": hps, "torques": torques,
        "pspeed": pspeed, "gsin": gsin, "gsout": gsout, "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 6. PANEL FLOWBENCH & PISTON SPEED ---
    st.header("🌪️ Flowbench & Engine Speed Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Flow In (CFM)", f"{round((latest['v_in'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with m2: st.metric("Flow Out (CFM)", f"{round((latest['v_out'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with m3: st.metric("Gas Speed In", f"{latest['gsin']:.1f} m/s")
    with m4: st.metric("Gas Speed Out", f"{latest['gsout']:.1f} m/s")
    with m5: st.metric("Piston Speed", f"{latest['pspeed']:.1f} m/s")

    # --- 7. DATA TABLES ---
    st.write("### 📊 Performance & Drag Results")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "T201"]], hide_index=True, use_container_width=True)

    # --- 8. GRAPH AXIS VX5 STYLE ---
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    for i, r in enumerate(st.session_state.history):
        c = colors[i % 4]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=c, width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], line=dict(color=c, dash='dot'), yaxis="y2", showlegend=False))
        fig.add_annotation(x=r['RPM_HP'], y=r['Max_HP'], text=f"{r['Max_HP']} HP", showarrow=True, arrowhead=2)

    fig.update_layout(template="plotly_dark", height=550, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="Engine Speed (RPM)", gridcolor="#222"), 
                      yaxis=dict(title="Power (HP)", gridcolor="#222"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. EXPERT ANALYSIS ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    
    st.info(f"**Analisa:** Kapasitas {latest['CC']}cc. Gas Speed In {latest['gsin']:.1f} m/s. {'⚠️ Klep In Terlalu Kecil!' if latest['gsin'] > 105 else '✅ Efisiensi Klep Bagus.'}")
    
    vhead_ideal = round(latest['CC'] / (12.5 - 1), 2)
    st.success(f"**Solusi:** Untuk CR 12.5:1, bubut Vol Head ke **{vhead_ideal} cc**. {'Ganti Klep In minimal ' + str(round(latest['bore']*0.52, 1)) + ' mm.' if latest['gsin'] > 105 else 'Settingan sudah harmonis.'}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Simulator berbasis kalkulasi rumus. Hasil bisa berbeda sesuai pengerjaan mekanik.")
