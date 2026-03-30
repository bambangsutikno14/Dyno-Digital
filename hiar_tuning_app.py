import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide", page_icon="🏍️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap');
    .big-font { font-family: 'Orbitron', sans-serif; font-size: 26px !important; color: #ff4b4b; text-align: center; }
    .stApp { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MASTER (ADVANCED) ---
DATABASE_MATIC = {
    "YAMAHA": {
        "Mio Karbu / Soul / Fino 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "klep_in": 23.0, "klep_ex": 19.0, "count": 2},
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "klep_in": 20.5, "klep_ex": 17.5, "count": 4}
    },
    "HONDA": {
        "BeAT Karbu / Scoopy": {"bore": 50.0, "stroke": 55.0, "v_head_std": 13.2, "klep_in": 25.5, "klep_ex": 21.0, "count": 2},
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "klep_in": 29.0, "klep_ex": 23.0, "count": 2}
    }
}

# --- 3. LOGIKA ENGINE (EXPERT) ---
def kalkulasi_mesin(bore, stroke, v_head, klep_in, n_valve):
    v_d = (math.pi * (bore**2) * stroke) / 4000
    cr = (v_d + v_head) / v_head
    
    # Menghitung Gas Speed (Idealnya < 100 m/s untuk efisiensi puncak)
    area_klep = (math.pi * (klep_in**2) / 4) * (n_valve/2)
    return round(v_d, 1), round(cr, 2), area_klep

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<p class='big-font'>EXPERT PANEL</p>", unsafe_allow_html=True)
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data = DATABASE_MATIC[merk][motor]
    
    st.subheader("🛠️ Bore & Head Setup")
    bore_in = st.number_input("Diameter Piston (mm)", value=data['bore'] + 3.0, step=0.5)
    v_head_in = st.number_input("Volume Buret Head (cc)", value=data['v_head_std'], step=0.1)
    
    st.subheader("🏁 Valve & Flow")
    klep_custom = st.number_input("Ukuran Klep In (mm)", value=data['klep_in'], step=0.5)
    is_forged = st.checkbox("Gunakan Forged Piston", value=True)
    
    st.subheader("🚦 Dyno Target")
    rpm_in = st.slider("Target Peak RPM", 6000, 15000, 10500, 500)
    btn = st.button("RUN ADVANCED DYNO")

# --- 5. MAIN DASHBOARD ---
if btn:
    cc, cr, area = kalkulasi_mesin(bore_in, data['stroke'], v_head_in, klep_custom, data['count'])
    mps = (2 * data['stroke'] * rpm_in) / 60000
    
    # Rumus HP Estimasi berdasarkan Volumetric Efficiency (VE)
    # Semakin kecil klep dibanding CC, VE semakin turun di RPM tinggi
    ve_ratio = (area / cc) * 100 
    hp = (cc * rpm_in * 13.2) / 45000 * (min(ve_ratio, 12)/12)

    # VISUAL 1: SPEEDOMETER & MPS GAUGE
    c1, c2 = st.columns(2)
    with c1:
        fig_rpm = go.Figure(go.Indicator(mode="gauge+number", value=rpm_in, title={'text': "Engine RPM"},
                  gauge={'axis': {'range': [None, 15000]}, 'bar': {'color': "#ff4b4b"}}))
        st.plotly_chart(fig_rpm, use_container_width=True)
    with c2:
        limit = 24 if is_forged else 21
        fig_mps = go.Figure(go.Indicator(mode="gauge+number", value=mps, title={'text': "Piston Speed (m/s)"},
                  gauge={'axis': {'range': [None, 30]}, 'bar': {'color': "green" if mps < limit else "red"}}))
        st.plotly_chart(fig_mps, use_container_width=True)

    # VISUAL 2: EXPERT METRICS
    st.write("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kapasitas", f"{cc} cc")
    m2.metric("Compression", f"{cr}:1")
    m3.metric("Flow Area", f"{round(area,1)} mm²")
    m4.metric("Est. Power", f"{round(hp,1)} HP")

    # VISUAL 3: POWER CURVE
    st.subheader("📈 Horsepower & Torque Projection")
    rpms = np.arange(4000, rpm_in + 2500, 500)
    curve = [((cc * r * 13.2)/45000) * math.sin(math.radians(min((r/rpm_in)*90, 105))) for r in rpms]
    fig_curve = go.Figure(go.Scatter(x=rpms, y=curve, fill='tozeroy', line=dict(color='red', width=3)))
    fig_curve.update_layout(template="plotly_dark", xaxis_title="RPM", yaxis_title="HP")
    st.plotly_chart(fig_curve, use_container_width=True)

    # --- 6. TUNER ADVISORY SYSTEM ---
    st.write("---")
    st.subheader("🧠 Tuner's Advisory")
    col_a, col_b = st.columns(2)
    
    with col_a:
        if cr > 13.0:
            st.error("🚨 **KOMPRESI EKSTREM:** Butuh Avgas / Racing Fuel untuk mencegah knocking.")
        elif cr > 11.5:
            st.warning("⛽ **OKTAN TINGGI:** Wajib Pertamax Turbo.")
        else:
            st.success("✅ **AMAN:** Bisa menggunakan Pertamax (RON 92).")
            
    with col_b:
        gas_speed = (cc * rpm_in) / (area * 300) # Simplified Gas Speed index
        if gas_speed > 110:
            st.error(f"🌬️ **CHOKING:** Ukuran klep {klep_custom}mm terlalu kecil untuk {cc}cc. Tenaga akan 'ngempos' di RPM tinggi.")
        else:
            st.success("🌪️ **FLOW IDEAL:** Ukuran klep sudah proporsional dengan kapasitas mesin.")

else:
    st.info("👈 Selamat datang di Markas Tuning. Masukkan spesifikasi mesin di kiri untuk memulai simulasi.")
