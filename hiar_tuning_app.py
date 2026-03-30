import streamlit as st
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
        "Mio Karbu / Soul / Fino 115": {"bore": 50.0, "stroke": 57.9, "pin": 15, "v_head_std": 13.7, "klep_std": "23/19", "valve_count": 2},
        "Mio J / Soul GT 115 (FI)": {"bore": 50.0, "stroke": 57.9, "pin": 13, "v_head_std": 13.7, "klep_std": "26/21", "valve_count": 2},
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "pin": 14, "v_head_std": 14.6, "klep_std": "20.5/17.5", "valve_count": 4}
    },
    "HONDA": {
        "BeAT Karbu": {"bore": 50.0, "stroke": 55.0, "pin": 13, "v_head_std": 13.2, "klep_std": "25.5/21", "valve_count": 2},
        "BeAT New / Genio (KOJ)": {"bore": 47.0, "stroke": 63.1, "pin": 12, "v_head_std": 12.2, "klep_std": "24/21", "valve_count": 2},
        "Vario 150": {"bore": 57.3, "stroke": 57.9, "pin": 14, "v_head_std": 15.6, "klep_std": "29/23", "valve_count": 2}
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
    
    st.subheader("🛠️ Konfigurasi Mesin")
    bore_input = st.number_input("Diameter Piston (mm)", value=data_std['bore'] + 3.0, step=0.5)
    v_head_input = st.number_input("Volume Head / Buret (cc)", value=data_std['v_head_std'], step=0.1)
    is_forged = st.checkbox("Gunakan Part Racing (Forged)", value=False)
    
    st.subheader("🚦 Dyno Setting")
    rpm_input = st.slider("Target RPM Peak", 5000, 15000, 10000, 500)
    btn_run = st.button("RUN DYNO SIMULATION")

# --- 5. MAIN PANEL ---
st.markdown(f"## 📊 DYNO DASHBOARD: {motor_nama.upper()}")

if btn_run:
    cc_baru, cr_baru = hitung_geometri(bore_input, data_std['stroke'], v_head_input)
    mps, hp = estimasi_performa(cc_baru, data_std['stroke'], rpm_input)

    # --- SPEEDOMETER ANALOG (VERSI PLOTLY) ---
    c1, c2 = st.columns(2)
    
    with c1:
        fig_rpm = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = rpm_input,
            title = {'text': "Engine RPM", 'font': {'family': "Orbitron", 'size': 24}},
            gauge = {
                'axis': {'range': [None, 15000], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#ff4b4b"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 9000], 'color': 'rgba(0, 255, 0, 0.1)'},
                    {'range': [9000, 12000], 'color': 'rgba(255, 165, 0, 0.2)'},
                    {'range': [12000, 15000], 'color': 'rgba(255, 0, 0, 0.3)'}],
            }
        ))
        fig_rpm.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"}, height=350)
        st.plotly_chart(fig_rpm, use_container_width=True)

    with c2:
        limit_green = 24.0 if is_forged else 21.0
        fig_mps = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = mps,
            title = {'text': "Piston Speed (m/s)", 'font': {'family': "Orbitron", 'size': 24}},
            gauge = {
                'axis': {'range': [None, 30], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#33cc33" if mps <= limit_green else "#ff3333"},
                'steps': [
                    {'range': [0, 16], 'color': "#3399ff"},
                    {'range': [16, limit_green], 'color': "#33cc33"},
                    {'range': [limit_green, 30], 'color': "#ff3333"}],
            }
        ))
        fig_mps.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=350)
        st.plotly_chart(fig_mps, use_container_width=True)

    # METRICS & GRAPH (Sama seperti sebelumnya)
    st.write("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kapasitas", f"{cc_baru} cc")
    k2.metric("Kompresi", f"{cr_baru}:1")
    k3.metric("Klep Standar", data_std['klep_std'])
    k4.metric("Est. Tenaga", f"{hp} HP")

    # GRAFIK KURVA
    st.subheader("📈 Virtual Dyno Graph")
    rpms = np.arange(4000, rpm_input + 2000, 500)
    hps = [estimasi_performa(cc_baru, data_std['stroke'], r)[1] * math.sin(math.radians(min((r/rpm_input)*90, 105))) for r in rpms]
    fig_curve = go.Figure(data=go.Scatter(x=rpms, y=hps, name="Power", line=dict(color='#ff4b4b', width=4), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.1)'))
    fig_curve.update_layout(template="plotly_dark", xaxis_title="Engine RPM", yaxis_title="Horsepower (HP)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_curve, use_container_width=True)

    # ADVICE AREA
    st.write("---")
    if mps > limit_green:
        st.error(f"⚠️ **RISIKO KRITIKAL:** Piston speed {mps} m/s melampaui batas aman material!")
    if cr_baru > 13.0:
        st.warning(f"⛽ **HIGH COMPRESSION:** Rasio {cr_baru}:1 butuh bahan bakar oktan tinggi (RON 100+).")
    
    with st.expander("📝 ANALISIS CAMSHAFT & HEAD"):
        if rpm_input > 10500:
            st.success("Saran: Gunakan klep lebar & per klep jepang untuk mencegah valve float.")
        else:
            st.info("Saran: Porting polish harian sudah cukup untuk target ini.")

else:
    st.info("👈 Pilih motor dan atur bore-up di panel kiri, lalu klik RUN SIMULATION")
