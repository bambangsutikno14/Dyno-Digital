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

# --- 3. SESSION STATE FOR DYNAMIC SYNC ---
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. CORE ENGINE LOGIC ---
def calculate_axis_master(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    adj_peak = std['peak_rpm'] + (((dur_in + dur_out)/2 - 240) * 55)
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
        if venturi > std['venturi']: hp_val *= (1 + (venturi - std['venturi']) * 0.012)
        hps.append(round(hp_val, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
    return rpms, hps, torques, gs_in, gs_out

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]

    # Persistent Session State per Model
    if 'current_bore' not in st.session_state or st.session_state.get('active_model') != model:
        st.session_state.current_bore = float(std['bore'])
        st.session_state.current_cc = (math.pi * (float(std['bore'])**2) * float(std['stroke'])) / 4000
        st.session_state.active_model = model

    st.divider()
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter Dasar & Sync", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        
        def sync_cc_from_bore():
            st.session_state.current_cc = (math.pi * (st.session_state.sb_bore_key**2) * std['stroke']) / 4000
        def sync_bore_from_cc():
            st.session_state.current_bore = math.sqrt((st.session_state.sb_cc_key * 4000) / (math.pi * std['stroke']))

        in_bore = st.number_input(f"Bore (std: {std['bore']})", key="sb_bore_key", 
                                 value=st.session_state.current_bore, step=0.1, on_change=sync_cc_from_bore)
        in_cc = st.number_input(f"CC Motor Real (std: {(math.pi*(std['bore']**2)*std['stroke'])/4000:.1f})", 
                               key="sb_cc_key", value=st.session_state.current_cc, step=0.1, on_change=sync_bore_from_cc)
        
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Perimeter Expert (High-End)", value=True)
    if expert_on:
        with st.expander("🧪 Expert Details (Graham Bell)", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.1)
            in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
            in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
            in_venturi = st.number_input(f"Venturi (std: {float(std['venturi'])})", value=float(std['venturi']), step=0.5)
            in_dur_in = st.slider("Durasi Noken In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Noken Out", 200, 320, 240)
            in_afr = st.slider("Target AFR Injeksi", 11.5, 14.7, 13.0, step=0.1)
            in_fratio = st.number_input(f"Final Ratio (std: {std['f_ratio']})", value=float(std['f_ratio']), step=0.01)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, in_fratio = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0, std['f_ratio']

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60)
    run_btn = st.button("🔥 ANALYZE & RUN AXIS DYNO")

# --- 6. EXECUTION ---
if run_btn:
    # Mengambil nilai final dari sidebar keys
    final_cc = st.session_state.sb_cc_key
    final_bore = st.session_state.sb_bore_key
    cr_calc = (final_cc + in_vhead) / in_vhead
    
    rpms, hps, torques, gsin, gsout = calculate_axis_master(final_cc, final_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    
    max_hp = max(hps)
    pwr = max_hp / (std['weight_std'] + in_joki)
    st.session_state.history.append({
        "Run": f"{label_run} {model.split(' ')[0]}", "CC": round(final_cc, 2), "CR": round(cr_calc, 2),
        "Max_HP": max_hp, "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
        "T201": round(10.2/math.pow(pwr, 0.45), 2), "rpms": rpms, "hps": hps, "torques": torques, 
        "gsin": gsin, "gsout": gsout, "v_in": in_v_in, "v_out": in_v_out, "afr": in_afr, "bore": final_bore
    })

# --- 7. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- RESTORASI PANEL FLOWBENCH ---
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

    # --- TABLES & DYNAMIC GRAPH ---
    st.write("### 📊 Performance & Drag Results")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "T201"]], hide_index=True, use_container_width=True)

    fig = go.Figure()
    clrs = ["#FF0000", "#00FF00", "#0000FF"]
    for i, r in enumerate(st.session_state.history):
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=clrs[i%3], width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], line=dict(color=clrs[i%3], dash='dot'), yaxis="y2", showlegend=False))

    fig.update_layout(template="plotly_dark", height=500, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="RPM", gridcolor="#1a1a1a"), yaxis=dict(title="Power (HP)"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT SOLUTIONS ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    st.info(f"**1. Analisa Performa:** Kapasitas **{latest['CC']}cc** pada Bore {latest['bore']}mm. Gas Speed In: {latest['gsin']:.1f} m/s.")
    
    vhead_ideal = round(latest['CC'] / (12.5 - 1), 2)
    st.warning(f"**2. Rekomendasi:** Target Vol Head ideal untuk CR 12.5:1 adalah **{vhead_ideal} cc**. Rasio Klep Out/In: {(latest['v_out']/latest['v_in'])*100:.1f}%")
    
    st.success(f"**3. Solusi:** Bubut kubah head ke {vhead_ideal} cc. {'Ganti Klep In minimal ' + str(round(latest['bore']*0.52, 1)) + 'mm.' if latest['gsin'] > 105 else 'Konfigurasi mesin sudah harmonis.'}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Simulator berbasis rumus. Hasil nyata bergantung pada kualitas porting dan kondisi lingkungan.")
