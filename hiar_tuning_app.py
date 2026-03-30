import streamlit as st
from streamlit_echarts import st_echart
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE & TEMA ---
st.set_page_config(page_title="MotoTuning Master | Dyno Simulator", layout="wide", page_icon="🏍️")

# Custom CSS untuk tema gelap
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap');
    .big-font { font-family: 'Orbitron', sans-serif; font-size: 26px !important; color: #ff4b4b; }
    .stApp { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MASTER ---
DATABASE_MATIC = {
    "YAMAHA": {
        "Mio Karbu / Soul / Fino 115": {"bore": 50.0, "stroke": 57.9, "pin": 15, "v_head_std": 13.7, "klep_std": "23/19", "valve_count": 2, "cc_std": 113.7},
        "Mio J / Soul GT 115 (FI)": {"bore": 50.0, "stroke": 57.9, "pin": 13, "v_head_std": 13.7, "klep_std": "26/21", "valve_count": 2, "cc_std": 113.7},
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "pin": 14, "v_head_std": 14.6, "klep_std": "20.5/17.5", "valve_count": 4, "cc_std": 155.1}
    },
    "HONDA": {
        "BeAT Karbu": {"bore": 50.0, "stroke": 55.0, "pin": 13, "v_head_std": 13.2, "klep_std": "25.5/21", "valve_count": 2, "cc_std": 108.0},
        "Vario 125": {"bore": 52.4, "stroke": 57.9, "pin": 13, "v_head_std": 12.5, "klep_std": "27/22", "valve_count": 2, "cc_std": 124.8},
        "Vario 150": {"bore": 57.3, "stroke": 57.9, "pin": 14, "v_head_std": 15.6, "klep_std": "29/23", "valve_count": 2, "cc_std": 149.3}
    }
}

# --- 3. LOGIKA TUNING ---
def hitung_geometri(bore, stroke, v_head, v_deck=0.8):
    v_d = (math.pi * (bore**2) * stroke) / 4000
    v_deck_vol = (math.pi * (bore**2) * v_deck) / 4000
    v_total = v_d + v_head + v_deck_vol
    cr = v_total / (v_head + v_deck_vol)
    return round(v_d, 1), round(cr, 1)

def estimasi_performa(cc_baru, stroke, rpm, bmep_base=13.5):
    mps = (2 * stroke * rpm) / 60000
    hp = (bmep_base * cc_baru * rpm) / 45000
    return round(mps, 2), round(hp, 1)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<p class='big-font'>CONTROL PANEL</p>", unsafe_allow_html=True)
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor_nama = st.selectbox("Pilih Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor_nama]
    
    st.subheader("🛠️ Bore-Up")
    bore_input = st.number_input("Diameter Piston (mm)", value=data_std['bore'] + 3.0, step=0.5)
    v_head_input = st.number_input("Volume Head (cc)", value=data_std['v_head_std'], step=0.1)
    is_forged = st.checkbox("Gunakan Part Racing (Forged)", value=False)
    
    st.subheader("🚦 Dyno Setting")
    rpm_input = st.slider("Target RPM Peak", 5000, 15000, 10000, 500)
    btn_run = st.button("RUN DYNO SIMULATION")

# --- 5. MAIN PANEL ---
st.markdown(f"## 📊 DYNO DASHBOARD: {motor_nama.upper()}")

if btn_run:
    cc_baru, cr_baru = hitung_geometri(bore_input, data_std['stroke'], v_head_input)
    mps, hp = estimasi_performa(cc_baru, data_std['stroke'], rpm_input)

    # GAUGE ANALOG
    c1, c2 = st.columns(2)
    with c1:
        opt_rpm = {"series": [{"type": "gauge", "min": 0, "max": 15000, "detail": {"formatter": "{value} RPM"}, "data": [{"value": rpm_input}]}]}
        st_echart(options=opt_rpm, height="350px")
    with c2:
        limit_green = 24.0 if is_forged else 21.0
        mps_color = "#33cc33" if mps <= limit_green else "#ff3333"
        opt_mps = {"series": [{"type": "gauge", "min": 0, "max": 30, "detail": {"formatter": "{value} m/s"}, "data": [{"value": mps}], "itemStyle": {"color": mps_color}}]}
        st_echart(options=opt_mps, height="350px")

    # METRICS
    st.write("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kapasitas", f"{cc_baru} cc")
    k2.metric("Kompresi", f"{cr_baru}:1")
    k3.metric("Klep", data_std['klep_std'])
    k4.metric("Tenaga", f"{hp} HP")

    # GRAFIK DYNO
    st.subheader("📈 Virtual Dyno Graph")
    rpms = np.arange(4000, rpm_input + 2000, 500)
    hps = [estimasi_performa(cc_baru, data_std['stroke'], r)[1] * math.sin(math.radians(min((r/rpm_input)*90, 105))) for r in rpms]
    fig = go.Figure(data=go.Scatter(x=rpms, y=hps, line=dict(color='#ff4b4b', width=4)))
    fig.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP")
    st.plotly_chart(fig, use_container_width=True)

    # ADVICE
    st.write("---")
    if mps > limit_green: st.error(f"⚠️ MPS {mps} m/s: Material Berisiko Patah!")
    if cr_baru > 12.8: st.warning(f"⛽ Kompresi {cr_baru}: Wajib BBM RON 100+ / Racing Fuel")

else:
    st.info("👈 Atur mesin di kiri dan tekan RUN")
