import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE & UI ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# CSS Custom untuk tampilan gelap premium
st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    th, td { text-align: center !important; vertical-align: middle !important; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; border-radius: 8px; height: 3em; }
    .stExpander { border: 1px solid #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
        "Jupiter MX 135": {"bore": 54.0, "stroke": 58.7, "v_head": 12.2, "valve_in": 19.0, "valve_out": 17.0, "venturi": 22.0, "hp_std": 12.50, "peak_rpm": 8500, "limit_std": 10000, "weight_std": 109, "f_ratio": 2.85},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
        "Sonic 150 / CB150R": {"bore": 57.3, "stroke": 57.8, "v_head": 14.0, "valve_in": 22.0, "valve_out": 19.0, "venturi": 28.0, "hp_std": 16.00, "peak_rpm": 9000, "limit_std": 10500, "weight_std": 114, "f_ratio": 2.80},
    }
}

# --- 3. SESSION STATE FOR DYNAMIC SYNC ---
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. CORE ENGINE LOGIC (GRAHAM BELL TUNING) ---
def calculate_axis_master(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    
    # Logic Pergeseran Peak Power berdasarkan durasi noken
    avg_dur = (dur_in + dur_out) / 2
    peak_shift = (avg_dur - 240) * 55 
    adjusted_peak = std['peak_rpm'] + peak_shift
    
    # Efisiensi Termis & AFR
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    afr_mod = 1.0 - abs(afr - 13.0) * 0.035
    bmep_lock = (std['hp_std'] * 950000) / (cc * adjusted_peak * eff)
    
    for r in rpms:
        # Volumetric Efficiency Curve
        ve = math.exp(-((r - adjusted_peak) / 4500)**2) if r <= adjusted_peak else math.exp(-((r - adjusted_peak) / 1600)**2)
        
        # Gas Speed Calculation
        ps_speed = (2 * stroke * r) / 60000
        gs_in = ((bore / valve_in)**2) * ps_speed
        gs_out = ((bore / valve_out)**2) * ps_speed
        
        # Choke Flow Limitation
        if gs_in > 105: ve *= (105 / gs_in)
        if gs_out > 115: ve *= (115 / gs_out)
        
        # Final HP Calculation
        hp_val = (bmep_lock * cc * r * ve * eff * afr_mod) / 950000
        
        # Bonus Kapasitas & Kompresi
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.022)
        if venturi > std['venturi']: hp_val *= (1 + (venturi - std['venturi']) * 0.012)
            
        hps.append(round(hp_val, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques, gs_in, gs_out

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Pilih Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Pilih Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]

    # Initialize State Khusus untuk Model yang Sedang Dipilih
    if 'cur_bore' not in st.session_state or st.session_state.get('last_model') != model_name:
        st.session_state.cur_bore = float(std['bore'])
        st.session_state.cur_cc = (math.pi * (float(std['bore'])**2) * float(std['stroke'])) / 4000
        st.session_state.last_model = model_name

    st.divider()
    st.header("2️⃣ ENGINE SIMULATION")
    
    # Callback untuk Sinkronisasi Bore -> CC
    def update_cc():
        st.session_state.cur_cc = (math.pi * (st.session_state.sb_bore**2) * std['stroke']) / 4000
    
    # Callback untuk Sinkronisasi CC -> Bore
    def update_bore():
        st.session_state.cur_bore = math.sqrt((st.session_state.sb_cc * 4000) / (math.pi * std['stroke']))

    with st.expander("🛠️ Perimeter 1 (Auto-Sync Bore & CC)", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        
        in_bore = st.number_input(f"Bore (std: {std['bore']})", key="sb_bore", 
                                 value=st.session_state.cur_bore, step=0.1, on_change=update_cc)
        
        in_cc = st.number_input(f"CC Motor Real (std: {(math.pi*(std['bore']**2)*std['stroke'])/4000:.1f})", 
                               key="sb_cc", value=st.session_state.cur_cc, step=0.1, on_change=update_bore)
        
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Perimeter Expert (High-End)", value=True)
    if expert_on:
        with st.expander("🧪 Expert Details (Graham Bell Tuning)", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.1)
            in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
            in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
            in_venturi = st.number_input(f"Venturi/TB (std: {float(std['venturi'])})", value=float(std['venturi']), step=0.5)
            in_dur_in = st.slider("Durasi Noken In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Noken Out", 200, 320, 240)
            in_afr = st.slider("Target AFR Injeksi", 11.5, 14.7, 13.0, step=0.1)
            in_fratio = st.number_input(f"Final Ratio (std: {std['f_ratio']})", value=float(std['f_ratio']), step=0.01)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, in_fratio = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0, std['f_ratio']

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60)
    
    run_btn = st.button("🚀 ANALYZE & RUN AXIS DYNO")

# --- 6. CORE EXECUTION ---
if run_btn:
    # Mengambil nilai final dari session state agar sinkron dengan sidebar
    final_cc = st.session_state.sb_cc
    final_bore = st.session_state.sb_bore
    final_cr = (final_cc + in_vhead) / in_vhead
    
    rpms, hps, torques, gsin, gsout = calculate_axis_master(final_cc, final_bore, in_stroke, final_cr, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    
    # Save History
    max_hp = max(hps)
    total_w = std['weight_std'] + in_joki
    pwr = max_hp / total_w
    
    st.session_state.history.append({
        "Run": f"{label_run} {model_name.split(' ')[0]}", 
        "CC": round(final_cc, 2), 
        "CR": round(final_cr, 2),
        "Max_HP": max_hp, 
        "RPM_HP": rpms[np.argmax(hps)], 
        "Max_Nm": max(torques), 
        "RPM_Nm": rpms[np.argmax(torques)],
        "T201": round(10.2/math.pow(pwr, 0.45), 2), 
        "rpms": rpms, "hps": hps, "torques": torques, 
        "gsin": gsin, "gsout": gsout, "v_in": in_v_in, "v_out": in_v_out, 
        "afr": in_afr, "bore": final_bore, "venturi": in_venturi
    })

# --- 7. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 7.1 FLOWBENCH PANEL (4 METRIC UTAMA) ---
    st.header("🌪️ Axis Expert Flowbench Analysis")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Flow In (CFM)", f"{round((latest['v_in'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with c2:
        st.metric("Flow Out (CFM)", f"{round((latest['v_out'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with c3:
        st.metric("Mean Gas Speed In", f"{latest['gsin']:.1f} m/s")
    with c4:
        st.metric("Mean Gas Speed Out", f"{latest['gsout']:.1f} m/s")

    # --- 7.2 RESULTS TABLES ---
    st.write("### 📊 Performance & Drag Results")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "T201"]], hide_index=True, use_container_width=True)

    # --- 7.3 GRAPH DYNO AXIS VX5 ---
    fig = go.Figure()
    clrs = ["#FF0000", "#00FF00", "#0000FF"]
    for i, r in enumerate(st.session_state.history):
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=clrs[i%3], width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], line=dict(color=clrs[i%3], dash='dot'), yaxis="y2", showlegend=False))

    fig.update_layout(template="plotly_dark", height=550, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="RPM", gridcolor="#1a1a1a"), 
                      yaxis=dict(title="Power (HP)", gridcolor="#1a1a1a"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

    # --- 7.4 EXPERT SOLUTIONS ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    st.info(f"**1. Analisa Performa:** Kapasitas **{latest['CC']}cc** pada Bore {latest['bore']}mm. AFR Target: {latest['afr']}. Gas Speed In: {latest['gsin']:.1f} m/s.")
    
    vhead_ideal = round(latest['CC'] / (12.5 - 1), 2)
    st.warning(f"**2. Rekomendasi:** Target Vol Head ideal untuk CR 12.5:1 adalah **{vhead_ideal} cc**. Rasio Klep Out/In: {(latest['v_out']/latest['v_in'])*100:.1f}%")
    
    st.success(f"**3. Solusi Tuning:** Bubut kubah head ke {vhead_ideal} cc. {'Ganti Klep In minimal ' + str(round(latest['bore']*0.52, 1)) + 'mm.' if latest['gsin'] > 105 else 'Konfigurasi aliran udara sudah efisien.'}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Simulator berbasis rumus. Hasil nyata dapat berbeda tergantung kualitas pengerjaan porting dan kondisi lingkungan.")
