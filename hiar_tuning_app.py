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
    th, td { text-align: center !important; vertical-align: middle !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA (MATIC)": {
        "Karbu": {
            "115cc": {"Mio / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "valves": 2, "lift_std": 7.0, "dur_std": 230}},
            "125cc": {"Xeon (Carb)": {"bore": 52.4, "stroke": 57.9, "v_head": 14.5, "valve_in": 26.0, "valve_out": 21.0, "venturi": 26.0, "hp_std": 10.7, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 103.0, "valves": 2, "lift_std": 7.5, "dur_std": 235}}
        },
        "Injeksi": {
            "125cc": {"Mio Fino 125 FI": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 9.5, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 98.0, "valves": 2, "lift_std": 7.8, "dur_std": 235}},
            "155cc": {"NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "valves": 4, "lift_std": 8.2, "dur_std": 240}},
            "250cc": {"XMAX 250": {"bore": 70.0, "stroke": 64.9, "v_head": 22.5, "valve_in": 26.5, "valve_out": 22.5, "venturi": 32.0, "hp_std": 22.5, "peak_rpm": 7000, "limit_std": 9000, "weight_std": 179.0, "valves": 4, "lift_std": 8.5, "dur_std": 245}}
        }
    },
    "HONDA (MATIC)": {
        "Karbu": {
            "110cc": {
                "Beat 110 Karbu": {"bore": 50.0, "stroke": 55.0, "v_head": 11.8, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.22, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 89.0, "valves": 2, "lift_std": 7.0, "dur_std": 230},
                "Vario 110 Karbu": {"bore": 50.0, "stroke": 55.0, "v_head": 11.5, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 8.99, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 99.0, "valves": 2, "lift_std": 7.2, "dur_std": 230}
            }
        },
        "Injeksi": {
            "110cc": {"Beat 110 FI (eSP)": {"bore": 50.0, "stroke": 55.1, "v_head": 12.0, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.68, "peak_rpm": 7500, "limit_std": 9300, "weight_std": 93.0, "valves": 2, "lift_std": 7.2, "dur_std": 232}},
            "125cc": {"Vario 125 eSP": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 11.1, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 111.0, "valves": 2, "lift_std": 7.8, "dur_std": 235}},
            "150cc": {"Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "valves": 2, "lift_std": 8.0, "dur_std": 235}},
            "160cc": {"Vario 160 / PCX 160": {"bore": 60.0, "stroke": 55.5, "v_head": 12.8, "valve_in": 23.0, "valve_out": 19.5, "venturi": 28.0, "hp_std": 15.4, "peak_rpm": 8500, "limit_std": 10000, "weight_std": 115.0, "valves": 4, "lift_std": 8.5, "dur_std": 245}}
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION ---
def calculate_axis_v22(cc, bore, stroke, cr, rpm_limit, v_in, n_v_in, v_out, n_v_out, v_lift, venturi, dur_in, dur_out, afr, material, d_type, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    avg_dur = (float(dur_in) + float(dur_out)) / 2.0
    adj_peak_rpm = float(std['peak_rpm']) + ((avg_dur - 240.0) * 50.0)
    d_loss = 0.82 if d_type == "CVT" else 0.94
    afr_mod = 1.0 - abs(float(afr) - 12.8) * 0.05
    eff_v_in = math.sqrt(n_v_in * (v_in**2))
    eff_v_out = math.sqrt(n_v_out * (v_out**2))
    bmep_base = (float(std['hp_std']) * 950000.0) / (float(std['bore']**2 * 0.785 * std['stroke']/1000) * float(std['peak_rpm']) * 0.85)

    for r in rpms:
        ve = math.exp(-((r - adj_peak_rpm) / 4800.0)**2) if r <= adj_peak_rpm else math.exp(-((r - adj_peak_rpm) / 1200.0)**2)
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / eff_v_in)**2) * ps_speed
        gs_out = ((float(bore) / eff_v_out)**2) * ps_speed 
        if gs_in > 115.0: ve *= (115.0 / gs_in)**2.5 
        if gs_out > 110.0: ve *= (110.0 / gs_out)**2.0
        friction_loss = (r / 15000.0)**2 
        hp = (bmep_base * float(cc) * float(r) * ve * d_loss * afr_mod) / 950000.0
        hp *= (1.0 - friction_loss) 
        if v_lift / v_in > 0.30: hp *= (1.0 + ((v_lift/v_in) - 0.30) * 0.1)
        if cr > 14.5: hp *= (1.0 - (cr - 14.5) * 0.15)
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
    return rpms, hps, torques, ps_speed, gs_in, gs_out

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    sel_merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    sel_sys = st.selectbox("Sistem Bahan Bakar", list(DATABASE_REF[sel_merk].keys()))
    sel_cc = st.selectbox("Kapasitas (CC)", list(DATABASE_REF[sel_merk][sel_sys].keys()))
    sel_model = st.selectbox("Model Motor", list(DATABASE_REF[sel_merk][sel_sys][sel_cc].keys()))
    std = DATABASE_REF[sel_merk][sel_sys][sel_cc][sel_model]
    
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        full_label = f"{raw_label} {sel_model.split(' ')[0]}" 
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std['bore']), step=0.1)
        in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)
        cc_placeholder = st.empty()

    with st.expander("🧪 Detail Expert Tuning", expanded=True):
        in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2, 4], index=1 if std['valves']>=4 else 0)
        in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2, 4], index=1 if std['valves']>=4 else 0)
        in_venturi = st.number_input(f"Venturi/TB (std: {std['venturi']})", value=float(std['venturi']), step=0.5)
        in_v_lift = st.number_input(f"Lift (std: {std['lift_std']})", value=float(std['lift_std']), step=0.1)
        in_dur_in = st.number_input(f"Durasi In (std: {std['dur_std']})", value=float(std['dur_std']), step=1.0)
        in_dur_out = st.number_input(f"Durasi Out (std: {std['dur_std']})", value=float(std['dur_std']), step=1.0)
        in_afr = st.number_input("AFR", value=12.8, min_value=11.0, max_value=15.0, step=0.1)
        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC: {cc_calc:.2f}")
    in_joki = st.number_input("Berat Joki (kg)", value=60.0)
    run_btn = st.button("🚀 ANALYZE & RUN AXIS")

# --- 5. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v22(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in, 
        in_v_out, in_n_v_out, in_v_lift, in_venturi, in_dur_in, in_dur_out, in_afr, in_material, in_d_type, std
    )
    hp_max = max(hps)
    pwr = (hp_max / (std['weight_std'] + in_joki)) * 10.0
    st.session_state.history.append({
        "Run": full_label, "CC": cc_calc, "CR": cr_calc, "AFR": in_afr, 
        "Max_HP": hp_max, "RPM_HP": rpms[np.argmax(hps)],
        "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)], 
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed, 
        "rpms": rpms, "hps": hps, "torques": torques, 
        "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore, "stroke": in_stroke,
        "lift": in_v_lift, "venturi": in_venturi, "material": in_material, "model": sel_model, "std_data": std,
        "T100": 6.5 / math.pow(pwr, 0.45), "T201": 10.2 / math.pow(pwr, 0.45),
        "T402": 16.5 / math.pow(pwr, 0.45), "T1000": 32.8 / math.pow(pwr, 0.45),
        "rpm_limit": in_rpm
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # --- LOGIKA PEWARNAAN SPESIFIK (HANYA CR) ---
    def style_cr_logic(row):
        styles = ['color: white'] * len(row) # Default Putih untuk semua kolom
        cr_val = row['CR']
        
        # Logika warna untuk kolom CR (Index 2 dalam subset)
        if cr_val < 11.5:
            cr_color = 'color: #00BFFF' # Biru (Aman)
        elif 11.5 <= cr_val <= 13.0:
            cr_color = 'color: #00FF00' # Hijau (Optimal)
        else:
            cr_color = 'color: #FF4B4B' # Merah (Resiko Tinggi)
            
        styles[2] = cr_color
        return styles

    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4: st.metric("Flow In (est)", f"{round((latest['v_in']/25.4)**2 * 146, 1)} CFM")
    with m5: st.metric("Flow Out (est)", f"{round((latest['v_out']/25.4)**2 * 146, 1)} CFM")

    # --- GRAFIK ---
    fig = go.Figure()
    colors_list = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
    for i, r in enumerate(st.session_state.history):
        color = colors_list[i % len(colors_list)]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} HP", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], name=f"{r['Run']} Nm", line=dict(color=color, width=2, dash='dot'), yaxis="y2"))
        idx_hp, idx_nm = np.argmax(r['hps']), np.argmax(r['torques'])
        fig.add_vline(x=r['rpms'][idx_hp], line_dash="dash", line_color=color, opacity=0.5)
        fig.add_annotation(x=r['rpms'][idx_hp], y=r['hps'][idx_hp], text=f"Peak {r['hps'][idx_hp]}HP", showarrow=True, arrowhead=2, bgcolor=color)
        fig.add_annotation(x=r['rpms'][idx_nm], y=r['torques'][idx_nm], text=f"{r['torques'][idx_nm]}Nm", showarrow=True, arrowhead=2, yref="y2", bgcolor="#333")

    fig.update_layout(template="plotly_dark", height=600, xaxis=dict(title="Engine RPM", dtick=1000, gridcolor="#333"), yaxis=dict(title="Power (HP)", gridcolor="#333"), yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)"))
    st.plotly_chart(fig, use_container_width=True)
    
    # --- PERFORMANCE TABLE (DYNAMIC CR COLORING) ---
    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Performance Dyno Result")
    # Terapkan fungsi pewarnaan CR
    styled_df = df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].style.apply(style_cr_logic, axis=1).format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    })
    st.dataframe(styled_df, hide_index=True, use_container_width=True)

    # --- DRAG TABLE ---
    st.write("### 🏁 Drag Simulation Predictions")
    df_drag = df[["Run", "T100", "T201", "T402", "T1000"]].rename(columns={"T100":"100m","T201":"201m","T402":"402m","T1000":"1000m"})
    st.dataframe(df_drag.style.format({"100m": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s"}), hide_index=True, use_container_width=True)

    # --- AXIS EXPERT SECTIONS (NEW DYNAMIC LOGIC) ---
    st.divider()
    st.header(f"🏁 Axis Expert Physics Analysis: {latest['model']}")
    
    # Variabel Kalkulasi Lanjutan untuk Axis Expert
    bore_stroke_ratio = latest['bore'] / latest['stroke']
    lift_valve_ratio = latest['lift'] / latest['v_in']
    exh_in_ratio = latest['v_out'] / latest['v_in']
    std_cc = (0.785398 * latest['std_data']['bore']**2 * latest['std_data']['stroke'] / 1000)
    diff_cc_pct = ((latest['CC'] - std_cc) / std_cc) * 100
    ideal_lift_bell = latest['v_in'] * 0.28  # Rekomendasi median Graham Bell (28% dari diameter klep in)

    c1, c2, c3 = st.columns(3)
    
    # 1. ANALISA PERFORMA
    with c1:
        st.subheader("📊 1. Analisa Performa")
        msg = []
        
        # Karakteristik Bore x Stroke
        if bore_stroke_ratio > 1.05:
            msg.append(f"• **Karakter Mesin:** Overbore (Rasio {bore_stroke_ratio:.2f}). Mesin ini dominan di putaran menengah ke atas. Puncak HP diprediksi geser ke RPM lebih tinggi.")
        elif bore_stroke_ratio < 0.95:
            msg.append(f"• **Karakter Mesin:** Long-Stroke (Rasio {bore_stroke_ratio:.2f}). Torsi instan di putaran bawah, sangat cocok untuk trek pendek atau stop-and-go.")
        else:
            msg.append(f"• **Karakter Mesin:** Square/Near-Square (Rasio {bore_stroke_ratio:.2f}). Keseimbangan sempurna antara torsi bawah dan nafas tenaga atas.")
            
        # Analisis Gas Speed Intake
        if latest['gsin'] < 85:
            msg.append(f"• **Velocity:** Sangat lambat ({latest['gsin']:.1f} m/s). Efek *scavenging* buruk, bahan bakar berisiko mengembun di leher angsa, putaran bawah 'ngempos'.")
        elif 85 <= latest['gsin'] <= 110:
            msg.append(f"• **Velocity:** Sangat Ideal ({latest['gsin']:.1f} m/s). Campuran udara/BBM teratomisasi dengan sempurna, power band terasa padat padat.")
        else:
            msg.append(f"• **Velocity:** Indikasi Choking ({latest['gsin']:.1f} m/s). Gas speed terlalu ekstrim mendekati ambang batas sonik. Tenaga mesin akan tertahan (mentok) di RPM tinggi.")

        # Analisis Piston Speed
        if latest['pspeed'] < 16:
            msg.append(f"• **Daya Tahan:** Piston speed {latest['pspeed']:.1f} m/s. Masih dalam ambang batas harian yang sangat aman untuk pemakaian jangka panjang.")
        elif 16 <= latest['pspeed'] <= 21:
            msg.append(f"• **Daya Tahan:** Piston speed {latest['pspeed']:.1f} m/s. Kategori Racing-Harian. Beban gesekan *liner* meningkat tajam di batas limit RPM {latest['rpm_limit']}.")
        else:
            msg.append(f"• **Daya Tahan:** Piston speed {latest['pspeed']:.1f} m/s. Kategori EKSTRIM. Risiko setang seher putus atau piston macet sangat tinggi.")

        st.info("\n\n".join(msg))

    # 2. REKOMENDASI AHLI (GRAHAM BELL)
    with c2:
        st.subheader("📚 2. Rekomendasi Ahli (Bell)")
        bell = []
        
        # Rekomendasi Lift Klep
        if lift_valve_ratio < 0.25:
            bell.append(f"• **Valve Lift:** Menurut Bell, rasio angkatan klep Anda ({lift_valve_ratio:.2f}D) masih kurang maksimal. Untuk *flow* optimal tanpa mengubah diameter klep {latest['v_in']}mm, idealnya lift berada di angka **{ideal_lift_bell:.1f}mm** (0.28D).")
        elif 0.25 <= lift_valve_ratio <= 0.31:
            bell.append(f"• **Valve Lift:** Efisiensi luar biasa! Rasio angkatan klep ({lift_valve_ratio:.2f}D) sudah memenuhi standar *High Performance Tuning* Graham Bell (0.25D - 0.30D).")
        else:
            bell.append(f"• **Valve Lift:** Rasio Over-Lift ({lift_valve_ratio:.2f}D). Bell memperingatkan bahwa lift di atas 0.30D membawa keuntungan *flow* yang sangat kecil namun meningkatkan risiko *valve floating* secara drastis.")

        # Rasio Klep In & Out
        if exh_in_ratio < 0.75:
            bell.append(f"• **Exhaust Flow:** Diameter klep out ({latest['v_out']}mm) terlalu kecil (hanya {exh_in_ratio*100:.1f}% dari in). Graham Bell menyarankan ukuran klep out minimal 80-85% dari klep in untuk membuang panas sisa pembakaran.")
        elif exh_in_ratio > 0.88:
            bell.append(f"• **Exhaust Flow:** Diameter klep out terlalu besar ({exh_in_ratio*100:.1f}%). Dapat menyebabkan terbuangnya campuran BBM segar saat fase *overlap*.")
            
        # Rasio Kompresi & AFR
        if latest['CR'] > 13.5:
            bell.append(f"• **Compression (CR):** Dengan rasio kompresi statis {latest['CR']:.2f}:1, mesin ini sudah masuk zona rawan detonasi. Wajib menggunakan bahan bakar beroktan tinggi (RON 98+) atau bensol/AvGas.")
        elif latest['CR'] < 11.0:
            bell.append(f"• **Compression (CR):** Kompresi {latest['CR']:.2f}:1 sangat aman untuk menenggak Pertalite/Pertamax (RON 90-92) tanpa khawatir *knocking*.")
            
        st.warning("\n\n".join(bell))

    # 3. SOLUSI & PART GANTI
    with c3:
        st.subheader("🛠️ 3. Solusi & Part Ganti")
        parts = []
        
        # Penanganan berdasarkan analisa CC
        if diff_cc_pct > 25:
            parts.append(f"⚙️ **Sistem Injeksi/Karbu:** Mesin mengalami pembengkakan kapasitas {diff_cc_pct:.1f}%. Wajib *upgrade* ukuran Venturi TB/Karbu menjadi minimal {latest['venturi'] + 2}mm dan Injector *High-Flow* (jika injeksi).")
        elif diff_cc_pct > 10:
            parts.append(f"⚙️ **Suplai BBM:** Kapasitas naik {diff_cc_pct:.1f}%. Remap ECU / spuyer karbu wajib disesuaikan ulang untuk mengejar target AFR {latest['AFR']}.")

        # Penanganan berdasarkan Gas Speed & Klep
        if latest['gsin'] < 85:
            parts.append("⚙️ **Intake Porting:** Tambal *porting* intake menggunakan lem *epoxy* atau gunakan leher angsa (manifold) yang lebih panjang & sempit untuk mengompresi Velocity.")
        if lift_valve_ratio < 0.25:
            parts.append(f"⚙️ **Camshaft / Noken As:** Beli atau custom noken as racing dengan profil *lift* di kisaran {ideal_lift_bell:.1f}mm - {latest['v_in']*0.30:.1f}mm untuk membebaskan aliran.")
            
        # Penanganan Material dan Piston Speed
        if latest['pspeed'] > 20 or latest['CR'] > 13.0:
            if latest['material'] == "Casting":
                parts.append("⚙️ **Piston Material:** BACA INI! Piston Speed / Kompresi tinggi tetapi Anda memilih piston 'Casting'. SEGERA ganti ke bahan **Forged** untuk menghindari piston bolong/pecah.")
            parts.append("⚙️ **Bottom End:** Ganti *conrod* (stang seher) forged dan bearing kruk as tipe *high-speed* (Faito/sejenisnya).")
            parts.append("⚙️ **Cylinder Head:** Pasang Per Klep Racing (Swedia/Jepang) agar klep tidak bertabrakan dengan piston di putaran atas.")
            
        # Jika tidak ada anomali berat
        if len(parts) <= 1:
            parts.append("✅ **Kondisi Mesin Optimal:** Konfigurasi komponen di ruang bakar terpantau efisien. Modifikasi bisa difokuskan pada sektor **Transmisi / CVT (Roller, Per CVT, Gear Ratio)** untuk transfer tenaga maksimal ke aspal.")

        for p in parts: st.success(p)

st.write("---")
st.caption("⚠️ **DISCLAIMER:** Simulasi ini berdasarkan kalkulasi matematis. Hasil dyno asli bergantung pada keahlian mekanik di lapangan. GassPoll!")
