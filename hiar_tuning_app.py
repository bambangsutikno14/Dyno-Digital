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
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89.0},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION ---
def calculate_axis_v10(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    adj_peak = float(std['peak_rpm']) + (((float(dur_in) + float(dur_out))/2.0 - 240.0) * 55.0)
    eff = 0.85
    afr_mod = 1.0 - abs(float(afr) - 13.0) * 0.04
    thermal_penalty = 1.0 - ((cr - 14.5) * 0.15) if cr > 14.5 else 1.0
    bmep = (float(std['hp_std']) * 950000.0) / (float(cc) * adj_peak * eff)
    
    for r in rpms:
        ve = math.exp(-((r - adj_peak) / 4500.0)**2) if r <= adj_peak else math.exp(-((r - adj_peak) / 1800.0)**2)
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / float(v_in))**2) * ps_speed
        if gs_in > 110.0: ve *= (110.0 / gs_in)
        hp = (bmep * float(cc) * float(r) * ve * eff * afr_mod * thermal_penalty) / 950000.0
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
    return rpms, hps, torques, ps_speed, gs_in, ((float(bore) / float(v_out))**2) * ps_speed

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    
    st.header("2️⃣ ENGINE SIMULATION")
    raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input("Bore", value=float(std['bore']), step=0.1)
    in_vhead = st.number_input("Vol Head", value=float(std['v_head']), step=0.1)
    in_rpm = st.number_input("Limit RPM", value=int(std['limit_std']), step=100)
    
    expert_on = st.toggle("🚀 Detail Expert Tuning", value=True)
    if expert_on:
        in_stroke = st.number_input("Stroke", value=float(std['stroke']), step=0.1)
        in_v_in = st.number_input("Klep In", value=float(std['valve_in']), step=0.1)
        in_v_out = st.number_input("Klep Out", value=float(std['valve_out']), step=0.1)
        in_venturi = st.number_input("Venturi", value=float(std['venturi']), step=0.5)
        in_dur_in = st.slider("Durasi In", 200, 320, 240)
        in_dur_out = st.slider("Durasi Out", 200, 320, 240)
        in_afr = st.slider("Target AFR", 11.5, 14.7, 13.0, step=0.1)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0

    cc_calc = (0.785398 * in_bore**2 * in_stroke) / 1000.0
    st.success(f"CC Motor: {cc_calc:.2f} cc")
    run_btn = st.button("🚀 RUN AXIS DYNO")

# --- 5. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + in_vhead) / in_vhead
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v10(cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    pwr = (max(hps) / (std['weight_std'] + 60.0)) * 10.0
    
    st.session_state.history.append({
        "Run": f"{raw_label} {model_name}", "CC": round(cc_calc, 2), "CR": round(cr_calc, 2),
        "Max_HP": max(hps), "RPM_HP": int(rpms[np.argmax(hps)]), "Max_Nm": max(torques), "RPM_Nm": int(rpms[np.argmax(torques)]),
        "T100m": round(6.5/math.pow(pwr, 0.45), 2), "T201m": round(10.2/math.pow(pwr, 0.45), 2),
        "T402m": round(16.5/math.pow(pwr, 0.45), 2), "T1000m": round(32.8/math.pow(pwr, 0.45), 2),
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed, "rpms": rpms, "hps": hps, "torques": torques,
        "bore": in_bore, "v_in": in_v_in, "v_out": in_v_out
    })

if not st.session_state.history:
    st.info("👋 Atur spek di Sidebar dan klik **RUN AXIS DYNO**.")
else:
    latest = st.session_state.history[-1]
    
    # METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("Peak Power", f"{latest['Max_HP']:.2f} HP")
    m2.metric("Peak Torque", f"{latest['Max_Nm']:.2f} Nm")
    m3.metric("Gas Speed", f"{latest['gsin']:.1f} m/s")

    # TABEL DYNO & DRAG
    st.write("### 📊 Dyno Performance Results")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)
    
    st.write("### 🏁 Drag Simulation Times")
    st.dataframe(df[["Run", "T100m", "T201m", "T402m", "T1000m"]], hide_index=True, use_container_width=True)

    # GRAFIK
    fig = go.Figure()
    for r in st.session_state.history:
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} HP"))
    fig.update_layout(template="plotly_dark", height=450, xaxis_title="RPM", yaxis_title="Power (HP)")
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. AXIS EXPERT (STATIC STRUCTURE) ---
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    
    v_now, cr_now, cc_now = round(latest['gsin'], 2), round(latest['CR'], 2), round(latest['CC'], 2)

    # 1. ANALISA PERFORMA
    ana_txt = f"Mesin {latest['Run']} (CC: {cc_now}). "
    if v_now > 115: ana_txt += f"❌ **Kritis:** Choke Flow ({v_now} m/s). "
    elif v_now > 100: ana_txt += f"⚠️ **Peringatan:** High Velocity ({v_now} m/s). "
    else: ana_txt += f"✅ **Optimal:** Flow ({v_now} m/s) sangat efisien. "
    st.info(f"**1. Analisa Performa:** {ana_txt} Kondisi termal {'⚠️ Tinggi' if cr_now > 13.5 else '✅ Aman'} (CR {cr_now}:1).")

    # 2. REKOMENDASI
    rk, rv = round(math.sqrt(cc_now*0.15)*10, 1), round(cc_now/12.5, 2)
    st.warning(f"**2. Rekomendasi:** Pakai leher knalpot {rk}mm dan target Volume Head {rv}cc.")

    # 3. SOLUSI
    st.write("**3. Solusi (Opsi Perbaikan):**")
    if cr_now > 14.5:
        st.write(f"• **Manajemen Kompresi:** Tambah paking 0.5-1.0mm atau papas dome piston {round(cc_now*0.01, 1)}cc.")
        st.write(f"• **Cam Timing:** Pakai noken as overlap tinggi untuk buang tekanan statis.")
    if v_now > 105:
        st.write(f"• **Upgrade Flow:** Ganti Klep IN ke {round(latest['bore']*0.55, 1)}mm atau Reamer Throttle Body.")
    if cr_now <= 14.5 and v_now <= 105:
        st.success("✅ **Balanced Engine:** Konfigurasi sudah harmonis. Fokus pada settingan AFR dan Porting Stage 1.")
