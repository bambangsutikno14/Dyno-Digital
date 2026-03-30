import streamlit as st
from streamlit_echarts import st_echart
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE & TEMA ---
st.set_page_config(page_title="MotoTuning Master | Dyno Simulator", layout="wide", page_icon="🏍️")

# Custom CSS untuk tema gelap & font racing
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap');
    .big-font { font-family: 'Orbitron', sans-serif; font-size: 26px !important; color: #ff4b4b; }
    .stApp { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)


# --- 2. DATABASE MASTER (MATIK TAHAP 1) ---
DATABASE_MATIC = {
    "YAMAHA": {
        "Mio Karbu / Soul / Fino 115": {"bore": 50.0, "stroke": 57.9, "pin": 15, "v_head_std": 13.7, "klep_std": "23/19", "valve_count": 2, "cc_std": 113.7},
        "Mio J / Soul GT 115 (FI)": {"bore": 50.0, "stroke": 57.9, "pin": 13, "v_head_std": 13.7, "klep_std": "26/21", "valve_count": 2, "cc_std": 113.7},
        "Mio M3 / Soul GT 125 (Bluecore)": {"bore": 52.4, "stroke": 57.9, "pin": 13, "v_head_std": 14.7, "klep_std": "26/21", "valve_count": 2, "cc_std": 124.8},
        "NMAX 155 / Aerox 155 (VVA)": {"bore": 58.0, "stroke": 58.7, "pin": 14, "v_head_std": 14.6, "klep_std": "20.5/17.5 (x2)", "valve_count": 4, "cc_std": 155.1}
    },
    "HONDA": {
        "BeAT Karbu / Scoopy Karbu": {"bore": 50.0, "stroke": 55.0, "pin": 13, "v_head_std": 13.2, "klep_std": "25.5/21", "valve_count": 2, "cc_std": 108.0},
        "BeAT New / Genio (KOJ)": {"bore": 47.0, "stroke": 63.1, "pin": 12, "v_head_std": 12.2, "klep_std": "24/21", "valve_count": 2, "cc_std": 109.5},
        "Vario 125": {"bore": 52.4, "stroke": 57.9, "pin": 13, "v_head_std": 12.5, "klep_std": "27/22", "valve_count": 2, "cc_std": 124.8},
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "pin": 14, "v_head_std": 15.6, "klep_std": "29/23", "valve_count": 2, "cc_std": 149.3}
    }
}

# --- 3. FUNGSI LOGIKA TUNING (BACKEND) ---
def hitung_geometri(bore, stroke, v_head, v_deck=0.8):
    v_d = (math.pi * (bore**2) * stroke) / 4000
    v_deck_vol = (math.pi * (bore**2) * v_deck) / 4000
    v_total = v_d + v_head + v_deck_vol
    cr = v_total / (v_head + v_deck_vol)
    return round(v_d, 1), round(cr, 1)

def estimasi_performa(cc_baru, stroke, rpm, bmep_base=13.0):
    mps = (2 * stroke * rpm) / 60000
    hp = (bmep_base * cc_baru * rpm) / 45000
    return round(mps, 2), round(hp, 1)


# --- 4. SIDEBAR - CONTROL PANEL (INPUT) ---
with st.sidebar:
    st.markdown("<p class='big-font'>CONTROL PANEL</p>", unsafe_allow_html=True)
    st.write("---")
    
    merk = st.selectbox("1. Pilih Merk Motor", list(DATABASE_MATIC.keys()))
    motor_list = list(DATABASE_MATIC[merk].keys())
    motor_nama = st.selectbox("2. Pilih Model", motor_list)
    
    data_std = DATABASE_MATIC[merk][motor_nama]
    
    st.info(f"💾 **Specs Std:** Bore {data_std['bore']}mm, Stroke {data_std['stroke']}mm, Klep {data_std['klep_std']}, Pin {data_std['pin']}")
    st.write("---")
    
    st.subheader("🛠️ Bore-Up Configuration")
    bore_input = st.number_input(f"Diameter Piston Baru (mm)", 
                                  min_value=data_std['bore'], max_value=70.0, value=data_std['bore'] + 3.0, step=0.5)
    
    st.subheader("⛽ Compression Setup")
    v_head_input = st.number_input(f"Volume Head / Buret (cc)", 
                                    min_value=8.0, max_value=25.0, value=data_std['v_head_std'], step=0.1)
    
    st.subheader("🏎️ Engine Material")
    is_forged = st.checkbox("Menggunakan Forged Piston & Stang Racing", value=False)
    
    st.write("---")
    st.subheader("🚦 Dyno Run Setting")
    rpm_input = st.slider("Target RPM Maksimal", min_value=5000, max_value=16000, value=10000, step=500)
    
    st.write("---")
    btn_run = st.button("RUN DYNO SIMULATION")


# --- 5. MAIN PANEL - DIGITAL DYNO (OUTPUT) ---
st.markdown(f"## 📊 DIGITAL DYNO DASHBOARD: <span style='color:#ff4b4b;'>{motor_nama.upper()}</span>", unsafe_allow_html=True)

if btn_run:
    # 5.1 Hitung Data
    cc_baru, cr_baru = hitung_geometri(bore_input, data_std['stroke'], v_head_input)
    mps, hp = estimasi_performa(cc_baru, data_std['stroke'], rpm_input)
    
    # 5.2 GAUGE ANALOG
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔄 Engine RPM")
        option_rpm = {
            "series": [{
                "type": "gauge", "min": 0, "max": 16000, "splitNumber": 8,
                "detail": {"formatter": "{value} RPM", "color": "white", "fontSize": 20},
                "data": [{"value": rpm_input}],
                "axisLine": {"lineStyle": {"width": 10, "color": [[0.7, '#33cc33'], [0.85, '#ff9900'], [1, '#ff3333']]}}
            }]
        }
        st_echart(options=option_rpm, height="350px")
        
    with c2:
        st.subheader("🛹 Piston Speed (MPS)")
        limit_green = 24.0 if is_forged else 21.0
        limit_max = 28.0 if is_forged else 25.0
        mps_color = "#33cc33" if mps <= limit_green else "#ff3333"
        
        option_mps = {
            "series": [{
                "type": "gauge", "min": 0, "max": 30,
                "detail": {"formatter": "{value} m/s", "color": mps_color, "fontSize": 20},
                "data": [{"value": mps}],
                "itemStyle": {"color": mps_color}
            }]
        }
        st_echart(options=option_mps, height="350px")

    # 5.3 INDICATORS
    st.write("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kapasitas Mesin", f"{cc_baru} cc")
    k2.metric("Rasio Kompresi", f"{cr_baru} : 1")
    k3.metric("Valve Size", f"{data_std['klep_std']}")
    k4.metric("Est. Power", f"{hp} HP")

    # 5.4 GRAFIK KURVA PERFORMA
    st.write("---")
    st.subheader("📈 Virtual Dyno Graph")
    rpm_range = np.arange(4000, rpm_input + 1500, 500)
    hp_curve = []
    torque_curve = []
    for r in rpm_range:
        ve_factor = math.sin(math.radians(min((r/rpm_input) * 90, 110)))
        _, curr_hp = estimasi_performa(cc_baru, data_std['stroke'], r)
        real_hp = curr_hp * ve_factor
        hp_curve.append(real_hp)
        torque_nm = (real_hp * 7127) / r if r > 0 else 0
        torque_curve.append(round(torque_nm, 2))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rpm_range, y=hp_curve, name='Power (HP)', line=dict(color='#ff4b4b', width=4)))
    fig.add_trace(go.Scatter(x=rpm_range, y=torque_curve, name='Torque (Nm)', line=dict(color='#00d4ff', width=4), yaxis="y2"))
    fig.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

    # 5.5 EXPERT CONSULTANT
    st.write("---")
    st.subheader("🧠 Expert Consultant")
    if mps > limit_green:
        st.error(f"⚠️ **LIMIT MATERIAL!** MPS {mps} m/s terlalu tinggi.")
    if cr_baru > 12.8:
        st.warning(f"⛽ **DETONASI!** Kompresi {cr_baru}:1 butuh bahan bakar racing.")
    
    with st.expander("📝 REKOMENDASI CAMSHAFT"):
        if rpm_input <= 9500: st.info("Cam Touring (Durasi 255-260)")
        else: st.success("Cam Racing (Durasi 270++)")

else:
    st.info("👈 Silakan atur konfigurasi di Sidebar lalu klik RUN DYNO")
