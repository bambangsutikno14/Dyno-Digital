import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    .expert-box { padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "valves": 4},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "valves": 2},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "valves": 2},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION (V15 - FULL PHYSICS LOGIC) ---
def calculate_axis_v15(cc, bore, stroke, cr, rpm_limit, v_in, n_v_in, v_out, n_v_out, v_lift, venturi, dur_in, dur_out, afr, material, d_type, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    
    # Tuning Logic: Shift Peak based on Duration
    avg_dur = (float(dur_in) + float(dur_out)) / 2.0
    adj_peak_rpm = float(std['peak_rpm']) + ((avg_dur - 240.0) * 50.0)
    
    d_loss = 0.85 if d_type == "CVT" else 0.95
    afr_mod = 1.0 - abs(float(afr) - 12.8) * 0.05
    
    eff_v_in = math.sqrt(n_v_in * (v_in**2))
    eff_v_out = math.sqrt(n_v_out * (v_out**2))
    
    bmep_base = (float(std['hp_std']) * 950000.0) / (float(std['bore']**2 * 0.785 * std['stroke']/1000) * float(std['peak_rpm']) * 0.85)

    for r in rpms:
        # Volumetric Efficiency Curve
        ve = math.exp(-((r - adj_peak_rpm) / 4800.0)**2) if r <= adj_peak_rpm else math.exp(-((r - adj_peak_rpm) / 2800.0)**2)
        
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / eff_v_in)**2) * ps_speed
        gs_out = ((float(bore) / eff_v_out)**2) * ps_speed 
        
        # Physics Barriers (4-Stroke Performance Tuning Principles)
        if gs_in > 115.0: ve *= (115.0 / gs_in)**2.2 
        if gs_out > 110.0: ve *= (110.0 / gs_out)**1.8
        
        ps_limit = 27.5 if material == "Forged" else 21.5
        if ps_speed > ps_limit: ve *= (ps_limit / ps_speed)**2.5
        
        hp = (bmep_base * float(cc) * float(r) * ve * d_loss * afr_mod) / 960000.0
        
        # Lift Benefit (Diminishing returns after 0.35 * Valve Diameter)
        lift_ratio = v_lift / v_in
        if lift_ratio > 0.25: hp *= (1.0 + (lift_ratio - 0.25) * 0.15)
        
        # Compression Penalty/Bonus
        if cr > 14.5: hp *= (1.0 - (cr - 14.5) * 0.12) # Detonation loss
        
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques, ps_speed, gs_in, gs_out

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        full_label = f"{raw_label} {model_name.split(' ')[0]}" 
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std['bore']), step=0.1)
        in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)
        cc_placeholder = st.empty()

    with st.expander("🧪 Detail Expert Tuning", expanded=True):
        in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2], index=1 if std['valves']==4 else 0)
        in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2], index=1 if std['valves']==4 else 0)
        in_v_lift = st.number_input("Lift (mm)", value=8.5, step=0.1)
        in_dur_in = st.slider("Durasi In", 200, 320, 275)
        in_dur_out = st.slider("Durasi Out", 200, 320, 270)
        in_afr = st.slider("AFR", 11.0, 15.0, 12.8)
        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Drive", ["CVT", "Rantai"])

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC: {cc_calc:.2f}")
    in_joki = st.number_input("Joki (kg)", value=60.0)
    run_btn = st.button("🚀 RUN AXIS DYNO")

# --- 5. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v15(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in, 
        in_v_out, in_n_v_out, in_v_lift, 28.0, in_dur_in, in_dur_out, in_afr, in_material, in_d_type, std
    )
    
    hp_max = max(hps)
    pwr = (hp_max / (std['weight_std'] + in_joki)) * 10.0
    st.session_state.history.append({
        "Run": full_label, "CC": cc_calc, "CR": cr_calc, "Max_HP": hp_max, "RPM_HP": rpms[np.argmax(hps)],
        "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)], "gsin": gsin, "gsout": gsout, 
        "pspeed": pspeed, "rpms": rpms, "hps": hps, "torques": torques, "v_in": in_v_in, "v_out": in_v_out,
        "bore": in_bore, "T201": 10.2 / math.pow(pwr, 0.45)
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # 1. METRICS GRID
    st.header("🌪️ Flowbench & Velocity Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4: st.metric("Flow In (est)", f"{round((latest['v_in']/25.4)**2 * 146, 1)} CFM")
    with m5: st.metric("T-201m (est)", f"{latest['T201']:.2f} s")

    # 2. GRAPH WITH 1000 RPM GRID
    fig = go.Figure()
    for r in st.session_state.history:
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(width=3)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], name=f"{r['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))

    fig.update_layout(template="plotly_dark", height=500,
                      xaxis=dict(title="RPM", showgrid=True, gridcolor="#444", dtick=1000), # GRID SETIAP 1000
                      yaxis=dict(title="Horsepower (HP)", showgrid=True, gridcolor="#444"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"))
    st.plotly_chart(fig, use_container_width=True)

    # 3. PERFORMANCE TABLE
    st.write("### 📊 Run Comparison Ledger")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "T201"]], hide_index=True, use_container_width=True)

    # 4. FULL EXPERT ADVICE (THE BRAIN)
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    
    c1, c2 = st.columns(2)
    with c1:
        # Analisa Mesin
        st.subheader("🧐 Analisa Kondisi Mesin")
        if latest['gsin'] > 115:
            st.error(f"❌ **CHOKE FLOW:** Velocity Intake {latest['gsin']:.1f} m/s melampaui batas suara. Klep In kekecilan untuk bore {latest['bore']}mm.")
        elif latest['gsin'] < 90:
            st.warning(f"⚠️ **LOW VELOCITY:** Velocity {latest['gsin']:.1f} m/s terlalu rendah. Torsi bawah akan loyo. Kecilkan ukuran klep atau porting.")
        else:
            st.success(f"✅ **IDEAL FLOW:** Velocity {latest['gsin']:.1f} m/s sangat optimal untuk efisiensi volumetrik.")
            
        if latest['CR'] > 14.5:
            st.error(f"❌ **CRITICAL DETONATION:** Kompresi {latest['CR']:.1f}:1 terlalu tinggi untuk bahan bakar umum. Resiko piston jebol!")
            
    with c2:
        # Saran Ahli & Solusi
        st.subheader("💡 Saran Ahli (4-Stroke Tuning)")
        ideal_head = latest['CC'] / 12.5
        st.info(f"📍 **Target Vol Head:** Untuk mengejar performa, targetkan Vol Head di {ideal_head:.2f}cc.")
        
        ex_diam = round(math.sqrt(latest['CC'] * 0.16) * 10, 1)
        st.warning(f"📍 **Knalpot:** Gunakan diameter header (leher) {ex_diam}mm untuk scavenging optimal.")
        
        solusi_porting = "Lakukan porting polish minimalis, fokus pada area 'Back-Cut' klep." if latest['gsin'] < 100 else f"Segera perbesar Klep In ke minimal {round(latest['bore']*0.52, 1)}mm."
        st.success(f"📍 **Solusi Utama:** {solusi_porting}")

st.write("---")
st.caption("Aplikasi ini menggunakan algoritma simulasi internal combustion engine berbasis Mean Effective Pressure (BMEP).")
