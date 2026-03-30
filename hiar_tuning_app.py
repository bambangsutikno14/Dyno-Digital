import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. VERIFIED FACTORY DATABASE ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, 
            "target_hp": 6.54, "peak_hp_rpm": 8000, "target_nm": 7.84, "peak_nm_rpm": 7000
        },
        "NMAX 155 / Aerox": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, 
            "target_hp": 15.1, "peak_hp_rpm": 8000, "target_nm": 13.9, "peak_nm_rpm": 6500
        },
    },
    "HONDA": {
        "Vario 150 / PCX": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, 
            "target_hp": 13.0, "peak_hp_rpm": 8500, "target_nm": 13.4, "peak_nm_rpm": 5000
        },
        "BeAT FI / Scoopy": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, 
            "target_hp": 8.68, "peak_hp_rpm": 7500, "target_nm": 9.01, "peak_nm_rpm": 6500
        },
    }
}

# --- 3. UNIVERSAL DYNAMIC LOGIC (CALIBRATED) ---
def calculate_precision(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, model_data):
    rpms = np.arange(2000, rpm_limit + 250, 250)
    hps, torques = [], []
    
    # Mencari nilai BMEP spesifik motor agar HP pas sesuai target
    # Rumus: BMEP = (HP * 950000) / (CC * RPM * VE)
    # Untuk Mio Karbu, BMEP efektif berada di kisaran 7.8 - 8.2 Bar
    t_hp = model_data['target_hp']
    t_rpm = model_data['peak_hp_rpm']
    base_bmep = (t_hp * 950000) / (cc * t_rpm * 0.85) 
    
    for r in rpms:
        # Kurva Nafas (Parabolic Decay)
        # Menghasilkan puncak tepat di peak_hp_rpm pabrikan
        ve = math.exp(-((r - model_data['peak_hp_rpm']) / 4200)**2)
        
        # Expert Analysis: Gas Speed (Klep vs Bore)
        ps = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps
        if gs > 105: ve *= (105 / gs) # Power drop jika klep tercekik
        
        # Kalkulasi HP & Torque
        hp = (base_bmep * cc * r * ve) / 950000
        # Koreksi kecil untuk modifikasi (jika bore dinaikkan, BMEP naik dikit)
        if bore > model_data['bore']: hp *= (1 + (cr - 9.5)*0.02)
        
        trq = (hp * 7127) / r if r > 0 else 0
        
        hps.append(round(hp, 2))
        torques.append(round(trq, 2))
        
    return rpms, hps, torques

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🏁 MOTOR SELECTION")
    merk = st.selectbox("Pilih Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]

    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input(f"Bore ({std['bore']} std)", value=std['bore'], step=0.1)
    in_vhead = st.number_input(f"Vol Head ({std['v_head']} std)", value=std['v_head'], step=0.1)
    in_valve = st.number_input(f"Klep In ({std['valve']} std)", value=std['valve'], step=0.1)
    in_venturi = st.number_input(f"Venturi ({std['venturi']} std)", value=float(std['venturi']), step=1.0)
    in_rpm = st.slider("RPM Limit", 5000, 15000, int(std['peak_hp_rpm'] + 1500))

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * std['stroke']) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_max = (2 * std['stroke'] * in_rpm) / 60000
        
        rpms, hps, torques = calculate_precision(cc, in_bore, std['stroke'], cr, in_rpm, in_valve, in_venturi, std)
        
        idx_hp, idx_trq = np.argmax(hps), np.argmax(torques)
        run_name = f"{label_run} ({model.split(' ')[0]})"
        
        st.session_state.history.append({
            "Run": run_name, "CC": cc, "CR": cr, "PS": ps_max, "GS": ((in_bore/in_valve)**2)*ps_max,
            "HP": hps[idx_hp], "RPM_HP": rpms[idx_hp], "Nm": torques[idx_trq], "RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "hps": hps, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning (Beta) ")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- 🛡️ EXPERT SAFETY ANALYSIS (STILL MAINTAINED) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Piston Speed", f"{latest['PS']:.2f} m/s", "Safe" if latest['PS']<=18 else "Risky")
    with c2:
        st.metric("Static CR", f"{latest['CR']:.2f}:1", "Safe" if latest['CR']<=11.5 else "Racing")
    with c3:
        st.metric("Gas Speed", f"{latest['GS']:.2f} m/s", "Optimal" if latest['GS']<=100 else "Choked")

    # --- TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "HP", "RPM_HP", "Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)

    # --- GRAPH ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} HP"))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} Nm", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP", 
                      yaxis2=dict(overlaying="y", side="right", title="Nm"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
