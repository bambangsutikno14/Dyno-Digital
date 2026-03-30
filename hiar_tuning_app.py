import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. DATABASE PABRIKAN (Kunci Utama Presisi) ---
DATABASE_REF = {
    "YAMAHA": {
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, "type": "Matic", "hp_target": 12.0},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, "type": "Matic", "hp_target": 6.54},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, "type": "Matic", "hp_target": 11.5},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, "type": "Matic", "hp_target": 8.5},
    }
}

# --- 3. ENGINE LOGIC (Dinamis & Presisi) ---
def calculate_performance(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, model_name):
    rpms = np.arange(2000, rpm_limit + 250, 250)
    hps, torques = [], []
    
    # Penentuan Peak RPM berdasarkan stroke (Overstroke vs Overbore)
    peak_rpm_hp = 8000 if "Mio" in model_name else 8500
    
    # Multiplier BMEP khusus agar Mio Standar Pas 6.54 HP
    # Kalibrasi: 8.95 adalah angka 'Magic' untuk mencapai target klaim pabrikan
    base_bmep = 8.95 * (venturi / 24) * (cr / 9.5)
    
    for r in rpms:
        # Efek Nafas (Drop-off Parabolik)
        ve = math.exp(-((r - peak_rpm_hp) / 3800)**2)
        
        # Expert Flow Analysis (Gas Speed)
        piston_speed = (2 * stroke * r) / 60000
        gas_speed = ((bore / valve_in)**2) * piston_speed
        if gas_speed > 105: ve *= (105 / gas_speed) # Tercekik jika gas speed > 105m/s
        
        # Horsepower & Torque (Loss CVT Matic 18%)
        hp = (base_bmep * cc * r * ve * 0.82) / 950000
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
    in_stroke = st.number_input(f"Stroke ({std['stroke']} std)", value=std['stroke'], step=0.1)
    in_vhead = st.number_input(f"Vol Head ({std['v_head']} std)", value=std['v_head'], step=0.1)
    in_valve = st.number_input(f"Klep In ({std['valve']} std)", value=std['valve'], step=0.1)
    in_venturi = st.number_input(f"Venturi ({std['venturi']} std)", value=float(std['venturi']), step=1.0)
    in_rpm = st.slider("RPM Limit", 5000, 15000, 9000)

    if st.button("🚀 ANALYZE"):
        cc = (math.pi * (in_bore**2) * in_stroke) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_max = (2 * in_stroke * in_rpm) / 60000
        
        rpms, hps, torques = calculate_performance(cc, in_bore, in_stroke, cr, in_rpm, in_valve, in_venturi, model)
        
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
    
    # --- EXPERT SAFETY ANALYSIS (Graham Bell) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        ps = latest['PS']
        label = "Safe (Biru)" if ps <= 18 else "Optimal (Hijau)" if ps <= 21 else "Risky (Merah)"
        st.metric("Piston Speed", f"{ps:.2f} m/s", label)
        if ps > 21: st.error("⚠️ Resiko patah stang seher!")

    with c2:
        cr = latest['CR']
        label = "Safe (Biru)" if cr <= 11.5 else "Optimal (Hijau)" if cr <= 13.0 else "Risky (Merah)"
        st.metric("Static CR", f"{cr:.2f}:1", label)
        if cr > 13.0: st.error("⚠️ Rawan Detonasi/Lumer!")

    with c3:
        gs = latest['GS']
        label = "Efficient (Hijau)" if gs <= 100 else "Choked (Kuning)"
        st.metric("Gas Speed", f"{gs:.2f} m/s", label)
        if gs > 100: st.warning("⚠️ Klep terlalu kecil!")

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

    # --- DYNAMIC CHART ---
    fig = go.Figure()
    for run in st.session_state.history:
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)"))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP", 
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Input data di kiri untuk memulai analisis.")
