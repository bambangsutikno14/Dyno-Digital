import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETTING PAGE (Widescreen) ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# Custom CSS untuk menengahkan tabel dan merapikan tampilan
st.markdown("""
<style>
    th, td { text-align: center !important; }
    div[data-testid="stDataFrame"] div[class^="st-"] { justify-content: center; }
    .stNumberInput, .stSlider { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 2. DATABASE PABRIKAN (VERIFIED) ---
# Data Mio dimodifikasi dikit agar PS pas di 8.9 sesuai request sebelumnya
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve": 23.0, "venturi": 24, "ps_std": 8.9, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve": 20.5, "venturi": 28, "ps_std": 15.3, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve": 29.0, "venturi": 26, "ps_std": 13.1, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve": 22.0, "venturi": 22, "ps_std": 8.68, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89, "f_ratio": 3.20},
    }
}

# --- 3. CORE LOGIC (CALIBRATED & DROP-OFF TAJAM) ---
def calculate_advanced_engine(cc, bore, stroke, cr, rpm_limit, valve_in, venturi, durasi, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    pss, torques = [], []
    
    # Graham Bell: Power shift based on duration
    # Setiap kenaikan 10 derajat durasi dari std (asumsi 240), peak RPM naik 500
    peak_shift = (durasi - 240) * 50
    adjusted_peak = std['peak_rpm'] + peak_shift
    
    target_hp = std['ps_std'] * 0.986
    # Faktor efisiensi untuk mengunci angka pabrikan (Mio/Beat diset lebih rendah)
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    bmep_lock = (target_hp * 950000) / (cc * adjusted_peak * eff)
    
    for r in rpms:
        # Kurva Nafas (Turun tajam setelah peak seperti image_4.png)
        if r <= adjusted_peak:
            ve = math.exp(-((r - adjusted_peak) / 4500)**2)
        else:
            # Drop off lebih ekstrim di RPM tinggi
            ve = math.exp(-((r - adjusted_peak) / 1600)**2) 
        
        ps_speed = (2 * stroke * r) / 60000
        gs = ((bore / valve_in)**2) * ps_speed
        if gs > 105: ve *= (105 / gs) # Faktor tercekik Graham Bell
        
        hp_val = (bmep_lock * cc * r * ve * eff) / 950000
        # Multiplier modifikasi (diperhalus)
        if bore > std['bore']: hp_val *= (1 + (cr - 9.5) * 0.021)
        if venturi > std['venturi']: hp_val *= (1 + (venturi - std['venturi']) * 0.011)
            
        final_ps = round(hp_val / 0.986, 2)
        pss.append(final_ps)
        
        # Torsi (Round ke 2 desimal)
        final_trq = round((hp_val * 7127) / r if r > 0 else 0, 2)
        torques.append(final_trq)
        
    return rpms, pss, torques

# --- 4. SIDEBAR (3 PANELS: CONFIG, ENGINE, DRAG) ---
with st.sidebar:
    # PANEL 1: MOTOR CONFIG
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model]
    
    st.divider()
    
    # PANEL 2: ENGINE SIMULATION
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        label_run = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=std['bore'], step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=std['v_head'], step=0.1)
        in_valve = st.number_input(f"Klep In (std: {std['valve']})", value=std['valve'], step=0.1)
        in_venturi = st.number_input(f"Venturi (std: {std['venturi']})", value=float(std['venturi']), step=1.0)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)

    # TOGGLE UNTUK FITUR EXPERT
    expert_on = st.toggle("🚀 Aktifkan Perimeter Expert (Noken As & Rasio)")
    if expert_on:
        with st.expander("🧪 Perimeter Expert (Graham Bell Mode)", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=std['stroke'], step=0.1)
            in_durasi = st.slider("Durasi Noken As (In)", 200, 320, 240, step=2)
            in_lsa = st.slider("LSA Cam", 90, 120, 105, step=1)
            in_fratio = st.number_input(f"Final Gear Ratio (std: {std['f_ratio']})", value=std['f_ratio'], step=0.01)
    else:
        # Default value jika expert off
        in_stroke, in_durasi, in_lsa, in_fratio = std['stroke'], 240, 105, std['f_ratio']

    st.divider()

    # PANEL 3: DRAG SIMULATION
    st.header("3️⃣ DRAG RACE CONFIG")
    in_joki = st.number_input("Berat Joki (kg)", value=60, step=1)

    # TOMBOL ANALYZE
    run_btn = st.button("🔥 ANALYZE & RUN DYNO")
    
    st.write("---")
    
    # --- FITUR BARU: CFM FLOW BENCH CALCULATOR ---
    with st.expander("🌪️ Expert: CFM Flow Bench Calc", expanded=False):
        st.write("Prediksi Flow berdasarkan diameter klep.")
        c_klep = st.number_input("Diameter Klep In (mm)", value=in_valve if expert_on else std['valve'], step=0.1)
        c_press = st.selectbox("Test Pressure (Inches H2O)", [10, 25, 28], index=2)
        
        # Rumus dasar CFM: D^2 * sqrt(H2O) * K (Koefisien Flow efisien Graham Bell)
        cfm_pred = round((c_klep / 25.4)**2 * math.sqrt(c_press) * 128, 1)
        st.metric("Estimasi Flow (CFM)", f"{cfm_pred} CFM", f"pada {c_press}\" H2O")
        
    st.divider()

    # Logika Eksekusi
    if run_btn:
        cc = (math.pi * (in_bore**2) * in_stroke) / 4000
        cr = (cc + in_vhead) / in_vhead
        ps_m = (2 * in_stroke * in_rpm) / 60000
        gs_m = ((in_bore/in_valve)**2)*ps_m
        
        rpms, pss, torques = calculate_advanced_engine(cc, in_bore, in_stroke, cr, in_rpm, in_valve, in_venturi, in_durasi, std)
        
        max_ps = max(pss)
        # Power-to-Weight Ratio & Final Ratio Impact
        total_w = std['weight_std'] + in_joki
        pwr_factor = (max_ps / total_w) * (in_fratio / std['f_ratio'])
        
        # Estimasi waktu Drag (PWR Based)
        t100 = round(6.5 / math.pow(pwr_factor, 0.45), 2)
        t201 = round(10.2 / math.pow(pwr_factor, 0.45), 2)
        t402 = round(16.5 / math.pow(pwr_factor, 0.45), 2)

        # Simpan ke History (cc & cr bulatkan ke 2 desimal)
        st.session_state.history.append({
            "Run": f"{label_run} {model.split(' ')[0]}", "CC": round(cc, 2), "CR": round(cr, 2),
            "PS_Max": ps_m, "GS_Max": gs_m, "Max_PS": max_ps, "RPM_PS": rpms[np.argmax(pss)],
            "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
            "Joki": in_joki, "T100": t100, "T201": t201, "T402": t402,
            "rpms": rpms, "pss": pss, "torques": torques, "lsa": in_lsa, "durasi": in_durasi
        })

# --- 5. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")
st.caption("Ver 6.0 - Precision & Expert Tuning Mode")
st.warning("⚠️ **Disclaimer:** Hasil kalkulasi adalah prediksi sistem berdasarkan spesifikasi mekanis. Margin error aktual ±5%. GassPoll")

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- EXPERT SAFETY ANALYSIS (DENGAN INDIKATOR WARNA) ---
    st.subheader(f"🛡️ Safety Analysis: {latest['Run']}")
    c1, c2, c3 = st.columns(3)
    
    # Piston Speed
    with c1:
        ps = latest['PS_Max']
        color = "blue" if ps <= 18 else "green" if ps <= 21 else "red"
        st.markdown(f"### <span style='color:{color}'>Piston Speed: {ps:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Status: {'Safe (Awet Harian)' if ps<=18 else 'Optimal (Tuned)' if ps<=21 else 'Risky (Race)'}")

    # Static CR
    with c2:
        cr = latest['CR']
        color = "blue" if cr <= 11.5 else "green" if cr <= 13.0 else "red"
        st.markdown(f"### <span style='color:{color}'>Static CR: {cr:.2f}:1</span>", unsafe_allow_html=True)
        st.write(f"BBM: {'RON 92 Cukup' if cr<=11.5 else 'RON 98 Wajib' if cr<=13.0 else 'Racing Fuel Only'}")

    # Gas Speed
    with c3:
        gs = latest['GS_Max']
        color = "green" if gs <= 100 else "red"
        st.markdown(f"### <span style='color:{color}'>Gas Speed: {gs:.2f} m/s</span>", unsafe_allow_html=True)
        st.write(f"Nafas: {'Efficient (Lega)' if gs<=100 else 'Choked (Tercekik)'}")

    # --- PERFORMANCE TABLES (RATA TENGAH & 2 DESIMAL) ---
    st.write("---")
    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Power & Torque (2 Desimal)")
    st.dataframe(df[["Run", "CC", "CR", "Max_PS", "RPM_PS", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)
    
    st.write("### 🏁 Drag Simulation (Seconds)")
    st.dataframe(df[["Run", "Joki", "T100", "T201", "T402"]], hide_index=True, use_container_width=True)

    # --- GRAFIK DYNO PRO (Style Dynojet image_4.png) ---
    st.write("---")
    st.subheader("📈 Dyno Graph (Professional Mode)")
    
    # Penentuan Warna Berdasarkan Run (Gaya Dynojet: Biru, Hijau, Merah)
    colors_ps = ["#3366CC", "#109618", "#DC3912"] # Blue, Green, Red
    colors_trq = ["#99CCFF", "#99FF99", "#FF9999"] # Lighter shades for torque
    
    fig = go.Figure()
    for i, run in enumerate(st.session_state.history):
        c_idx = i % 3 # Cycle through colors
        
        # Garis Power (PS) - Garis Tebal Sesuai Foto
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['pss'], 
            name=f"{run['Run']} (PS)",
            mode='lines',
            line=dict(color=colors_ps[c_idx], width=4)
        ))
        # Tag PS Maksimal
        fig.add_annotation(x=run['RPM_PS'], y=run['Max_PS'], text=f"{run['Max_PS']} PS", showarrow=True, arrowhead=2)
        
        # Garis Torque (Nm) - Garis Putus-putus
        fig.add_trace(go.Scatter(
            x=run['rpms'], y=run['torques'], 
            name=f"{run['Run']} (Nm)", 
            line=dict(color=colors_trq[c_idx], dash='dot', width=3), 
            yaxis="y2"
        ))
        # Tag Nm Maksimal (yref="y2" agar mengacu pada sumbu kanan)
        fig.add_annotation(x=run['RPM_Nm'], y=run['Max_Nm'], text=f"{run['Max_Nm']} Nm", 
                           showarrow=True, arrowhead=2, yref="y2", ay=30)
    
    # Update Layout Grafik Meniru image_4.png (Background Hitam, Grid Abu, Legenda Kanan)
    fig.update_layout(
        template="plotly_dark", # Tema dasar gelap
        height=650, # Tinggi grafik
        paper_bgcolor="black", # Background luar hitam pekat
        plot_bgcolor="black", # Background plot hitam pekat
        xaxis=dict(title="RPM", gridcolor="#333333", zeroline=False), # Grid abu-abu gelap
        yaxis=dict(title="Power (PS)", gridcolor="#333333", side="left", range=[0, max(df['Max_PS'])*1.15]), # Sumbu PS Kiri
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", gridcolor="#333333", showgrid=False, range=[0, max(df['Max_Nm'])*1.15]), # Sumbu Nm Kanan
        legend=dict(
            orientation="v", # Vertikal
            yanchor="top", y=1.0, # Posisi atas
            xanchor="left", x=1.02, # Menempel di sebelah kanan luar grafik
            bgcolor="rgba(0,0,0,0.5)", bordercolor="white" # Background legenda transparan
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPERT ADVICE SECTION (GRAHAM BELL PRINCIPLES) ---
    st.divider()
    st.subheader("💡 Expert Advice & Solutions (Graham Bell)")
    
    # Logika Saran Pintar (AI-Based)
    advices = []
    if latest['GS_Max'] > 105:
        advices.append("**MASALAH:** Klep tercekik (Gas Speed terlalu tinggi). **SOLUSI:** Ganti ke klep lebar atau lebarkan *porting* (Porting Polish). Nafas mesin akan jauh lebih lega di RPM tinggi.")
    if latest['CR'] > 13.0:
        advices.append("**MASALAH:** Kompresi Static terlalu ekstrim untuk harian. **SOLUSI:** Gunakan paking blok bawah lebih tebal atau kubah head dilebarkan. Wajib bensol/RON 100+.")
    if latest['PS_Max'] > 21:
        advices.append("**MASALAH:** Kecepatan Piston kritis (Batas material). **SOLUSI:** Ganti kruk as/stang seher *forged* atau turunkan RPM limit untuk mencegah patah.")
    if latest['T201'] > 10.0:
        advices.append("**MASALAH:** Waktu 201m kurang tajam. **SOLUSI:** Ringankan *Roller* CVT atau per CVT diganti ke 1500 RPM untuk akselerasi awal lebih responsif.")
    if latest['lsa'] < 102:
        advices.append("**INFO LSA:** LSA sempit memberikan *Power Band* kuat di tengah, tapi nafas atas kurang panjang.")
    if latest['durasi'] > 280:
        advices.append("**INFO NOKEN:** Durasi tinggi membutuhkan *porting flow* yang besar agar tidak kempos di RPM bawah.")
    
    if advices:
        for a in advices: st.write(a)
    else:
        st.success("Konfigurasi mesin sangat harmonis dan aman untuk dijalankan!")
