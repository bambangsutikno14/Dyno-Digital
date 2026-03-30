import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. VERIFIED DATABASE (SATUAN PS SESUAI BROSUR) ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, 
            "ps_std": 8.9, "trq_std": 7.84, "peak_rpm": 8000, "efficiency": 0.85
        },
        "NMAX 155 / Aerox": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, 
            "ps_std": 15.3, "trq_std": 13.9, "peak_rpm": 8000, "efficiency": 0.92
        },
    },
    "HONDA": {
        "Vario 150 / PCX": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, 
            "ps_std": 13.1, "trq_std": 13.4, "peak_rpm": 8500, "efficiency": 0.90
        },
        "BeAT FI / Scoopy": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, 
            "ps_std": 8.68, "trq_std": 9.01, "peak_rpm": 7500, "efficiency": 0.88
        },
    }
}

# --- 3. CORE LOGIC (PS TO HP CONVERSION) ---
def calculate_engine_pro(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, pss, torques = [], [], []
    
    # Konversi Target PS ke HP (1 PS = 0.986 HP)
    target_hp = std['ps_std'] * 0.986
    
    # BMEP Lock (Mengunci agar standar selalu pas)
    # BMEP = (HP * 950000) / (CC * RPM * Efficiency)
    bmep_lock = (target_hp * 950000) / (cc * std['peak_rpm'] * std['efficiency'])
    
    for r in rpms:
        # Kurva Nafas Parabolic
        ve = math.exp(-((r - std['peak_rpm']) / 3500)**2)
        
        # Expert Analysis: Gas Speed (Klep vs Bore)
        ps_speed = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps_speed
        if gs > 105: ve *= (105 / gs) 
        
        # Kalkulasi HP & PS
        hp_val = (bmep_lock * cc * r * ve * std['efficiency']) / 950000
        # Jika Bore Up atau Kompresi naik, berikan bonus tenaga proporsional
        if bore > std['bore'] or cr > 11.0:
            hp_val *= (1 + (cr - 9.5) * 0.02)
            
        ps_val = hp_val / 0.986
        trq_val = (hp_val * 7127) / r if r > 0 else 0
        
        hps.append(round(hp_val, 2))
        pss.append(round(ps_val, 2))
        torques.append(round(trq_val, 2))
        
    return rpms, hps, pss, torques

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🏁 MOTOR SELECTION")
    merk = st.selectbox("Pilih Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]

    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input(f"Bore ({std['bore']} mm)", value=std['bore'], step=0.1)
    in_vhead = st.number_input(f"Vol Head ({std['v_head']} cc)", value=std['v_head'], step=0.1)
    in_valve = st.number_input(f"Klep In ({std['valve']} mm)", value=std['valve'], step=0.1)
    in_venturi = st.number_input(f"Venturi ({std['venturi']} mm)", value=float(std['venturi']), step=1.0)
    in_rpm = st.slider("Limit RPM", 5000, 15000, int(std['peak_rpm'] + 1500))

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * std['stroke']) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_m = (2 * std['stroke'] * in_rpm) / 60000
        gs_m = ((in_bore/in_valve)**2)*ps_m
        
        rpms, hps, pss, torques = calculate_engine_pro(cc, in_bore, std['stroke'], cr, in_rpm, in_valve, in_venturi, std)
        
        idx = np.argmax(pss)
        st.session_state.history.append({
            "Run": f"{label_run} ({model.split(' ')[0]})", "CC": cc, "CR": cr, "PS_Max": ps_m, "GS_Max": gs_m,
            "Max_PS": pss[idx], "Max_HP": hps[idx], "Max_Nm": torques[np.argmax(torques)], "RPM_Peak": rpms[idx],
            "rpms": rpms, "pss": pss, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning (Beta)")
st.caption("Ver 3.0 - Precision & Expert Tuning Mode")

st.warning("⚠️ **Disclaimer:** Hasil kalkulasi adalah estimasi prediktif berdasarkan spesifikasi input. Margin error ±5% dapat terjadi tergantung kondisi mesin aktual.")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- EXPERT SAFETY ANALYSIS (GRAHAM BELL) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        color = "blue" if latest['PS_Max'] <= 18 else "green" if latest['PS_Max'] <= 21 else "red"
        st.markdown(f"### <span style='color:{color}'>Piston Speed: {latest['PS_Max']:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Status: {'Aman' if latest['PS_Max']<=18 else 'Tuned' if latest['PS_Max']<=21 else 'Risiko Tinggi'}")

    with c2:
        color = "blue" if latest['CR'] <= 11.5 else "green" if latest['CR'] <= 13.0 else "red"
        st.markdown(f"### <span style='color:{color}'>Static CR: {latest['CR']:.2f}:1</span>", unsafe_allow_html=True)
        st.write(f"Rekomendasi: {'Pertamax/92' if latest['CR']<=11.5 else 'Turbo/98' if latest['CR']<=13.0 else 'Racing Fuel'}")

    with c3:
        color = "green" if latest['GS_Max'] <= 100 else "red"
        st.markdown(f"### <span style='color:{color}'>Gas Speed: {latest['GS_Max']:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Nafas: {'Efisien' if latest['GS_Max']<=100 else 'Tercekik (Choked)'}")

    # --- TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_PS", "Max_HP", "Max_Nm", "RPM_Peak"]], hide_index=True, use_container_width=True)

    # --- GRAPH ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['pss'], name=f"{run['Run']} (PS)"))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", height=500, xaxis_title="RPM", yaxis_title="Power (PS)", 
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
