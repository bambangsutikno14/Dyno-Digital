import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    th, td { text-align: center !important; }
    div[data-testid="stDataFrame"] div[class^="st-"] { justify-content: center; }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. DATABASE PABRIKAN (CONVERTED TO HP) ---
# 1 PS = 0.986 HP
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
    }
}

# --- 3. CORE LOGIC (HP BASED) ---
def calculate_axis_engine(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, durasi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    
    peak_shift = (durasi - 240) * 50
    adjusted_peak = std['peak_rpm'] + peak_shift
    
    # Faktor efisiensi kalibrasi HP
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    bmep_lock = (std['hp_std'] * 950000) / (cc * adjusted_peak * eff)
    
    for r in rpms:
        if r <= adjusted_peak:
            ve = math.exp(-((r - adjusted_peak) / 4500)**2)
        else:
            ve = math.exp(-((r - adjusted_peak) / 1600)**2) 
        
        ps_speed = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps_speed
        if gs > 105: ve *= (105 / gs) 
        
        hp_val = (bmep_lock * cc * r * ve * eff) / 950000
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.021)
        if venturi > std['venturi']: hp_val *= (1 + (venturi - std['venturi']) * 0.011)
            
        hps.append(round(hp_val, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]
    
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=std['bore'], step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=std['v_head'], step=0.1)
        in_valve = st.number_input(f"Klep In (std: {std['valve']})", value=std['valve'], step=0.1)
        in_venturi = st.number_input(f"Venturi (std: {std['venturi']})", value=float(std['venturi']), step=1.0)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Aktifkan Perimeter Expert")
    if expert_on:
        with st.expander("🧪 Perimeter Expert", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=std['stroke'], step=0.1)
            in_durasi = st.slider("Durasi Noken As (In)", 200, 320, 240, step=2)
            in_fratio = st.number_input(f"Final Gear Ratio (std: {std['f_ratio']})", value=std['f_ratio'], step=0.01)
    else:
        in_stroke, in_durasi, in_fratio = std['stroke'], 240, std['f_ratio']

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60, step=1)

    if st.button("🔥 ANALYZE"):
        cc = (math.pi * (in_bore**2) * in_stroke) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_m = (2 * in_stroke * in_rpm) / 60000
        gs_m = ((in_bore/in_valve)**2)*ps_m
        rpms, hps, torques = calculate_axis_engine(cc, in_bore, in_stroke, cr, in_rpm, in_valve, in_venturi, in_durasi, std)
        
        max_hp = max(hps)
        total_w = std['weight_std'] + in_joki
        pwr = max_hp / total_w
        
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", "CC": round(cc, 2), "CR": round(cr, 2),
            "PS_Max": ps_m, "GS_Max": gs_m, "Max_HP": max_hp, "RPM_HP": rpms[np.argmax(hps)],
            "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
            "Joki": in_joki, "T100": round(6.5/math.pow(pwr, 0.45), 2), 
            "T201": round(10.2/math.pow(pwr, 0.45), 2), "T402": round(16.5/math.pow(pwr, 0.45), 2),
            "rpms": rpms, "hps": hps, "torques": torques, "durasi": in_durasi
        })

    with st.expander("🌪️ CFM Flow Bench Calc", expanded=False):
        c_klep = st.number_input("Diameter Klep In (mm)", value=in_valve, step=0.1)
        cfm_pred = round((c_klep / 25.4)**2 * math.sqrt(28) * 128, 1)
        st.metric("Flow (CFM @ 28\")", f"{cfm_pred} CFM")

# --- 5. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- SAFETY ANALYSIS ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Piston Speed", f"{latest['PS_Max']:.2f} m/s")
    with c2: st.metric("Static CR", f"{latest['CR']:.2f}:1")
    with c3: st.metric("Gas Speed", f"{latest['GS_Max']:.2f} m/s")

    # --- TABLES ---
    st.write("### 📊 Performance & Drag Table")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)
    st.dataframe(df[["Run", "Joki", "T100", "T201", "T402"]], hide_index=True, use_container_width=True)

    # --- AXIS DYNO VX5 GRAPH STYLE ---
    st.write("---")
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF"] # Axis khas warna kontras
    
    for i, run in enumerate(st.session_state.history):
        clr = colors[i % 3]
        # HP Line
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)",
                                 mode='lines', line=dict(color=clr, width=3)))
        fig.add_annotation(x=run['RPM_HP'], y=run['Max_HP'], text=f"{run['Max_HP']} HP @ {run['RPM_HP']}", showarrow=True)
        # Torque Line
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)",
                                 line=dict(color=clr, dash='dot', width=2), yaxis="y2"))
        fig.add_annotation(x=run['RPM_Nm'], y=run['Max_Nm'], text=f"{run['Max_Nm']} Nm", yref="y2", showarrow=True, ay=30)

    fig.update_layout(
        template="plotly_dark", height=600, paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
        xaxis=dict(title="Engine Speed (RPM)", gridcolor="#222", showline=True, linecolor="white"),
        yaxis=dict(title="Power (HP)", gridcolor="#222", range=[0, max(df['Max_HP'])*1.2]),
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False, range=[0, max(df['Max_Nm'])*1.2]),
        legend=dict(orientation="v", x=1.05, y=1, bordercolor="white", borderwidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ADVICE (3 BARIS SESUAI INSTRUKSI) ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    
    # Baris 1: Analisa Performa
    st.write("**1. Analisa Performa Mesin:**")
    analisa = f"Mesin {latest['Run']} memiliki kapasitas {latest['CC']}cc dengan efisiensi gas speed {latest['GS_Max']:.2f} m/s. "
    if latest['GS_Max'] > 105: analisa += "Terdeteksi hambatan aliran (choke) pada porting akibat ukuran klep yang tidak proporsional dengan RPM limit."
    else: analisa += "Aliran udara sangat ideal, memungkinkan pengisian silinder maksimal hingga RPM tinggi."
    st.info(analisa)

    # Baris 2: Rekomendasi Expert
    st.write("**2. Rekomendasi Expert:**")
    rekomendasi = f"Berdasarkan Graham Bell Tuning, untuk CR {latest['CR']}:1, sebaiknya gunakan LSA noken as di angka 104-106 derajat untuk memperkuat torsi tengah. "
    if latest['PS_Max'] > 20: rekomendasi += "Gunakan pelumas high-grade dan pastikan kruk as sudah di-balance ulang untuk meredam vibrasi."
    st.warning(rekomendasi)

    # Baris 3: Solusi Setingan & Part
    st.write("**3. Solusi Setingan & Part:**")
    if latest['GS_Max'] > 105: solusi = "Ganti Klep In ke ukuran lebih lebar (contoh: 26/22 atau 28/24) dan lakukan porting polish ulang."
    elif latest['CR'] > 13: solusi = "Gunakan bahan bakar Racing (VP/Bensol) dan tambahkan paking tembaga 0.5mm untuk menjaga suhu ruang bakar."
    else: solusi = "Optimalkan pengapian (maju 2 derajat) dan gunakan knalpot dengan diameter leher 26-28mm (Mio/Beat) untuk memaksimalkan flow."
    st.success(solusi)
