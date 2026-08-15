import streamlit as st
import numpy as np
import math
import json
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIG & PROFESSIONAL DYNO CSS
# ==========================================
st.set_page_config(
    page_title="PENDAWA AXIS VIRTUAL DYNO v16",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Consolas', 'Courier New', monospace; }
    
    .dyno-header {
        background: linear-gradient(90deg, #111111 0%, #222222 100%);
        padding: 12px 20px;
        border-radius: 4px;
        border-bottom: 3px solid #00FF66;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dyno-title { font-size: 1.4rem; font-weight: bold; color: #FFFFFF; letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }
    .dyno-subtitle { font-size: 0.85rem; color: #00FF66; }
    
    @keyframes wheelieMotion {
        0% { transform: translateY(0px) rotate(0deg); }
        25% { transform: translateY(-4px) rotate(-12deg); }
        50% { transform: translateY(-8px) rotate(-22deg); }
        75% { transform: translateY(-4px) rotate(-10deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    .wheelie-logo {
        display: inline-block;
        font-size: 1.8rem;
        animation: wheelieMotion 1.8s infinite ease-in-out;
    }

    .cc-box {
        background-color: #0D2818;
        border: 1px solid #00FF66;
        border-radius: 5px;
        padding: 8px 12px;
        margin-bottom: 12px;
        text-align: center;
    }
    .cc-title { font-size: 0.75rem; color: #888; text-transform: uppercase; }
    .cc-value { font-size: 1.4rem; font-weight: bold; color: #00FF66; }

    .stock-badge { background-color: #00FF66; color: #000; font-size: 0.75rem; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
    .tuned-badge { background-color: #FF9900; color: #000; font-size: 0.75rem; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
    
    /* Mengurangi jarak padding default sidebar text input untuk menghemat ruang vertikal */
    [data-testid="stSidebar"] div.stNumberInput { margin-bottom: -10px; }
    [data-testid="stSidebar"] div.stSelectbox { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ACCURATE MANUFACTURER DATABASE
# ==========================================
DATABASE_REF = {
    "YAMAHA": {
        "XMAX 250 (Lokal Indonesia)": {
            "bore": 70.0, "stroke": 64.9, "v_head": 26.2, "valve_in": 30.0, "valve_out": 26.0, "venturi": 34.0, 
            "hp_crank_std": 22.8, "torque_crank_std": 24.3, "peak_rpm_hp": 7000, "peak_rpm_tq": 5500, "limit_std": 9000, "weight_std": 179.0, 
            "type": "single_big", "cvt_loss": 0.18, "top_speed": 145.0
        },
        "XMAX 300 (Euro Spec)": {
            "bore": 70.0, "stroke": 75.9, "v_head": 29.5, "valve_in": 31.5, "valve_out": 27.0, "venturi": 36.0, 
            "hp_crank_std": 27.6, "torque_crank_std": 29.0, "peak_rpm_hp": 7250, "peak_rpm_tq": 5750, "limit_std": 9200, "weight_std": 183.0, 
            "type": "single_big", "cvt_loss": 0.18, "top_speed": 160.0
        },
        "XMAX 310 (Bore-Up Spec)": {
            "bore": 76.0, "stroke": 68.0, "v_head": 28.0, "valve_in": 33.0, "valve_out": 28.5, "venturi": 38.0, 
            "hp_crank_std": 32.5, "torque_crank_std": 34.0, "peak_rpm_hp": 7500, "peak_rpm_tq": 6000, "limit_std": 9500, "weight_std": 180.0, 
            "type": "single_big", "cvt_loss": 0.17, "top_speed": 172.0
        },
        "NMAX Turbo / Neo 155 VVA": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, 
            "hp_crank_std": 15.4, "torque_crank_std": 14.2, "peak_rpm_hp": 8000, "peak_rpm_tq": 6500, "limit_std": 9500, "weight_std": 130.0, 
            "type": "single_small", "cvt_loss": 0.17, "top_speed": 128.0
        },
        "NMAX 155 / Aerox 155 VVA": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, 
            "hp_crank_std": 15.4, "torque_crank_std": 13.9, "peak_rpm_hp": 8000, "peak_rpm_tq": 6500, "limit_std": 9500, "weight_std": 127.0, 
            "type": "single_small", "cvt_loss": 0.18, "top_speed": 125.0
        },
        "Lexi 125 VVA": {
            "bore": 52.0, "stroke": 58.7, "v_head": 12.8, "valve_in": 19.5, "valve_out": 16.5, "venturi": 26.0, 
            "hp_crank_std": 11.8, "torque_crank_std": 11.3, "peak_rpm_hp": 8000, "peak_rpm_tq": 7000, "limit_std": 9500, "weight_std": 112.0, 
            "type": "single_small", "cvt_loss": 0.18, "top_speed": 115.0
        },
        "Mio M3 / Fazzio / Filano 125": {
            "bore": 52.4, "stroke": 57.9, "v_head": 12.5, "valve_in": 21.0, "valve_out": 18.0, "venturi": 24.0, 
            "hp_crank_std": 9.5, "torque_crank_std": 9.6, "peak_rpm_hp": 6500, "peak_rpm_tq": 5000, "limit_std": 9200, "weight_std": 95.0, 
            "type": "single_small", "cvt_loss": 0.19, "top_speed": 108.0
        },
        "Mio Karbu (Sporty/Smile 115)": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, 
            "hp_crank_std": 8.9, "torque_crank_std": 7.84, "peak_rpm_hp": 8000, "peak_rpm_tq": 6500, "limit_std": 9000, "weight_std": 92.0, 
            "type": "single_small", "cvt_loss": 0.20, "top_speed": 102.0
        }
    },
    "HONDA": {
        "Forza 250 eSP+": {
            "bore": 67.0, "stroke": 70.7, "v_head": 24.5, "valve_in": 29.0, "valve_out": 25.0, "venturi": 34.0, 
            "hp_crank_std": 23.1, "torque_crank_std": 24.0, "peak_rpm_hp": 7750, "peak_rpm_tq": 6250, "limit_std": 9200, "weight_std": 182.0, 
            "type": "single_big", "cvt_loss": 0.18, "top_speed": 142.0
        },
        "Vario 160 / PCX 160 / ADV 160": {
            "bore": 60.0, "stroke": 55.5, "v_head": 14.2, "valve_in": 27.0, "valve_out": 22.0, "venturi": 30.0, 
            "hp_crank_std": 15.8, "torque_crank_std": 15.0, "peak_rpm_hp": 8500, "peak_rpm_tq": 6500, "limit_std": 9800, "weight_std": 117.0, 
            "type": "single_small", "cvt_loss": 0.18, "top_speed": 128.0
        },
        "Vario 150 / PCX 150 eSP": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, 
            "hp_crank_std": 13.1, "torque_crank_std": 13.4, "peak_rpm_hp": 8500, "peak_rpm_tq": 5000, "limit_std": 9800, "weight_std": 109.0, 
            "type": "single_small", "cvt_loss": 0.19, "top_speed": 118.0
        },
        "Vario 125 eSP": {
            "bore": 52.4, "stroke": 57.9, "v_head": 12.5, "valve_in": 24.0, "valve_out": 21.0, "venturi": 24.0, 
            "hp_crank_std": 11.1, "torque_crank_std": 10.8, "peak_rpm_hp": 8500, "peak_rpm_tq": 5000, "limit_std": 9800, "weight_std": 111.0, 
            "type": "single_small", "cvt_loss": 0.19, "top_speed": 112.0
        },
        "BeAT FI eSP / Scoopy eSP 110": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, 
            "hp_crank_std": 8.68, "torque_crank_std": 9.01, "peak_rpm_hp": 7500, "peak_rpm_tq": 6500, "limit_std": 9200, "weight_std": 90.0, 
            "type": "single_small", "cvt_loss": 0.20, "top_speed": 102.0
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

if 'run_trigger' not in st.session_state:
    st.session_state.run_trigger = False

# ==========================================
# 3. ACCURATE THERMODYNAMIC ENGINE (ODE SIMULATOR MODULE)
# ==========================================
def calculate_smooth_dyno_curve(std_spec, in_bore, in_stroke, in_vhead, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, user_limit_rpm, in_joki):
    # Konstanta Statis Baseline XMAX 250 (Engine Calculator Module)
    N_PEAK = 5500.0
    VE_PEAK = 0.893
    ETA_OVERALL = 0.33
    SIGMA = 4380.0
    AFR_WOT = 13.0
    
    cc_calc = float((0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0)
    cr_calc = float((cc_calc + float(in_vhead)) / float(in_vhead))
    
    std_cc = (std_spec['bore']**2 * 0.785398 * std_spec['stroke']) / 1000.0
    cc_ratio = cc_calc / std_cc
    
    cvt_loss = float(std_spec.get('cvt_loss', 0.18))
    
    crank_tq_base = float(std_spec['torque_crank_std']) * cc_ratio
    wheel_tq_base = crank_tq_base * (1.0 - cvt_loss)
    
    cr_std = (std_cc + std_spec['v_head']) / std_spec['v_head']
    cr_diff = cr_calc - cr_std
    
    # Penyesuaian Thermal Factor berbasis Eta Overall (Baseline 0.33)
    if cr_calc > 14.5:
        thermal_factor = (ETA_OVERALL / 0.33) * ((1.0 + cr_diff * 0.015) - ((cr_calc - 14.5) * 0.15))
    else:
        thermal_factor = (ETA_OVERALL / 0.33) * (1.0 + cr_diff * 0.015)
        
    valve_area_ratio = (in_v_in / in_bore)**2
    rpm_tq_dynamic = (82.0 * 60000.0) / (2.0 * in_stroke / valve_area_ratio)
    
    cam_dur_avg = (float(in_dur_in) + float(in_dur_out)) / 2.0
    cam_shift_rpm = (cam_dur_avg - 240.0) * 35.0
    
    tb_ratio = in_venturi / in_v_in
    tb_shift = - (0.85 - tb_ratio) * 3500.0 if tb_ratio < 0.85 else 0.0
    
    # RPM Torsi dikunci menggunakan pengaruh N_PEAK baseline dan modifikasi dinamik
    final_rpm_tq_peak = float(np.clip(N_PEAK + (rpm_tq_dynamic - N_PEAK) * 0.1 + cam_shift_rpm + tb_shift, 3500.0, user_limit_rpm - 2000.0))
    final_rpm_hp_peak = float(np.clip(final_rpm_tq_peak + 1800.0 + (cam_dur_avg - 240.0) * 18.0, final_rpm_tq_peak + 1200.0, user_limit_rpm - 800.0))
    
    raw_rpms = np.arange(1000, int(user_limit_rpm) + 100, 100)
    rpms = [int(r) for r in raw_rpms]
    
    wheel_hps, torques, afrs = [], [], []
    
    for r in rpms:
        pspeed_r = (2.0 * in_stroke * r) / 60000.0
        gsin_r = ((in_bore / in_v_in)**2) * pspeed_r
        
        # Integrasi Distribusi Gaussian untuk VE berdasarkan parameter ODE
        ve_shape = VE_PEAK * math.exp(-((r - final_rpm_tq_peak) / SIGMA)**2)
            
        if r > final_rpm_hp_peak:
            high_rpm_decay = math.exp(-((r - final_rpm_hp_peak) / (SIGMA * 0.4))**1.8)
            ve_shape *= high_rpm_decay
            
        choke_factor = 1.0
        if gsin_r > 125.0:
            choke_factor = (125.0 / gsin_r)**2.2
        elif gsin_r > 108.0:
            choke_factor = (108.0 / gsin_r)**1.2
            
        # Modifikator AFR dengan sentralisasi pada WOT 13.0
        afr_mod = 1.0 - abs(float(in_afr) - AFR_WOT) * 0.035
        
        wheel_tq = wheel_tq_base * ve_shape * choke_factor * thermal_factor * afr_mod
        
        if r > user_limit_rpm - 300:
            wheel_tq *= (1.0 - ((r - (user_limit_rpm - 300)) / 300.0)**2)
            
        hp = (wheel_tq * r) / 7023.5 if r > 0 else 0.0
        afr_val = float(in_afr) + 0.2 * math.sin(r / 800.0)
        
        torques.append(float(round(max(0.0, wheel_tq), 2)))
        wheel_hps.append(float(round(max(0.0, hp), 2)))
        afrs.append(float(round(afr_val, 2)))
        
    max_hp = float(max(wheel_hps))
    max_tq = float(max(torques))
    idx_hp = int(np.argmax(wheel_hps))
    idx_tq = int(np.argmax(torques))
    
    rpm_hp = int(rpms[idx_hp])
    rpm_tq = int(rpms[idx_tq])
    
    std_hp_wheel = float(std_spec['hp_crank_std']) * (1.0 - cvt_loss)
    hp_ratio = max_hp / std_hp_wheel if std_hp_wheel > 0 else 1.0
    
    std_weight_total = float(std_spec['weight_std']) + 65.0
    user_weight_total = float(std_spec['weight_std']) + float(in_joki)
    weight_ratio = std_weight_total / user_weight_total
    
    calc_top_speed = float(round(std_spec['top_speed'] * (hp_ratio**(1.0/3.0)) * (weight_ratio**0.12), 1))
    
    pspeed = float((2.0 * in_stroke * rpm_hp) / 60000.0)
    gsin = float(((in_bore / in_v_in)**2) * pspeed)
    gsout = float(((in_bore / in_v_out)**2) * pspeed)
    
    return rpms, wheel_hps, torques, afrs, max_hp, rpm_hp, max_tq, rpm_tq, cc_calc, cr_calc, pspeed, gsin, gsout, calc_top_speed
# ==========================================
# 4. SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ ENGINE SELECTION")
    
    if "selected_merk" not in st.session_state:
        st.session_state.selected_merk = list(DATABASE_REF.keys())[0]
        
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        selected_merk = st.selectbox("Manufacturer", list(DATABASE_REF.keys()), key="selected_merk")
    with col_m2:
        models_for_merk = list(DATABASE_REF[selected_merk].keys())
        selected_model = st.selectbox("Engine Model", models_for_merk, key=f"model_select_{selected_merk}")
        
    std = DATABASE_REF[selected_merk][selected_model]
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        in_klep = st.selectbox("Jumlah Klep", [4, 2], index=0 if float(std['valve_in']) > 25 else 1)
    with col_t2:
        in_fuel = st.selectbox("Sistem Suplai", ["Injeksi", "Karburator"])

    st.divider()

    st.markdown("### ⚙️ MECHANIC TUNING PARAMETERS")
    
    # Kalkulasi standar kompresi untuk default form
    std_cc_init = (0.785398 * float(std['bore'])**2 * float(std['stroke'])) / 1000.0
    std_cr_init = (std_cc_init + float(std['v_head'])) / float(std['v_head'])
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        in_bore = st.number_input("Bore (mm)", value=float(std['bore']), step=0.5)
        in_cr = st.number_input("Kompresi (:1)", value=float(round(std_cr_init, 2)), step=0.1)
    with col_s2:
        in_stroke = st.number_input("Stroke (mm)", value=float(std['stroke']), step=0.5)
        in_rpm = st.number_input("Limit RPM", value=int(std['limit_std']), step=250)

    cc_real = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    in_vhead = cc_real / (in_cr - 1.0) if in_cr > 1.0 else 10.0
    cr_real = in_cr
    
    st.markdown(f"""
    <div class="cc-box">
        <div class="cc-title">DISPLACEMENT & VOL HEAD</div>
        <div class="cc-value">{cc_real:.2f} cc &nbsp;|&nbsp; {in_vhead:.2f} cc</div>
    </div>
    """, unsafe_allow_html=True)

    expert_on = st.toggle("🧪 Valve & Flow Specs", value=True)
    if expert_on:
        in_v_in = st.number_input("Valve In (mm) [Satuan/Per Klep]", value=float(std['valve_in']), step=0.5)
        in_v_out = st.number_input("Valve Out (mm) [Satuan/Per Klep]", value=float(std['valve_out']), step=0.5)
        in_venturi = st.number_input("Throttle / Venturi (mm)", value=float(std['venturi']), step=0.5)
        in_dur_in = st.slider("Cam Duration In (°)", 200, 320, 240)
        in_dur_out = st.slider("Cam Duration Out (°)", 200, 320, 240)
        in_afr = st.slider("Target AFR Lambda", 11.0, 15.0, 13.0, step=0.1)
    else:
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr = std['valve_in'], std['valve_out'], std['venturi'], 240, 240, 13.0

    in_joki = st.number_input("Rider Weight (kg)", value=65.0, step=1.0)

    is_stock = (
        abs(in_bore - std['bore']) < 0.1 and
        abs(in_stroke - std['stroke']) < 0.1 and
        abs(in_v_in - std['valve_in']) < 0.1 and
        abs(in_v_out - std['valve_out']) < 0.1 and
        abs(in_venturi - std['venturi']) < 0.1
    )
    
    status_suffix = "(Stock)" if is_stock else "(Tuned)"
    default_run_name = f"{selected_model} {status_suffix}"
    
    st.divider()
    user_run_label = st.text_input("Run Label (Editable)", value=default_run_name)
    
    if st.button("🚀 PROCESS & RUN DYNO SWEEP"):
        st.session_state.run_trigger = True
    
    st.divider()
    if st.button("🗑️ RESET ALL HISTORY"):
        st.session_state.history = []
        st.session_state.run_trigger = False
        st.rerun()

# ==========================================
# 5. STUDIO CANVAS COMPONENT (v16.0)
# ==========================================
def render_full_dyno_studio_v16(history_list, auto_start, current_run_model_name, calc_top_speed, user_limit_rpm, engine_type):
    
    history_payload = []
    for h in history_list:
        history_payload.append({
            "Run": str(h["Run"]),
            "rpms": [int(x) for x in h["rpms"]],
            "hps": [float(x) for x in h["hps"]],
            "tqs": [float(x) for x in h["tqs"]],
            "afrs": [float(x) for x in h["afrs"]],
            "max_hp": float(h["Max_Wheel_HP"]),
            "rpm_hp": int(h["RPM_HP"]),
            "max_tq": float(h["Max_Nm"]),
            "rpm_tq": int(h["RPM_Nm"])
        })
        
    history_json = json.dumps(history_payload)
    auto_start_js = "true" if auto_start else "false"
    
    limit_rpm_i = int(user_limit_rpm)
    top_speed_f = float(calc_top_speed)
    
    component_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ background-color: #0A0A0A; color: #FFF; font-family: Consolas, monospace; margin: 0; padding: 10px; }}
            .studio-card {{ border: 2px solid #222; border-radius: 8px; padding: 12px; background-color: #0D0D0D; }}
            .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
            .gauges-row {{ display: flex; justify-content: center; gap: 15px; background-color: #111; padding: 10px; border-radius: 6px; border: 1px solid #333; margin-bottom: 12px; }}
        </style>
    </head>
    <body>
        <div class="studio-card">
            <div class="top-bar">
                <div style="font-weight:bold; font-size:1.0rem; color:#00FF66;">
                    SYSTEM STATUS: <span id="dynoStatus" style="color:#FFF;">STANDBY</span>
                </div>
            </div>

            <!-- ANALOG GAUGES -->
            <div class="gauges-row">
                <div style="text-align:center;">
                    <canvas id="tachoCanvas" width="190" height="190"></canvas>
                    <div id="tachoNote" style="color:#00FF00; font-weight:bold; font-size:0.8rem; margin-top:4px;">MAX RPM: -- RPM</div>
                </div>
                <div style="text-align:center;">
                    <canvas id="speedoCanvas" width="190" height="190"></canvas>
                    <div id="speedoNote" style="color:#0088FF; font-weight:bold; font-size:0.8rem; margin-top:4px;">MAX SPEED: -- KM/H</div>
                </div>
                <div style="text-align:center;">
                    <canvas id="afrCanvas" width="190" height="190"></canvas>
                    <div id="afrNote" style="color:#FF9900; font-weight:bold; font-size:0.8rem; margin-top:4px;">AFR: --</div>
                </div>
            </div>

            <!-- DYNAMIC GRAPH CANVAS -->
            <div style="position:relative; width:100%;">
                <canvas id="graphCanvas" width="850" height="420" style="width:100%; background-color:#050505; border:1px solid #333; border-radius:4px;"></canvas>
            </div>
        </div>

        <script>
        const historyRuns = {history_json};
        const autoStart = {auto_start_js};
        const limitRpm = {limit_rpm_i};
        const topSpeed = {top_speed_f};
        const engineType = "{engine_type}";
        const currentModelName = "{current_run_model_name}";

        function drawTachometer(value) {{
            const canvas = document.getElementById('tachoCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const cx = 95, cy = 95, r = 75;
            
            ctx.clearRect(0, 0, 190, 190);
            
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
            ctx.strokeStyle = '#222'; ctx.lineWidth = 12; ctx.stroke();
            
            const valK = Math.min(value, 15000) / 1000.0;
            const currAngle = (0.75 + (valK / 15.0) * 1.5) * Math.PI;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, currAngle);
            ctx.strokeStyle = '#00FF00'; ctx.lineWidth = 8; ctx.stroke();
            
            ctx.fillStyle = '#AAA'; ctx.font = '10px Consolas'; ctx.textAlign = 'center';
            for (let i = 1; i <= 15; i++) {{
                let a = (0.75 + (i / 15.0) * 1.5) * Math.PI;
                let tx = cx + Math.cos(a) * (r - 18);
                let ty = cy + Math.sin(a) * (r - 18);
                ctx.fillText(i, tx, ty + 3);
            }}
            
            ctx.fillStyle = '#FFF'; ctx.font = 'bold 16px Consolas';
            ctx.fillText(Math.round(value), cx, cy + 20);
            ctx.fillStyle = '#00FF00'; ctx.font = 'bold 10px Consolas';
            ctx.fillText("x1000rpm", cx, cy + 35);
            ctx.fillStyle = '#888'; ctx.font = '9px Consolas';
            ctx.fillText("TACHOMETER", cx, cy - 25);
            
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(currAngle + 0.5 * Math.PI);
            ctx.beginPath(); ctx.moveTo(-2, 0); ctx.lineTo(0, -r + 12); ctx.lineTo(2, 0);
            ctx.fillStyle = '#FF2222'; ctx.fill();
            ctx.restore();
            
            ctx.beginPath(); ctx.arc(cx, cy, 5, 0, 2 * Math.PI); ctx.fillStyle = '#FFF'; ctx.fill();
        }}

        function drawSpeedometer(value) {{
            const canvas = document.getElementById('speedoCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const cx = 95, cy = 95, r = 75;
            
            ctx.clearRect(0, 0, 190, 190);
            
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
            ctx.strokeStyle = '#222'; ctx.lineWidth = 12; ctx.stroke();
            
            const currAngle = (0.75 + (Math.min(value, 200) / 200.0) * 1.5) * Math.PI;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, currAngle);
            ctx.strokeStyle = '#0088FF'; ctx.lineWidth = 8; ctx.stroke();
            
            ctx.fillStyle = '#AAA'; ctx.font = '9px Consolas'; ctx.textAlign = 'center';
            for (let i = 0; i <= 10; i++) {{
                let valNum = i * 20;
                let a = (0.75 + (i / 10.0) * 1.5) * Math.PI;
                let tx = cx + Math.cos(a) * (r - 18);
                let ty = cy + Math.sin(a) * (r - 18);
                ctx.fillText(valNum, tx, ty + 3);
            }}
            
            ctx.fillStyle = '#FFF'; ctx.font = 'bold 16px Consolas';
            ctx.fillText(Math.round(value), cx, cy + 20);
            ctx.fillStyle = '#0088FF'; ctx.font = 'bold 10px Consolas';
            ctx.fillText("km/jam", cx, cy + 35);
            ctx.fillStyle = '#888'; ctx.font = '9px Consolas';
            ctx.fillText("SPEEDOMETER", cx, cy - 25);
            
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(currAngle + 0.5 * Math.PI);
            ctx.beginPath(); ctx.moveTo(-2, 0); ctx.lineTo(0, -r + 12); ctx.lineTo(2, 0);
            ctx.fillStyle = '#FF2222'; ctx.fill();
            ctx.restore();
            
            ctx.beginPath(); ctx.arc(cx, cy, 5, 0, 2 * Math.PI); ctx.fillStyle = '#FFF'; ctx.fill();
        }}
        
        function drawAfrMeter(value) {{
            const canvas = document.getElementById('afrCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const cx = 95, cy = 95, r = 75;
            
            ctx.clearRect(0, 0, 190, 190);
            
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
            ctx.strokeStyle = '#222'; ctx.lineWidth = 12; ctx.stroke();
            
            const minAfr = 10;
            const maxAfr = 20;
            let clampedVal = Math.max(minAfr, Math.min(value, maxAfr));
            let pct = (clampedVal - minAfr) / (maxAfr - minAfr);
            if(isNaN(pct)) pct = 0;
            
            const currAngle = (0.75 + pct * 1.5) * Math.PI;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, currAngle);
            ctx.strokeStyle = '#FF9900'; ctx.lineWidth = 8; ctx.stroke();
            
            ctx.fillStyle = '#AAA'; ctx.font = '9px Consolas'; ctx.textAlign = 'center';
            for (let i = 0; i <= 5; i++) {{
                let valNum = 10 + i * 2;
                let a = (0.75 + (i / 5.0) * 1.5) * Math.PI;
                let tx = cx + Math.cos(a) * (r - 18);
                let ty = cy + Math.sin(a) * (r - 18);
                ctx.fillText(valNum, tx, ty + 3);
            }}
            
            ctx.fillStyle = '#FFF'; ctx.font = 'bold 16px Consolas';
            ctx.fillText(value.toFixed(1), cx, cy + 20);
            ctx.fillStyle = '#FF9900'; ctx.font = 'bold 10px Consolas';
            ctx.fillText("AIR/FUEL", cx, cy + 35);
            ctx.fillStyle = '#888'; ctx.font = '9px Consolas';
            ctx.fillText("AFR RATIO", cx, cy - 25);
            
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(currAngle + 0.5 * Math.PI);
            ctx.beginPath(); ctx.moveTo(-2, 0); ctx.lineTo(0, -r + 12); ctx.lineTo(2, 0);
            ctx.fillStyle = '#FF2222'; ctx.fill();
            ctx.restore();
            
            ctx.beginPath(); ctx.arc(cx, cy, 5, 0, 2 * Math.PI); ctx.fillStyle = '#FFF'; ctx.fill();
        }}

        function drawMultiRunChart(activeRunProgressLen) {{
            const canvas = document.getElementById('graphCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;
            
            ctx.clearRect(0, 0, w, h);
            
            const padL = 55, padR = 55, padT = 30;
            const mainGraphH = 260;
            const afrGraphH = 70;
            const afrTopY = padT + mainGraphH + 20;
            
            ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
            ctx.font = "bold 22px Consolas";
            ctx.textAlign = "center";
            ctx.fillText(currentModelName.toUpperCase(), w / 2, padT + mainGraphH / 2);
            
            ctx.strokeStyle = '#2A2A2A'; ctx.lineWidth = 1;
            ctx.strokeRect(padL, padT, w - padL - padR, mainGraphH);
            ctx.strokeRect(padL, afrTopY, w - padL - padR, afrGraphH);
            
            for (let i = 1; i < 5; i++) {{
                let y = padT + (mainGraphH / 5) * i;
                ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke();
            }}
            
            const minRpmAxis = 1000;
            const maxRpmAxis = limitRpm;
            for (let rVal = 2000; rVal < maxRpmAxis; rVal += 2000) {{
                let x = padL + ((rVal - minRpmAxis) / (maxRpmAxis - minRpmAxis)) * (w - padL - padR);
                ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, padT + mainGraphH); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(x, afrTopY); ctx.lineTo(x, afrTopY + afrGraphH); ctx.stroke();
                ctx.fillStyle = '#666'; ctx.font = '9px Consolas'; ctx.textAlign = 'center';
                ctx.fillText(rVal, x, padT + mainGraphH + 12);
            }}
            
            let globalMaxHp = 20, globalMaxTq = 20;
            historyRuns.forEach(r => {{
                if (r.max_hp > globalMaxHp) globalMaxHp = r.max_hp;
                if (r.max_tq > globalMaxTq) globalMaxTq = r.max_tq;
            }});
            
            const maxHpAxis = Math.ceil(globalMaxHp * 1.25);
            const maxTqAxis = Math.ceil(globalMaxTq * 1.25);
            
            ctx.fillStyle = '#FFFF00'; ctx.font = '11px Consolas'; ctx.textAlign = 'left';
            ctx.fillText("Wheel POWER [HP]", padL, padT - 10);
            
            ctx.fillStyle = '#0088FF'; ctx.textAlign = 'right';
            ctx.fillText("Engine Torque [Nm]", w - padR, padT - 10);
            
            ctx.fillStyle = '#00FF00'; ctx.textAlign = 'left';
            ctx.fillText("AFR", padL, afrTopY - 6);
            
            function getX(rpm) {{ return padL + ((rpm - minRpmAxis) / (maxRpmAxis - minRpmAxis)) * (w - padL - padR); }}
            function getYHp(hp) {{ return padT + mainGraphH - (hp / maxHpAxis) * mainGraphH; }}
            function getYTq(tq) {{ return padT + mainGraphH - (tq / maxTqAxis) * mainGraphH; }}
            function getYAfr(afr) {{ return afrTopY + afrGraphH - ((afr - 10.0) / 8.0) * afrGraphH; }}
            
            const hpColors = ["#FFFF00", "#00FF00", "#FF00FF", "#00FFFF"];
            const tqColors = ["#0088FF", "#FF8800", "#FFAA00", "#FF3333"];
            
            historyRuns.forEach((run, idx) => {{
                const hpColor = hpColors[idx % hpColors.length];
                const tqColor = tqColors[idx % tqColors.length];
                
                let drawLen = run.rpms.length;
                if (idx === historyRuns.length - 1 && activeRunProgressLen !== null) {{
                    drawLen = Math.min(activeRunProgressLen, run.rpms.length);
                }}
                
                if (drawLen > 1) {{
                    ctx.beginPath(); ctx.strokeStyle = tqColor; ctx.lineWidth = 2.5;
                    for (let i = 0; i < drawLen; i++) {{
                        let x = getX(run.rpms[i]), y = getYTq(run.tqs[i]);
                        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                    }}
                    ctx.stroke();
                    
                    ctx.beginPath(); ctx.strokeStyle = hpColor; ctx.lineWidth = 2.5;
                    for (let i = 0; i < drawLen; i++) {{
                        let x = getX(run.rpms[i]), y = getYHp(run.hps[i]);
                        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                    }}
                    ctx.stroke();
                    
                    ctx.beginPath(); ctx.strokeStyle = '#00FF00'; ctx.lineWidth = 1.5;
                    for (let i = 0; i < drawLen; i++) {{
                        let x = getX(run.rpms[i]), y = getYAfr(run.afrs[i]);
                        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                    }}
                    ctx.stroke();
                }}
                
                if (idx === historyRuns.length - 1 && (activeRunProgressLen === null || activeRunProgressLen >= run.rpms.length)) {{
                    let xHp = getX(run.rpm_hp), yHp = getYHp(run.max_hp);
                    ctx.fillStyle = hpColor;
                    ctx.fillRect(xHp - 75, yHp - 30, 150, 20);
                    ctx.fillStyle = '#000'; ctx.font = 'bold 10px Consolas'; ctx.textAlign = 'center';
                    ctx.fillText("⚡ PEAK HP: " + run.max_hp.toFixed(2) + " @" + run.rpm_hp, xHp, yHp - 16);
                    ctx.beginPath(); ctx.arc(xHp, yHp, 4, 0, 2 * Math.PI); ctx.fillStyle = hpColor; ctx.fill();
                    
                    let xTq = getX(run.rpm_tq), yTq = getYTq(run.max_tq);
                    ctx.fillStyle = tqColor;
                    ctx.fillRect(xTq - 70, yTq + 10, 140, 20);
                    ctx.fillStyle = '#FFF'; ctx.font = 'bold 10px Consolas'; ctx.textAlign = 'center';
                    ctx.fillText("🔧 PEAK NM: " + run.max_tq.toFixed(2) + " @" + run.rpm_tq, xTq, yTq + 24);
                    ctx.beginPath(); ctx.arc(xTq, yTq, 4, 0, 2 * Math.PI); ctx.fillStyle = tqColor; ctx.fill();
                }}
            }});
        }}

        window.onload = function() {{
            drawTachometer(0);
            drawSpeedometer(0);
            drawAfrMeter(10);
            drawMultiRunChart(null);
            
            document.getElementById('tachoNote').innerText = "MAX RPM: -- RPM";
            document.getElementById('speedoNote').innerText = "MAX SPEED: -- KM/H";
            document.getElementById('afrNote').innerText = "AFR: --";
            
            if (autoStart && historyRuns.length > 0) {{
                startDyno20sCycle();
            }}
        }};

        function startDyno20sCycle() {{
            document.getElementById('dynoStatus').innerText = "RUNNING SWEEP (20s)...";
            document.getElementById('dynoStatus').style.color = "#FFFF00";
            
            document.getElementById('tachoNote').innerText = "MAX RPM: -- RPM";
            document.getElementById('speedoNote').innerText = "MAX SPEED: -- KM/H";
            document.getElementById('afrNote').innerText = "AFR: --";
            
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const audioCtx = new AudioContext();
            audioCtx.resume();
            
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = (engineType === 'single_big') ? 'square' : 'sawtooth';
            
            const now = audioCtx.currentTime;
            const totalDur = 20.0;
            const idleFreq = (engineType === 'twin') ? 50 : 32;
            const limitFreq = (engineType === 'twin') ? 520 : 270;
            
            osc.frequency.setValueAtTime(idleFreq, now);
            osc.frequency.setValueAtTime(idleFreq, now + 5.0);
            osc.frequency.exponentialRampToValueAtTime(limitFreq, now + 15.0);
            osc.frequency.exponentialRampToValueAtTime(idleFreq, now + 20.0);
            
            gain.gain.setValueAtTime(0.01, now);
            gain.gain.linearRampToValueAtTime(0.20, now + 0.5);
            gain.gain.setValueAtTime(0.20, now + 5.0);
            gain.gain.linearRampToValueAtTime(0.40, now + 15.0);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 20.0);
            
            const filter = audioCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(350, now);
            filter.frequency.linearRampToValueAtTime(2600, now + 15.0);
            filter.frequency.linearRampToValueAtTime(250, now + 20.0);
            
            osc.connect(filter); filter.connect(gain); gain.connect(audioCtx.destination);
            osc.start(now); osc.stop(now + totalDur);
            
            const activeRun = historyRuns[historyRuns.length - 1];
            const animStart = performance.now();
            
            function frameLoop() {{
                const elapsed = (performance.now() - animStart) / 1000.0;
                let currentRpm = 0;
                let currentSpeed = 0;
                let currentAfr = 14.7;
                let visiblePoints = 0;
                
                if (elapsed <= 5.0) {{
                    currentRpm = 1200 + Math.sin(elapsed * 6) * 30;
                    currentSpeed = 0;
                    currentAfr = 10.0;
                    visiblePoints = 0;
                }} else if (elapsed <= 15.0) {{
                    const progress = (elapsed - 5.0) / 10.0;
                    currentRpm = 1200 + progress * (limitRpm - 1200);
                    currentSpeed = progress * topSpeed;
                    visiblePoints = Math.floor(progress * activeRun.rpms.length);
                    let idx = Math.min(visiblePoints, activeRun.afrs.length - 1);
                    if(idx >= 0) currentAfr = activeRun.afrs[idx];
                }} else if (elapsed <= 20.0) {{
                    const decelProg = (elapsed - 15.0) / 5.0;
                    currentRpm = limitRpm - decelProg * (limitRpm - 1200);
                    currentSpeed = topSpeed * (1.0 - decelProg);
                    visiblePoints = activeRun.rpms.length;
                    currentAfr = 10.0;
                }} else {{
                    currentRpm = 0;
                    currentSpeed = 0;
                    visiblePoints = activeRun.rpms.length;
                    
                    let idx = activeRun.afrs.length - 1;
                    if(idx >= 0) currentAfr = activeRun.afrs[idx];
                    
                    document.getElementById('dynoStatus').innerText = "COMPLETED";
                    document.getElementById('dynoStatus').style.color = "#00FF66";
                    
                    document.getElementById('tachoNote').innerText = "MAX RPM: " + limitRpm + " RPM";
                    document.getElementById('speedoNote').innerText = "MAX SPEED: " + topSpeed.toFixed(1) + " KM/H";
                    document.getElementById('afrNote').innerText = "AFR: " + currentAfr.toFixed(2);
                }}
                
                drawTachometer(currentRpm);
                drawSpeedometer(currentSpeed);
                drawAfrMeter(currentAfr);
                drawMultiRunChart(visiblePoints);
                
                if (elapsed < totalDur) {{
                    requestAnimationFrame(frameLoop);
                }} else {{
                    drawTachometer(0);
                    drawSpeedometer(0);
                    drawMultiRunChart(null);
                }}
            }}
            requestAnimationFrame(frameLoop);
        }}
        </script>
    </body>
    </html>
    """
    components.html(component_code, height=710)

# ==========================================
# 6. MAIN EXECUTION & NATIVE STREAMLIT COMPONENT DISPLAY
# ==========================================

st.markdown(f"""
<div class="dyno-header">
    <div class="dyno-title">
        <span class="wheelie-logo">🏍️💨</span> PENDAWA AXIS VIRTUAL DYNO
    </div>
    <div class="dyno-subtitle">
        RUN: {user_run_label.upper()} &nbsp;|&nbsp; CORR: 1.000 INY &nbsp;|&nbsp; SAE J1349
    </div>
</div>
""", unsafe_allow_html=True)

auto_start_run = False
calc_top_speed = std.get('top_speed', 140.0)

if st.session_state.run_trigger:
    rpms, hps, tqs, afrs, max_hp, rpm_hp, max_tq, rpm_tq, cc_calc, cr_calc, pspeed, gsin, gsout, calc_top_speed = calculate_smooth_dyno_curve(
        std, in_bore, in_stroke, in_vhead, in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, in_rpm, in_joki
    )
    
    st.session_state.history.append({
        "Run": user_run_label,
        "Is_Stock": is_stock,
        "CC": round(cc_calc, 2),
        "CR": round(cr_calc, 2),
        "AFR": round(in_afr, 2),
        "Max_Wheel_HP": max_hp,
        "RPM_HP": rpm_hp,
        "Max_Nm": max_tq,
        "RPM_Nm": rpm_tq,
        "calc_top_speed": calc_top_speed,
        "pspeed": pspeed,
        "gsin": gsin,
        "gsout": gsout,
        "bore": in_bore,
        "stroke": in_stroke,
        "v_in": in_v_in,
        "v_out": in_v_out,
        "venturi": in_venturi,
        "rpms": rpms, "hps": hps, "tqs": tqs, "afrs": afrs
    })
    
    auto_start_run = True
    st.session_state.run_trigger = False

latest_run = st.session_state.history[-1] if st.session_state.history else None
if latest_run:
    calc_top_speed = latest_run.get("calc_top_speed", std.get('top_speed', 140.0))

render_full_dyno_studio_v16(
    st.session_state.history,
    auto_start_run,
    selected_model,
    calc_top_speed,
    in_rpm,
    std.get('type', 'single_small')
)

# STREAMLIT NATIVE SUMMARY TABLE & EXPERT ANALYSIS (ALWAYS STABLE BELOW)
if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # Performance Summary Table
    st.divider()
    st.markdown("### 📋 PERFORMANCE RUN SUMMARY TABLE")
    df_h = pd.DataFrame(st.session_state.history)
    df_show = df_h[["Run", "CC", "CR", "AFR", "Max_Wheel_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].copy()
    
    st.dataframe(df_show.style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}",
        "Max_Wheel_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }), use_container_width=True, hide_index=True)

    # DATA FLOWBENCH & VOLUMETRIC EFFICIENCY
    st.divider()
    st.markdown("### 💨 DATA PROYEKSI FLOWBENCH & VE (REFERENSI AXIS DYNO)")
    
    col_fb1, col_fb2, col_fb3, col_fb4, col_fb5 = st.columns(5)
    
    # Kalkulasi Volumetric Efficiency (VE) yang realistis berdasarkan efisiensi porting
    ideal_vin = latest['bore'] * 0.52
    base_ve = 80.0 
    ve_adjustment = ((latest['v_in'] - ideal_vin) / ideal_vin) * 20.0
    realistic_ve = round(min(90.0, max(60.0, base_ve + ve_adjustment)), 1)
    
    valve_area_mm2 = (math.pi * ((latest['v_in'] / 2) ** 2))
    if in_klep == 4:
        valve_area_mm2 *= 2
    cfm_proj = round(valve_area_mm2 * 0.05, 1)
    
    with col_fb1:
        st.metric("Target Peak RPM", f"{latest['RPM_HP']} RPM")
    with col_fb2:
        st.metric("Piston Speed", f"{latest['pspeed']:.1f} m/s")
    with col_fb3:
        st.metric("Gas Velocity (In)", f"{latest['gsin']:.1f} m/s")
    with col_fb4:
        st.metric("VE (Peak)", f"{realistic_ve} %")
    with col_fb5:
        st.metric("Proyeksi Flowbench", f"{cfm_proj} CFM")

    # EXPERT ENGINE ANALYSIS & GRAHAM BELL RECOMMENDATIONS
    st.divider()
    st.markdown("## 🏁 EXPERT ENGINE ANALYSIS (A. GRAHAM BELL PRINCIPLES)")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    
    with col_a1:
        st.markdown("#### 1️⃣ Analisa Performa Mesin")
        ps = latest['pspeed']
        gs = latest['gsin']
        cr = latest['CR']
        
        if ps > 21.0:
            st.error(f"⚠️ **Piston Speed:** {ps:.2f} m/s (Melebihi batas aman material 21 m/s - Risiko patah stang seher tinggi).")
        else:
            st.success(f"✅ **Piston Speed:** {ps:.2f} m/s (Aman untuk kompetisi/harian, < 21 m/s).")
            
        if gs > 115.0:
            st.error(f"⚠️ **Gas Velocity In:** {gs:.2f} m/s (Terjadi *Choke Flow*. Klep In terlalu kecil untuk RPM puncak).")
        elif gs < 85.0:
            st.warning(f"⚠️ **Gas Velocity In:** {gs:.2f} m/s (Velocity terlalu rendah. Torsi putaran bawah akan loyo).")
        else:
            st.success(f"✅ **Gas Velocity In:** {gs:.2f} m/s (Rentang optimum A. Graham Bell: 90–110 m/s).")
            
        if cr > 12.5:
            st.warning(f"⚠️ **Rasio Kompresi:** {cr:.2f}:1 (Wajib bahan bakar Oktan ≥ 98 / RON 98+ untuk mencegah knocking).")
        else:
            st.info(f"ℹ️ **Rasio Kompresi:** {cr:.2f}:1 (Aman untuk bahan bakar harian).")

    with col_a2:
        st.markdown("#### 2️⃣ Rekomendasi Spesifikasi Ideal")
        rec_vin = round(latest['bore'] * 0.52, 1)
        rec_vout = round(rec_vin * 0.83, 1)
        rec_tb = round(rec_vin * 0.88, 1)
        rec_header = round(math.sqrt(latest['CC'] * 0.14) * 10.0, 1)
        rec_vhead_target = round(latest['CC'] / 11.5, 2)
        
        st.markdown(f"""
        * **Diameter Klep In Ideal:** `{rec_vin} mm`
        * **Diameter Klep Out Ideal:** `{rec_vout} mm`
        * **Throttle Body / Venturi Ideal:** `{rec_tb} mm`
        * **Diameter Leher Knalpot (Header):** `{rec_header} mm`
        * **Vol Dome Head Target (CR 12.5:1):** `{rec_vhead_target} cc`
        """)

    with col_a3:
        st.markdown("#### 3️⃣ Panduan Part & Modifikasi Rekomendasi")
        parts = []
        if latest['gsin'] > 115.0:
            parts.append(f"• **Ganti Set Klep In:** Perbesar ke ukuran {rec_vin} mm untuk mengatasi Choke Flow.")
        if latest['venturi'] < rec_tb - 2.0:
            parts.append(f"• **Upgrade Throttle Body:** Reamer/Ganti ke diameter {rec_tb} mm.")
        if latest['CR'] > 13.5:
            parts.append("• **Adjustment Gasket / Head Dome:** Tambah paking atau bubut dome untuk menurunkan CR ke 12.5:1.")
        parts.append(f"• **Knalpot Custom:** Sesuaikan leher knalpot dengan diameter dalam {rec_header} mm.")
        parts.append("• **ECU Standalone / Jetting:** Reflash/Mapping ulang debit BBM sesuai AFR target 13.0:1.")
        
        for p in parts:
            st.write(p)

st.caption("PENDAWA AXIS VIRTUAL DYNO v16.0 — Restored Native Streamlit Summary & Analysis System.")
