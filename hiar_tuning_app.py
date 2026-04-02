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
    th, td { text-align: center !important; vertical-align: middle !important; }
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

# --- 3. CORE CALCULATION (V22 - FRICTION & SHARP DROP LOGIC) ---
def calculate_axis_v22(cc, bore, stroke, cr, rpm_limit, v_in, n_v_in, v_out, n_v_out, v_lift, venturi, dur_in, dur_out, afr, material, d_type, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    
    avg_dur = (float(dur_in) + float(dur_out)) / 2.0
    adj_peak_rpm = float(std['peak_rpm']) + ((avg_dur - 240.0) * 50.0)
    
    d_loss = 0.82 if d_type == "CVT" else 0.94
    afr_mod = 1.0 - abs(float(afr) - 12.8) * 0.05
    
    eff_v_in = math.sqrt(n_v_in * (v_in**2))
    eff_v_out = math.sqrt(n_v_out * (v_out**2))
    
    bmep_base = (float(std['hp_std']) * 950000.0) / (float(std['bore']**2 * 0.785 * std['stroke']/1000) * float(std['peak_rpm']) * 0.85)

    for r in rpms:
        # 1. VE Drop-off (Dibuat lebih curam/agresif: 1200)
        ve = math.exp(-((r - adj_peak_rpm) / 4800.0)**2) if r <= adj_peak_rpm else math.exp(-((r - adj_peak_rpm) / 1200.0)**2)
        
        # 2. Gas Speed Analysis
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / eff_v_in)**2) * ps_speed
        gs_out = ((float(bore) / eff_v_out)**2) * ps_speed 
        
        if gs_in > 115.0: ve *= (115.0 / gs_in)**2.5 # Penalti gas speed lebih ketat
        if gs_out > 110.0: ve *= (110.0 / gs_out)**2.0
        
        # 3. Mechanical Friction Loss (Kunci agar grafik turun setelah peak)
        # Semakin tinggi RPM, gesekan mesin memakan tenaga secara eksponensial
        friction_loss = (r / 15000.0)**2 
        
        # 4. Final HP Calculation
        hp = (bmep_base * float(cc) * float(r) * ve * d_loss * afr_mod) / 950000.0
        hp *= (1.0 - friction_loss) # Menerapkan kerugian gesek
        
        if v_lift / v_in > 0.30: hp *= (1.0 + ((v_lift/v_in) - 0.30) * 0.1)
        if cr > 14.5: hp *= (1.0 - (cr - 14.5) * 0.15)
        
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
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC: {cc_calc:.2f}")
    in_joki = st.number_input("Berat Joki (kg)", value=60.0)
    run_btn = st.button("🚀 ANALYZE & RUN AXIS")

# --- 5. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v22(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in, 
        in_v_out, in_n_v_out, in_v_lift, 28.0, in_dur_in, in_dur_out, in_afr, in_material, in_d_type, std
    )
    
    hp_max = max(hps)
    pwr = (hp_max / (std['weight_std'] + in_joki)) * 10.0
    st.session_state.history.append({
        "Run": full_label, "CC": cc_calc, "CR": cr_calc, "Max_HP": hp_max, "RPM_HP": rpms[np.argmax(hps)],
        "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)], "gsin": gsin, "gsout": gsout, 
        "pspeed": pspeed, "rpms": rpms, "hps": hps, "torques": torques, "v_in": in_v_in, "v_out": in_v_out,
        "bore": in_bore, "AFR": in_afr,
        "T100": 6.5 / math.pow(pwr, 0.45), "T201": 10.2 / math.pow(pwr, 0.45),
        "T402": 16.5 / math.pow(pwr, 0.45), "T1000": 32.8 / math.pow(pwr, 0.45)
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4: st.metric("Flow In (est)", f"{round((latest['v_in']/25.4)**2 * 146, 1)} CFM")
    with m5: st.metric("Flow Out (est)", f"{round((latest['v_out']/25.4)**2 * 146, 1)} CFM")

    fig = go.Figure()
    for r in st.session_state.history:
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], name=f"{r['Run']} (Nm)", line=dict(dash='dot'), yaxis="y2"))
        
        # LABEL PEAK HP
        fig.add_trace(go.Scatter(
            x=[r['RPM_HP']], y=[r['Max_HP']], mode='markers+text',
            text=[f"Peak: {r['Max_HP']:.2f} HP @ {r['RPM_HP']} RPM"],
            textposition="top center", marker=dict(size=12, symbol='star', color='yellow'), showlegend=False
        ))
        
        # LABEL PEAK Nm
        fig.add_trace(go.Scatter(
            x=[r['RPM_Nm']], y=[r['Max_Nm']], mode='markers+text',
            text=[f"Peak: {r['Max_Nm']:.2f} Nm @ {r['RPM_Nm']} RPM"],
            textposition="bottom center", marker=dict(size=12, symbol='star', color='cyan'),
            yaxis="y2", showlegend=False
        ))

    fig.update_layout(template="plotly_dark", height=550,
                      xaxis=dict(title="RPM", showgrid=True, gridcolor="#333", dtick=1000), 
                      yaxis=dict(title="HP", showgrid=True, gridcolor="#333"),
                      yaxis2=dict(overlaying="y", side="right", title="Nm"))
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Performance Dyno Result")
    st.dataframe(df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }), hide_index=True, use_container_width=True)

    st.write("### 🏁 Drag Simulation Predictions")
    df_drag = df[["Run", "T100", "T201", "T402", "T1000"]].rename(columns={"T100":"100m","T201":"201m","T402":"402m","T1000":"1000m"})
    st.dataframe(df_drag.style.format({
        "100m": "{:.2f}", "201m": "{:.2f}", "402m": "{:.2f}", "1000m": "{:.2f}"
    }), hide_index=True, use_container_width=True)

    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🧐 Analisa Kondisi Mesin")
        if latest['gsin'] > 115: st.error(f"❌ **CHOKE FLOW:** Intake Velocity {latest['gsin']:.1f} m/s terlalu tinggi.")
        elif latest['gsin'] < 90: st.warning(f"⚠️ **LOW VELOCITY:** {latest['gsin']:.1f} m/s. Torsi bawah loyo.")
        else: st.success(f"✅ **IDEAL FLOW:** Velocity {latest['gsin']:.1f} m/s. Sangat efisien.")
        
        if latest['CR'] > 14.5: st.error(f"❌ **CRITICAL DETONATION:** Kompresi {latest['CR']:.1f}:1 resiko knocking.")
        if latest['pspeed'] > 21: st.warning(f"⚠️ **PISTON SPEED:** {latest['pspeed']:.1f} m/s mendekati batas aman.")

    with c2:
        st.subheader("💡 Saran Ahli & Solusi")
        st.info(f"📍 **Target Vol Head:** Idealnya {latest['CC'] / 12.5:.2f}cc.")
        st.warning(f"📍 **Knalpot:** Diameter leher {round(math.sqrt(latest['CC'] * 0.16) * 10, 1)}mm.")
        
        solusi = f"Perbesar Klep In ke {round(latest['bore']*0.53, 1)}mm." if latest['gsin'] > 108 else "Optimalkan profil porting dan noken as."
        st.success(f"📍 **Solusi Utama:** {solusi}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Batas fisik (Choke Flow & Friction) diterapkan secara ketat.")
