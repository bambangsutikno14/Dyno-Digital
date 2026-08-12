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
    page_title="HIAR AXIS VIRTUAL DYNO v7",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Consolas', 'Courier New', monospace; }
    
    .dyno-header {
        background: linear-gradient(90deg, #111111 0%, #222222 100%);
        padding: 10px 18px;
        border-radius: 4px;
        border-bottom: 3px solid #00FF66;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dyno-title { font-size: 1.3rem; font-weight: bold; color: #FFFFFF; letter-spacing: 1px; }
    .dyno-subtitle { font-size: 0.85rem; color: #00FF66; }
    
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ACCURATE MANUFACTURER DATABASE
# ==========================================
DATABASE_REF = {
    "YAMAHA": {
        "XMAX 250 (Lokal Indonesia)": {
            "bore": 70.0, "stroke": 64.9, "v_head": 26.2, "valve_in": 30.0, "valve_out": 26.0, "venturi": 34.0, 
            "hp_crank_std": 22.5, "torque_crank_std": 24.3, "peak_rpm_hp": 7000, "peak_rpm_tq": 5500, "limit_std": 9000, "weight_std": 179.0, 
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
        "NMAX 155 / Aerox 155 (VVA)": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, 
            "hp_crank_std": 15.1, "torque_crank_std": 13.9, "peak_rpm_hp": 8000, "peak_rpm_tq": 6500, "limit_std": 9500, "weight_std": 127.0, 
            "type": "single_small", "cvt_loss": 0.18, "top_speed": 125.0
        },
        "Mio Karbu 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, 
            "hp_crank_std": 8.8, "torque_crank_std": 7.84, "peak_rpm_hp": 8000, "peak_rpm_tq": 6500, "limit_std": 9000, "weight_std": 92.0, 
            "type": "single_small", "cvt_loss": 0.20, "top_speed": 105.0
        }
    },
    "HONDA": {
        "Vario 160 / PCX 160 (eSP+)": {
            "bore": 60.0, "stroke": 55.5, "v_head": 14.2, "valve_in": 27.0, "valve_out": 22.0, "venturi": 30.0, 
            "hp_crank_std": 15.6, "torque_crank_std": 15.0, "peak_rpm_hp": 8500, "peak_rpm_tq": 6500, "limit_std": 9800, "weight_std": 117.0, 
            "type": "single_small", "cvt_loss": 0.18, "top_speed": 128.0
        },
        "Vario 150 / PCX 150": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, 
            "hp_crank_std": 12.9, "torque_crank_std": 13.4, "peak_rpm_hp": 8500, "peak_rpm_tq": 5000, "limit_std": 9800, "weight_std": 109.0, 
            "type": "single_small", "cvt_loss": 0.19, "top_speed": 118.0
        },
        "BeAT FI / Scoopy 110": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, 
            "hp_crank_std": 8.56, "torque_crank_std": 9.01, "peak_rpm_hp": 7500, "peak_rpm_tq": 6500, "limit_std": 9200, "weight_std": 89.0, 
            "type": "single_small", "cvt_loss": 0.20, "top_speed": 102.0
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 3. THERMODYNAMIC ENGINE CALCULATION
# ==========================================
def calculate_smooth_dyno_curve(std_spec, in_bore, in_stroke, in_vhead, in_v_in, in_v_out, in_venturi, in_afr, limit_rpm):
    raw_rpms = np.arange(1000, int(limit_rpm) + 100, 100)
    rpms = [int(r) for r in raw_rpms]
    
    cc_calc = float((0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0)
    cr_calc = float((cc_calc + float(in_vhead)) / float(in_vhead))
    
    cvt_loss = float(std_spec.get('cvt_loss', 0.18))
    crank_tq_peak = float(std_spec['torque_crank_std'])
    if in_bore > std_spec['bore']: crank_tq_peak *= (1.0 + (in_bore - std_spec['bore'])*0.02)
    wheel_tq_peak = crank_tq_peak * (1.0 - cvt_loss)
    
    rpm_tq_peak = float(std_spec['peak_rpm_tq'])
    rpm_hp_peak = float(std_spec['peak_rpm_hp'])
    
    wheel_hps, torques, afrs = [], [], []
    
    for r in rpms:
        if r < 1500:
            tq = wheel_tq_peak * 0.30 * (r / 1500.0)
        else:
            tq = wheel_tq_peak * (0.40 + 0.60 * math.exp(-((r - rpm_tq_peak) / 3800.0)**2))
            if r > limit_rpm - 400:
                tq *= (1.0 - ((r - (limit_rpm - 400)) / 400.0)**2)
                
        hp = (tq * r) / 7023.5 if r > 0 else 0.0
        afr_val = float(in_afr) + 0.2 * math.sin(r / 800.0)
        
        torques.append(float(round(max(0.0, tq), 2)))
        wheel_hps.append(float(round(max(0.0, hp), 2)))
        afrs.append(float(round(afr_val, 2)))
        
    max_hp = float(max(wheel_hps))
    max_tq = float(max(torques))
    idx_hp = int(np.argmax(wheel_hps))
    idx_tq = int(np.argmax(torques))
    
    rpm_hp = int(rpms[idx_hp])
    rpm_tq = int(rpms[idx_tq])
    
    # Mechanics Physics Indicators
    pspeed = float((2.0 * in_stroke * rpm_hp) / 60000.0)
    gsin = float(((in_bore / in_v_in)**2) * pspeed)
    gsout = float(((in_bore / in_v_out)**2) * pspeed)
    
    return rpms, wheel_hps, torques, afrs, max_hp, rpm_hp, max_tq, rpm_tq, cc_calc, cr_calc, pspeed, gsin, gsout

# ==========================================
# 4. DYNAMIC SIDEBAR CONTROLS (BUG-FREE SWITCHING)
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ ENGINE SELECTION")
    
    # Fixed Manufacturer Selection
    if "selected_merk" not in st.session_state:
        st.session_state.selected_merk = list(DATABASE_REF.keys())[0]
        
    selected_merk = st.selectbox("Manufacturer", list(DATABASE_REF.keys()), key="selected_merk")
    
    # Dynamic Engine Model Selection tied to selected Manufacturer
    models_for_merk = list(DATABASE_REF[selected_merk].keys())
    selected_model = st.selectbox("Engine Model", models_for_merk, key=f"model_select_{selected_merk}")
    
    std = DATABASE_REF[selected_merk][selected_model]
    st.divider()

    st.markdown("### ⚙️ MECHANIC TUNING PARAMETERS")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        in_bore = st.number_input("Bore (mm)", value=float(std['bore']), step=0.5)
        in_vhead = st.number_input("Vol Head (cc)", value=float(std['v_head']), step=0.1)
    with col_s2:
        in_stroke = st.number_input("Stroke (mm)", value=float(std['stroke']), step=0.5)
        in_rpm = st.number_input("Limit RPM", value=int(std['limit_std']), step=250)

    # Real-Time Display of Engine Displacement & CR (FIXED)
    cc_real = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    cr_real = (cc_real + float(in_vhead)) / float(in_vhead)
    
    st.markdown(f"""
    <div class="cc-box">
        <div class="cc-title">DISPLACEMENT & COMPRESSION</div>
        <div class="cc-value">{cc_real:.2f} cc &nbsp;|&nbsp; {cr_real:.2f}:1</div>
    </div>
    """, unsafe_allow_html=True)

    expert_on = st.toggle("🧪 Valve & Flow Specs", value=True)
    if expert_on:
        in_v_in = st.number_input("Valve In (mm)", value=float(std['valve_in']), step=0.5)
        in_v_out = st.number_input("Valve Out (mm)", value=float(std['valve_out']), step=0.5)
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
    
    run_btn = st.button("🚀 PROCESS & RUN DYNO SWEEP")
    
    if st.button("🗑️ RESET ALL HISTORY"):
        st.session_state.history = []
        st.rerun()

# ==========================================
# 5. FULLY SYNCHRONIZED STUDIO CANVAS COMPONENT
# ==========================================
def render_full_dyno_studio_v7(rpms, hps, tqs, afrs, max_hp, rpm_hp, max_tq, rpm_tq, top_speed, limit_rpm, engine_type, run_label):
    
    rpms_clean = [int(x) for x in rpms]
    hps_clean = [float(x) for x in hps]
    tqs_clean = [float(x) for x in tqs]
    afrs_clean = [float(x) for x in afrs]
    
    rpms_json = json.dumps(rpms_clean)
    hps_json = json.dumps(hps_clean)
    tqs_json = json.dumps(tqs_clean)
    afrs_json = json.dumps(afrs_clean)
    
    max_hp_f = float(max_hp)
    max_tq_f = float(max_tq)
    rpm_hp_i = int(rpm_hp)
    rpm_tq_i = int(rpm_tq)
    limit_rpm_i = int(limit_rpm)
    top_speed_f = float(top_speed)
    
    component_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ background-color: #0A0A0A; color: #FFF; font-family: Consolas, monospace; margin: 0; padding: 10px; }}
            .studio-card {{ border: 2px solid #222; border-radius: 8px; padding: 12px; background-color: #0D0D0D; }}
            .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
            .run-btn {{
                background-color: #00FF66; color: #000; font-weight: bold; font-size: 1.1rem;
                border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer;
                box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
            }}
            .run-btn:hover {{ background-color: #00CC52; box-shadow: 0 0 20px rgba(0, 255, 102, 0.7); }}
            .gauges-row {{ display: flex; justify-content: center; gap: 30px; background-color: #111; padding: 10px; border-radius: 6px; border: 1px solid #333; margin-bottom: 12px; }}
        </style>
    </head>
    <body>
        <div class="studio-card">
            <div class="top-bar">
                <button class="run-btn" onclick="startFullDynoCycle()">▶️ MULAI RUN DYNO (20 DETIK) + SUARA MESIN</button>
                <div style="text-align:right; color:#00FF66; font-size:0.9rem;">
                    STATUS: <span id="dynoStatus" style="color:#FFF;">READY</span>
                </div>
            </div>

            <!-- ANALOG GAUGES -->
            <div class="gauges-row">
                <div style="text-align:center;">
                    <canvas id="tachoCanvas" width="180" height="180"></canvas>
                    <div style="color:#00FF00; font-weight:bold; font-size:0.85rem; margin-top:2px;">TACHOMETER (RPM)</div>
                </div>
                <div style="text-align:center;">
                    <canvas id="speedoCanvas" width="180" height="180"></canvas>
                    <div style="color:#0088FF; font-weight:bold; font-size:0.85rem; margin-top:2px;">SPEEDOMETER (KM/H)</div>
                </div>
            </div>

            <!-- DYNAMIC GRAPH CANVAS -->
            <div style="position:relative; width:100%;">
                <canvas id="graphCanvas" width="850" height="420" style="width:100%; background-color:#050505; border:1px solid #333; border-radius:4px;"></canvas>
            </div>
        </div>

        <script>
        const rpms = {rpms_json};
        const hps = {hps_json};
        const tqs = {tqs_json};
        const afrs = {afrs_json};
        
        const maxHp = {max_hp_f};
        const rpmHp = {rpm_hp_i};
        const maxTq = {max_tq_f};
        const rpmTq = {rpm_tq_i};
        
        const limitRpm = {limit_rpm_i};
        const topSpeed = {top_speed_f};
        const engineType = "{engine_type}";

        function drawGauge(canvasId, value, maxVal, unit, isRpm) {{
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const cx = 90, cy = 90, r = 70;
            
            ctx.clearRect(0, 0, 180, 180);
            
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
            ctx.strokeStyle = '#222';
            ctx.lineWidth = 10;
            ctx.stroke();
            
            const currAngle = (0.75 + (Math.min(value, maxVal) / maxVal) * 1.5) * Math.PI;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0.75 * Math.PI, currAngle);
            ctx.strokeStyle = isRpm ? '#00FF00' : '#0088FF';
            ctx.lineWidth = 6;
            ctx.stroke();
            
            ctx.fillStyle = '#FFF';
            ctx.font = 'bold 16px Consolas';
            ctx.textAlign = 'center';
            ctx.fillText(Math.round(value), cx, cy + 25);
            ctx.fillStyle = '#888';
            ctx.font = '9px Consolas';
            ctx.fillText(unit, cx, cy + 38);
            
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(currAngle + 0.5 * Math.PI);
            ctx.beginPath();
            ctx.moveTo(-2, 0);
            ctx.lineTo(0, -r + 10);
            ctx.lineTo(2, 0);
            ctx.fillStyle = '#FF2222';
            ctx.fill();
            ctx.restore();
            
            ctx.beginPath();
            ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
            ctx.fillStyle = '#FFF';
            ctx.fill();
        }}

        function drawDynoChart(visibleLen, showBadges) {{
            const canvas = document.getElementById('graphCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;
            
            ctx.clearRect(0, 0, w, h);
            
            const padL = 55, padR = 55, padT = 30;
            const mainGraphH = 260;
            const afrGraphH = 70;
            const afrTopY = padT + mainGraphH + 20;
            
            ctx.strokeStyle = '#222'; ctx.lineWidth = 1;
            ctx.strokeRect(padL, padT, w - padL - padR, mainGraphH);
            ctx.strokeRect(padL, afrTopY, w - padL - padR, afrGraphH);
            
            for (let i = 1; i < 5; i++) {{
                let y = padT + (mainGraphH / 5) * i;
                ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke();
            }}
            
            const maxHpAxis = Math.ceil(maxHp * 1.25);
            const maxTqAxis = Math.ceil(maxTq * 1.25);
            const minRpmAxis = 1000;
            const maxRpmAxis = limitRpm;
            
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
            
            const drawLen = Math.min(visibleLen, rpms.length);
            
            if (drawLen > 1) {{
                // Torque Line (Blue)
                ctx.beginPath(); ctx.strokeStyle = '#0088FF'; ctx.lineWidth = 3;
                for (let i = 0; i < drawLen; i++) {{
                    let x = getX(rpms[i]), y = getYTq(tqs[i]);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }}
                ctx.stroke();
                
                // HP Line (Yellow)
                ctx.beginPath(); ctx.strokeStyle = '#FFFF00'; ctx.lineWidth = 3;
                for (let i = 0; i < drawLen; i++) {{
                    let x = getX(rpms[i]), y = getYHp(hps[i]);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }}
                ctx.stroke();
                
                // AFR Line (Green)
                ctx.beginPath(); ctx.strokeStyle = '#00FF00'; ctx.lineWidth = 2;
                for (let i = 0; i < drawLen; i++) {{
                    let x = getX(rpms[i]), y = getYAfr(afrs[i]);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }}
                ctx.stroke();
            }}
            
            // PEAK NOTIFICATION BADGES
            if (showBadges) {{
                // Peak HP
                let xHp = getX(rpmHp), yHp = getYHp(maxHp);
                ctx.fillStyle = '#FFFF00';
                ctx.fillRect(xHp - 75, yHp - 32, 150, 22);
                ctx.fillStyle = '#000'; ctx.font = 'bold 10px Consolas'; ctx.textAlign = 'center';
                ctx.fillText("⚡ PEAK HP: " + maxHp.toFixed(2) + " @" + rpmHp, xHp, yHp - 18);
                ctx.beginPath(); ctx.arc(xHp, yHp, 5, 0, 2 * Math.PI); ctx.fillStyle = '#FFFF00'; ctx.fill();
                
                // Peak Torque
                let xTq = getX(rpmTq), yTq = getYTq(maxTq);
                ctx.fillStyle = '#0088FF';
                ctx.fillRect(xTq - 75, yTq + 10, 150, 22);
                ctx.fillStyle = '#FFF'; ctx.font = 'bold 10px Consolas'; ctx.textAlign = 'center';
                ctx.fillText("🔧 PEAK NM: " + maxTq.toFixed(2) + " @" + rpmTq, xTq, yTq + 24);
                ctx.beginPath(); ctx.arc(xTq, yTq, 5, 0, 2 * Math.PI); ctx.fillStyle = '#0088FF'; ctx.fill();
            }}
        }}

        window.onload = function() {{
            drawGauge('tachoCanvas', 1200, limitRpm, 'RPM', true);
            drawGauge('speedoCanvas', 0, topSpeed, 'KM/H', false);
            drawDynoChart(rpms.length, true);
        }};

        function startFullDynoCycle() {{
            document.getElementById('dynoStatus').innerText = "RUNNING (20s)...";
            document.getElementById('dynoStatus').style.color = "#FFFF00";
            
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
            
            const animStart = performance.now();
            function frameLoop() {{
                const elapsed = (performance.now() - animStart) / 1000.0;
                let currentRpm = 1200;
                let currentSpeed = 0;
                let visiblePoints = 0;
                let isFinished = false;
                
                if (elapsed <= 5.0) {{
                    currentRpm = 1200 + Math.sin(elapsed * 6) * 35;
                    currentSpeed = 0;
                    visiblePoints = 0;
                }} else if (elapsed <= 15.0) {{
                    const progress = (elapsed - 5.0) / 10.0;
                    currentRpm = 1200 + progress * (limitRpm - 1200);
                    currentSpeed = progress * topSpeed;
                    visiblePoints = Math.floor(progress * rpms.length);
                }} else if (elapsed <= 20.0) {{
                    const decelProg = (elapsed - 15.0) / 5.0;
                    currentRpm = limitRpm - decelProg * (limitRpm - 1200);
                    currentSpeed = topSpeed * (1.0 - decelProg);
                    visiblePoints = rpms.length;
                    isFinished = true;
                }} else {{
                    currentRpm = 1200; currentSpeed = 0; visiblePoints = rpms.length; isFinished = true;
                    document.getElementById('dynoStatus').innerText = "COMPLETED";
                    document.getElementById('dynoStatus').style.color = "#00FF66";
                }}
                
                drawGauge('tachoCanvas', currentRpm, limitRpm, 'RPM', true);
                drawGauge('speedoCanvas', currentSpeed, topSpeed, 'KM/H', false);
                drawDynoChart(visiblePoints, isFinished);
                
                if (elapsed < totalDur) {{
                    requestAnimationFrame(frameLoop);
                }}
            }}
            requestAnimationFrame(frameLoop);
        }}
        </script>
    </body>
    </html>
    """
    components.html(component_code, height=680)

# ==========================================
# 6. MAIN EXECUTION & EXPERT ANALYSIS
# ==========================================

st.markdown(f"""
<div class="dyno-header">
    <div>
        <span class="dyno-title">HORSE POWER RUN &nbsp;|&nbsp; {user_run_label.upper()}</span>
    </div>
    <div class="dyno-subtitle">
        CORR: 1.000 INY &nbsp;|&nbsp; SAE J1349 &nbsp;|&nbsp; REALTIME CHASSIS DYNO
    </div>
</div>
""", unsafe_allow_html=True)

if run_btn:
    rpms, hps, tqs, afrs, max_hp, rpm_hp, max_tq, rpm_tq, cc_calc, cr_calc, pspeed, gsin, gsout = calculate_smooth_dyno_curve(
        std, in_bore, in_stroke, in_vhead, in_v_in, in_v_out, in_venturi, in_afr, std['limit_std']
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

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # 1. Render Full Dyno Studio Canvas (Live 60 FPS + Audio)
    render_full_dyno_studio_v7(
        latest['rpms'], latest['hps'], latest['tqs'], latest['afrs'],
        latest['Max_Wheel_HP'], latest['RPM_HP'], latest['Max_Nm'], latest['RPM_Nm'],
        std.get('top_speed', 140.0), std['limit_std'], std.get('type', 'single_small'), latest['Run']
    )
    
    # 2. Performance Summary Table
    st.divider()
    st.markdown("### 📋 PERFORMANCE RUN SUMMARY TABLE")
    df_h = pd.DataFrame(st.session_state.history)
    df_show = df_h[["Run", "CC", "CR", "AFR", "Max_Wheel_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].copy()
    
    st.dataframe(df_show.style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}",
        "Max_Wheel_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }), use_container_width=True, hide_index=True)

    # 3. EXPERT ENGINE ANALYSIS & GRAHAM BELL RECOMMENDATIONS
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

st.caption("HIAR AXIS VIRTUAL DYNO v7.0 — Advanced Engine Tuning Engine & Graham Bell Diagnostics.")
