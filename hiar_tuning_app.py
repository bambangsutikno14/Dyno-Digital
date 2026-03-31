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

# --- 2. DATABASE PABRIKAN ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "f_ratio": 3.10},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "f_ratio": 3.05},
    },
    "HONDA": {
        "Vario 150 / PCX": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "f_ratio": 2.90},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89.0, "f_ratio": 3.20},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION (PHYSICS ACCURATE) ---
def calculate_axis_v10(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    adj_peak = float(std['peak_rpm']) + (((float(dur_in) + float(dur_out))/2.0 - 240.0) * 55.0)
    eff = 0.835 if "Mio" in str(std) or "BeAT" in str(std) else 0.91
    afr_mod = 1.0 - abs(float(afr) - 13.0) * 0.04
    
    thermal_penalty = 1.0
    if cr > 14.5:
        thermal_penalty = 1.0 - ((cr - 14.5) * 0.15)
    
    bmep = (float(std['hp_std']) * 950000.0) / (float(cc) * adj_peak * eff)
    
    for r in rpms:
        if r <= adj_peak:
            ve = math.exp(-((r - adj_peak) / 4500.0)**2)
        else:
            ve = math.exp(-((r - adj_peak) / 1800.0)**2)
            
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / float(v_in))**2) * ps_speed
        gs_out = ((float(bore) / float(v_out))**2) * ps_speed
        
        if gs_in > 130.0:
            ve *= (130.0 / gs_in)**2 
        elif gs_in > 110.0:
            ve *= (110.0 / gs_in)
        
        hp = (bmep * float(cc) * float(r) * ve * eff * afr_mod * thermal_penalty) / 950000.0
        if float(bore) > float(std['bore']): hp *= (1.0 + (float(cr) - 9.5) * 0.025)
        if float(venturi) > float(std['venturi']): hp *= (1.0 + (float(venturi) - float(std['venturi'])) * 0.012)
        
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
        
    return rpms, hps, torques, ps_speed, gs_in, gs_out

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    st.divider()

    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1 (Standar)", expanded=True):
        raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        full_label = f"{raw_label} {model_name.split(' ')[0]}" 
        in_bore = st.number_input(f"Bore", value=float(std['bore']), step=0.1)
        in_vhead = st.number_input(f"Vol Head", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM", value=int(std['limit_std']), step=100)
        cc_placeholder = st.empty()

    expert_on = st.toggle("🚀 Perimeter 2 (Expert Advice)", value=True)
    if expert_on:
        with st.expander("🧪 Detail Tuning", expanded=True):
            in_stroke = st.number_input(f"Stroke", value=float(std['stroke']), step=0.1)
            in_v_in = st.number_input(f"Klep In", value=float(std['valve_in']), step=0.1)
            in_v_out = st.number_input(f"Klep Out", value=float(std['valve_out']), step=0.1)
            in_venturi = st.number_input(f"Venturi", value=float(std['venturi']), step=0.5)
            in_dur_in = st.slider("Durasi In", 200, 320, 240)
            in_dur_out = st.slider("Durasi Out", 200, 320, 240)
            in_afr = st.slider("Target AFR", 11.5, 14.7, 13.0, step=0.1)
    else:
        in_stroke, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr = std['stroke'], std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC Motor Real: {cc_calc:.2f} cc")
    st.divider()

    st.header("3️⃣ DRAG SIMULATION")
    in_joki = st.number_input("Berat Joki (kg)", value=60.0, step=1.0)
    run_btn = st.button("🚀 ANALYZE & RUN AXIS DYNO")

# --- 5. MAIN LOGIC ---
if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v10(cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std)
    pwr = (float(max(hps)) / (float(std['weight_std']) + float(in_joki))) * 10.0 
    
    st.session_state.history.append({
        "Run": full_label, "CC": round(cc_calc, 2), "CR": round(cr_calc, 2), "AFR": in_afr,
        "Max_HP": float(max(hps)), "RPM_HP": int(rpms[np.argmax(hps)]), "Max_Nm": float(max(torques)), "RPM_Nm": int(rpms[np.argmax(torques)]),
        "T100m": round(6.5/math.pow(pwr, 0.45), 2), "T201m": round(10.2/math.pow(pwr, 0.45), 2),
        "T402m": round(16.5/math.pow(pwr, 0.45), 2), "T1000m": round(32.8/math.pow(pwr, 0.45), 2),
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed, "rpms": rpms, "hps": hps, "torques": torques, "v_in": in_v_in, "bore": in_bore, "v_out": in_v_out, "venturi": in_venturi
    })

# --- 6. DISPLAY & AXIS EXPERT (RE-RESTORED FULL v11.3 LOGIC) ---
if st.session_state.history:
    latest = st.session_state.history[-1]
    st.title("📟 Axis Dyno Suite Master v11.5")
    
    # Graphs & Tables
    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Performance Results")
    st.dataframe(df[["Run", "CC", "CR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]], hide_index=True, use_container_width=True)

    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    for i, r in enumerate(st.session_state.history):
        c = colors[i % 4]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=c, width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], line=dict(color=c, dash='dot'), yaxis="y2", name=f"{r['Run']} (Nm)"))
    fig.update_layout(template="plotly_dark", height=500, paper_bgcolor="#000", plot_bgcolor="#000", xaxis=dict(title="RPM", gridcolor="#333"), yaxis=dict(title="HP"), yaxis2=dict(overlaying="y", side="right", title="Nm"))
    st.plotly_chart(fig, use_container_width=True)

    # --- FULL LOGIC EXPERT SECTION ---
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")

    # 1. ANALISA PERFORMA
    with st.container():
        # Pre-formatting variables to avoid f-string display issues
        v_now = round(latest['gsin'], 2)
        cr_now = round(latest['CR'], 2)
        cc_now = round(latest['CC'], 2)
        
        ana_txt = f"Konfigurasi {latest['Run']} memiliki kapasitas {cc_now} cc. "
        
        if v_now > 115:
            ana_status = f"❌ **Kritis:** Terjadi *Choke Flow* (Velocity {v_now} m/s). Udara menabrak dinding porting, pengisian silinder terhenti di RPM atas."
        elif v_now > 100:
            ana_status = f"⚠️ **Peringatan:** *High Velocity* ({v_now} m/s). Karakter mesin 'Peak Power' tinggi namun nafas cepat habis."
        else:
            ana_status = f"✅ **Optimal:** Aliran gas ({v_now} m/s) sangat efisien, memberikan rentang tenaga yang luas."

        if cr_now > 15.0:
            cr_status = f"Serta kondisi termal **Ekstrim** (CR {cr_now}:1) yang beresiko fatal pada piston."
        elif cr_now > 13.5:
            cr_status = f"Dengan kompresi **Tinggi** (CR {cr_now}:1), memerlukan manajemen panas dan BBM oktan tinggi."
        else:
            cr_status = f"Dan rasio kompresi ({cr_now}:1) masih dalam batas aman operasional."

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
        
        if latest['CR'] > 14.5:
            solusi_list.append(f"• **Manajemen Kompresi:** Gunakan paking blok/head lebih tebal (0.5-1.0mm) atau papas dome piston {round(latest['CC']*0.01, 1)}cc.")
            solusi_list.append(f"• **Timing Cam:** Gunakan noken as dengan LSA lebih sempit/overlap tinggi untuk membuang tekanan statis berlebih.")
        
        if latest['gsin'] > 105:
            solusi_list.append(f"• **Upgrade Klep:** Perbesar diameter klep IN ke {round(latest['bore']*0.55, 1)}mm untuk menurunkan hambatan udara.")
            solusi_list.append(f"• **Induksi Udara:** Reamer venturi atau ganti Throttle Body ke ukuran {round(latest['v_in']*1.15, 1)}mm.")
        
        if latest['Max_HP'] < (latest['CC'] * 0.12):
            solusi_list.append(f"• **Sistem Gas Buang:** Gunakan knalpot tipe *taper* (kerucut) dengan diameter awal {round(latest['v_out']*1.1, 1)}mm.")

        if not solusi_list:
            st.success("✅ **Balanced Engine:** Konfigurasi sudah harmonis. Fokus pada penyempurnaan porting polish tahap akhir (Stage 1) dan settingan AFR.")
        else:
            for s in solusi_list:
                st.write(s)

    # REKOMENDASI FINAL
    st.info(f"💡 **Rekomendasi Final:** Untuk spek ini, gunakan knalpot dengan diameter leher **{rekom_knalpot}mm** dan target Vol Head **{rekom_vhead}cc** untuk mengejar daya tahan harian yang optimal.")
