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
    th, td { text-align: center !important; vertical-align: middle !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN (MATIC ONLY + BEAT FI) ---
DATABASE_REF = {
    "YAMAHA (MATIC)": {
        "Karbu": {
            "115cc": {
                "Mio / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "valves": 2, "lift_std": 7.0, "dur_std": 230}
            },
            "125cc": {
                "Xeon (Carb)": {"bore": 52.4, "stroke": 57.9, "v_head": 14.5, "valve_in": 26.0, "valve_out": 21.0, "venturi": 26.0, "hp_std": 10.7, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 103.0, "valves": 2, "lift_std": 7.5, "dur_std": 235}
            }
        },
        "Injeksi": {
            "125cc": {
                "Mio Fino 125 FI": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 9.5, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 98.0, "valves": 2, "lift_std": 7.8, "dur_std": 235}
            },
            "155cc": {
                "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "valves": 4, "lift_std": 8.2, "dur_std": 240}
            },
            "250cc": {
                "XMAX 250": {"bore": 70.0, "stroke": 64.9, "v_head": 22.5, "valve_in": 26.5, "valve_out": 22.5, "venturi": 32.0, "hp_std": 22.5, "peak_rpm": 7000, "limit_std": 9000, "weight_std": 179.0, "valves": 4, "lift_std": 8.5, "dur_std": 245}
            }
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
            "110cc": {
                "Beat 110 FI (eSP)": {"bore": 50.0, "stroke": 55.1, "v_head": 12.0, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.68, "peak_rpm": 7500, "limit_std": 9300, "weight_std": 93.0, "valves": 2, "lift_std": 7.2, "dur_std": 232}
            },
            "125cc": {
                "Vario 125 eSP": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 11.1, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 111.0, "valves": 2, "lift_std": 7.8, "dur_std": 235}
            },
            "150cc": {
                "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "valves": 2, "lift_std": 8.0, "dur_std": 235}
            },
            "160cc": {
                "Vario 160 / PCX 160": {"bore": 60.0, "stroke": 55.5, "v_head": 12.8, "valve_in": 23.0, "valve_out": 19.5, "venturi": 28.0, "hp_std": 15.4, "peak_rpm": 8500, "limit_std": 10000, "weight_std": 115.0, "valves": 4, "lift_std": 8.5, "dur_std": 245}
            }
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION (LOGIKA ASLI) ---
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
        
        # PERUBAHAN 1: Mengubah Slider AFR menjadi Number Input (+-)
        in_afr = st.number_input("AFR (Rasio Udara/BBM)", min_value=11.0, max_value=15.0, value=12.8, step=0.1)
        
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
        "lift": in_v_lift, "venturi": in_venturi, "material": in_material,
        "T100": 6.5 / math.pow(pwr, 0.45), "T201": 10.2 / math.pow(pwr, 0.45),
        "T402": 16.5 / math.pow(pwr, 0.45), "T1000": 32.8 / math.pow(pwr, 0.45)
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4: st.metric("Flow In (est)", f"{round((latest['v_in']/25.4)**2 * 146, 1)} CFM")
    with m5: st.metric("Flow Out (est)", f"{round((latest['v_out']/25.4)**2 * 146, 1)} CFM")

    # --- GRAFIK ---
    fig = go.Figure()
    colors = ["rgba(255, 0, 0, 1)", "rgba(0, 255, 0, 1)", "rgba(0, 0, 255, 1)", "rgba(255, 255, 0, 1)", "rgba(255, 0, 255, 1)", "rgba(0, 255, 255, 1)"]
    bg_colors = [c.replace("1)", "0.4)") for c in colors]

    for i, r in enumerate(st.session_state.history):
        color = colors[i % len(colors)]
        bg_color = bg_colors[i % len(bg_colors)]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], name=f"{r['Run']} (Nm)", line=dict(color=color, width=2, dash='dot'), yaxis="y2"))
        fig.add_annotation(x=r['rpms'][-1], y=r['hps'][-1], text=r['Run'], showarrow=False, xanchor="left", font=dict(color=color, size=10))
        idx_hp = np.argmax(r['hps'])
        idx_nm = np.argmax(r['torques'])
        fig.add_annotation(x=r['rpms'][idx_hp], y=r['hps'][idx_hp], text=f"Peak: {r['hps'][idx_hp]}HP@{r['rpms'][idx_hp]}", showarrow=True, arrowhead=1, bgcolor=bg_color, font=dict(color="white", size=11))
        fig.add_annotation(x=r['rpms'][idx_nm], y=r['torques'][idx_nm], text=f"Peak: {r['torques'][idx_nm]}Nm@{r['rpms'][idx_nm]}", showarrow=True, arrowhead=1, bgcolor=bg_color, font=dict(color="white", size=11), yref="y2")

    fig.update_layout(template="plotly_dark", height=600, showlegend=False,
                      xaxis=dict(title="Engine RPM", showgrid=True, gridcolor="#333", dtick=1000),
                      yaxis=dict(title="Power (HP)", showgrid=True, gridcolor="#333"),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)
    
    # --- TABLES ---
    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Performance Dyno Result")
    st.dataframe(df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }), hide_index=True, use_container_width=True)

    st.write("### 🏁 Drag Simulation Predictions")
    df_drag = df[["Run", "T100", "T201", "T402", "T1000"]].rename(columns={"T100":"100m","T201":"201m","T402":"402m","T1000":"1000m"})
    st.dataframe(df_drag.style.format({
        "100m": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s"
    }), hide_index=True, use_container_width=True)

    # --- PERUBAHAN 2: ANALISA DINAMIS (GRAHAM BELL PRINCIPLES) 3 KOLOM ---
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    
    c1, c2, c3 = st.columns(3)
    lift_ratio = latest['lift'] / latest['v_in']
    
    with c1:
        st.subheader("🧐 1. Analisa Spek Mesin")
        st.markdown(f"- **Kapasitas Nyata:** Berada di angka **{latest['CC']:.2f} cc** dengan kompresi statis terukur **{latest['CR']:.2f}:1**.")
        st.markdown(f"- **Efisiensi Klep:** Rasio lift terhadap diameter klep in berada pada persentase **{(lift_ratio * 100):.1f}%** ({lift_ratio:.3f}).")

    with c2:
        st.subheader("📚 2. Saran Ahli (Teori)")
        # Analisa Dinamis Gas Speed berdasarkan buku
        if latest['gsin'] > 115:
            st.error(f"Menurut A.G. Bell, Gas Speed {latest['gsin']:.2f} m/s menyebabkan **Port Choking**. Udara menabrak dinding porting, tenaga akan 'tertahan' secara tiba-tiba di RPM atas.")
        elif latest['gsin'] < 95:
            st.warning(f"Gas Speed {latest['gsin']:.2f} m/s terlalu lambat. Teori scavenging menyatakan inersia yang lemah membuat torsi bawah loyo.")
        else:
            st.success(f"Velositas {latest['gsin']:.2f} m/s sangat ideal. Efisiensi Volumetrik (VE) terjaga optimal untuk mengail tenaga di seluruh rentang RPM.")

        # Analisa Dinamis Lift Ratio berdasarkan buku
        if lift_ratio < 0.25:
            st.warning(f"Rasio lift {lift_ratio:.3f} dinilai kurang. Mesin gagal memanfaatkan ukuran klep {latest['v_in']} mm sepenuhnya, udara tercekik oleh durasi buka.")
        elif lift_ratio > 0.33:
            st.error(f"Rasio lift {lift_ratio:.3f} tergolong agresif. A.G. Bell mengingatkan bahwa profil ekstrim meningkatkan friksi mekanikal tajam.")

        # Analisa Dinamis Piston Speed
        if latest['pspeed'] > 21:
            st.error(f"Piston Speed {latest['pspeed']:.2f} m/s mendekati batas stres metalurgi! Panas berlebih akan mengancam pelumasan liner.")
            
    with c3:
        st.subheader("🛠️ 3. Solusi & Rekomendasi Part")
        rekomendasi_ditemukan = False
        
        # Rekomendasi Porting / TB dinamis
        if latest['gsin'] > 115:
            st.info(f"🔹 **Intake/TB:** Ganti Throttle Body (TB) / Karbu lebih besar dari **{latest['venturi']} mm** atau perlebar porting intake.")
            rekomendasi_ditemukan = True
        elif latest['gsin'] < 95:
            st.info(f"🔹 **Manifold:** Gunakan Intake Manifold lebih sempit untuk menaikkan velositas mendekati 100-110 m/s.")
            rekomendasi_ditemukan = True

        # Rekomendasi Piston & Kompresi dinamis
        if latest['CR'] > 12.8 and latest['material'] == "Casting":
            st.error(f"🔹 **Piston:** Wajib ganti ke **Forged Piston ukuran {latest['bore']} mm** untuk menahan kompresi statis {latest['CR']:.2f}:1.")
            rekomendasi_ditemukan = True

        # Rekomendasi Noken As (Camshaft) dinamis
        if lift_ratio < 0.28:
            target_lift = latest['v_in'] * 0.30
            st.info(f"🔹 **Noken As:** Ganti dengan noken as profil tinggi, cari yang memiliki lift klep minimal **{target_lift:.2f} mm**.")
            rekomendasi_ditemukan = True

        # Rekomendasi Per Klep dinamis
        if latest['pspeed'] > 20 or lift_ratio > 0.33:
            st.warning(f"🔹 **Per Klep:** Segera pasang **Per Klep Racing / High Tension** untuk mencegah *valve floating* di kecepatan piston {latest['pspeed']:.2f} m/s.")
            rekomendasi_ditemukan = True
            
        # Rekomendasi Injector/Spuyer
        if latest['AFR'] > 13.5:
            st.warning(f"🔹 **Sistem BBM:** AFR {latest['AFR']:.1f} terlalu kering. Ganti **Injektor Debit Lebih Besar** agar mesin tidak overheat.")
            rekomendasi_ditemukan = True

        if not rekomendasi_ditemukan:
            st.success("✅ Setingan saat ini sudah sangat seimbang menurut parameter Graham Bell. Tidak ada part mendesak yang perlu diganti.")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Perhitungan hanya estimasi kalkulasi data, hasil mungkin berbeda dengan kenyataan tergantung tuning mekanik.")
