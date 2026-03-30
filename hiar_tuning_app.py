import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. DATABASE PABRIKAN ---
DATABASE_MATIC = {
    "YAMAHA": {
        "NMAX 155 / Aerox": {
            "bore_std": 58.0, "stroke_std": 58.7, "v_head_std": 14.6, 
            "vva": True, "weight": 127, "valve_in": 20.5, "venturi_std": 28,
            "cam_dur_std": 230, "gear_ratio_final": 10.2
        },
        "Mio Karbu / Soul 115": {
            "bore_std": 50.0, "stroke_std": 57.9, "v_head_std": 13.7, 
            "vva": False, "weight": 94, "valve_in": 23.0, "venturi_std": 24,
            "cam_dur_std": 215, "gear_ratio_final": 10.5
        },
    },
    "HONDA": {
        "Vario 150 / PCX 150": {
            "bore_std": 57.3, "stroke_std": 57.9, "v_head_std": 15.6, 
            "vva": False, "weight": 112, "valve_in": 29.0, "venturi_std": 26,
            "cam_dur_std": 220, "gear_ratio_final": 9.8
        },
        "BeAT FI / Scoopy": {
            "bore_std": 50.0, "stroke_std": 55.1, "v_head_std": 12.7, 
            "vva": False, "weight": 90, "valve_in": 22.0, "venturi_std": 22,
            "cam_dur_std": 210, "gear_ratio_final": 10.8
        },
    }
}

# --- 4. ENGINE LOGIC (REVISED FOR DROP-OFF) ---
def calculate_performance(cc, rpm_limit, vva, venturi, cam_dur, motor_name):
    rpms = np.arange(3000, rpm_limit + 250, 250)
    hp_list = []
    torque_list = []
    
    # Titik puncak teoritis (Mio di 8000, Nmax di 8500)
    peak_rpm = 8500 if "NMAX" in motor_name else 8000
    
    for r in rpms:
        # Volumetric Efficiency Curve (Parabolic)
        # Menghasilkan puncak di peak_rpm, lalu turun tajam setelahnya
        deviation = (r - peak_rpm) / 3500
        ve = math.exp(-(deviation**2)) 
        
        if vva and r > 6500: ve *= 1.05 # Booster VVA
        
        # BMEP Adjustment agar Mio standar ~6.5 HP
        # Base BMEP untuk matic standar sekitar 8.5 - 9.0 Bar
        base_bmep = 11.2 * (cam_dur / 225) * (venturi / 25)
        
        hp = (base_bmep * cc * r * ve) / 950000 
        trq = (hp * 7127) / r if r > 0 else 0
        
        hp_list.append(round(hp, 2))
        torque_list.append(round(trq, 2))
        
    return rpms, hp_list, torque_list

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏁 FACTORY BASELINE")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    std = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    bore = st.number_input(f"Bore ({std['bore_std']} std)", value=std['bore_std'], step=0.1)
    v_head = st.number_input(f"Vol Head ({std['v_head_std']} std)", value=std['v_head_std'], step=0.1)
    rpm_target = st.slider(f"Limit RPM", 5000, 15000, 9500 if "NMAX" in motor else 9000)
    
    with st.expander("🛠️ Advanced Setup"):
        cam_dur = st.number_input(f"Durasi Cam ({std['cam_dur_std']} std)", value=float(std['cam_dur_std']))
        venturi = st.number_input(f"Venturi ({std['venturi_std']} std)", value=float(std['venturi_std']))
        valve_in = st.number_input(f"Klep In ({std['valve_in']} std)", value=float(std['valve_in']))

    if st.button("🚀 ANALYZE ENGINE"):
        cc = (math.pi * (bore**2) * std['stroke_std']) / 4000
        cr = (cc + v_head) / v_head
        piston_speed = (2 * std['stroke_std'] * rpm_target) / 60000 
        
        rpms, hps, torques = calculate_performance(cc, rpm_target, std['vva'], venturi, cam_dur, motor)
        
        idx_hp = np.argmax(hps)
        idx_trq = np.argmax(torques)
        
        # Labeling Otomatis: Run X (Nama Motor)
        run_name = f"Run {len(st.session_state.history) + 1} ({motor.split(' ')[0]})"
        
        st.session_state.history.append({
            "Run": run_name, "Motor": motor, "CC": cc, "CR": cr, "Piston_Speed": piston_speed,
            "Max_HP": hps[idx_hp], "at_RPM_HP": rpms[idx_hp],
            "Max_Nm": torques[idx_trq], "at_RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "hps": hps, "torques": torques
        })

# --- 6. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    # --- SAFETY ANALYSIS ---
    latest = st.session_state.history[-1]
    st.subheader(f"🛡️ Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        ps = latest['Piston_Speed']
        if ps <= 18: st.info(f"🔵 **Piston Speed: {ps:.2f} m/s**\n\nSafe (Biru)")
        elif ps <= 21: st.success(f"🟢 **Piston Speed: {ps:.2f} m/s**\n\nOptimal (Hijau)")
        else: st.error(f"🔴 **Piston Speed: {ps:.2f} m/s**\n\nRisky (Merah)")

    with c2:
        cr = latest['CR']
        if cr <= 11.5: st.info(f"🔵 **Static CR: {cr:.1f}:1**\n\nSafe (Biru)")
        elif cr <= 13.0: st.success(f"🟢 **Static CR: {cr:.1f}:1**\n\nOptimal (Hijau)")
        else: st.error(f"🔴 **Static CR: {cr:.1f}:1**\n\nRisky (Merah)")
        
    with c3:
        # Menampilkan Torsi dan HP Maksimum di Summary
        st.metric("Peak Power", f"{latest['Max_HP']} HP", f"@{latest['at_RPM_HP']} RPM")

    # --- TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df[["Run", "CC", "CR", "Max_HP", "at_RPM_HP", "Max_Nm", "at_RPM_Nm"]],
        column_config={
            "CC": st.column_config.NumberColumn("cc", format="%.2f"),
            "CR": st.column_config.NumberColumn("CR", format="%.2f"),
            "Max_HP": st.column_config.NumberColumn("HP", format="%.2f"),
            "Max_Nm": st.column_config.NumberColumn("Nm", format="%.2f"),
        },
        hide_index=True, use_container_width=True
    )

    # --- GRAPH (Dynamic Labeling) ---
    fig = go.Figure()
    for run in st.session_state.history:
        # Garis HP
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)", line=dict(width=3)))
        # Garis Torsi
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(
        template="plotly_dark", height=500,
        xaxis_title="RPM", yaxis_title="Horsepower",
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)
