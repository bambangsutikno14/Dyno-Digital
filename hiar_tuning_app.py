import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIG & PROFESSIONAL DYNO CSS
# ==========================================
st.set_page_config(
    page_title="HIAR AXIS VIRTUAL DYNO SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Dyno Studio Theme */
    .stApp { background-color: #080808; color: #E0E0E0; font-family: 'Consolas', 'Courier New', monospace; }
    
    /* Header Bar */
    .dyno-header {
        background: linear-gradient(90deg, #151515 0%, #222222 100%);
        padding: 10px 20px;
        border-radius: 4px;
        border-bottom: 2px solid #00FF66;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dyno-title { font-size: 1.3rem; font-weight: bold; color: #FFFFFF; letter-spacing: 1px; }
    .dyno-subtitle { font-size: 0.9rem; color: #00FF66; }
    
    /* Digital LED Metrics Panel */
    .gauge-card {
        background-color: #0D0D0D;
        border: 2px solid #222222;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
        text-align: right;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
    }
    .gauge-label {
        font-size: 0.85rem;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 1px;
        float: left;
    }
    .gauge-value-main {
        font-size: 2.5rem;
        font-weight: 900;
        color: #00FF00;
        text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        line-height: 1.1;
    }
    .gauge-sub-row {
        margin-top: 5px;
        font-size: 0.8rem;
        color: #666666;
        border-top: 1px solid #1A1A1A;
        padding-top: 4px;
    }
    .gauge-value-sub { color: #00CC00; font-weight: bold; }
    
    /* Dyno Buttons */
    .stButton>button {
        width: 100%;
        background-color: #00FF66 !important;
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        border-radius: 4px !important;
        padding: 10px !important;
        border: none !important;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
    }
    .stButton>button:hover {
        background-color: #00CC52 !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.7);
    }
    
    /* Control Action Bar */
    .btn-share { background-color: #3b5998; color: white; padding: 6px 14px; border-radius: 3px; font-size: 0.8rem; font-weight: bold; }
    .btn-print { background-color: #555555; color: white; padding: 6px 14px; border-radius: 3px; font-size: 0.8rem; font-weight: bold; }
    .btn-diag { background-color: #00a8ff; color: white; padding: 6px 14px; border-radius: 3px; font-size: 0.8rem; font-weight: bold; }
    .btn-clear { background-color: #e1b12c; color: black; padding: 6px 14px; border-radius: 3px; font-size: 0.8rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. EXTENDED PABRIKAN DATABASE
# ==========================================
DATABASE_REF = {
    "YAMAHA": {
        "XMAX 250/300/310": {"bore": 70.0, "stroke": 64.9, "v_head": 28.0, "valve_in": 30.0, "valve_out": 26.0, "venturi": 34.0, "hp_std": 22.8, "peak_rpm": 7000, "limit_std": 9000, "weight_std": 179.0, "f_ratio": 2.80, "cvt_loss": 0.18},
        "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "f_ratio": 3.05, "cvt_loss": 0.17},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "f_ratio": 3.10, "cvt_loss": 0.20},
    },
    "HONDA": {
        "Vario 160 / PCX 160": {"bore": 60.0, "stroke": 55.5, "v_head": 15.0, "valve_in": 27.0, "valve_out": 22.0, "venturi": 30.0, "hp_std": 15.8, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 117.0, "f_ratio": 2.85, "cvt_loss": 0.16},
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "f_ratio": 2.90, "cvt_loss": 0.18},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, "hp_std": 8.56, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89.0, "f_ratio": 3.20, "cvt_loss": 0.20},
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 3. ADVANCED THERMODYNAMICS & FLUID ENGINE
# ==========================================
def calculate_dyno_run(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std_spec):
    rpms = np.arange(2500, int(rpm_limit) + 100, 100)
    crank_hps, wheel_hps, torques, afr_trace = [], [], [], []
    
    # Peak RPM adjustment based on Camshaft duration
    adj_peak = float(std_spec['peak_rpm']) + (((float(dur_in) + float(dur_out))/2.0 - 240.0) * 55.0)
    eff = 0.88 if "XMAX" in str(std_spec) or "160" in str(std_spec) else 0.84
    afr_mod = 1.0 - abs(float(afr) - 13.0) * 0.035
    
    # Detonation / High CR Thermal Penalty
    thermal_penalty = 1.0
    if cr > 14.5:
        thermal_penalty = 1.0 - ((cr - 14.5) * 0.12)
        
    # BMEP Base Calculation (Standard SAE Internal Combustion Engine Physics)
    bmep_bar = (float(std_spec['hp_std']) * 120000.0) / (float(cc) * adj_peak * eff)
    
    # Drivetrain CVT Loss Factor
    cvt_loss_factor = float(std_spec.get('cvt_loss', 0.18))
    
    for r in rpms:
        # Volumetric Efficiency Curve
        if r <= adj_peak:
            ve = math.exp(-((r - adj_peak) / 4200.0)**2)
        else:
            ve = math.exp(-((r - adj_peak) / 1900.0)**2)
            
        # Piston Speed & Gas Velocities
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / float(v_in))**2) * ps_speed
        gs_out = ((float(bore) / float(v_out))**2) * ps_speed
        
        # Choke Flow Penalty
        if gs_in > 125.0:
            ve *= (125.0 / gs_in)**1.8
        elif gs_in > 105.0:
            ve *= (105.0 / gs_in)
            
        # Crankshaft Power Calculation
        crank_hp = (bmep_bar * float(cc) * float(r) * ve * eff * afr_mod * thermal_penalty) / 120000.0
        if float(bore) > float(std_spec['bore']): crank_hp *= (1.0 + (float(cr) - 9.5) * 0.02)
        if float(venturi) > float(std_spec['venturi']): crank_hp *= (1.0 + (float(venturi) - float(std_spec['venturi'])) * 0.01)
        
        # Wheel Power (Drivetrain Efficiency subtracted)
        wheel_hp = crank_hp * (1.0 - cvt_loss_factor)
        
        # Torque Calculation (Nm) = (HP * 7023.5) / RPM
        torque_nm = (wheel_hp * 7023.5) / r if r > 0 else 0.0
        
        # Simulated Dynamic AFR Curve Trace
        dynamic_afr = float(afr) + 0.6 * math.sin(r / 700.0) - 0.3 * ((r - adj_peak) / 3000.0)
        
        crank_hps.append(round(crank_hp, 2))
        wheel_hps.append(round(wheel_hp, 2))
        torques.append(round(torque_nm, 2))
        afr_trace.append(round(dynamic_afr, 2))
        
    return rpms, wheel_hps, crank_hps, torques, afr_trace, ps_speed, gs_in, gs_out

# ==========================================
# 4. SIDEBAR ENGINE CONFIGURATION
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ DYNO BENCH CONFIG")
    merk = st.selectbox("Brand / Manufacturer", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Engine Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    st.divider()

    st.markdown("### ⚙️ PARAMETERS & BORE UP")
    raw_label = st.text_input("Run Name", value=f"Run-00{len(st.session_state.history)+1}")
    full_label = f"{raw_label}:autosave"
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std['bore']), step=0.5)
        in_vhead = st.number_input(f"Vol Head (cc)", value=float(std['v_head']), step=0.1)
    with col_s2:
        in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std['stroke']), step=0.5)
        in_rpm = st.number_input(f"Limit RPM", value=int(std['limit_std']), step=250)

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0
    st.info(f"Displacement: **{cc_calc:.2f} cc**")

    expert_on = st.toggle("🧪 Expert Tuning Parameters", value=True)
    if expert_on:
        in_v_in = st.number_input(f"Valve In (mm)", value=float(std['valve_in']), step=0.5)
        in_v_out = st.number_input(f"Valve Out (mm)", value=float(std['valve_out']), step=0.5)
        in_venturi = st.number_input(f"Throttle / Venturi (mm)", value=float(std['venturi']), step=0.5)
        in_dur_in = st.slider("Cam Duration In (°)", 200, 320, 240)
        in_dur_out = st.slider("Cam Duration Out (°)", 200, 320, 240)
        in_afr = st.slider("Target AFR Lambda", 11.0, 15.0, 13.0, step=0.1)
    else:
        in_v_in, in_v_out, in_venturi = std['valve_in'], std['valve_out'], std['venturi']
        in_dur_in, in_dur_out, in_afr = 240, 240, 13.0

    st.divider()
    in_joki = st.number_input("Rider Weight (kg)", value=65.0, step=1.0)
    
    run_btn = st.button("🏁 START DYNO RUN")

# ==========================================
# 5. ENGINE SOUND SYNTHESIZER (WEB AUDIO API)
# ==========================================
def play_dyno_audio_sweep():
    audio_js = """
    <script>
    function playDynoAudio() {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        // Oscillator 1 - Engine Pitch
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        
        // Pitch sweep simulating dyno pull (idle -> high RPM limit)
        const now = ctx.currentTime;
        osc.frequency.setValueAtTime(80, now);
        osc.frequency.exponentialRampToValueAtTime(450, now + 3.2);
        osc.frequency.setValueAtTime(450, now + 3.2);
        osc.frequency.setValueAtTime(0, now + 3.3); // Limiter Cutout
        
        // Gain Envelope
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.3, now + 0.5);
        gain.gain.linearRampToValueAtTime(0.4, now + 3.0);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 3.4);
        
        // Exhaust Noise Filter
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(400, now);
        filter.frequency.linearRampToValueAtTime(2500, now + 3.0);
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 3.5);
    }
    playDynoAudio();
    </script>
    """
    components.html(audio_js, height=0, width=0)

# ==========================================
# 6. MAIN EXECUTION & DISPLAY
# ==========================================

# Top Header Bar (Matching Real Dyno Software UI)
st.markdown(f"""
<div class="dyno-header">
    <div>
        <span class="dyno-title">HORSE POWER RUN &nbsp;|&nbsp; {merk} {model_name.upper()}</span>
    </div>
    <div class="dyno-subtitle">
        CORR: 1.000 INY &nbsp;|&nbsp; SAE J1349 &nbsp;|&nbsp; VIRTUAL AXIS DYNO
    </div>
</div>
""", unsafe_allow_html=True)

if run_btn:
    play_dyno_audio_sweep()
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, wheel_hps, crank_hps, torques, afr_trace, pspeed, gsin, gsout = calculate_dyno_run(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, 
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std
    )
    
    max_wheel_hp = float(max(wheel_hps))
    max_torque = float(max(torques))
    rpm_max_hp = int(rpms[np.argmax(wheel_hps)])
    rpm_max_torque = int(rpms[np.argmax(torques)])
    last_afr = float(afr_trace[np.argmax(wheel_hps)])
    
    pwr = (max_wheel_hp / (float(std['weight_std']) + float(in_joki))) * 10.0
    
    st.session_state.history.append({
        "Run": full_label,
        "CC": round(cc_calc, 2),
        "CR": round(cr_calc, 2),
        "AFR": round(in_afr, 2),
        "Max_Wheel_HP": max_wheel_hp,
        "RPM_HP": rpm_max_hp,
        "Max_Nm": max_torque,
        "RPM_Nm": rpm_max_torque,
        "last_afr": last_afr,
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed,
        "rpms": rpms, "wheel_hps": wheel_hps, "crank_hps": crank_hps, 
        "torques": torques, "afr_trace": afr_trace,
        "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore, "stroke": in_stroke
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    # 2-COLUMN MAIN LAYOUT: LEFT = GRAPH, RIGHT = LED METRICS PANEL
    col_graph, col_metrics = st.columns([0.76, 0.24])
    
    with col_graph:
        # SYNCHRONIZED DUAL PLOTLY GRAPH (Top: HP & Torque vs Speed/RPM, Bottom: AFR)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.75, 0.25]
        )
        
        # Color Palettes matching MotoDyno screen
        hp_colors = ["#FFFF00", "#00FF00", "#FF00FF", "#00FFFF"]  # Yellow for HP
        tq_colors = ["#0088FF", "#FF3333", "#FFAA00", "#FFFFFF"]  # Blue for Torque
        
        for i, r in enumerate(st.session_state.history):
            hp_color = hp_colors[i % len(hp_colors)]
            tq_color = tq_colors[i % len(tq_colors)]
            
            # 1. Wheel Power (HP) - Yellow Line
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['wheel_hps'],
                name=f"{r['Run']} Power",
                line=dict(color=hp_color, width=3)
            ), row=1, col=1)
            
            # 2. Engine Torque (Nm) - Blue Line
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['torques'],
                name=f"{r['Run']} Torque",
                line=dict(color=tq_color, width=3),
                yaxis="y2"
            ), row=1, col=1)
            
            # 3. AFR Trace Curve (Bottom Row)
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['afr_trace'],
                name=f"{r['Run']} AFR",
                line=dict(color=hp_color, width=2)
            ), row=2, col=1)

        # Graph Formatting matching Physical Dyno Software
        fig.update_layout(
            template="plotly_dark",
            height=540,
            paper_bgcolor="#0A0A0A",
            plot_bgcolor="#050505",
            margin=dict(l=50, r=50, t=30, b=30),
            showlegend=False,
            yaxis=dict(
                title=dict(text="Wheel POWER [HP]", font=dict(color="#FFFF00", size=13)),
                gridcolor="#222222", zeroline=False, showgrid=True
            ),
            yaxis2=dict(
                title=dict(text="Engine Torque [Nm]", font=dict(color="#0088FF", size=13)),
                overlaying="y", side="right", gridcolor="#222222", showgrid=False
            ),
            yaxis3=dict(
                title=dict(text="AFR", font=dict(color="#00FF00", size=12)),
                gridcolor="#222222", showgrid=True, range=[10, 18]
            ),
            xaxis2=dict(
                title=dict(text="Engine Speed [RPM]", font=dict(size=12)),
                gridcolor="#222222", showgrid=True, dtick=1000
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Action Control Buttons (Share, Print, Diagnostic, Clear)
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.markdown('<button class="btn-share">SHARE</button>', unsafe_allow_html=True)
        with b2: st.markdown('<button class="btn-print">PRINT</button>', unsafe_allow_html=True)
        with b3: st.markdown('<button class="btn-diag">DIAGNOSTIC</button>', unsafe_allow_html=True)
        with b4: 
            if st.button("CLEAR HISTORI"):
                st.session_state.history = []
                st.rerun()

    with col_metrics:
        # RIGHT PANEL: DIGITAL LED DISPLAY BOXES (Exact match to Dyno image)
        
        # Run Legend Box
        st.markdown(f"""
        <div style="background-color:#111; padding:8px; border-radius:4px; border:1px solid #333; margin-bottom:12px; font-size:0.8rem;">
            <span style="color:#00FF00;">■</span> (EMPTY)<br>
            <span style="color:#FFFF00;">■</span> <b>{latest['Run']}</b>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge 1: Wheel POWER
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">⚙️ Wheel POWER (HP)</div>
            <div class="gauge-value-main">{latest['Max_Wheel_HP']:.1f}</div>
            <div class="gauge-sub-row">
                HIGH / MAX READING: <span class="gauge-value-sub">{latest['Max_Wheel_HP']:.2f} HP</span> @ {latest['RPM_HP']} RPM
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge 2: Engine Torque
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">🔩 Engine Torque</div>
            <div class="gauge-value-main">{latest['Max_Nm']:.1f}</div>
            <div class="gauge-sub-row">
                HIGH / MAX READING: <span class="gauge-value-sub">{latest['Max_Nm']:.2f} Nm</span> @ {latest['RPM_Nm']} RPM
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge 3: RPM Engine
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">⏱️ RPM Engine</div>
            <div class="gauge-value-main">{latest['RPM_HP']}</div>
            <div class="gauge-sub-row">
                PEAK RPM: <span class="gauge-value-sub">{latest['RPM_HP']} RPM</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge 4: AFR
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">📊 AFR</div>
            <div class="gauge-value-main" style="color:#FFFFFF;">{latest['last_afr']:.2f}</div>
            <div class="gauge-sub-row">
                TARGET LAMBDA: <span class="gauge-value-sub" style="color:#FFF;">{latest['AFR']:.1f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # 7. PERFORMANCE DATA TABLE & DIAGNOSTICS
    # ==========================================
    st.divider()
    st.markdown("### 📋 PERFORMANCE RUN SUMMARY TABLE")
    
    df_history = pd.DataFrame(st.session_state.history)
    df_display = df_history[["Run", "CC", "CR", "AFR", "Max_Wheel_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].copy()
    
    def highlight_limits(val, col):
        if col == 'CR' and val > 14.5: return 'background-color: #8b0000; color: white; font-weight: bold;'
        return ''

    styled_df = df_display.style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}",
        "Max_Wheel_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }).apply(lambda x: [highlight_limits(v, x.name) for v in x], axis=0)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # FLOWBENCH & VELOCITY AUDIT
    st.markdown("### 🌪️ FLOWBENCH & GAS VELOCITY ANALYSIS")
    f1, f2, f3, f4 = st.columns(4)
    with f1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s", delta="Ideal < 110 m/s", delta_color="inverse" if latest['gsin'] > 110 else "normal")
    with f2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with f3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s", delta="Limit < 21 m/s", delta_color="inverse" if latest['pspeed'] > 21 else "normal")
    with f4: st.metric("CVT Power Loss", f"{latest['wheel_hps'][-1] * 0.18:.2f} HP", delta="~18% CVT Loss")

    # PROFESSIONAL TUNER ADVICE
    st.markdown("### 🏁 EXPERT ENGINE TUNING DIAGNOSTIC")
    if latest['CR'] > 14.5:
        st.error(f"⚠️ **THERMAL PENALTY DETECTED:** Rasio kompresi ({latest['CR']:.2f}:1) terlalu tinggi. Potensi terjadi knockout/detonasi yang menurunkan tenaga puncak.")
    elif latest['gsin'] > 110:
        st.error(f"⚠️ **CHOKE FLOW WARNING:** Kecepatan gas inlet ({latest['gsin']:.2f} m/s) melebihi batas efisiensi (110 m/s). Diperlukan porting/penggantian diameter klep In yang lebih besar.")
    else:
        st.success(f"✅ **OPTIMAL FLOW:** Efisiensi volumetrik dan kecepatan gas ({latest['gsin']:.2f} m/s) berada dalam rentang performa puncak.")

st.markdown("---")
st.caption("HIAR AXIS VIRTUAL DYNO ENGINE v2.5 — Professional Dynamometer Simulation System.")
