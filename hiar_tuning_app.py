import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIG & UI ---
st.set_page_config(Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #444; }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. CORE ENGINE LOGIC (INTEGRATED PARAMETERS) ---
def calculate_pro_dyno(cc, bore, stroke, cr, rpm_limit, v_in, v_count, piston_mat, liner_mat, ve, air_temp, drive_type, v_lift):
    rpms = np.arange(1000, int(rpm_limit) + 200, 100)
    hps, torques = [], []
    
    # A. Valve Area Calculation (Multi-Valve Logic)
    # Area = pi * r^2 * jumlah klep
    total_valve_area = (math.pi * (v_in/2)**2) * v_count
    equiv_diameter = math.sqrt(4 * total_valve_area / math.pi) # Diameter ekuivalen untuk Gas Speed
    
    # B. Friction & Thermal Tolerance
    # Forged + Ceramic menaikkan limit piston speed
    base_ps_limit = 21.0 # m/s (Standar)
    if piston_mat == "Forged": base_ps_limit += 3.0
    if liner_mat == "Ceramic/Diasil": base_ps_limit += 2.0
    
    # C. Air Density Correction (Altitude/Temp)
    # Standar 25°C. Setiap naik 5 derajat, densitas turun ~1.5%
    air_corr = 1.0 - ((air_temp - 25) * 0.003)
    
    # D. Drivetrain Loss Logic
    loss_map = {"Chain (Manual)": 0.12, "CVT (Matic)": 0.18, "Direct Drive": 0.05}
    loss_pct = loss_map.get(drive_type, 0.15)
    
    for r in rpms:
        # 1. Piston Speed & Gas Speed
        ps_speed = (2.0 * stroke * r) / 60000.0
        # Gas Speed menggunakan diameter ekuivalen dari jumlah klep
        gs_in = ((bore / equiv_diameter)**2) * ps_speed
        
        # 2. BMEP Calculation (Brake Mean Effective Pressure)
        # Dipengaruhi VE, CR, dan Flow Coefficient (Lift/Valve)
        flow_coeff = min(1.0, v_lift / (v_in * 0.30)) # Lift ideal biasanya 30% dari diameter klep
        current_ve = (ve / 100.0) * flow_coeff * air_corr
        
        # Reduksi VE saat Gas Speed melewati batas Choke (115 m/s)
        if gs_in > 115:
            current_ve *= (115 / gs_in)**2
            
        # Penalti Gesekan saat mendekati limit Piston Speed
        friction_loss = 1.0
        if ps_speed > base_ps_limit:
            friction_loss = math.exp(-0.15 * (ps_speed - base_ps_limit))
            
        # Rumus Torsi: (BMEP * Displacement) / 4pi
        # Standar BMEP mesin bensin atmosfir ~9-13 Bar
        bmep = 11.5 * (cr / 10.5) * current_ve * friction_loss
        torque_nm = (bmep * cc) / (4 * math.pi * 1.0) # Simplifikasi Nm
        
        # Rumus HP: (Torque * RPM) / 5252 (dalam Ft-Lbs, dikonversi ke Metric)
        hp_crank = (torque_nm * r) / 7127.0
        hp_wheel = hp_crank * (1.0 - loss_pct)
        
        hps.append(round(hp_wheel, 2))
        torques.append(round(torque_nm * (1.0 - loss_pct), 2))
        
    return rpms, hps, torques, ps_speed, gs_in

# --- 3. SIDEBAR (NEW ADVANCED PARAMETERS) ---
with st.sidebar:
    st.header("🛠️ Pro Engine Builder")
    
    with st.expander("💎 Mechanical Hardware", expanded=True):
        in_bore = st.number_input("Bore (mm)", 50.0, 150.0, 58.0)
        in_stroke = st.number_input("Stroke (mm)", 40.0, 150.0, 58.7)
        in_vhead = st.number_input("Vol Head (cc)", 5.0, 50.0, 14.5)
        in_v_in = st.number_input("Ukuran Klep In (mm)", 15.0, 50.0, 20.5)
        in_v_count = st.selectbox("Jumlah Klep In", [1, 2], index=1)
        in_v_lift = st.number_input("Valve Lift (mm)", 3.0, 15.0, 8.5)
    
    with st.expander("🧪 Material & Efficiency"):
        in_piston = st.selectbox("Material Piston", ["Casting", "Forged"])
        in_liner = st.selectbox("Material Liner", ["Besi", "Ceramic/Diasil"])
        in_ve = st.slider("Volumetric Efficiency (%)", 70, 115, 90)
        in_cr = ( ( (0.785 * in_bore**2 * in_stroke) / 1000) + in_vhead ) / in_vhead
        st.write(f"**Static CR:** {in_cr:.2f}:1")
        
    with st.expander("🌍 Environment & Drive"):
        in_temp = st.slider("Ambient Temp (°C)", 15, 45, 30)
        in_drive = st.selectbox("Transmission", ["Chain (Manual)", "CVT (Matic)", "Direct Drive"])
        in_rpm = st.number_input("Limit RPM", 5000, 18000, 10000)

    cc_real = (0.785398 * in_bore**2 * in_stroke) / 1000.0
    run_btn = st.button("🚀 ANALYZE REAL WHP")

# --- 4. MAIN VIEW ---
st.title("📟 Axis Dyno Pro v12.0")
st.caption("Advanced Internal Combustion Engine Simulator (WHp Accurate)")

if run_btn:
    rpms, hps, torques, pspeed, gsin = calculate_pro_dyno(cc_real, in_bore, in_stroke, in_cr, in_rpm, in_v_in, in_v_count, in_piston, in_liner, in_ve, in_temp, in_drive, in_v_lift)
    
    st.session_state.history.append({
        "Run": f"Run {len(st.session_state.history)+1}", "CC": cc_real, "CR": in_cr, 
        "HP": max(hps), "RPM": rpms[np.argmax(hps)], "Nm": max(torques), 
        "GS": gsin, "PS": pspeed, "rpms": rpms, "hps": hps, "torques": torques
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # METRICS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wheel HP", f"{latest['HP']:.2f} hp")
    c2.metric("Wheel Torque", f"{latest['Nm']:.2f} nm")
    c3.metric("Gas Speed", f"{latest['GS']:.1f} m/s")
    c4.metric("Piston Speed", f"{latest['PS']:.1f} m/s")

    # TABLES
    st.write("### 📊 Measurement Logs")
    df = pd.DataFrame(st.session_state.history).drop(columns=['rpms', 'hps', 'torques'])
    st.dataframe(df, hide_index=True, use_container_width=True)

    # CHART
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=latest['rpms'], y=latest['hps'], name="Power (WHP)", line=dict(color='#00FF00', width=4)))
    fig.add_trace(go.Scatter(x=latest['rpms'], y=latest['torques'], name="Torque (Nm)", line=dict(color='#FF0000', width=2), yaxis="y2"))
    fig.update_layout(template="plotly_dark", height=500, yaxis=dict(title="Horsepower"), yaxis2=dict(title="Newton Meter", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. EXPERT ADVICE (UPDATED) ---
    st.divider()
    st.header("🏁 Hiar Lima Pendawa Tuning")
    
    # 1. Analisa Performa
    status = "✅ Safe"
    if latest['GS'] > 115: status = "❌ CHOKE FLOW"
    elif latest['PS'] > 24: status = "⚠️ CRITICAL SPEED"
    
    st.info(f"**1. Analisa Performa:** {latest['Run']} mencapai {latest['HP']:.2f} WHP. Efisiensi Aliran: {status}. Kehilangan daya transmisi diestimasikan {(1.0-(latest['HP']/(latest['HP']/0.82)))*100:.0f}% (WHP).")

    # 2. Rekomendasi
    st.warning(f"**2. Rekomendasi:** Untuk VE {in_ve}%, pastikan durasi noken as berada di angka {240 + (in_ve-90)*2}° untuk menjaga pengisian silinder tetap optimal di RPM tinggi.")

    # 3. Solusi
    st.write("**3. Solusi Multi-Opsi:**")
    if latest['GS'] > 105:
        st.write(f"• **Velocity Terlalu Tinggi:** Meskipun ada {in_v_count} klep, kecepatan udara {latest['GS']:.1f} m/s mulai menghambat daya. Naikkan Valve Lift ke {in_v_lift + 1}mm atau perbesar klep.")
    if latest['PS'] > 21 and in_piston == "Casting":
        st.write("• **Risiko Material:** Piston Speed melewati 21 m/s. Sangat disarankan upgrade ke Piston Forged untuk menghindari pecah liner.")
