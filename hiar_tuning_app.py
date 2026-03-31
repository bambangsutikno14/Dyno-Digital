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
    
    # Physics Barrier: Thermal/Detonation Penalty
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
        
        # Physics Barrier: Choke Flow (Velocity Drop)
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
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std['bore']), step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std['v_head']), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std['limit_std']), step=100)
        cc_placeholder = st.empty()

    expert_on = st.toggle("🚀 Perimeter 2 (Expert Advice)", value=True)
    if expert_on:
        with st.expander("🧪 Detail Expert Tuning", expanded=True):
            in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.1)
            in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std['valve_in']), step=0.1)
            in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
            in_venturi = st.number_input(f"Venturi (std: {float(std['venturi'])})", value=float(std['venturi']), step=0.5)
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

# --- 5. MAIN LOGIC & DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, pspeed, gsin, gsout = calculate_axis_v10(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, 
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std
    )
    
    hp_max = float(max(hps))
    berat_total = float(std['weight_std']) + float(in_joki)
    pwr = (hp_max / berat_total) * 10.0 
    
    st.session_state.history.append({
        "Run": full_label, "CC": round(cc_calc, 2), "CR": round(cr_calc, 2), "AFR": in_afr,
        "Max_HP": hp_max, "RPM_HP": rpms[np.argmax(hps)], "Max_Nm": max(torques), "RPM_Nm": rpms[np.argmax(torques)],
        "T100m": round(6.5 / math.pow(pwr, 0.45), 2),
        "T201m": round(10.2 / math.pow(pwr, 0.45), 2),
        "T402m": round(16.5 / math.pow(pwr, 0.45), 2),
        "T1000m": round(32.8 / math.pow(pwr, 0.45), 2),
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed,
        "rpms": rpms, "hps": hps, "torques": torques, "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore, "stroke": in_stroke, "dur": (in_dur_in+in_dur_out)/2, "venturi": in_venturi
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # FLOWBENCH
    st.header("🌪️ Flowbench & Engine Speed Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Flow In (CFM)", f"{round((latest['v_in'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with m2: st.metric("Flow Out (CFM)", f"{round((latest['v_out'] / 25.4)**2 * math.sqrt(28) * 128, 1)}")
    with m3: st.metric("Gas Speed In", f"{latest['gsin']:.1f} m/s")
    with m4: st.metric("Gas Speed Out", f"{latest['gsout']:.1f} m/s")
    with m5: st.metric("Piston Speed", f"{latest['pspeed']:.1f} m/s")

    # TABLES WITH STYLING
    def style_abnormal(val, col):
        if col == 'CR' and val > 14.5: return 'background-color: #8b0000; color: white'
        if col == 'Velocity' and val > 110.0: return 'background-color: #8b0000; color: white'
        return ''

    df = pd.DataFrame(st.session_state.history)
    
    st.write("### 📊 Performance Dyno Results")
    df_dyno = df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].copy()
    df_dyno['Velocity'] = df['gsin'].round(1)
    styled_dyno = df_dyno.style.apply(lambda x: [style_abnormal(v, x.name) for v in x], axis=0)
    st.dataframe(styled_dyno, hide_index=True, use_container_width=True)
    
    st.write("### 🏁 Drag Race Simulation (Time Predictions)")
    st.dataframe(df[["Run", "T100m", "T201m", "T402m", "T1000m"]], hide_index=True, use_container_width=True)

    # GRAPH
    fig = go.Figure()
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    for i, r in enumerate(st.session_state.history):
        c = colors[i % 4]
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['hps'], name=f"{r['Run']} (HP)", line=dict(color=c, width=4)))
        fig.add_trace(go.Scatter(x=r['rpms'], y=r['torques'], line=dict(color=c, dash='dot'), yaxis="y2", name=f"{r['Run']} (Nm)"))
        fig.add_annotation(x=r['RPM_HP'], y=r['Max_HP'], text=f"HP: {r['Max_HP']}@{r['RPM_HP']}", showarrow=True, arrowhead=2, bgcolor=c, font=dict(color="black"))
        fig.add_annotation(x=r['RPM_Nm'], y=r['Max_Nm'], text=f"Nm: {r['Max_Nm']}@{r['RPM_Nm']}", showarrow=True, yref="y2", arrowhead=2, bgcolor="white", font=dict(color="black"))

    fig.update_layout(template="plotly_dark", height=600, paper_bgcolor="#000", plot_bgcolor="#000",
                      xaxis=dict(title="RPM", gridcolor="#333", dtick=1000, showgrid=True), 
                      yaxis=dict(title="Power (HP)", gridcolor="#333", showgrid=True),
                      yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

    # EXPERT ADVICE (DYNAMIC & LIMIT BASED)
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    
    # Logic Analisa
    if latest['CR'] > 14.5:
        st.error(f"⚠️ **DETONATION LIMIT:** CR {latest['CR']}:1 melampaui batas efisiensi termal. HP turun karena detonasi.")
    elif latest['gsin'] > 110:
        st.error(f"⚠️ **CHOKE FLOW:** Kecepatan gas {latest['gsin']:.1f} m/s terlalu tinggi. Udara terhambat di intake.")
    else:
        st.info(f"**1. Analisa Performa:** Karakter mesin {latest['Run']} cukup ideal dengan kecepatan gas {latest['gsin']:.1f} m/s.")

    # Logic Rekomendasi
    st.warning(f"**2. Rekomendasi:** Target Vol Head ideal {round(latest['CC']/12.5, 2)}cc. Gunakan knalpot diameter leher {round(math.sqrt(latest['CC']*0.15)*10, 1)}mm.")

    # Logic Solusi
    if latest['gsin'] > 105:
        solusi = f"Perbesar Klep In ke {round(latest['bore']*0.54, 1)}mm untuk menurunkan velocity."
    else:
        solusi = "Fokus pada optimalisasi porting area bowl dan penyelarasan durasi noken as."
    st.success(f"**3. Solusi:** {solusi}")

st.write("---")
st.error("⚠️ **DISCLAIMER:** Berdasarkan 4-Stroke Performance Tuning. Batas fisik diterapkan pada CR > 14.5 dan Velocity > 110 m/s.")
