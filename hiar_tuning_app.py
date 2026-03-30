import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. DATABASE ---
DATABASE_MATIC = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "klep_in_std": 23.0},
        "NMAX 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "klep_in_std": 20.5}
    },
    "HONDA": {
        "BeAT Karbu": {"bore": 50.0, "stroke": 55.0, "v_head_std": 13.2, "klep_in_std": 25.5},
        "Vario 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "klep_in_std": 29.0}
    }
}

# --- 3. LOGIKA ENGINE ---
def hitung_performa_rasional(cc, stroke, rpm, ve=0.82):
    bmep = 9.2 
    hp = (bmep * cc * rpm * ve) / 900000
    mps = (2 * stroke * rpm) / 60000
    return round(hp, 1), round(mps, 2)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ENGINE CONFIG")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    bore_in = st.number_input("Diameter Piston (mm)", value=data['bore'] + 3.0, step=0.5)
    v_head_in = st.number_input("Volume Head (cc)", value=data['v_head_std'], step=0.1)
    rpm_target = st.slider("Target Peak RPM", 6000, 12000, 9500, 500)
    
    btn = st.button("GENERATE DYNO REPORT")

# --- 5. MAIN PANEL ---
st.title("🏁 Digital Dyno Analysis Report")

if btn:
    # Kalkulasi Dasar
    cc = (math.pi * (bore_in**2) * data['stroke']) / 4000
    cr = (cc + v_head_in) / v_head_in
    hp, mps = hitung_performa_rasional(cc, data['stroke'], rpm_target)
    
    # --- SECTION A: METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kapasitas", f"{round(cc,1)} cc")
    c2.metric("Rasio Kompresi", f"{round(cr,1)}:1")
    c3.metric("Max Power", f"{hp} HP")
    c4.metric("Piston Speed", f"{mps} m/s")

    # --- SECTION B: GRAPH ---
    st.write("---")
    rpms = np.arange(4000, rpm_target + 2000, 500)
    powers = [hitung_performa_rasional(cc, data['stroke'], r, ve=0.85 if r <= rpm_target else 0.70)[0] for r in rpms]
    fig = go.Figure(go.Scatter(x=rpms, y=powers, fill='tozeroy', name='Power', line=dict(color='#ff4b4b', width=4)))
    fig.update_layout(template="plotly_dark", title="Power Curve Projection", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- SECTION C: TUNER RECOMMENDATION (MAIN PANEL) ---
    st.subheader("🛠️ Setup Recommendation (Expert Advice)")
    
    # Logika Dinamis Berdasarkan Target HP
    if hp < 10:
        advice_level = "Daily Refresh (Kirian + Bore Up Tipis)"
        cam_spec = "Standar / Custom Harian (250°)"
    elif 10 <= hp <= 15:
        advice_level = "Touring / Harian Speed"
        cam_spec = "Noken As Racing Tahap 1 (255°-265°)"
    else:
        advice_level = "Racing / FFA Style"
        cam_spec = "Noken As Racing Tahap 2 (270°++)"

    # Tampilan Panel Penjelasan
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.info(f"📋 **Kategori Mesin:** {advice_level}")
        st.markdown(f"""
        **1. Mekanisme Katup (Valvetrain):**
        * **Noken As:** Gunakan {cam_spec}.
        * **Klep:** {'Standar cukup' if cc < 130 else 'Wajib naik ukuran klep (minimal 28/24)'}.
        * **Per Klep:** Disarankan ganti per klep kompetisi (misal: Swedia/Japan) untuk mencegah floating di {rpm_target} RPM.
        """)
        
    with col_b:
        # Kalkulasi TB/Karbu Otomatis
        tb_size = math.sqrt(0.85 * (cc * rpm_target) / 3000)
        st.warning(f"🔋 **Sektor Udara & Bahan Bakar:**")
        st.markdown(f"""
        * **Induksi:** Gunakan Throttle Body/Karbu ukuran **{round(tb_size)} mm**.
        * **Knalpot:** Header diameter dalam **{round(math.sqrt(cc/20)*10)} mm**.
        * **BBM:** {'RON 92 (Pertamax)' if cr < 12 else 'RON 98 (Pertamax Turbo)'}.
        """)

    # Safety Warning
    if mps > 21:
        st.error(f"🚨 **WARNING:** Piston speed {mps} m/s sangat berisiko untuk stang seher standar. Wajib gunakan material Forged!")

else:
    # Tampilan awal saat belum klik RUN
    st.info("👈 Silakan atur spesifikasi mesin di panel kiri dan klik 'GENERATE DYNO REPORT'")
    st.write("---")
    st.write("### Simulasi ini akan memberikan:")
    st.write("* ✅ Estimasi Horsepower & Torsi")
    st.write("* ✅ Analisis Rasio Kompresi")
    st.write("* ✅ Rekomendasi Part (Klep, Noken As, Karburator/TB)")
