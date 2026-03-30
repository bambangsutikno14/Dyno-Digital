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
        "Mio Karbu / Soul / Fino 115": {"bore": 50.0, "stroke": 57.9, "pin": 15, "v_head_std": 13.7, "klep_std": "23/19", "valve_count": 2},
        "Mio J / Soul GT 115 (FI)": {"bore": 50.0, "stroke": 57.9, "pin": 13, "v_head_std": 13.7, "klep_std": "26/21", "valve_count": 2},
        "NMAX 155 / Aerox 155 (VVA)": {"bore": 58.0, "stroke": 58.7, "pin": 14, "v_head_std": 14.6, "klep_std": "20.5/17.5 (x2)", "valve_count": 4}
    },
    "HONDA": {
        "BeAT Karbu / Scoopy Karbu": {"bore": 50.0, "stroke": 55.0, "pin": 13, "v_head_std": 13.2, "klep_std": "25.5/21", "valve_count": 2},
        "BeAT New / Genio (KOJ)": {"bore": 47.0, "stroke": 63.1, "pin": 12, "v_head_std": 12.2, "klep_std": "24/21", "valve_count": 2},
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "pin": 14, "v_head_std": 15.6, "klep_std": "29/23", "valve_count": 2}
    }
}

# --- 3. FUNGSI LOGIKA TUNING (BACKEND) ---
def hitung_geometri(bore, stroke, v_head, v_deck=0.8):
    # Kapasitas (CC)
    v_d = (math.pi * (bore**2) * stroke) / 4000
    
    # Volume Total (V2)
    # v_deck adalah volume celah piston saat TMA
    v_deck_vol = (math.pi * (bore**2) * v_deck) / 4000
    v_total = v_d + v_head + v_deck_vol
    
    # Kompresi (CR)
    cr = v_total / (v_head + v_deck_vol)
    return round(v_d, 1), round(cr, 1)

def estimasi_performa(cc_baru, stroke, rpm, bmep_base=13.0):
    # MPS (Piston Speed)
    mps = (2 * stroke * rpm) / 60000
    
    # Estimasi HP (Asumsi Ve optimal)
    hp = (bmep_base * cc_baru * rpm) / 45000
    return round(mps, 2), round(hp, 1)


# --- 4. SIDEBAR - CONTROL PANEL (INPUT) ---
with st.sidebar:
    st.markdown("<p class='big-font'>CONTROL PANEL</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Pilih Motor
    merk = st.selectbox("1. Pilih Merk Motor", list(DATABASE_MATIC.keys()))
    motor_list = list(DATABASE_MATIC[merk].keys())
    motor_nama = st.selectbox("2. Pilih Model", motor_list)
    
    # Load Data Standar
    data_std = DATABASE_MATIC[merk][motor_nama]
    
    st.info(f"💾 **Specs Std:** Bore {data_std['bore']}mm, Stroke {data_std['stroke']}mm, Klep {data_std['klep_std']}, Pin {data_std['pin']}")
    st.write("---")
    
    # Input Tuning (Bore Up)
    st.subheader("🛠️ Bore-Up Configuration")
    bore_input = st.number_input(f"Diameter Piston Baru (mm) [Std: {data_std['bore']}]", 
                                  min_value=data_std['bore'], max_value=70.0, value=data_std['bore'] + 3.0, step=0.5)
    
    st.subheader("⛽ Compression Setup")
    v_head_input = st.number_input(f"Volume Head / Buret (cc) [Std: {data_std['v_head_std']}]", 
                                    min_value=8.0, max_value=25.0, value=data_std['v_head_std'], step=0.1)
    
    st.subheader("🏎️ Engine Material")
    is_forged = st.checkbox("Menggunakan Forged Piston & Stang Racing", value=False)
    
    st.write("---")
    # Slider RPM Peak (Dinamis)
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
    
    # 5.2 BARIS 1: GAUGE ANALOG (RPM & MPS)
    c1, c2 = st.columns(2)
    
    # A. Speedometer/Tachometer RPM (ECharts)
    with c1:
        st.subheader("🔄 Engine RPM")
        option_rpm = {
            "tooltip": {"formatter": "{a} : {c}"},
            "series": [{
                "name": "RPM",
                "type": "gauge",
                "min": 0, "max": 16000,
                "splitNumber": 8,
                "progress": {"show": True, "width": 10},
                "axisLine": {"lineStyle": {"width": 10}},
                "axisTick": {"show": False},
                "splitLine": {"length": 15, "lineStyle": {"width": 2, "color": "#999"}},
                "axisLabel": {"distance": 15, "color": "#999", "fontSize": 12},
                "anchor": {"show": True, "showSize": 14, "itemStyle": {"color": "#ff4b4b"}},
                "title": {"show": False},
                "detail": {"valueAnimation": True, "formatter": "{value|{value}}\n{unit|RPM}", 
                           "offsetCenter": [0, "70%"], 
                           "rich": {"value": {"fontSize": 30, "fontWeight": "bolder", "color": "white"}, 
                                    "unit": {"fontSize": 14, "color": "#999"}}},
                "data": [{"value": rpm_input}]
            }]
        }
        st_echart(options=option_rpm, height="400px")
        
    # B. Piston Speed (MPS) Gauge - Indikator Warna
    with c2:
        st.subheader("🛹 Mean Piston Speed (MPS)")
        # Batas Warna Dinamis
        limit_green = 24.0 if is_forged else 21.0
        limit_max = 28.0 if is_forged else 25.0
        
        # Logika Warna MPS
        mps_color = "#3399ff" # Blue (Safe)
        if mps >= 16 and mps <= limit_green: mps_color = "#33cc33" # Green (Optimal)
        elif mps > limit_green and mps <= limit_max: mps_color = "#ff9900" # Orange (Risk)
        elif mps > limit_max: mps_color = "#ff3333" # Red (Danger)

        option_mps = {
            "series": [{
                "type": "gauge",
                "center": ["50%", "55%"],
                "startAngle": 200, "endAngle": -20,
                "min": 0, "max": limit_max + 2,
                "splitNumber": 7,
                "itemStyle": {"color": mps_color},
                "progress": {"show": True, "width": 15},
                "axisLine": {"lineStyle": {"width": 15}},
                "axisTick": {"distance": -20, "splitNumber": 5, "lineStyle": {"width": 2, "color": "#999"}},
                "splitLine": {"distance": -20, "length": 20, "lineStyle": {"width": 3, "color": "#999"}},
                "axisLabel": {"distance": 5, "color": "#999", "fontSize": 12},
                "detail": {"valueAnimation": True, "formatter": "{value}\nm/s", "color": "white", "fontSize": 26},
                "data": [{"value": mps}]
            }]
        }
        st_echart(options=option_mps, height="400px")


    # 5.3 BARIS 2: INDIKATOR NUMERIK (CR, CC, HP)
    st.write("---")
    st.subheader("📋 Engine Specs & Performance Output")
    k1, k2, k3, k4 = st.columns(4)
    
    # Indikator CC (Biru)
    k1.metric("Kapasitas Mesin Baru", f"{cc_baru} cc", f"+{round(cc_baru - data_std['cc_std'] if 'cc_std' in data_std else 0,1)} cc")
    
    # Indikator Kompresi (Warna)
    cr_color = "normal"
    if cr_baru > 12.5: cr_color = "off" # Merah
    elif cr_baru > 11.5: cr_color = "inverse" # Oranye
    k2.metric("Rasio Kompresi (CR)", f"{cr_baru} : 1", help="Target < 12.5 untuk Pertamax Turbo")
    
    # Indikator Klep (Informasi)
    k3.metric(f"Valve Size ({data_std['valve_count']}V)", f"{data_std['klep_std']} mm", help="Semakin besar CC, butuh klep besar")
    
    # Indikator TENAGA (POWER!)
    k4.markdown(f"### <span style='color:#ff4b4b;'>{hp} HP</span>", unsafe_allow_html=True)
    st.caption(f"Estimasi tenaga puncak pada {rpm_input} RPM")
    
    
    # 5.4 BARIS 3: EXPERT CONSULTANT (Peringatan Risiko & Solusi)
    st.write("---")
    st.subheader("🧠 MotoTuning Expert Consultant")

    # --- 6. GRAFIK KURVA PERFORMA (DYNO CHART) ---
st.write("---")
st.subheader("📈 Virtual Dyno Graph")

# Generate Data Kurva (Simulasi)
rpm_range = np.arange(4000, rpm_input + 2000, 500)
hp_curve = []
torque_curve = []

for r in rpm_range:
    # Simulasi VE (Volumetric Efficiency) yang menurun di RPM sangat tinggi
    ve_factor = math.sin(math.radians((r/rpm_input) * 90)) 
    curr_mps, curr_hp = estimasi_performa(cc_baru, data_std['stroke'], r)
    
    real_hp = curr_hp * ve_factor
    hp_curve.append(real_hp)
    # Rumus Torsi: (HP * 5252) / RPM (dalam lb-ft, lalu konversi ke Nm)
    torque_nm = (real_hp * 7127) / r if r > 0 else 0
    torque_curve.append(round(torque_nm, 2))

# Buat Grafik dengan Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(x=rpm_range, y=hp_curve, name='Power (HP)', line=dict(color='#ff4b4b', width=4)))
fig.add_trace(go.Scatter(x=rpm_range, y=torque_curve, name='Torque (Nm)', line=dict(color='#00d4ff', width=4), yaxis="y2"))

fig.update_layout(
    title="Simulasi Kurva Tenaga & Torsi",
    xaxis_title="Engine RPM",
    yaxis_title="Horsepower (HP)",
    yaxis2=dict(title="Torque (Nm)", overlaying="y", side="right"),
    template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# --- 7. MODUL CAMSHAFT (TAMBAHAN EXPERT) ---
with st.expander("📝 REKOMENDASI DURASI CAMSHAFT"):
    st.write("Berdasarkan Target RPM dan Kapasitas Mesin:")
    if rpm_input <= 9500:
        st.info("**Tipe Cam: Touring / Daily Speed**\n\n* Durasi: 250° - 260°\n* LSA: 102° - 105°\n* Karakter: Torsi padat di putaran bawah-menengah.")
    elif 9500 < rpm_input <= 11500:
        st.success("**Tipe Cam: Racing / Drag**\n\n* Durasi: 265° - 275°\n* LSA: 98° - 102°\n* Karakter: Powerband kuat di putaran tengah-atas.")
    else:
        st.error("**Tipe Cam: FFA / Extreme Racing**\n\n* Durasi: 280°++\n* LSA: < 98°\n* Karakter: Mesin hanya bertenaga di RPM sangat tinggi, idle tidak stabil.")
    # Logika Peringatan
    if mps > limit_green and not is_forged:
        st.error(f"⚠️ **BAHAYA PISTON SPEED!** MPS mencapai **{mps} m/s**. Piston & Stang seher standar akan patah!")
        st.write("✅ **Solusi:** Centang kotak 'Menggunakan Part Forged' di control panel (beli part racing) atau turunkan RPM.")
    elif mps > limit_green and is_forged:
        st.warning(f"⚠️ **RISIKO TINGGI!** MPS **{mps} m/s**. Meski sudah Forged, mesin butuh perawatan ekstra balap.")

    if cr_baru > 12.8:
        st.warning(f"⛽ **KOMPRESI TERLALU PADAT!** CR {cr_baru}:1. Potensi knocking (ngelitik) parah.")
        st.write("✅ **Solusi:** Gunakan buret head lebih besar, gunakan bensin RON 100+, atau mundurkan pengapian 2 derajat.")
        
    if hp > 18.0 and data_std['klep_std'] == "23/19": # Contoh untuk Mio
        st.success(f"🚀 **HEAD SPECS UNTUK HP TINGGI:**")
        st.write("Tenaga ini hanya tercapai jika Gas Flow (Aliran Udara) maksimal. Wajib ganti Klep besar (min 28/24) dan porting ulang.")

if btn_run:
    # Semua kode di bawah if ini HARUS menjorok masuk (1 tab atau 4 spasi)
    cc_baru, cr_baru = hitung_geometri(bore_input, data_std['stroke'], v_head_input)
    ...
    ...
#else: ini harus sejajar lurus dengan 'if btn_run' di atas
else:
    st.info("👈 Selamat Datang! Silakan atur konfigurasi...")
