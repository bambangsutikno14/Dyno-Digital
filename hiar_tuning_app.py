import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. DATABASE (Lengkap dengan Berat & Aerodinamika) ---
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

# --- 4. LOGIKA DRAG SIMULATION (Physics Based) ---
def simulate_drag(hp, weight_total, distance):
    # Watts conversion (1 HP = 746W)
    watts = hp * 746 * 0.85 # 0.85 as drivetrain efficiency
    # t = cuberoot((9/2) * (m/P) * d^2) -> Basic acceleration physics
    time = ( (4.5 * weight_total * (distance**2)) / watts )**(1/3)
    return round(time, 2)

def get_dyno_data(cc, stroke, rpm_limit, vva, temp=25, humidity=0):
    cf = (1.18 * (((temp + 273) / 298) * math.sqrt(298 / (temp + 273)))) - 0.18
    cf = 1/cf
    rpms = np.arange(4000, rpm_limit + 500, 250)
    hp_list = []
    torque_list = []
    for r in rpms:
        ve = 0.90 if vva and r > 6000 else 0.84
        ve_curve = ve * math.cos(math.radians((r - (rpm_limit*0.75)) / (rpm_limit*0.45) * 40))
        hp = (10.2 * cc * r * ve_curve) / 900000 * cf
        hp_list.append(round(hp, 2))
        torque_list.append(round((hp * 7127) / r, 2))
    return rpms, hp_list, torque_list

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏁 DRAG CONTROL")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history) + 1}")
    bore_in = st.number_input("Bore (mm)", value=data_std['bore'], step=0.1)
    v_head_in = st.number_input("Vol Head (cc)", value=data_std['v_head_std'], step=0.1)
    rpm_target = st.slider("Limit RPM", 5000, 14000, 9500)
    
    st.subheader("👤 Rider Weight")
    rider_w = st.number_input("Berat Joki (kg)", value=65)

    if st.button("🚀 RUN SIMULATION"):
        cc = (math.pi * (bore_in**2) * data_std['stroke']) / 4000
        cr = (cc + v_head_in) / v_head_in
        rpms, hps, torques = get_dyno_data(cc, data_std['stroke'], rpm_target, data_std['vva'])
        
        # Drag Calculation
        total_w = data_std['weight'] + rider_w
        t100 = simulate_drag(max(hps), total_w, 100)
        t201 = simulate_drag(max(hps), total_w, 201)
        t402 = simulate_drag(max(hps), total_w, 402)
        
        st.session_state.history.append({
            "Label": label_run, "CC": round(cc,1), "CR": round(cr,1), "Max HP": max(hps),
            "100m (s)": t100, "201m (s)": t201, "402m (s)": t402,
            "rpms": rpms, "hps": hps, "torques": torques
        })

    if st.button("🗑️ RESET ALL"):
        st.session_state.history = []
        st.rerun()

# --- 6. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa: Drag & Dyno Station")

if st.session_state.history:
    # --- DRAG TIMES TABLE ---
    st.subheader("⏱️ Drag Race Simulation Results")
    # Tampilkan tabel perbandingan waktu tempuh
    comparison_df = []
    for r in st.session_state.history:
        comparison_df.append({
            "Run": r['Label'], "CC": r['CC'], "HP": r['Max HP'], 
            "100m": r['100m (s)'], "201m": r['201m (s)'], "402m": r['402m (s)']
        })
    st.table(comparison_df)

    # --- DYNO GRAPH ---
    st.subheader("📊 Power & Torque Curve")
    fig = go.Figure()
    colors = ['#ff4b4b', '#00d4ff', '#00ff00', '#ffcc00']
    for i, run in enumerate(st.session_state.history):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Label']} (HP)", line=dict(color=color, width=4)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Label']} (Nm)", line=dict(color=color, dash='dot'), yaxis="y2"))

    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP", yaxis2=dict(overlaying="y", side="right"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ADVICE ---
    latest = st.session_state.history[-1]
    st.write("---")
    st.subheader("🧠 Tuner's Drag Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🏁 **Acceleration Note:**\n"
                f"Untuk memangkas waktu 402m, Graham Bell menyarankan fokus pada **'Mid-Range Torque'**. "
                f"Gunakan knalpot dengan diameter leher {round(math.sqrt(latest['CC']/20)*10)}mm.")
    with col2:
        st.warning(f"⚖️ **Power-to-Weight:**\n"
                   f"Setiap pengurangan 1kg berat motor/joki setara dengan kenaikan tenaga sekitar 0.15 HP pada jarak 402m.")

else:
    st.info("👈 Masukkan data motor di sidebar dan klik RUN. Bandingkan waktu 100m, 201m, dan 402m antar tiap perubahan!")
