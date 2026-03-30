import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE (Storage) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. DATABASE ---
DATABASE_MATIC = {
    "YAMAHA": {
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "vva": True, "weight": 127},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "vva": False, "weight": 94},
    },
    "HONDA": {
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "vva": False, "weight": 112},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head_std": 12.7, "vva": False, "weight": 90},
    }
}

# --- 4. LOGIKA HIGH-END DYNO ---
def get_dyno_data(cc, stroke, rpm_limit, vva, temp=30, humidity=50):
    # SAE J1349 Correction Factor (Simplified)
    cf = (1.18 * (((temp + 273) / 298) * math.sqrt(298 / (temp + 273)))) - 0.18
    
    rpms = np.arange(4000, rpm_limit + 500, 250)
    hp_list = []
    torque_list = []
    
    for r in rpms:
        # VE Curve: Bell says VE peaks at 75-80% of max RPM
        ve_base = 0.92 if vva and r > 6000 else 0.85
        ve_curve = ve_base * math.cos(math.radians((r - (rpm_limit*0.8)) / (rpm_limit*0.4) * 45))
        
        bmep = 9.8 # Bar
        hp = (bmep * cc * r * ve_curve) / 900000 * cf
        torque = (hp * 7127) / r # Nm
        
        hp_list.append(round(hp, 2))
        torque_list.append(round(torque, 2))
        
    return rpms, hp_list, torque_list

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏁 DYNO CONTROL")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor]
    
    with st.expander("🛠️ Engine Specs"):
        label_run = st.text_input("Run Label", value=f"Run {len(st.session_state.history) + 1}")
        bore_in = st.number_input("Bore (mm)", value=data_std['bore'], step=0.1)
        v_head_in = st.number_input("Vol Head (cc)", value=data_std['v_head_std'], step=0.1)
        rpm_target = st.slider("Limit RPM", 5000, 14000, 9500)
        bike_weight = st.number_input("Bike Weight (kg)", value=data_std['weight'])

    with st.expander("🌡️ Weather Env (SAE)"):
        amb_temp = st.slider("Ambient Temp (°C)", 15, 45, 30)
        amb_hum = st.slider("Humidity (%)", 10, 90, 50)

    c1, c2 = st.columns(2)
    if c1.button("🚀 RUN DYNO"):
        cc = (math.pi * (bore_in**2) * data_std['stroke']) / 4000
        cr = (cc + v_head_in) / v_head_in
        rpms, hps, torques = get_dyno_data(cc, data_std['stroke'], rpm_target, data_std['vva'], amb_temp, amb_hum)
        
        # Acceleration Calc (Simplified 0-201m)
        avg_hp = max(hps) * 0.85
        accel_time = math.sqrt((2 * 201 * (bike_weight + 70)) / (avg_hp * 746 / 10)) # Estimasi kasar
        
        st.session_state.history.append({
            "label": label_run, "hp": max(hps), "torque": max(torques), "cc": round(cc,1),
            "cr": round(cr,1), "rpms": rpms, "hps": hps, "torques": torques, "accel": round(accel_time,2)
        })

    if c2.button("🗑️ RESET"):
        st.session_state.history = []
        st.rerun()

# --- 6. MAIN PANEL ---
st.title("📟 High-End Digital Dyno Station")

if st.session_state.history:
    # --- METRICS DASHBOARD ---
    latest = st.session_state.history[-1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Max Power", f"{latest['hp']} HP")
    m2.metric("Max Torque", f"{latest['torque']} Nm")
    m3.metric("Compression", f"{latest['cr']}:1")
    m4.metric("Est. 201m Time", f"{latest['accel']} s")

    # --- PROFESSIONAL DYNO GRAPH ---
    st.subheader("📊 Multi-Run Power & Torque Overlay")
    fig = go.Figure()
    
    colors = ['#ff4b4b', '#00d4ff', '#00ff00', '#ffcc00']
    for i, run in enumerate(st.session_state.history):
        color = colors[i % len(colors)]
        # Power Line (Solid)
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['label']} (HP)", line=dict(color=color, width=4)))
        # Torque Line (Dashed)
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['label']} (Nm)", line=dict(color=color, width=2, dash='dot'), yaxis="y2"))

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Engine RPM",
        yaxis_title="Horsepower (HP)",
        yaxis2=dict(title="Torque (Nm)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- ADVANCED TUNER ANALYSIS ---
    st.write("---")
    st.subheader("🧠 High-End Tuner Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        ### 📉 Powerband Analysis
        * **Peak Power:** Tercapai di {run['rpms'][np.argmax(run['hps'])]} RPM.
        * **Over-rev Capacity:** Tenaga turun sebesar {round(run['hps'][-1]/run['hp']*100,1)}% di limiter.
        * **Bell's Recommendation:** {'Perlebar porting exhaust' if run['hps'][-1] < run['hp']*0.8 else 'Kapasitas porting sudah optimal'}.
        """)
    
    with col2:
        st.markdown(f"""
        ### 🌡️ Thermal & Combustion
        * **SAE Correction:** Faktor koreksi cuaca saat ini sangat berpengaruh pada performa.
        * **BMEP Level:** {round((latest['hp']*900000)/(latest['cc']*latest['rpms'][np.argmax(latest['hps'])]*0.85),1)} Bar.
        * **Status:** {'Extreme Racing (Butuh Fuel High Octane)' if latest['cr'] > 13 else 'Highly Efficient Street'}
        """)
else:
    st.info("👈 Masukkan data Standar, klik RUN, lalu modifikasi spek untuk melihat perbandingan High-End Dyno!")
