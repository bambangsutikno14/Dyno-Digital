import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
# Perbaikan error pada st.set_page_config yang terlihat di image_a486bd.png
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. VERIFIED DATABASE & TARGET ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, 
            "hp_std": 6.54, "trq_std": 7.84, "peak_rpm": 8000, "loss_coeff": 0.72
        },
        "NMAX 155 / Aerox": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, 
            "hp_std": 15.1, "trq_std": 13.9, "peak_rpm": 8000, "loss_coeff": 0.88
        },
    },
    "HONDA": {
        "Vario 150 / PCX": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, 
            "hp_std": 13.0, "trq_std": 13.4, "peak_rpm": 8500, "loss_coeff": 0.86
        },
        "BeAT FI / Scoopy": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, 
            "hp_std": 8.68, "trq_std": 9.01, "peak_rpm": 7500, "loss_coeff": 0.84
        },
    }
}

# --- 3. DYNAMIC ENGINE CALCULATOR ---
def calculate_precision_engine(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    
    # Mencari BMEP ideal agar HP standar sesuai target
    # BMEP = (HP * 950000) / (CC * RPM_Peak * Loss_Coeff)
    target_bmep = (std['hp_std'] * 950000) / (cc * std['peak_rpm'] * std['loss_coeff'])
    
    for r in rpms:
        # Kurva VE Parabolik (Puncak tepat di RPM standar)
        ve = math.exp(-((r - std['peak_rpm']) / 3200)**2)
        
        # Expert Analysis: Gas Speed (Klep vs Bore)
        ps = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps
        if gs > 105: ve *= (105 / gs) # Power drop jika klep tercekik
        
        # Kalkulasi HP & Torsi
        hp = (target_bmep * cc * r * ve * std['loss_coeff']) / 950000
        
        # Koreksi jika Bore Up / Kompresi Naik
        if bore > std['bore'] or cr > 10.0:
            hp *= (1 + (cr - 9.5) * 0.015) # Kenaikan kompresi menambah tenaga
        
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
    
    # Limit RPM Otomatis menyesuaikan karakter mesin
    in_rpm = st.slider("Limit RPM", 5000, 15000, int(std['peak_rpm'] + 1500))

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * std['stroke']) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_max = (2 * std['stroke'] * in_rpm) / 60000
        gs_max = ((in_bore/in_valve)**2)*ps_max
        
        rpms, hps, torques = calculate_precision_engine(cc, in_bore, std['stroke'], cr, in_rpm, in_valve, in_venturi, std)
        
        idx_hp, idx_trq = np.argmax(hps), np.argmax(torques)
        run_name = f"{label_run} ({model.split(' ')[0]})"
        
        st.session_state.history.append({
            "Run": run_name, "CC": cc, "CR": cr, "PS": ps_max, "GS": gs_max,
            "HP": hps[idx_hp], "RPM_HP": rpms[idx_hp], "Nm": torques[idx_trq], "RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "hps": hps, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

# --- DISCLAIMER ---
st.warning("⚠️ **Disclaimer:** Hasil kalkulasi adalah estimasi prediktif berdasarkan spesifikasi input dan rumus mekanis. Margin error dapat terjadi karena faktor eksternal (suhu, kualitas bahan bakar, dan kondisi fisik komponen).")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- EXPERT SAFETY ANALYSIS (STILL MAINTAINED) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    # 1. Piston Speed (Biru, Hijau, Merah)
    with c1:
        ps = latest['PS']
        color = "blue" if ps <= 18 else "green" if ps <= 21 else "red"
        st.markdown(f"### <span style='color:{color}'>Piston Speed: {ps:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Status: {'Aman (Daily)' if ps<=18 else 'Optimal (Tuned)' if ps<=21 else 'Beresiko (Race)'}")

    # 2. Compression Ratio
    with c2:
        cr = latest['CR']
        color = "blue" if cr <= 11.5 else "green" if cr <= 13.0 else "red"
        st.markdown(f"### <span style='color:{color}'>Static CR: {cr:.2f}:1</span>", unsafe_allow_html=True)
        st.write(f"BBM: {'RON 92' if cr<=11.5 else 'RON 98' if cr<=13.0 else 'Racing Fuel'}")

    # 3. Gas Speed
    with c3:
        gs = latest['GS']
        color = "green" if gs <= 100 else "red"
        st.markdown(f"### <span style='color:{color}'>Gas Speed: {gs:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Nafas: {'Lega' if gs<=100 else 'Tercekik (Choked)'}")

    # --- PERFORMANCE TABLE ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "HP", "RPM_HP", "Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)

    # --- DYNAMIC CHART ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)"))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP", 
                      yaxis2=dict(overlaying="y", side="right", title="Nm"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
