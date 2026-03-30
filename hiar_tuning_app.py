import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE ---
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

# --- 4. LOGIKA DRAG SIMULATION ---
def simulate_drag(hp, weight_total, distance):
    watts = hp * 746 * 0.85 
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
        
        total_w = data_std['weight'] + rider_w
        t100 = simulate_drag(max(hps), total_w, 100)
        t201 = simulate_drag(max(hps), total_w, 201)
        t402 = simulate_drag(max(hps), total_w, 402)
        
        st.session_state.history.append({
            "Label": label_run, "CC": cc, "HP": max(hps),
            "100m": t100, "201m": t201, "402m": t402,
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
    
    # Membuat DataFrame untuk tampilan tabel yang rapi
    df = pd.DataFrame(st.session_state.history)
    # Memilih kolom yang ingin ditampilkan saja
    display_df = df[["Label", "CC", "HP", "100m", "201m", "402m"]]
    
    # Styling Tabel: Rata Tengah dan 2 Desimal
    st.dataframe(
        display_df,
        column_config={
            "Label": st.column_config.TextColumn("Run", width="medium"),
            "CC": st.column_config.NumberColumn("Kapasitas (cc)", format="%.2f"),
            "HP": st.column_config.NumberColumn("Tenaga (HP)", format="%.2f"),
            "100m": st.column_config.NumberColumn("100m (s)", format="%.2f"),
            "201m": st.column_config.NumberColumn("201m (s)", format="%.2f"),
            "402m": st.column_config.NumberColumn("402m (s)", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

    # --- DYNO GRAPH ---
    st.subheader("📊 Power & Torque Curve")
    fig = go.Figure()
    colors = ['#ff4b4b', '#00d4ff', '#00ff00', '#ffcc00']
    for i, run in enumerate(st.session_state.history):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Label']} (HP)", line=dict(color=color, width=4)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Label']} (Nm)", line=dict(color=color, dash='dot'), yaxis="y2"))

    fig.update_layout(
        template="plotly_dark", 
        xaxis_title="RPM", 
        yaxis_title="HP", 
        yaxis2=dict(title="Torque (Nm)", overlaying="y", side="right"), 
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ADVICE ---
    latest = st.session_state.history[-1]
    st.write("---")
    st.subheader("🧠 Tuner's Drag Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🏁 **Acceleration Note:**\n\n"
                f"Untuk memangkas waktu 402m, Graham Bell menyarankan fokus pada **'Mid-Range Torque'**. "
                f"Gunakan knalpot dengan diameter leher **{round(math.sqrt(latest['CC']/20)*10, 1)}mm**.")
    with col2:
        st.warning(f"⚖️ **Power-to-Weight:**\n\n"
                   f"Setiap pengurangan 1kg berat motor/joki setara dengan kenaikan tenaga sekitar **0.15 HP** pada jarak 402m.")

else:
    st.info("👈 Masukkan data motor di sidebar dan klik RUN. Bandingkan waktu 100m, 201m, dan 402m antar tiap perubahan!")
