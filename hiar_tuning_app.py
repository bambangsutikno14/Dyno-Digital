import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. VERIFIED DATABASE ---
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

# --- 3. CORE LOGIC (REVISED DROP-OFF) ---
def calculate_engine_v4_5(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    pss, torques = [], []
    
    target_hp = std['ps_std'] * 0.986
    eff = 0.84 if "Mio" in str(std) else 0.90
    bmep_lock = (target_hp * 950000) / (cc * std['peak_rpm'] * eff)
    
    for r in rpms:
        # Penurunan VE lebih tajam setelah Peak RPM agar grafik turun jelas
        if r <= std['peak_rpm']:
            ve = math.exp(-((r - std['peak_rpm']) / 4500)**2)
        else:
            ve = math.exp(-((r - std['peak_rpm']) / 2000)**2) # Drop lebih curam
        
        ps_speed = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps_speed
        if gs > 105: ve *= (105 / gs) 
        
        hp_val = (bmep_lock * cc * r * ve * eff) / 950000
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.02)
            
        pss.append(round(hp_val / 0.986, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
        
    return rpms, pss, torques

# --- 4. SIDEBAR ---
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
        
        rpms, pss, torques = calculate_engine_v4_5(cc, in_bore, std['stroke'], cr, in_rpm, in_valve, in_venturi, std)
        
        idx_ps = np.argmax(pss)
        idx_trq = np.argmax(torques)
        
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", 
            "CC": round(cc, 2), "CR": round(cr, 2), "PS_Max": ps_m, "GS_Max": gs_m,
            "Max_PS": pss[idx_ps], "RPM_PS": rpms[idx_ps],
            "Max_Nm": torques[idx_trq], "RPM_Nm": rpms[idx_trq],
            "rpms": rpms, "pss": pss, "torques": torques
        })

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning (Beta)")
st.warning("⚠️ **Disclaimer:** Hitungan adalah prediksi berdasarkan spesifikasi dan kalkulasi sistem. Gasspoll")

if st.session_state.history:
    # --- EXPERT SAFETY ANALYSIS ---
    latest = st.session_state.history[-1]
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

    # --- TABLE (CENTER ALIGNED) ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    
    # CSS untuk tengahkan tabel
    st.markdown("""
        <style>
            div[data-testid="stDataFrame"] div[class^="st-"] {
                display: flex;
                justify-content: center;
            }
            th, td { text-align: center !important; }
        </style>
        """, unsafe_allow_html=True)
    
    st.dataframe(
        df[["Run", "CC", "CR", "Max_PS", "RPM_PS", "Max_Nm", "RPM_Nm"]], 
        hide_index=True, use_container_width=True
    )

    # --- GRAPH ---
    fig = go.Figure()
    for run in st.session_state.history:
        # Garis Power
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['pss'], name=f"{run['Run']} (PS)",
            mode='lines+text',
            text=[run['Run'] if i == len(run['rpms'])-1 else "" for i in range(len(run['rpms']))],
            textposition="middle right"
        ))
        # Tag Power Max
        fig.add_annotation(x=run['RPM_PS'], y=run['Max_PS'], text=f"{run['Max_PS']} PS", showarrow=True, arrowhead=2)
        
        # Garis Torque
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)",
            line=dict(dash='dot'), yaxis="y2"
        ))
        # Tag Torque Max
        fig.add_annotation(x=run['RPM_Nm'], y=run['Max_Nm'], text=f"{run['Max_Nm']} Nm", 
                           showarrow=True, arrowhead=2, yref="y2", ay=30)

    fig.update_layout(
        template="plotly_dark", height=600,
        xaxis_title="RPM", yaxis_title="Power (PS)",
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"),
        showlegend=False # Legend dimatikan karena nama sudah ada di ujung garis
    )
    st.plotly_chart(fig, use_container_width=True)
