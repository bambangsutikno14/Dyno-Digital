import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION ---
def calculate_axis_v10(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    adj_peak = float(std['peak_rpm']) + (((float(dur_in) + float(dur_out))/2.0 - 240.0) * 55.0)
    eff = 0.85 
    afr_mod = 1.0 - abs(float(afr) - 13.0) * 0.04
    thermal_penalty = 1.0 - ((cr - 14.5) * 0.15) if cr > 14.5 else 1.0
    bmep = (float(std['hp_std']) * 950000.0) / (float(cc) * adj_peak * eff)
    
    for r in rpms:
        ve = math.exp(-((r - adj_peak) / 4500.0)**2) if r <= adj_peak else math.exp(-((r - adj_peak) / 1800.0)**2)
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / float(v_in))**2) * ps_speed
        if gs_in > 110.0: ve *= (110.0 / gs_in)
        hp = (bmep * float(cc) * float(r) * ve * eff * afr_mod * thermal_penalty) / 950000.0
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
    return rpms, hps, torques, ps_speed, gs_in, ((float(bore) / float(v_out))**2) * ps_speed

# --- 4. SIDEBAR (INPUT) ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    
    st.header("2️⃣ ENGINE SIMULATION")
    raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
    in_bore = st.number_input("Bore", value=float(std['bore']), step=0.1)
    in_vhead = st.number_input("Vol Head", value=float(std['v_head']), step=0.1)
    in_rpm = st.number_input("Limit RPM", value=int(std['limit_std']), step=100)
    
    expert_on = st.toggle("🚀 Detail Expert Tuning", value=True)
    if expert_on:
        in_stroke = st.number_input("Stroke", value=float(std['stroke']), step=0.1)
        in_v_in = st.number_input("Klep In", value=float(std['valve_in']), step=0.1)
        in_v_out = st.number_input("Klep Out", value=float(std['valve_out']), step=0.1)
        in_venturi = st.number_input("Venturi", value=float(std['venturi']), step=0.5)
        in_dur_in = st.slider("Durasi In", 200, 320, 240)
        in_dur_out = st.slider("Durasi Out", 200, 320, 240)
        in_afr = st.slider("Target AFR", 11.5, 14.7, 13.0, step=0.1)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0

    cc_calc = (0.785398 * in_bore**2 * in_stroke) / 1000.0
    st.success(f"CC Motor: {cc_calc:.2f} cc")
    
    run_btn = st.button("🚀 RUN AXIS DYNO")

# --- 5. MAIN VIEW ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + in_vhead) / in_vhead
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v10(cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    pwr = (max(hps) / (std['weight_std'] + 60.0)) * 10.0
    
    st.session_state.history.append({
        "Run": f"{raw_label} {model_name}", "CC": round(cc_calc, 2), "CR": round(cr_calc, 2),
        "Max_HP": max(hps), "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed, "rpms": rpms, "hps": hps, "torques": torques,
        "bore": in_bore, "v_in": in_v_in, "v_out": in_v_out, "T201m": round(10.2/math.pow(pwr, 0.45), 2)
    })

# AGAR TIDAK HITAM KOSONG: Tampilkan pesan jika history masih kosong
if not st.session_state.history:
    st.info("👋 Selamat Datang! Silakan atur spek di Sidebar kiri dan klik tombol **RUN AXIS DYNO** untuk melihat hasil.")
else:
    latest = st.session_state.history[-1]
    
    # 📊 HASIL RINGKAS
    col1, col2, col3 = st.columns(3)
    col1.metric("Max Power", f"{latest['Max_HP']:.2f} HP")
    col2.metric("Max Torque", f"{latest['Max_Nm']:.2f} Nm")
    col3.metric("Gas Speed In", f"{latest['gsin']:.1f} m/s")

    # 📈 GRAFIK DYNO
    fig = go.Figure()
    for r in st.session_state.history:
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=r['Run']))
    fig.update_layout(template="plotly_dark", height=400, title="Power Curve Comparison")
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. AXIS EXPERT (v11.3) ---
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")

    # 1. ANALISA PERFORMA
    with st.container():
        ana_txt = f"Konfigurasi {latest['Run']} memiliki kapasitas {latest['CC']:.2f} cc. "
        
        # Logika Analisa Velocity
        if latest['gsin'] > 115:
            ana_status = "❌ **Kritis:** Terjadi *Choke Flow* (Velocity {latest['gsin']:.2f} m/s). Udara menabrak dinding porting, pengisian silinder terhenti di RPM atas."
        elif latest['gsin'] > 100:
            ana_status = "⚠️ **Peringatan:** *High Velocity* ({latest['gsin']:.2f} m/s). Karakter mesin 'Peak Power' tinggi namun nafas cepat habis."
        else:
            ana_status = "✅ **Optimal:** Aliran gas ({latest['gsin']:.2f} m/s) sangat efisien, memberikan rentang tenaga yang luas."

        # Logika Analisa CR
        if latest['CR'] > 15.0:
            cr_status = f"Serta kondisi termal **Ekstrim** (CR {latest['CR']:.2f}:1) yang beresiko fatal pada piston."
        elif latest['CR'] > 13.5:
            cr_status = f"Dengan kompresi **Tinggi** (CR {latest['CR']:.2f}:1), memerlukan manajemen panas dan BBM oktan tinggi."
        else:
            cr_status = f"Dan rasio kompresi ({latest['CR']:.2f}:1) masih dalam batas aman operasional."

        st.info(f"**1. Analisa Performa:** {ana_txt} {ana_status} {cr_status}")

    # 2. REKOMENDASI
    with st.container():
        rekom_knalpot = round(math.sqrt(latest['CC']*0.15)*10, 1)
        rekom_vhead = round(latest['CC']/12.5, 2)
        rekom_txt = f"Untuk durabilitas optimal, gunakan leher knalpot diameter **{rekom_knalpot} mm** dan target volume *Head* di angka **{rekom_vhead} cc**."
        if latest['CR'] > 13.5:
            rekom_txt += " Gunakan bahan bakar minimal RON 98 atau Avgas."
        st.warning(f"**2. Rekomendasi:** {rekom_txt}")

    # 3. SOLUSI (LIST MULTI-OPSI)
    with st.container():
        st.write("**3. Solusi (Pilihan perbaikan sesuai budget & kebutuhan):**")
        solusi_list = []
        
        # Opsi Kelistrikan & Bahan Bakar (Umum)
        if latest['CR'] > 14.5:
            solusi_list.append(f"• **Manajemen Kompresi:** Gunakan paking blok/head lebih tebal (0.5-1.0mm) atau papas dome piston {round(latest['CC']*0.01, 1)}cc.")
            solusi_list.append(f"• **Timing Cam:** Gunakan noken as dengan LSA lebih sempit/overlap tinggi untuk membuang tekanan statis berlebih.")
        
        # Opsi Mekanis Flow
        if latest['gsin'] > 105:
            solusi_list.append(f"• **Upgrade Klep:** Perbesar diameter klep IN ke {round(latest['bore']*0.55, 1)}mm untuk menurunkan hambatan udara.")
            solusi_list.append(f"• **Induksi Udara:** Reamer venturi atau ganti Throttle Body ke ukuran {round(latest['v_in']*1.15, 1)}mm.")
        
        # Opsi Tambahan jika Power di bawah standar
        if latest['Max_HP'] < (latest['CC'] * 0.12): # Simulasi mesin lemes
            solusi_list.append(f"• **Sistem Gas Buang:** Gunakan knalpot tipe *taper* (kerucut) dengan diameter awal {round(latest['v_out']*1.1, 1)}mm.")

        if not solusi_list:
            st.success("✅ **Balanced Engine:** Konfigurasi sudah harmonis. Fokus pada penyempurnaan porting polish tahap akhir (Stage 1) dan settingan AFR.")
        else:
            # Menampilkan List Solusi dengan Bullet Points
            for s in solusi_list:
                st.write(s)

# DISCLAIMER
st.write("---")
st.error("⚠️ **DISCLAIMER:** Aplikasi ini adalah simulator berbasis rumus teori mesin. Hasil nyata dapat berbeda tergantung pada kualitas pengerjaan porting, efisiensi knalpot, dan kondisi cuaca saat dyno. Gunakan hasil ini sebagai referensi riset awal.")
