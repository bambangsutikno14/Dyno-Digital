import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIG & UI (TETAP) ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    th, td { text-align: center !important; vertical-align: middle !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE PABRIKAN (TETAP) ---
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
                "Beat 110 Karbu": {"bore": 50.0, "stroke": 55.0, "v_head": 11.8, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.22, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 89.0, "valves": 2, "lift_std": 7.0, "dur_std": 230}
            }
        },
        "Injeksi": {
            "160cc": {"Vario 160 / PCX 160": {"bore": 60.0, "stroke": 55.5, "v_head": 12.8, "valve_in": 23.0, "valve_out": 19.5, "venturi": 28.0, "hp_std": 15.4, "peak_rpm": 8500, "limit_std": 10000, "weight_std": 115.0, "valves": 4, "lift_std": 8.5, "dur_std": 245}}
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. CORE CALCULATION (TETAP) ---
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

# --- 4. SIDEBAR (TETAP) ---
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    sel_merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    sel_sys = st.selectbox("Sistem Bahan Bakar", list(DATABASE_REF[sel_merk].keys()))
    sel_cc = st.selectbox("Kapasitas (CC)", list(DATABASE_REF[sel_merk][sel_sys].keys()))
    sel_model = st.selectbox("Model Motor", list(DATABASE_REF[sel_merk][sel_sys][sel_cc].keys()))
    std = DATABASE_REF[sel_merk][sel_sys][sel_cc][sel_model]
    
    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Perimeter 1", expanded=True):
        raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.history)+1}")
        full_label = f"{raw_label} {sel_model.split(' ')[0]}" 
        in_bore = st.number_input(f"Bore", value=float(std['bore']), step=0.1)
        in_stroke = st.number_input(f"Stroke", value=float(std['stroke']), step=0.1)
        in_vhead = st.number_input(f"Vol Head", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM", value=int(std['limit_std']), step=100)
        cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
        st.success(f"CC: {cc_calc:.2f}")

    with st.expander("🧪 Detail Tuning", expanded=True):
        in_v_in = st.number_input(f"Klep In", value=float(std['valve_in']), step=0.1)
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2, 4], index=1 if std['valves']>=4 else 0)
        in_v_out = st.number_input(f"Klep Out", value=float(std['valve_out']), step=0.1)
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2, 4], index=1 if std['valves']>=4 else 0)
        in_venturi = st.number_input(f"Venturi/TB", value=float(std['venturi']), step=0.5)
        in_v_lift = st.number_input(f"Lift", value=float(std['lift_std']), step=0.1)
        in_dur_in = st.number_input(f"Durasi In", value=float(std['dur_std']), step=1.0)
        in_dur_out = st.number_input(f"Durasi Out", value=float(std['dur_std']), step=1.0)
        in_afr = st.number_input("AFR", value=12.8, step=0.1)
        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])

    in_joki = st.number_input("Berat Joki (kg)", value=60.0)
    run_btn = st.button("🚀 ANALYZE & RUN AXIS")

# --- 5. MAIN DISPLAY (TETAP) ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v22(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in, 
        in_v_out, in_n_v_out, in_v_lift, in_venturi, in_dur_in, in_dur_out, in_afr, in_material, in_d_type, std
    )
    st.session_state.history.append({
        "Run": full_label, "CC": cc_calc, "CR": cr_calc, "AFR": in_afr, 
        "Max_HP": max(hps), "RPM_HP": rpms[np.argmax(hps)],
        "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)], 
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed, 
        "rpms": rpms, "hps": hps, "torques": torques, 
        "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore, "stroke": in_stroke,
        "lift": in_v_lift, "venturi": in_venturi, "material": in_material, "model": sel_model, "std_data": std,
        "dur_in": in_dur_in, "dur_out": in_dur_out, "valves": in_n_v_in + in_n_v_out
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # GRAFIK (Grid 1000 RPM)
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    for i, r in enumerate(st.session_state.history):
        c = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} HP", line=dict(color=c, width=3)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], name=f"{r['Run']} Nm", line=dict(color=c, dash='dot'), yaxis="y2"))
    
    fig.update_layout(template="plotly_dark", xaxis=dict(dtick=1000, showgrid=True, gridcolor="#444"), yaxis2=dict(overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)
    
    # --- 6. PERFORMANCE TABLE (REVISI: FIX ERROR .format()) ---
    st.write("### 📊 Performance Dyno Result")
    df_res = pd.DataFrame(st.session_state.history)
    # Menggunakan .style.format() untuk memperbaiki AttributeError
    st.dataframe(
        df_res[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].style.format({
            "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}"
        }), 
        hide_index=True, use_container_width=True
    )

    # --- 7. AXIS EXPERT (REVISI: LOGIKA DINAMIS GRAHAM BELL) ---
    st.divider()
    st.header(f"🏁 Axis Expert Physics Analysis: {latest['model']}")
    
    b_s_ratio = latest['bore'] / latest['stroke']
    l_v_ratio = latest['lift'] / latest['v_in']
    port_valve_ratio = latest['venturi'] / latest['v_in']
    diff_cc = latest['CC'] - (0.785 * latest['std_data']['bore']**2 * latest['std_data']['stroke'] / 1000)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 1. Analisa Performa")
        p_msg = []
        # Analisa Gas Speed (Bell Chapter 5)
        if latest['gsin'] > 115:
            p_msg.append(f"• **Sonic Choke ({latest['gsin']:.1f} m/s):** Aliran udara 'tercekik' di porting. Power akan drop tajam setelah {latest['RPM_HP']} RPM.")
        elif 95 <= latest['gsin'] <= 115:
            p_msg.append(f"• **Velocity Ideal ({latest['gsin']:.1f} m/s):** Kecepatan gas sangat efisien untuk pengisian silinder di RPM tinggi.")
        else:
            p_msg.append(f"• **Low Momentum ({latest['gsin']:.1f} m/s):** Lubang intake terlalu besar untuk CC ini. Respon gas bawah akan terasa 'ngok'.")
        
        # Analisa Piston Speed
        if latest['pspeed'] > 20:
            p_msg.append(f"• **Inertia Danger ({latest['pspeed']:.1f} m/s):** Beban mekanis sangat tinggi. Risiko kerusakan kruk as/stang seher meningkat.")
        st.info("\n".join(p_msg))

    with col2:
        st.subheader("📚 2. Rekomendasi Ahli (Bell)")
        b_msg = []
        # Curtain Area (Bell Chapter 4)
        if l_v_ratio < 0.25:
            b_msg.append(f"• **Valve Obstruction:** Lift {latest['lift']}mm terlalu rendah. Graham Bell menyarankan minimal 25% dari diameter klep ({round(latest['v_in']*0.25,1)}mm).")
        elif 0.25 <= l_v_ratio <= 0.35:
            b_msg.append(f"• **Flow Saturation:** Rasio Lift/Klep ({l_v_ratio:.2%}) sudah optimal untuk koefisien aliran maksimal.")
        
        # Porting Logic
        if port_valve_ratio > 0.88:
            b_msg.append(f"• **Taper Warning:** Ukuran TB/Venturi terlalu mendekati diameter klep. Kehilangan tekanan (pressure drop) akan merusak torsi.")
        st.warning("\n".join(b_msg))

    with col3:
        st.subheader("🛠️ 3. Solusi & Part Ganti")
        s_msg = []
        # Solusi spesifik berbasis angka presisi
        if diff_cc > 15:
            rec_inj = round(latest['Max_HP'] * 11.8, 0)
            s_msg.append(f"⚙️ **Fuel System:** Bore up signifikan (+{diff_cc:.1f}cc). Rekomendasi Injector minimal {int(rec_inj)} cc/min.")
        
        if latest['CR'] > 12.8:
            s_msg.append("⚙️ **Ignition:** Kompresi tinggi ({:.1f}:1). Wajib gunakan busi dingin (Iridium) dan mundurkan timing pengapian 2 derajat.".format(latest['CR']))
        
        if latest['gsin'] > 115:
            s_msg.append(f"⚙️ **Porting:** Haluskan area *bowl* dan *short turn radius* untuk menurunkan gas speed tanpa memperbesar diameter.")
            
        if not s_msg:
            s_msg.append("✅ **Fine Tuning:** Spek sudah balance. Fokus pada settingan berat Roller (CVT) atau Final Gear.")

        for s in s_msg: st.success(s)

st.caption("📟 Axis Engine Simulation v2.4 | Audited Logic: Graham Bell 4-Stroke Tuning.")
