import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. DATABASE PABRIKAN (Data Akurat) ---
DATABASE_MATIC = {
    "YAMAHA": {
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "vva": True, "weight": 127, "bmep_std": 8.5},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "vva": False, "weight": 94, "bmep_std": 7.2},
    },
    "HONDA": {
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "vva": False, "weight": 112, "bmep_std": 8.2},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head_std": 12.7, "vva": False, "weight": 90, "bmep_std": 7.0},
    }
}

# --- 4. LOGIKA ENGINE ---
def get_dyno_data(cc, stroke, rpm_limit, vva, bmep_ref, temp=25):
    # Koreksi udara standar SAE
    cf = (1.18 * (((temp + 273) / 298) * math.sqrt(298 / (temp + 273)))) - 0.18
    cf = 1/cf
    
    rpms = np.arange(4000, rpm_limit + 500, 250)
    hp_list = []
    torque_list = []
    
    for r in rpms:
        # VE kurva menyesuaikan karakteristik mesin standar
        ve = 0.88 if vva and r > 6000 else 0.82
        ve_curve = ve * math.cos(math.radians((r - (rpm_limit*0.7)) / (rpm_limit*0.5) * 45))
        
        # Rumus HP dengan BMEP yang disesuaikan ke data pabrikan
        hp = (bmep_ref * cc * r * ve_curve) / 900000 * cf
        hp_list.append(round(hp, 2))
        torque_list.append(round((hp * 7127) / r, 2) if r > 0 else 0)
        
    return rpms, hp_list, torque_list

def simulate_drag(hp, weight_total, distance):
    watts = hp * 746 * 0.82 # 0.82 efisiensi CVT standar
    time = ( (4.5 * weight_total * (distance**2)) / watts )**(1/3)
    return round(time, 2)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🏁 TUNING CONTROL")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history) + 1}")
    bore_in = st.number_input("Bore (mm)", value=data_std['bore'], step=0.1)
    v_head_in = st.number_input("Vol Head (cc)", value=data_std['v_head_std'], step=0.1)
    rpm_target = st.slider("Limit RPM", 5000, 14000, 8500 if "Mio" in motor else 9500)
    
    rider_w = st.number_input("Berat Joki (kg)", value=65)

    if st.button("🚀 RUN SIMULATION"):
        cc = (math.pi * (bore_in**2) * data_std['stroke']) / 4000
        # Jika Bore standar, gunakan BMEP standar. Jika Bore-up, BMEP naik sedikit (asumsi porting/kompresi)
        current_bmep = data_std['bmep_std'] if bore_in <= data_std['bore'] else data_std['bmep_std'] + 0.5
        
        rpms, hps, torques = get_dyno_data(cc, data_std['stroke'], rpm_target, data_std['vva'], current_bmep)
        
        total_w = data_std['weight'] + rider_w
        st.session_state.history.append({
            "Label": label_run, "CC": cc, "HP": max(hps),
            "100m": simulate_drag(max(hps), total_w, 100),
            "201m": simulate_drag(max(hps), total_w, 201),
            "402m": simulate_drag(max(hps), total_w, 402),
            "rpms": rpms, "hps": hps, "torques": torques
        })

    if st.button("🗑️ RESET"):
        st.session_state.history = []
        st.rerun()

# --- 6. MAIN PANEL ---
st.title("📟 Hiar Lima Pendawa Tuning")

if st.session_state.history:
    st.subheader("⏱️ Drag & Performance Result")
    
    # FORMAT TABEL: Rata tengah (default streamlit) & 2 Desimal
    df = pd.DataFrame(st.session_state.history)
    display_df = df[["Label", "CC", "HP", "100m", "201m", "402m"]]
    
    st.dataframe(
        display_df,
        column_config={
            "CC": st.column_config.NumberColumn("Kapasitas", format="%.2f"),
            "HP": st.column_config.NumberColumn("Tenaga (HP)", format="%.2f"),
            "100m": st.column_config.NumberColumn("100m (s)", format="%.2f"),
            "201m": st.column_config.NumberColumn("201m (s)", format="%.2f"),
            "402m": st.column_config.NumberColumn("402m (s)", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

    # --- GRAPH ---
    fig = go.Figure()
    colors = ['#ff4b4b', '#00d4ff', '#00ff00', '#ffcc00']
    for i, run in enumerate(st.session_state.history):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['hps'], name=f"{run['Label']} HP", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=run['rpms'], y=run['torques'], name=f"{run['Label']} Nm", line=dict(color=color, dash='dot'), yaxis="y2"))

    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP", 
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Input data dan klik RUN untuk melihat hasil berdasarkan spesifikasi pabrikan.")
