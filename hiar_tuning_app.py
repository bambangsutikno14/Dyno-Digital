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

# --- 4. ENGINE LOGIC ---
def calculate_performance(cc, cr, rpm_limit, vva, venturi, cam_dur):
    rpms = np.arange(3000, rpm_limit + 500, 250)
    hp_list = []
    torque_list = []
    
    # Faktor efisiensi berdasarkan durasi noken as dan venturi
    vol_eff_base = (cam_dur / 260) * (venturi / 28) 
    
    for r in rpms:
        ve_mod = 0.92 if vva and r > 6500 else 0.85
        ve_curve = ve_mod * math.cos(math.radians((r - (rpm_limit*0.8)) / (rpm_limit*0.45) * 45))
        bmep = 7.8 * vol_eff_base 
        hp = (bmep * cc * r * ve_curve) / 900000
        hp_list.append(round(hp, 2))
        torque_list.append(round((hp * 7127) / r, 2) if r > 0 else 0)
        
    return rpms, hp_list, torque_list

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏁 FACTORY BASELINE")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    std = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history) + 1}")
    
    bore = st.number_input(f"Bore ({std['bore_std']} std)", value=std['bore_std'], step=0.1)
    v_head = st.number_input(f"Vol Head ({std['v_head_std']} std)", value=std['v_head_std'], step=0.1)
    rpm_target = st.slider(f"Limit RPM (std: {9000 if 'NMAX' in motor else 8500})", 5000, 15000, 9000 if "NMAX" in motor else 8500)
    
    with st.expander("🛠️ Advanced (Noken, Klep, Karbu)"):
        cam_dur = st.number_input(f"Durasi Cam ({std['cam_dur_std']} std)", value=float(std['cam_dur_std']))
        venturi = st.number_input(f"Venturi Karbu/TB ({std['venturi_std']} std)", value=float(std['venturi_std']))
        valve_in = st.number_input(f"Klep In ({std['valve_in']} std)", value=float(std['valve_in']))

    if st.button("🚀 ANALYZE ENGINE"):
        cc = (math.pi * (bore**2) * std['stroke_std']) / 4000
        cr = (cc + v_head) / v_head
        piston_speed = (2 * std['stroke_std'] * rpm_target) / 60000 # m/s
        
        rpms, hps, torques = calculate_performance(cc, cr, rpm_target, std['vva'], venturi, cam_dur)
        
        idx_hp = np.argmax(hps)
        idx_trq = np.argmax(torques)
        
        st.session_state.history.append({
            "Run": label_run, "CC": cc, "CR": cr, "Piston_Speed": piston_speed,
            "Max_HP": hps[idx_hp], "at_RPM_HP": rpms[idx_hp],
            "Max_Nm": torques[idx_trq], "at_RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "hps": hps, "torques": torques
        })

# --- 6. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa: Engine Analyzer")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 7. EXPERT SAFETY ZONE (Graham Bell Reference) ---
    st.subheader("🛡️ Safety & Reliability Analysis")
    col1, col2, col3 = st.columns(3)
    
    # 1. Piston Speed Analysis
    with col1:
        ps = latest['Piston_Speed']
        if ps <= 18:
            st.info(f"🔵 **Piston Speed: {ps:.2f} m/s**\n\n**Safe (Biru):** Aman untuk pemakaian jangka panjang harian.")
        elif ps <= 21:
            st.success(f"🟢 **Piston Speed: {ps:.2f} m/s**\n\n**Optimal (Hijau):** Performa tinggi. Cek pelumasan & kualitas oli.")
        else:
            st.error(f"🔴 **Piston Speed: {ps:.2f} m/s**\n\n**Risky (Merah):** Melebihi batas material standar (21m/s). Resiko patah stang seher!")

    # 2. Compression Ratio Analysis
    with col2:
        cr = latest['CR']
        if cr <= 11.5:
            st.info(f"🔵 **Static CR: {cr:.1f}:1**\n\n**Safe:** Bisa Pertamax (92). Suhu mesin stabil.")
        elif cr <= 13.0:
            st.success(f"🟢 **Static CR: {cr:.1f}:1**\n\n**Optimal:** Wajib Pertamax Turbo (98). Butuh pendinginan extra.")
        else:
            st.error(f"🔴 **Static CR: {cr:.1f}:1**\n\n**Risky:** Resiko detonasi/ngelitik parah. Wajib bahan bakar balap (Avgas/VP).")

    # 3. Flow Efficiency (Klep vs Bore)
    with col3:
        flow_ratio = valve_in / bore
        if flow_ratio >= 0.45:
            st.success(f"🟢 **Valve-to-Bore: {flow_ratio:.2f}**\n\n**Optimal:** Pernapasan lega. Tenaga tidak 'nahan' di RPM atas.")
        else:
            st.warning(f"🟡 **Valve-to-Bore: {flow_ratio:.2f}**\n\n**Choked:** Klep terlalu kecil untuk piston ini. Solusi: Porting atau gedein klep.")

    # --- PERFORMANCE TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df[["Run", "CC", "CR", "Max_HP", "at_RPM_HP", "Max_Nm", "at_RPM_Nm"]],
        column_config={
            "CC": st.column_config.NumberColumn("cc", format="%.1f"),
            "CR": st.column_config.NumberColumn("CR", format="%.1f"),
            "Max_HP": st.column_config.NumberColumn("HP", format="%.2f"),
            "at_RPM_HP": st.column_config.NumberColumn("RPM", format="%d"),
        },
        hide_index=True, use_container_width=True
    )

    # --- GRAPH ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} HP"))
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="Horsepower")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Masukkan data di kiri untuk memulai analisis expert.")
