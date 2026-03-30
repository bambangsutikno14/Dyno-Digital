import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. VERIFIED DATABASE (Sesuai Data Pabrikan) ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, 
            "ps_std": 8.9, "trq_std": 7.84, "peak_rpm": 8000, "limit_std": 9000
        },
        "NMAX 155 / Aerox": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, 
            "ps_std": 15.3, "trq_std": 13.9, "peak_rpm": 8000, "limit_std": 9500
        },
    },
    "HONDA": {
        "Vario 150 / PCX": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, 
            "ps_std": 13.1, "trq_std": 13.4, "peak_rpm": 8500, "limit_std": 9800
        },
    }
}

# --- 3. CORE LOGIC CALIBRATION ---
def calculate_engine_v4(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, pss, torques = [], [], []
    
    # Target 8.9 PS = 8.78 HP
    target_hp = std['ps_std'] * 0.986
    # Kalibrasi BMEP khusus agar Mio Standar pas di 8.9 PS
    eff = 0.84 if "Mio" in str(std) else 0.90
    bmep_lock = (target_hp * 950000) / (cc * std['peak_rpm'] * eff)
    
    for r in rpms:
        ve = math.exp(-((r - std['peak_rpm']) / 3600)**2)
        ps_speed = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps_speed
        if gs > 105: ve *= (105 / gs) 
        
        hp_val = (bmep_lock * cc * r * ve * eff) / 950000
        # Bonus tenaga jika modifikasi
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.02)
            
        pss.append(round(hp_val / 0.986, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
        
    return rpms, pss, torques

# --- 4. SIDEBAR (PERIMETER INPUT) ---
with st.sidebar:
    st.header("🏁 MOTOR CONFIG")
    merk = st.selectbox("Pilih Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]

    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input("Bore (mm)", value=std['bore'], step=0.1)
    in_vhead = st.number_input("Vol Head (cc)", value=std['v_head'], step=0.1)
    in_valve = st.number_input("Klep In (mm)", value=std['valve'], step=0.1)
    in_venturi = st.number_input("Venturi (mm)", value=float(std['venturi']), step=1.0)
    in_rpm = st.number_input("Limit RPM", value=int(std['limit_std']), step=100)

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * std['stroke']) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_m = (2 * std['stroke'] * in_rpm) / 60000
        gs_m = ((in_bore/in_valve)**2)*ps_m
        
        rpms, pss, torques = calculate_engine_v4(cc, in_bore, std['stroke'], cr, in_rpm, in_valve, in_venturi, std)
        
        idx = np.argmax(pss)
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", 
            "CC": cc, "CR": cr, "PS_Max": ps_m, "GS_Max": gs_m,
            "Max_PS": pss[idx], "Max_Nm": torques[np.argmax(torques)], "RPM_Peak": rpms[idx],
            "rpms": rpms, "pss": pss, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning (Beta)")
st.warning("⚠️ **Disclaimer:** Hasil kalkulasi adalah prediksi sistem berdasarkan spesifikasi mekanis. Hasil aktual mungkin bervariasi. GassPoll")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- EXPERT SAFETY ANALYSIS (STAY) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    with c1:
        color = "blue" if latest['PS_Max'] <= 18 else "green" if latest['PS_Max'] <= 21 else "red"
        st.markdown(f"### <span style='color:{color}'>Piston Speed: {latest['PS_Max']:.2f} m/s</span>", unsafe_allow_html=True)
    with c2:
        color = "blue" if latest['CR'] <= 11.5 else "green" if latest['CR'] <= 13.0 else "red"
        st.markdown(f"### <span style='color:{color}'>Static CR: {latest['CR']:.2f}:1</span>", unsafe_allow_html=True)
    with c3:
        color = "green" if latest['GS_Max'] <= 100 else "red"
        st.markdown(f"### <span style='color:{color}'>Gas Speed: {latest['GS_Max']:.2f} m/s</span>", unsafe_allow_html=True)

    # --- PERFORMANCE TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_PS", "Max_Nm", "RPM_Peak"]], hide_index=True, use_container_width=True)

    # --- GRAPH (FIXED LABEL & POSITION) ---
    fig = go.Figure()
    for run in st.session_state.history:
        # Garis Power (PS)
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['pss'], name=f"{run['Run']} (PS)",
            mode='lines'
        ))
        # Anotasi angka di titik puncak garis
        fig.add_annotation(
            x=run['RPM_Peak'], y=run['Max_PS'],
            text=f"{run['Max_PS']} PS @ {run['RPM_Peak']} RPM",
            showarrow=True, arrowhead=2, ax=40, ay=-30,
            bgcolor="rgba(0,0,0,0.5)", bordercolor="white"
        )
        # Garis Torque (Nm) - Titik-titik
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)",
            line=dict(dash='dot'), yaxis="y2"
        ))

    fig.update_layout(
        template="plotly_dark", height=600,
        xaxis_title="RPM", yaxis_title="Power (PS)",
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"),
        legend=dict(orientation="h", y=-0.15)
    )
    st.plotly_chart(fig, use_container_width=True)
