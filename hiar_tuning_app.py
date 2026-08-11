import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit.components.v1 as components
import time

# ==========================================
# 1. PAGE CONFIG & PROFESSIONAL DYNO CSS
# ==========================================
st.set_page_config(
    page_title="HIAR AXIS VIRTUAL DYNO SYSTEM v3",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #080808; color: #E0E0E0; font-family: 'Consolas', 'Courier New', monospace; }
    
    .dyno-header {
        background: linear-gradient(90deg, #121212 0%, #222222 100%);
        padding: 12px 20px;
        border-radius: 4px;
        border-bottom: 3px solid #00FF66;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dyno-title { font-size: 1.4rem; font-weight: bold; color: #FFFFFF; letter-spacing: 1px; }
    .dyno-subtitle { font-size: 0.85rem; color: #00FF66; }
    
    .gauge-card {
        background-color: #0D0D0D;
        border: 2px solid #222222;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        text-align: right;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.9);
    }
    .gauge-label { font-size: 0.8rem; color: #888888; text-transform: uppercase; float: left; }
    .gauge-value-main { font-size: 2.3rem; font-weight: 900; color: #00FF00; text-shadow: 0 0 10px rgba(0, 255, 0, 0.5); line-height: 1.1; }
    .gauge-sub-row { font-size: 0.78rem; color: #666666; border-top: 1px solid #1A1A1A; margin-top: 4px; padding-top: 2px; }
    .gauge-value-sub { color: #00CC00; font-weight: bold; }
    
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
            "hp_crank_std": 22.5, "torque_crank_std": 24.3, "peak_rpm": 7000, "limit_std": 9000, "weight_std": 179.0, 
            "type": "single_big", "cvt_loss": 0.18
        },
        "XMAX 300 (Euro Spec)": {
            "bore": 70.0, "stroke": 75.9, "v_head": 29.5, "valve_in": 31.5, "valve_out": 27.0, "venturi": 36.0, 
            "hp_crank_std": 27.6, "torque_crank_std": 29.0, "peak_rpm": 7250, "limit_std": 9200, "weight_std": 183.0, 
            "type": "single_big", "cvt_loss": 0.18
        },
        "XMAX 310 (Bore-Up Spec)": {
            "bore": 76.0, "stroke": 68.0, "v_head": 28.0, "valve_in": 33.0, "valve_out": 28.5, "venturi": 38.0, 
            "hp_crank_std": 32.5, "torque_crank_std": 34.0, "peak_rpm": 7500, "limit_std": 9500, "weight_std": 180.0, 
            "type": "single_big", "cvt_loss": 0.17
        },
        "NMAX 155 / Aerox 155 (VVA)": {
            "bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, 
            "hp_crank_std": 15.1, "torque_crank_std": 13.9, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, 
            "type": "single_small", "cvt_loss": 0.18
        },
        "Mio Karbu 115": {
            "bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, 
            "hp_crank_std": 8.8, "torque_crank_std": 7.84, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, 
            "type": "single_small", "cvt_loss": 0.20
        },
        "YZF-R25 (2-Cylinder)": {
            "bore": 60.0, "stroke": 44.1, "v_head": 12.0, "valve_in": 23.0, "valve_out": 20.0, "venturi": 32.0, 
            "hp_crank_std": 35.5, "torque_crank_std": 22.6, "peak_rpm": 12000, "limit_std": 14000, "weight_std": 166.0, 
            "type": "twin", "cvt_loss": 0.11
        }
    },
    "HONDA": {
        "Vario 160 / PCX 160 (eSP+)": {
            "bore": 60.0, "stroke": 55.5, "v_head": 14.2, "valve_in": 27.0, "valve_out": 22.0, "venturi": 30.0, 
            "hp_crank_std": 15.6, "torque_crank_std": 15.0, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 117.0, 
            "type": "single_small", "cvt_loss": 0.18
        },
        "Vario 150 / PCX 150": {
            "bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, 
            "hp_crank_std": 12.9, "torque_crank_std": 13.4, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, 
            "type": "single_small", "cvt_loss": 0.19
        },
        "BeAT FI / Scoopy 110": {
            "bore": 50.0, "stroke": 55.1, "v_head": 12.7, "valve_in": 22.0, "valve_out": 19.0, "venturi": 22.0, 
            "hp_crank_std": 8.56, "torque_crank_std": 9.01, "peak_rpm": 7500, "limit_std": 9200, "weight_std": 89.0, 
            "type": "single_small", "cvt_loss": 0.20
        },
        "CBR250RR (2-Cylinder)": {
            "bore": 62.0, "stroke": 41.4, "v_head": 11.2, "valve_in": 24.5, "valve_out": 21.0, "venturi": 32.0, 
            "hp_crank_std": 40.4, "torque_crank_std": 25.0, "peak_rpm": 13000, "limit_std": 14500, "weight_std": 168.0, 
            "type": "twin", "cvt_loss": 0.10
        }
    }
}

if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 3. THERMODYNAMIC & ACCURATE PHYSICS ENGINE
# ==========================================
def calculate_dyno_curve(cc, bore, stroke, cr, rpm_limit, v_in, v_out, venturi, dur_in, dur_out, afr, std_spec):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    wheel_hps, crank_hps, torques, afr_trace = [], [], [], []
    
    adj_peak = float(std_spec['peak_rpm']) + (((float(dur_in) + float(dur_out))/2.0 - 240.0) * 50.0)
    eff = 0.88 if "250" in str(std_spec) or "300" in str(std_spec) or "160" in str(std_spec) else 0.83
    afr_mod = 1.0 - abs(float(afr) - 13.0) * 0.035
    
    thermal_penalty = 1.0
    if cr > 14.5:
        thermal_penalty = 1.0 - ((cr - 14.5) * 0.12)
        
    bmep_bar = (float(std_spec['hp_crank_std']) * 120000.0) / (float(cc) * adj_peak * eff)
    cvt_loss = float(std_spec.get('cvt_loss', 0.18))
    
    for r in rpms:
        if r < 1800:  # Idle Range
            ve = 0.15 + (r / 1800.0) * 0.25
        elif r <= adj_peak:
            ve = math.exp(-((r - adj_peak) / 4100.0)**2)
        else:
            ve = math.exp(-((r - adj_peak) / 1850.0)**2)
            
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        gs_in = ((float(bore) / float(v_in))**2) * ps_speed
        gs_out = ((float(bore) / float(v_out))**2) * ps_speed
        
        if gs_in > 125.0:
            ve *= (125.0 / gs_in)**1.8
            
        crank_hp = (bmep_bar * float(cc) * float(r) * ve * eff * afr_mod * thermal_penalty) / 120000.0
        
        # Scaling mods
        if float(bore) > float(std_spec['bore']): crank_hp *= (1.0 + (float(cr) - 9.5) * 0.02)
        if float(venturi) > float(std_spec['venturi']): crank_hp *= (1.0 + (float(venturi) - float(std_spec['venturi'])) * 0.01)
        
        wheel_hp = crank_hp * (1.0 - cvt_loss)
        torque_nm = (wheel_hp * 7023.5) / r if r > 0 else 0.0
        dynamic_afr = float(afr) + 0.4 * math.sin(r / 600.0)
        
        crank_hps.append(round(crank_hp, 2))
        wheel_hps.append(round(wheel_hp, 2))
        torques.append(round(torque_nm, 2))
        afr_trace.append(round(dynamic_afr, 2))
        
    return rpms, wheel_hps, crank_hps, torques, afr_trace, ps_speed, gs_in, gs_out

# ==========================================
# 4. SIDEBAR CONTROLS & STOCK DETECTOR
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ ENGINE SELECTION")
    merk = st.selectbox("Manufacturer", list(DATABASE_REF.keys()))
    model_name = st.selectbox("Engine Model", list(DATABASE_REF[merk].keys()))
    std = DATABASE_REF[merk][model_name]
    st.divider()

    st.markdown("### ⚙️ PARAMETERS & BORE UP")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        in_bore = st.number_input(f"Bore (mm)", value=float(std['bore']), step=0.5)
        in_vhead = st.number_input(f"Vol Head (cc)", value=float(std['v_head']), step=0.1)
    with col_s2:
        in_stroke = st.number_input(f"Stroke (mm)", value=float(std['stroke']), step=0.5)
        in_rpm = st.number_input(f"Limit RPM", value=int(std['limit_std']), step=250)

    cc_calc = (0.785398 * float(in_bore)**2 * float(in_stroke)) / 1000.0

    expert_on = st.toggle("🧪 Tuning / Porting Specs", value=True)
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

    # Stock Check
    is_stock = (
        abs(in_bore - std['bore']) < 0.1 and
        abs(in_stroke - std['stroke']) < 0.1 and
        abs(in_v_in - std['valve_in']) < 0.1 and
        abs(in_v_out - std['valve_out']) < 0.1 and
        abs(in_venturi - std['venturi']) < 0.1
    )
    
    status_suffix = "(Stock)" if is_stock else "(Tuned)"
    default_run_name = f"{model_name} {status_suffix}"
    
    st.divider()
    user_run_label = st.text_input("Run Label (Editable)", value=default_run_name)
    in_joki = st.number_input("Rider Weight (kg)", value=65.0, step=1.0)
    
    run_btn = st.button("🚀 START REALISTIC DYNO SWEEP")

# ==========================================
# 5. AUDIO SYNTHESIZER MATCHING ENGINE TYPE
# ==========================================
def play_engine_audio(engine_type):
    # Frequencies and harmonic profiles matching Engine Types
    freq_map = {
        "single_small": {"base": 40, "peak": 320, "type": "sawtooth"},
        "single_big": {"base": 30, "peak": 260, "type": "square"},
        "twin": {"base": 50, "peak": 550, "type": "sawtooth"}
    }
    spec = freq_map.get(engine_type, freq_map["single_small"])
    
    audio_js = f"""
    <script>
    function runDynoAudio() {{
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = '{spec["type"]}';
        
        const now = ctx.currentTime;
        // Phase 1: Idle (0s - 1s)
        osc.frequency.setValueAtTime({spec["base"]}, now);
        
        // Phase 2: Ramp Up Sweep (1s - 4.5s)
        osc.frequency.exponentialRampToValueAtTime({spec["peak"]}, now + 4.0);
        
        // Phase 3: Limiter Cutout Bounce (4.0s - 4.3s)
        osc.frequency.setValueAtTime({spec["peak"]}, now + 4.0);
        osc.frequency.setValueAtTime({spec["peak"] * 0.85}, now + 4.15);
        osc.frequency.setValueAtTime({spec["peak"]}, now + 4.3);
        
        // Phase 4: Decel Coast Down (4.3s - 5.5s)
        osc.frequency.exponentialRampToValueAtTime({spec["base"]}, now + 5.5);
        
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.25, now + 0.8);
        gain.gain.linearRampToValueAtTime(0.35, now + 4.0);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 5.6);
        
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(300, now);
        filter.frequency.linearRampToValueAtTime(2800, now + 4.0);
        filter.frequency.linearRampToValueAtTime(200, now + 5.5);
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 5.7);
    }}
    runDynoAudio();
    </script>
    """
    components.html(audio_js, height=0, width=0)

# ==========================================
# 6. MAIN UI & ANIMATED SWEEP DISPLAY
# ==========================================

# Top Header
st.markdown(f"""
<div class="dyno-header">
    <div>
        <span class="dyno-title">HORSE POWER RUN &nbsp;|&nbsp; {user_run_label.upper()}</span>
    </div>
    <div class="dyno-subtitle">
        CORR: 1.000 INY &nbsp;|&nbsp; SAE J1349 &nbsp;|&nbsp; REALISTIC CHASSIS DYNO
    </div>
</div>
""", unsafe_allow_html=True)

if run_btn:
    play_engine_audio(std.get('type', 'single_small'))
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    
    rpms, wheel_hps, crank_hps, torques, afr_trace, pspeed, gsin, gsout = calculate_dyno_curve(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, 
        in_v_in, in_v_out, in_venturi, in_dur_in, in_dur_out, in_afr, std
    )
    
    max_wheel_hp = float(max(wheel_hps))
    max_torque = float(max(torques))
    rpm_max_hp = int(rpms[np.argmax(wheel_hps)])
    rpm_max_torque = int(rpms[np.argmax(torques)])
    
    st.session_state.history.append({
        "Run": user_run_label,
        "Is_Stock": is_stock,
        "CC": round(cc_calc, 2),
        "CR": round(cr_calc, 2),
        "AFR": round(in_afr, 2),
        "Max_Wheel_HP": max_wheel_hp,
        "RPM_HP": rpm_max_hp,
        "Max_Nm": max_torque,
        "RPM_Nm": rpm_max_torque,
        "last_afr": float(afr_trace[np.argmax(wheel_hps)]),
        "gsin": gsin, "gsout": gsout, "pspeed": pspeed,
        "rpms": rpms, "wheel_hps": wheel_hps, "crank_hps": crank_hps, 
        "torques": torques, "afr_trace": afr_trace
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    
    col_graph, col_metrics = st.columns([0.76, 0.24])
    
    with col_graph:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.75, 0.25]
        )
        
        hp_colors = ["#FFFF00", "#00FF00", "#FF00FF", "#00FFFF"]
        tq_colors = ["#0088FF", "#FF3333", "#FFAA00", "#FFFFFF"]
        
        for i, r in enumerate(st.session_state.history):
            hp_c = hp_colors[i % len(hp_colors)]
            tq_c = tq_colors[i % len(tq_colors)]
            
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['wheel_hps'], name=f"{r['Run']} HP",
                line=dict(color=hp_c, width=3)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['torques'], name=f"{r['Run']} Torque",
                line=dict(color=tq_c, width=3), yaxis="y2"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=r['rpms'], y=r['afr_trace'], name=f"{r['Run']} AFR",
                line=dict(color=hp_c, width=2)
            ), row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=530,
            paper_bgcolor="#0A0A0A",
            plot_bgcolor="#050505",
            margin=dict(l=40, r=40, t=20, b=20),
            showlegend=False,
            yaxis=dict(title="Wheel POWER [HP]", titlefont=dict(color="#FFFF00"), gridcolor="#222"),
            yaxis2=dict(title="Engine Torque [Nm]", titlefont=dict(color="#0088FF"), overlaying="y", side="right", showgrid=False),
            yaxis3=dict(title="AFR", titlefont=dict(color="#00FF00"), gridcolor="#222", range=[10, 18]),
            xaxis2=dict(title="Engine Speed [RPM]", gridcolor="#222", dtick=1000)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col_metrics:
        # Status Badge
        badge_html = '<span class="stock-badge">STOCK SPEC</span>' if latest['Is_Stock'] else '<span class="tuned-badge">TUNED SPEC</span>'
        
        st.markdown(f"""
        <div style="background-color:#111; padding:8px; border-radius:4px; border:1px solid #333; margin-bottom:10px; font-size:0.8rem;">
            <b>RUN:</b> {latest['Run']} {badge_html}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">⚙️ Wheel POWER (HP)</div>
            <div class="gauge-value-main">{latest['Max_Wheel_HP']:.2f}</div>
            <div class="gauge-sub-row">PEAK: <span class="gauge-value-sub">{latest['Max_Wheel_HP']:.2f} HP</span> @ {latest['RPM_HP']} RPM</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">🔩 Engine Torque</div>
            <div class="gauge-value-main">{latest['Max_Nm']:.2f}</div>
            <div class="gauge-sub-row">PEAK: <span class="gauge-value-sub">{latest['Max_Nm']:.2f} Nm</span> @ {latest['RPM_Nm']} RPM</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">⏱️ Engine Speed</div>
            <div class="gauge-value-main">{latest['RPM_HP']}</div>
            <div class="gauge-sub-row">MAX RPM: <span class="gauge-value-sub">{latest['rpms'][-1]} RPM</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="gauge-card">
            <div class="gauge-label">📊 AFR Lambda</div>
            <div class="gauge-value-main" style="color:#FFF;">{latest['last_afr']:.2f}</div>
            <div class="gauge-sub-row">TARGET: <span class="gauge-value-sub" style="color:#FFF;">{latest['AFR']:.1f}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Performance Table
    st.divider()
    st.markdown("### 📋 PERFORMANCE RUN SUMMARY TABLE")
    df_h = pd.DataFrame(st.session_state.history)
    df_show = df_h[["Run", "CC", "CR", "AFR", "Max_Wheel_HP", "RPM_HP", "Max_Nm", "RPM_Nm"]].copy()
    
    st.dataframe(df_show.style.format({
        "CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}",
        "Max_Wheel_HP": "{:.2f}", "Max_Nm": "{:.2f}"
    }), use_container_width=True, hide_index=True)

st.caption("HIAR AXIS VIRTUAL DYNO v3.0 — Precision Automotive Engine Simulation System.")
