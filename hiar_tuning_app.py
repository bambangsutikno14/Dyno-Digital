import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. DATABASE REFERENSI (Data Standar) ---
DATABASE_REF = {
    "YAMAHA": {
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, "type": "Matic"},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, "type": "Matic"},
        "Jupiter Z (Bebek)": {"bore": 51.0, "stroke": 54.0, "v_head": 12.5, "valve": 23.0, "venturi": 19, "type": "Bebek"},
    },
    "HONDA": {
        "CBR 150R (Sport)": {"bore": 57.3, "stroke": 57.8, "v_head": 14.5, "valve": 24.5, "venturi": 26, "type": "Sport"},
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, "type": "Matic"},
        "Supra X 125 (Bebek)": {"bore": 52.4, "stroke": 57.9, "v_head": 13.5, "valve": 24.0, "venturi": 18, "type": "Bebek"},
    }
}

# --- 3. ENGINE LOGIC (Universal & Dinamis) ---
def calculate_performance(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, drivetrain, motor_name):
    rpms = np.arange(2000, rpm_limit + 250, 250)
    hps, torques = [], []
    
    # Efisiensi Transmisi (Dinamis)
    dt_loss = 0.82 if drivetrain == "Matic" else 0.89 # Sport/Bebek lebih efisien (Rantai)
    
    # Target Peak RPM (Dinamis sesuai karakter stroke)
    # Overbore cenderung peak di RPM lebih tinggi
    peak_rpm_hp = rpm_limit * 0.85 if bore > stroke else rpm_limit * 0.78
    
    for r in rpms:
        # Kurva Nafas (Drop-off setelah Peak)
        ve = math.exp(-((r - peak_rpm_hp) / 4000)**2)
        
        # Gas Speed Analysis (Klep vs Bore)
        piston_speed = (2 * stroke * r) / 60000
        gas_speed = ((bore / valve_in)**2) * piston_speed
        if gas_speed > 100: ve *= (100 / gas_speed) # Power tercekik jika klep kekecilan
        
        # BMEP Dinamis (Base BMEP disesuaikan agar Mio std ~6.5 HP)
        base_bmep = 7.15 * (venturi / 24) * (cr / 9.5)
        
        hp = (base_bmep * cc * r * ve * dt_loss) / 950000
        trq = (hp * 7127) / r if r > 0 else 0
        
        hps.append(round(hp, 2))
        torques.append(round(trq, 2))
        
    return rpms, hps, torques

# --- 4. SIDEBAR CONFIG ---
with st.sidebar:
    st.header("⚙️ ENGINE CONFIG")
    type_m = st.radio("Tipe Motor", ["Matic", "Bebek", "Sport"])
    
    with st.expander("Gunakan Data Pabrikan (std)"):
        merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
        model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
        std = DATABASE_REF[merk][model]

    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input(f"Bore ({std['bore']} std)", value=std['bore'], step=0.1)
    in_stroke = st.number_input(f"Stroke ({std['stroke']} std)", value=std['stroke'], step=0.1)
    in_vhead = st.number_input(f"Vol Head ({std['v_head']} std)", value=std['v_head'], step=0.1)
    in_valve = st.number_input(f"Klep In ({std['valve']} std)", value=std['valve'], step=0.1)
    in_venturi = st.number_input(f"Venturi ({std['venturi']} std)", value=float(std['venturi']), step=1.0)
    in_rpm = st.slider("RPM Limit", 5000, 16000, 9000)

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * in_stroke) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_max = (2 * in_stroke * in_rpm) / 60000
        
        rpms, hps, torques = calculate_performance(cc, in_bore, in_stroke, cr, in_rpm, in_valve, in_venturi, type_m, model)
        
        idx_hp, idx_trq = np.argmax(hps), np.argmax(torques)
        run_name = f"{label_run} ({model.split(' ')[0]})"
        
        st.session_state.history.append({
            "Run": run_name, "CC": cc, "CR": cr, "PS": ps_max, "GS": ((in_bore/in_valve)**2)*ps_max,
            "HP": hps[idx_hp], "RPM_HP": rpms[idx_hp], "Nm": torques[idx_trq], "RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "hps": hps, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 🛡️ EXPERT SAFETY ANALYSIS (GRAHAM BELL) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        ps = latest['PS']
        if ps <= 18: st.info(f"🔵 **Piston Speed: {ps:.2f} m/s**\n\n**Safe:** Awet harian.")
        elif ps <= 21: st.success(f"🟢 **Piston Speed: {ps:.2f} m/s**\n\n**Optimal:** Cek oli rutin.")
        else: st.error(f"🔴 **Piston Speed: {ps:.2f} m/s**\n\n**Risky:** Potensi patah stang seher!")

    with c2:
        cr = latest['CR']
        if cr <= 11.5: st.info(f"🔵 **Static CR: {cr:.2f}:1**\n\n**Safe:** RON 92 cukup.")
        elif cr <= 13.0: st.success(f"🟢 **Static CR: {cr:.2f}:1**\n\n**Optimal:** Wajib RON 98.")
        else: st.error(f"🔴 **Static CR: {cr:.2f}:1**\n\n**Risky:** Rawan Detonasi/Lumer!")

    with c3:
        gs = latest['GS']
        if gs <= 100: st.success(f"🟢 **Gas Speed: {gs:.2f} m/s**\n\n**Efficient:** Nafas mesin lega.")
        else: st.warning(f"🟡 **Gas Speed: {gs:.2f} m/s**\n\n**Choking:** Klep terlalu kecil!")

    # --- PERFORMANCE TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df[["Run", "CC", "CR", "HP", "RPM_HP", "Nm", "RPM_Nm"]],
        column_config={
            "CC": st.column_config.NumberColumn("cc", format="%.2f"),
            "CR": st.column_config.NumberColumn("CR", format="%.2f"),
            "HP": st.column_config.NumberColumn("HP", format="%.2f"),
            "Nm": st.column_config.NumberColumn("Nm", format="%.2f"),
        }, hide_index=True, use_container_width=True
    )

    # --- GRAPH (Dynamic Labeling & Drop-off) ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)"))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="Horsepower", 
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
