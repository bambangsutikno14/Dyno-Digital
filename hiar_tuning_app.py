import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE & UI STYLING ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# CSS untuk memastikan tabel profesional dan estetika gelap
st.markdown("""
<style>
    th, td { text-align: center !important; vertical-align: middle !important; }
    div[data-testid="stDataFrame"] { display: flex; justify-content: center; }
    .main { background-color: #050505; }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. DATABASE PABRIKAN (HP) ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
    }
}

# --- 3. CORE EXPERT LOGIC (HIGH-END TUNING) ---
def calculate_axis_extreme(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []
    
    # Graham Bell: Duration & LSA Impact on Peak Power
    avg_dur = (dur_in + dur_out) / 2
    peak_shift = (avg_dur - 240) * 55 
    adjusted_peak = std['peak_rpm'] + peak_shift
    
    # Efficiency factors
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    # AFR Impact: Peak power at 12.8-13.2
    afr_mod = 1.0 - abs(afr - 13.0) * 0.035
    
    bmep_lock = (std['hp_std'] * 950000) / (cc * adjusted_peak * eff)
    
    for r in rpms:
        # Curve Shaping (Axis Dyno style)
        if r <= adjusted_peak:
            ve = math.exp(-((r - adjusted_peak) / 4500)**2)
        else:
            ve = math.exp(-((r - adjusted_peak) / 1600)**2) 
        
        # Gas Speed Analysis (Graham Bell)
        ps_speed = (2 * stroke * r) / 60000
        gs_in = ((bore / valve_in)**2) * ps_speed
        gs_out = ((bore / valve_out)**2) * ps_speed
        
        # Choke flow simulation
        if gs_in > 105: ve *= (105 / gs_in)
        if gs_out > 115: ve *= (115 / gs_out)
        
        hp_val = (bmep_lock * cc * r * ve * eff * afr_mod) / 950000
        
        # Tuning Multipliers
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.022)
        if venturi > std['venturi']: hp_val *= (1 + (venturi - std['venturi']) * 0.012)
            
        hps.append(round(hp_val, 2))
        torques.append(round((hp_val * 7127) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques, gs_in, gs_out

# --- 4. SIDEBAR (3 PANELS) ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]
    
    st.divider()

    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        
        # Logic Sinkronisasi Bore vs CC Real
        col_b, col_c = st.columns(2)
        with col_b:
            in_bore = st.number_input(f"Bore (std: {std['bore']})", value=std['bore'], step=0.1)
        with col_c:
            cc_init = (math.pi * (in_bore**2) * std['stroke']) / 4000
            in_cc = st.number_input("CC Motor Real", value=float(cc_init), step=0.1)
            # Re-calculate bore if CC is edited
            if not math.isclose(in_cc, cc_init, rel_tol=1e-4):
                in_bore = math.sqrt((in_cc * 4000) / (math.pi * std['stroke']))

        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=std['v_head'], step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    expert_on = st.toggle("🚀 Aktifkan Perimeter Expert", value=True)
    if expert_on:
        with st.expander("🧪 Perimeter Expert (Graham Bell Mode)", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=std['stroke'], step=0.1)
            in_valve_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=std['valve_in'], step=0.1)
            in_valve_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=std['valve_out'], step=0.1)
            in_dur_in = st.slider("Durasi In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Out", 200, 320, 240)
            in_afr = st.slider("Target AFR (Injeksi)", 11.5, 14.7, 13.0, step=0.1)
            in_fratio = st.number_input(f"Final Ratio", value=std['f_ratio'], step=0.01)
    else:
        in_stroke, in_valve_in, in_valve_out, in_dur_in, in_dur_out, in_afr, in_fratio = std['stroke'], std['valve_in'], std['valve_out'], 240, 240, 13.0, std['f_ratio']

    st.divider()
    
    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60)

    if st.button("🔥 ANALYZE & RUN AXIS DYNO"):
        cc_f = (math.pi * (in_bore**2) * in_stroke) / 4000
        cr_f = (cc_f + in_vhead) / in_vhead
        rpms, hps, torques, gsin, gsout = calculate_axis_extreme(cc_f, in_bore, in_stroke, cr_f, in_rpm, in_valve_in, in_valve_out, std['venturi'], in_dur_in, in_dur_out, in_afr, std)
        
        max_hp = max(hps)
        total_w = std['weight_std'] + in_joki
        pwr = max_hp / total_w
        
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", "CC": round(cc_f, 2), "CR": round(cr_f, 2),
            "Max_HP": max_hp, "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
            "Joki": in_joki, "T100": round(6.5/math.pow(pwr, 0.45), 2), "T201": round(10.2/math.pow(pwr, 0.45), 2),
            "rpms": rpms, "hps": hps, "torques": torques, "gsin": gsin, "gsout": gsout, "afr": in_afr,
            "valve_in": in_valve_in, "valve_out": in_valve_out
        })

    with st.expander("🌪️ CFM Flow Bench Calculator", expanded=False):
        c_in = st.number_input("Klep In", value=in_valve_in)
        c_out = st.number_input("Klep Out", value=in_valve_out)
        cfm_in = round((c_in / 25.4)**2 * math.sqrt(28) * 128, 1)
        cfm_out = round((c_out / 25.4)**2 * math.sqrt(28) * 128, 1)
        st.metric("Flow In (CFM)", cfm_in)
        st.metric("Flow Out (CFM)", cfm_out)

# --- 5. MAIN DISPLAY (AXIS VX5 INTERFACE) ---
st.title("📟 Hiar Lima Pendawa Tuning")
st.caption("Professional High-End Engine Analysis | Ver 9.0")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- PERFORMANCE TABLES ---
    st.write("### 📊 Performance & Drag Results")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)
    st.dataframe(df[["Run", "Joki", "T100", "T201", "afr"]], hide_index=True, use_container_width=True)

    # --- AXIS DYNO VX5 GRAPH (ESTETIKA REAL) ---
    st.write("---")
    fig = go.Figure()
    colors_axis = ["#FF0000", "#00FF00", "#0000FF"]
    for i, run in enumerate(st.session_state.history):
        clr = colors_axis[i % 3]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Run']} (HP)", line=dict(color=clr, width=4)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Run']} (Nm)", line=dict(color=clr, dash='dot', width=2), yaxis="y2"))
        fig.add_annotation(x=run['RPM_HP'], y=run['Max_HP'], text=f"{run['Max_HP']} HP", showarrow=True, arrowhead=2)

    fig.update_layout(
        template="plotly_dark", height=600, paper_bgcolor="#000000", plot_bgcolor="#000000",
        xaxis=dict(title="Engine Speed (RPM)", gridcolor="#1a1a1a", showline=True, linecolor="white"),
        yaxis=dict(title="Power (HP)", gridcolor="#1a1a1a", range=[0, max(df['Max_HP'])*1.25]),
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False, range=[0, max(df['Max_Nm'])*1.25]),
        legend=dict(x=1.02, y=1, bordercolor="white", borderwidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ADVICE (3 BARIS MUTLAK) ---
    st.divider()
    st.header("🏁 Axis Expert Analysis & Solutions")
    
    # 1. Analisa Performa
    st.write("**1. Analisa Performa Mesin:**")
    analisa = f"Mesin berkapasitas {latest['CC']}cc menunjukkan Gas Speed In: {latest['gsin']:.1f} m/s dan Out: {latest['gsout']:.1f} m/s pada AFR {latest['afr']}. "
    if latest['gsin'] > 105: analisa += "Aliran udara masuk tercekik di RPM tinggi (Choke Flow), membatasi potensi HP maksimal."
    else: analisa += "Aliran gas sangat harmonis, efisiensi volumetrik terjaga dengan baik."
    st.info(analisa)

    # 2. Rekomendasi Expert
    st.write("**2. Rekomendasi Expert:**")
    v_ratio = (latest['valve_out'] / latest['valve_in']) * 100
    rekomendasi = f"Rasio klep Out/In saat ini {v_ratio:.1f}%. Graham Bell menyarankan rasio 80-85% untuk efisiensi scavaging. "
    if latest['CR'] > 12.8: rekomendasi += "Kompresi sangat tinggi, diperlukan durasi overlap lebih besar untuk cooling valve."
    st.warning(rekomendasi)

    # 3. Solusi Setingan & Part
    st.write("**3. Solusi Setingan & Part:**")
    if latest['gsin'] > 105 or latest['gsout'] > 115:
        solusi = "Besarkan diameter klep (Big Valve) dan sesuaikan diameter venturi throttle body. Pastikan porting tidak terlalu besar di area bowl."
    elif latest['afr'] > 13.5:
        solusi = "Setingan terlalu kering (Lean). Tambahkan fuel rate pada ECU atau ganti injektor dengan hole lebih banyak."
    else:
        solusi = "Konfigurasi sudah optimal. Lakukan 'Fine Tuning' pada ignition timing (dimajukan 1-2 derajat) untuk respon throttle lebih instan."
    st.success(solusi)
