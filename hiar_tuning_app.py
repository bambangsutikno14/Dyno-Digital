import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd
import hashlib
import time
import base64
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    th, td { text-align: center !important; vertical-align: middle !important; }
</style>
""", unsafe_allow_html=True)

DATABASE_REF = {
    "YAMAHA (MATIC)": {
        "Karbu": {
            "115cc": {
                "Mio / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24.0, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.0, "dur_std": 230}
            },
            "125cc": {
                "Xeon (Carb)": {"bore": 52.4, "stroke": 57.9, "v_head": 14.5, "valve_in": 26.0, "valve_out": 21.0, "venturi": 26.0, "hp_std": 10.7, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 103.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.5, "dur_std": 235}
            }
        },
        "Injeksi": {
            "125cc": {
                "Mio Fino 125 FI": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 9.5, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 98.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.8, "dur_std": 235}
            },
            "155cc": {
                "NMAX 155 / Aerox": {"bore": 58.0, "stroke": 58.7, "v_head": 14.6, "valve_in": 20.5, "valve_out": 17.5, "venturi": 28.0, "hp_std": 15.09, "peak_rpm": 8000, "limit_std": 9500, "weight_std": 127.0, "valves": 4, "valves_in_std": 2, "valves_out_std": 2, "lift_std": 8.2, "dur_std": 240}
            },
            "250cc": {
                "XMAX 250": {"bore": 70.0, "stroke": 64.9, "v_head": 22.5, "valve_in": 26.5, "valve_out": 22.5, "venturi": 32.0, "hp_std": 22.5, "peak_rpm": 7000, "limit_std": 9000, "weight_std": 179.0, "valves": 4, "valves_in_std": 2, "valves_out_std": 2, "lift_std": 8.5, "dur_std": 245}
            }
        }
    },
    "HONDA (MATIC)": {
        "Karbu": {
            "110cc": {
                "Beat 110 Karbu": {"bore": 50.0, "stroke": 55.0, "v_head": 11.8, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.22, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 89.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.0, "dur_std": 230},
                "Vario 110 Karbu": {"bore": 50.0, "stroke": 55.0, "v_head": 11.5, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 8.99, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 99.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.2, "dur_std": 230}
            }
        },
        "Injeksi": {
            "110cc": {
                "Beat 110 FI (eSP)": {"bore": 50.0, "stroke": 55.1, "v_head": 12.0, "valve_in": 25.5, "valve_out": 21.0, "venturi": 22.0, "hp_std": 8.68, "peak_rpm": 7500, "limit_std": 9300, "weight_std": 93.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.2, "dur_std": 232}
            },
            "125cc": {
                "Vario 125 eSP": {"bore": 52.4, "stroke": 57.9, "v_head": 14.2, "valve_in": 25.5, "valve_out": 21.0, "venturi": 24.0, "hp_std": 11.1, "peak_rpm": 8500, "limit_std": 9500, "weight_std": 111.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 7.8, "dur_std": 235}
            },
            "150cc": {
                "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head": 15.6, "valve_in": 29.0, "valve_out": 23.0, "venturi": 26.0, "hp_std": 12.92, "peak_rpm": 8500, "limit_std": 9800, "weight_std": 109.0, "valves": 2, "valves_in_std": 1, "valves_out_std": 1, "lift_std": 8.0, "dur_std": 235}
            },
            "160cc": {
                "Vario 160 / PCX 160": {"bore": 60.0, "stroke": 55.5, "v_head": 12.8, "valve_in": 23.0, "valve_out": 19.5, "venturi": 28.0, "hp_std": 15.4, "peak_rpm": 8500, "limit_std": 10000, "weight_std": 115.0, "valves": 4, "valves_in_std": 2, "valves_out_std": 2, "lift_std": 8.5, "dur_std": 245}
            }
        }
    }
}

if "history" not in st.session_state:
    st.session_state.history = []
if "drag_history" not in st.session_state:
    st.session_state.drag_history = []
if "mute_audio" not in st.session_state:
    st.session_state.mute_audio = False

def clamp(value, low, high):
    return max(low, min(high, value))

def safe_div(a, b, default=0.0):
    return a / b if abs(b) > 1e-12 else default

def param_signature(*values):
    parts = []
    for v in values:
        parts.append(f"{v:.4f}" if isinstance(v, float) else str(v))
    return int(hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest(), 16)

def choose_variant(options, *signature_values):
    return options[param_signature(*signature_values) % len(options)] if options else ""

def color_tag(text, level):
    palette = {"safe": "#3ba3ff", "optimal": "#39d353", "risk": "#ff4d4f"}
    return f"<span style='color:{palette.get(level, '#ffffff')}; font-weight:700'>{text}</span>"

def state_from_value(value, safe_low, safe_high, opt_low, opt_high):
    if opt_low <= value <= opt_high:
        return "optimal"
    if safe_low <= value <= safe_high:
        return "safe"
    return "risk"

def style_state(val, kind):
    if kind == "cr":
        if val < 10.0:
            return "color:#3ba3ff; font-weight:700"
        if 10.0 <= val <= 12.8:
            return "color:#39d353; font-weight:700"
        if 12.8 < val <= 13.8:
            return "color:#3ba3ff; font-weight:700"
        return "color:#ff4d4f; font-weight:700"
    if kind == "vel":
        if val < 90.0 or val > 118.0:
            return "color:#ff4d4f; font-weight:700"
        if 100.0 <= val <= 110.0:
            return "color:#39d353; font-weight:700"
        return "color:#3ba3ff; font-weight:700"
    if kind == "afr":
        if 12.4 <= val <= 13.0:
            return "color:#39d353; font-weight:700"
        if 12.1 <= val < 12.4 or 13.0 < val <= 13.4:
            return "color:#3ba3ff; font-weight:700"
        return "color:#ff4d4f; font-weight:700"
    return ""

def area_circle_mm2(diameter_mm):
    return math.pi * (diameter_mm / 2.0) ** 2

def curtain_area_mm2(valve_d_mm, lift_mm, n_valves):
    return math.pi * max(valve_d_mm, 0.1) * max(lift_mm, 0.1) * max(n_valves, 1)

def harmonic_mean(a, b):
    return (2.0 * a * b) / max(a + b, 1e-9)

def build_needle_gauge(label, value, max_value, unit, redline, optimal_low, optimal_high, size=360):
    value = max(0.0, min(float(value), float(max_value)))
    pct = 0 if max_value <= 0 else value / max_value
    angle = -135 + (pct * 270)
    return f"""
    <div style="width:100%; max-width:{size}px; margin:auto; background:#050505; border:1px solid #333; border-radius:22px; padding:14px 14px 18px 14px; box-shadow:0 10px 40px rgba(0,0,0,.35);">
      <div style="text-align:center; color:#fff; font-weight:800; font-size:22px; margin-bottom:8px;">{label}</div>
      <div style="position:relative; width:100%; aspect-ratio:1/1;">
        <svg viewBox="0 0 400 400" width="100%" height="100%">
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <circle cx="200" cy="200" r="165" fill="#0b0b0b" stroke="#2e2e2e" stroke-width="10"/>
          <circle cx="200" cy="200" r="145" fill="#050505" stroke="#1f1f1f" stroke-width="3"/>
          <path d="M 88 270 A 135 135 0 0 1 312 270" fill="none" stroke="#1d3f63" stroke-width="16" stroke-linecap="round"/>
          <path d="M 132 150 A 135 135 0 0 1 278 150" fill="none" stroke="#1b5c2d" stroke-width="16" stroke-linecap="round"/>
          <path d="M 278 150 A 135 135 0 0 1 312 270" fill="none" stroke="#5b2b16" stroke-width="16" stroke-linecap="round"/>
          <path d="M 312 270 A 135 135 0 0 1 323 296" fill="none" stroke="#7a1212" stroke-width="16" stroke-linecap="round"/>
          {''.join([f'<line x1="{200 + 145*math.cos(math.radians(-135 + i*27))}" y1="{200 + 145*math.sin(math.radians(-135 + i*27))}" x2="{200 + 128*math.cos(math.radians(-135 + i*27))}" y2="{200 + 128*math.sin(math.radians(-135 + i*27))}" stroke="#777" stroke-width="3"/>' for i in range(11)])}
          <text x="64" y="286" fill="#9aa4b2" font-size="16" font-family="Arial">0</text>
          <text x="110" y="150" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.25)}</text>
          <text x="190" y="105" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.50)}</text>
          <text x="272" y="150" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.75)}</text>
          <text x="308" y="286" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value)}</text>
          <g transform="rotate({angle} 200 200)" style="transition: transform 0.24s cubic-bezier(0.2, 0.9, 0.2, 1); filter:url(#glow);">
            <line x1="200" y1="205" x2="200" y2="78" stroke="#ff3b30" stroke-width="6" stroke-linecap="round"/>
            <line x1="200" y1="205" x2="200" y2="84" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
            <circle cx="200" cy="205" r="16" fill="#111" stroke="#d9d9d9" stroke-width="3"/>
          </g>
          <text x="200" y="248" text-anchor="middle" fill="#ffffff" font-size="38" font-family="Arial" font-weight="700">{value:.0f}</text>
          <text x="200" y="276" text-anchor="middle" fill="#8ab4ff" font-size="16" font-family="Arial">{unit}</text>
        </svg>
      </div>
    </div>
    """

def _audio_filter_chain_bytes(audio_bytes: bytes) -> bytes:
    return audio_bytes

def render_engine_audio_once(rpm_now, redline, asset_names=None):
    if asset_names is None:
        asset_names = ["assets/superbike_loop.mp3", "superbike_loop.mp3", "engine_loop.mp3"]
    audio_path = None
    for name in asset_names:
        p = Path(name)
        if p.exists() and p.is_file():
            audio_path = p
            break
    if audio_path is None:
        return
    try:
        audio_b64 = base64.b64encode(_audio_filter_chain_bytes(audio_path.read_bytes())).decode("utf-8")
        playback_rate = clamp(0.72 + (float(rpm_now) / max(float(redline), 1.0)) * 1.65, 0.72, 2.20)
        volume = clamp(0.18 + (float(rpm_now) / max(float(redline), 1.0)) * 0.42, 0.18, 0.60)
        html = f"""
        <html><body style='margin:0; padding:0; background:transparent; overflow:hidden;'>
          <audio id='engineAudio' autoplay style='display:none;'>
            <source src='data:audio/mp3;base64,{audio_b64}' type='audio/mp3'>
          </audio>
          <script>
            const a = document.getElementById('engineAudio');
            if (a) {{
              a.loop = false;
              a.playbackRate = {playback_rate:.4f};
              a.volume = {volume:.4f};
              a.play().catch(()=>{{}});
              a.addEventListener('ended', () => {{
                a.pause();
                a.currentTime = 0;
              }});
            }}
          </script>
        </body></html>
        """
        components.html(html, height=0)
    except Exception:
        pass

def build_live_graph(history, current_idx=None, current_rpm=None, current_hp=None, current_nm=None):
    fig = go.Figure()
    colors = ["rgba(255, 0, 0, 1)", "rgba(0, 255, 0, 1)", "rgba(0, 0, 255, 1)", "rgba(255, 255, 0, 1)", "rgba(255, 0, 255, 1)", "rgba(0, 255, 255, 1)"]
    for i, r in enumerate(history):
        color = colors[i % len(colors)]
        opacity = 0.18 if i < len(history) - 1 else 0.9
        width = 2 if i < len(history) - 1 else 3
        dash = "dot" if i < len(history) - 1 else "solid"
        fig.add_trace(go.Scatter(x=r["rpms"], y=r["hps"], name=f"{r['Run']} (HP)", line=dict(color=color, width=width, dash=dash), opacity=opacity))
        fig.add_trace(go.Scatter(x=r["rpms"], y=r["torques"], name=f"{r['Run']} (Nm)", line=dict(color=color, width=max(width - 1, 1), dash="dot"), opacity=opacity, yaxis="y2"))
    if current_idx is not None and history:
        current = history[current_idx]
        color = colors[current_idx % len(colors)]
        live_pos = current.get("live_pos", len(current["rpms"]) - 1)
        live_pos = clamp(int(live_pos), 0, len(current["rpms"]) - 1)
        fig.add_trace(go.Scatter(x=current["rpms"][: live_pos + 1], y=current["hps"][: live_pos + 1], name="Current Live HP", line=dict(color=color, width=5), opacity=1.0))
        fig.add_trace(go.Scatter(x=[current_rpm], y=[current_hp], mode="markers", marker=dict(size=12, color="#FFFFFF", line=dict(color=color, width=3)), name="Live Point", showlegend=False))
        fig.add_trace(go.Scatter(x=[current_rpm], y=[current_nm], mode="markers", marker=dict(size=10, color="#FFFFFF", line=dict(color=color, width=2)), name="Live Torque", yaxis="y2", showlegend=False))
        fig.add_vline(x=current_rpm, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.5)")
    fig.update_layout(template="plotly_dark", height=560, showlegend=False, xaxis=dict(title="Engine RPM", showgrid=True, gridcolor="#333", dtick=1000), yaxis=dict(title="Power (HP)", showgrid=True, gridcolor="#333"), yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False), paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=30, r=30, t=20, b=20))


def build_dyno_frame_buffer(rpms, hps, torques, rpm_limit, idle_rpm=1500.0):
    """
    Precalculate semua frame dulu supaya playback lebih smooth.
    Tidak ada hitung ulang saat render.
    """
    frames = []

    # standby / idle awal
    for _ in range(10):
        frames.append({"rpm": 0.0, "hp": 0.0, "nm": 0.0})

    for r in np.linspace(0.0, idle_rpm, 10):
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    # naik menuju peak lalu limiter
    peak_rpm = float(rpms[int(np.argmax(hps))]) if len(rpms) else idle_rpm
    for r in np.linspace(idle_rpm, peak_rpm, 18):
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    for r in np.linspace(peak_rpm, float(rpm_limit), 14):
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    # limiter bounce
    for r in [float(rpm_limit) * 0.97, float(rpm_limit), float(rpm_limit) * 1.01, float(rpm_limit) * 0.985] * 4:
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    # turun ke idle
    for r in np.linspace(float(rpm_limit), idle_rpm, 10):
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    # idle akhir lalu off
    for _ in range(8):
        frames.append({
            "rpm": idle_rpm,
            "hp": float(np.interp(idle_rpm, rpms, hps)),
            "nm": float(np.interp(idle_rpm, rpms, torques)),
        })

    for r in np.linspace(idle_rpm, 0.0, 8):
        frames.append({
            "rpm": float(r),
            "hp": float(np.interp(r, rpms, hps)),
            "nm": float(np.interp(r, rpms, torques)),
        })

    return frames



def calculate_axis_v22(cc, bore, stroke, cr, rpm_limit, v_in, n_v_in, v_out, n_v_out, v_lift, venturi, dur_in, dur_out, afr, material, d_type, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    pspeeds, vel_in_list, vel_out_list, ve_list = [], [], [], []
    std_cc = (0.785398 * float(std["bore"]) ** 2 * float(std["stroke"])) / 1000.0
    std_cr = (std_cc + float(std["v_head"])) / float(std["v_head"])
    std_avg_dur = float(std["dur_std"])
    std_lift_ratio = safe_div(float(std["lift_std"]), float(std["valve_in"]), 0.0)
    std_intake_curtain = curtain_area_mm2(float(std["valve_in"]), float(std["lift_std"]), int(std.get("valves_in_std", max(int(std["valves"]) // 2, 1))))
    std_exhaust_curtain = curtain_area_mm2(float(std["valve_out"]), float(std["lift_std"]) * 0.92, int(std.get("valves_out_std", max(int(std["valves"]) // 2, 1))))
    std_tb_area = area_circle_mm2(float(std["venturi"]))
    std_intake_area = harmonic_mean(std_tb_area * 0.95, std_intake_curtain * 0.80)
    std_exhaust_area = harmonic_mean(std_tb_area * 0.82, std_exhaust_curtain * 0.78)
    drive_factor = 0.985 if d_type == "CVT" else 1.015
    material_factor = 1.0 if material == "Casting" else 1.02
    afr_target = 12.8
    dur_delta = float(dur_in) - std_avg_dur
    lift_delta = float(v_lift) - float(std["lift_std"])
    flow_delta = float(venturi) - float(std["venturi"])
    adj_peak_rpm = float(std["peak_rpm"]) + (dur_delta * 42.0) + (lift_delta * 165.0) + (flow_delta * 26.0)
    adj_peak_rpm = clamp(adj_peak_rpm, 3500.0, float(rpm_limit) + 1200.0)

    for r in rpms:
        spread = 1800.0 + abs(dur_delta) * 10.0 + abs(lift_delta) * 55.0 + abs(flow_delta) * 18.0
        spread = clamp(spread, 1200.0, 5200.0)
        ve = math.exp(-((r - adj_peak_rpm) / spread) ** 2)
        cc_factor = (float(cc) / max(std_cc, 1e-9)) ** 0.92
        intake_curtain = curtain_area_mm2(float(v_in), float(v_lift), int(n_v_in))
        exhaust_curtain = curtain_area_mm2(float(v_out), float(v_lift) * 0.92, max(int(n_v_out), 1))
        tb_area = area_circle_mm2(float(venturi))
        intake_area = harmonic_mean(max(tb_area * 0.95, 1e-6), max(intake_curtain * 0.80, 1e-6))
        exhaust_area = harmonic_mean(max(tb_area * 0.82, 1e-6), max(exhaust_curtain * 0.78, 1e-6))
        flow_ratio_in = intake_area / max(std_intake_area, 1e-9)
        flow_ratio_out = exhaust_area / max(std_exhaust_area, 1e-9)
        lift_ratio = safe_div(float(v_lift), float(v_in), 0.0)
        lift_ratio_std = max(std_lift_ratio, 1e-6)
        lift_ratio_delta = lift_ratio - lift_ratio_std
        cam_factor = clamp(1.0 + (dur_delta * 0.0020) - (dur_delta ** 2) * 0.0000014, 0.78, 1.22)
        lift_factor = clamp(1.0 + (lift_ratio_delta * 2.15) - (lift_ratio_delta ** 2) * 5.6, 0.72, 1.28)
        flow_factor = clamp((flow_ratio_in ** 0.43) * (flow_ratio_out ** 0.23), 0.68, 1.38)
        afr_delta = float(afr) - afr_target
        afr_factor = clamp(1.0 - (afr_delta ** 2) * 0.045, 0.72, 1.08)
        cr_target = std_cr + 0.55
        cr_factor = math.exp(-((float(cr) - cr_target) / 1.35) ** 2)
        cr_ref = math.exp(-((std_cr - cr_target) / 1.35) ** 2)
        cr_factor = safe_div(cr_factor, cr_ref, 1.0)
        if float(cr) > 14.5:
            cr_factor *= max(0.18, 1.0 - ((float(cr) - 14.5) * 0.18))
        if float(cr) < 9.6:
            cr_factor *= max(0.55, 1.0 - ((9.6 - float(cr)) * 0.08))
        rpm_factor = math.exp(-((r - adj_peak_rpm) / (spread * 0.95)) ** 2)
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        friction_loss = clamp((r / float(rpm_limit)) ** 2 * 0.08 + (ps_speed / 28.0) ** 2 * 0.05, 0.00, 0.28)
        disp_m3 = float(cc) / 1_000_000.0
        q_m3s = disp_m3 * (r / 2.0) / 60.0 * ve
        vel_in = safe_div(q_m3s, max(intake_area / 1_000_000.0, 1e-9), 0.0) * 5.55
        vel_out = safe_div(q_m3s, max(exhaust_area / 1_000_000.0, 1e-9), 0.0) * 6.95
        if vel_in < 90.0:
            ve *= clamp(0.74 + (vel_in / 150.0), 0.74, 0.98)
        elif 100.0 <= vel_in <= 110.0:
            ve *= 1.06
        elif vel_in > 110.0:
            ve *= clamp((110.0 / vel_in) ** 1.12, 0.70, 1.00)
        if vel_out < 92.0:
            ve *= clamp(0.80 + (vel_out / 220.0), 0.80, 0.99)
        elif 102.0 <= vel_out <= 115.0:
            ve *= 1.05
        elif vel_out > 115.0:
            ve *= clamp((115.0 / vel_out) ** 1.05, 0.72, 1.00)
        if lift_ratio < 0.24:
            ve *= 0.88
        elif lift_ratio > 0.34:
            ve *= 0.94
        if flow_ratio_in < 0.85:
            ve *= 0.90 + (flow_ratio_in * 0.10)
        elif flow_ratio_in > 1.45:
            ve *= 0.95
        hp = float(std["hp_std"])
        hp *= cc_factor * flow_factor * cam_factor * lift_factor * afr_factor * cr_factor * rpm_factor * material_factor * drive_factor
        hp *= (0.78 + 0.42 * ve)
        hp *= (1.0 - friction_loss)
        if ps_speed > 23.0:
            hp *= max(0.68, 1.0 - ((ps_speed - 23.0) * 0.03))
        if float(cr) > 13.8 and material == "Casting":
            hp *= max(0.74, 1.0 - ((float(cr) - 13.8) * 0.06))
        if float(afr) < 12.0:
            hp *= max(0.82, 1.0 - ((12.0 - float(afr)) * 0.04))
        if float(afr) > 13.4:
            hp *= max(0.82, 1.0 - ((float(afr) - 13.4) * 0.04))
        ve_list.append(round(ve, 4))
        pspeeds.append(round(ps_speed, 2))
        vel_in_list.append(round(vel_in, 2))
        vel_out_list.append(round(vel_out, 2))
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))

    idx_hp = int(np.argmax(hps))
    idx_nm = int(np.argmax(torques))
    return rpms, hps, torques, pspeeds[idx_hp], vel_in_list[idx_hp], vel_out_list[idx_hp], vel_in_list, vel_out_list, ve_list, idx_hp, idx_nm

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
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std["bore"]), step=0.1)
        in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std["stroke"]), step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std["v_head"]), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std["limit_std"]), step=100)
        cc_placeholder = st.empty()
    with st.expander("🧪 Detail Expert Tuning", expanded=True):
        in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std["valve_in"]), step=0.1)
        std_in_cnt = int(std.get("valves_in_std", 1))
        std_out_cnt = int(std.get("valves_out_std", 1))
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2, 4], index=[1, 2, 4].index(std_in_cnt) if std_in_cnt in [1, 2, 4] else 0)
        in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std["valve_out"]), step=0.1)
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2, 4], index=[1, 2, 4].index(std_out_cnt) if std_out_cnt in [1, 2, 4] else 0)
        in_venturi = st.number_input(f"Venturi/TB (std: {std['venturi']})", value=float(std["venturi"]), step=0.5)
        in_v_lift = st.number_input(f"Lift (std: {std['lift_std']})", value=float(std["lift_std"]), step=0.1)
        in_dur_in = st.number_input(f"Durasi In (std: {std['dur_std']})", value=float(std["dur_std"]), step=1.0)
        in_dur_out = st.number_input(f"Durasi Out (std: {std['dur_std']})", value=float(std["dur_std"]), step=1.0)
        in_afr = st.number_input("AFR (Rasio Udara/BBM)", min_value=11.0, max_value=15.0, value=12.8, step=0.1)
        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])
    cc_calc = (0.785398 * float(in_bore) ** 2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC: {cc_calc:.2f}")

    st.markdown("---")
    st.subheader("3️⃣ DYNO")
    run_dyno_btn = st.button("🚀 ANALYZE & RUN AXIS", use_container_width=True)
    in_joki = st.number_input("Berat Joki (kg)", value=60.0, step=1.0)
    final_ratio = st.number_input("Final Ratio", value=1.0, step=0.01)

    st.markdown("---")
    st.subheader("4️⃣ DRAG")
    run_drag_btn = st.button("🏁 DRAG SIMULATOR", use_container_width=True)
    mute_audio = st.toggle("🔇 Mute Audio", value=st.session_state.mute_audio)
    st.session_state.mute_audio = mute_audio

st.title("📟 Hiar Lima Pendawa Tuning")

if run_dyno_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, peak_pspeed, peak_gsin, peak_gsout, vel_in_list, vel_out_list, ve_list, idx_hp, idx_nm = calculate_axis_v22(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in,
        in_v_out, in_n_v_out, in_v_lift, in_venturi, in_dur_in, in_dur_out,
        in_afr, in_material, in_d_type, std
    )
    hp_max = max(hps)
    nm_max = max(torques)
    pwr = max((hp_max / (float(std["weight_std"]) + float(in_joki))) * 10.0, 0.25)
    st.session_state.history.append({
        "Run": full_label, "CC": cc_calc, "CR": cr_calc, "AFR": in_afr,
        "Max_HP": hp_max, "RPM_HP": rpms[idx_hp], "Max_Nm": nm_max, "RPM_Nm": rpms[idx_nm],
        "Velocity": peak_gsin, "Velocity_Out": peak_gsout, "PistonSpeed": peak_pspeed,
        "gsin": peak_gsin, "gsout": peak_gsout, "pspeed": peak_pspeed,
        "rpms": rpms, "hps": hps, "torques": torques, "vel_in_list": vel_in_list, "vel_out_list": vel_out_list, "ve_list": ve_list,
        "v_in": in_v_in, "v_out": in_v_out, "bore": in_bore, "stroke": in_stroke, "lift": in_v_lift, "venturi": in_venturi, "material": in_material,
        "T100": 6.5 / math.pow(pwr, 0.45), "T201": 10.2 / math.pow(pwr, 0.45), "T402": 16.5 / math.pow(pwr, 0.45), "T1000": 32.8 / math.pow(pwr, 0.45)
    })

if st.session_state.history:
    latest = st.session_state.history[-1]
    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2: st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3: st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4: st.metric("Flow In (est)", f"{round((latest['v_in'] / 25.4) ** 2 * 146, 1)} CFM")
    with m5: st.metric("Flow Out (est)", f"{round((latest['v_out'] / 25.4) ** 2 * 146, 1)} CFM")

    st.markdown("### 🎥 Live Dyno Visual")
    gauge_left, gauge_mid = st.columns(2)
    tach_ph = gauge_left.empty()
    speed_ph = gauge_mid.empty()
    graph_ph = st.empty()

    history_idx = len(st.session_state.history) - 1
    current_run = st.session_state.history[history_idx]
    speed_max = max(120.0, 60.0 + current_run["Max_HP"] * 5.0)
    rpms = current_run["rpms"]
    hps = current_run["hps"]
    torques = current_run["torques"]
    frame_buffer = build_dyno_frame_buffer(rpms, hps, torques, float(in_rpm), idle_rpm=1500.0)

    # playback only: semua data sudah dihitung dulu
    for frame_idx, frame in enumerate(frame_buffer):
        rpm_now = frame["rpm"]
        hp_now = frame["hp"]
        nm_now = frame["nm"]

        current_run["live_pos"] = min(
            int((max(rpm_now, 1.0) / max(float(current_run["rpms"][-1]), 1.0)) * (len(current_run["rpms"]) - 1)),
            len(current_run["rpms"]) - 1
        )

        speed_now = clamp((rpm_now / max(float(current_run["rpms"][-1]), 1.0)) * speed_max, 0.0, speed_max)
        tach_show = 0 if frame_idx == 0 else rpm_now
        speed_show = 0 if frame_idx == 0 else speed_now

        tach_ph.markdown(
            build_needle_gauge("Tachometer", tach_show, max(float(in_rpm) + 1500.0, 1500.0), "RPM", float(in_rpm), 1500.0, max(1800.0, float(in_rpm) * 0.92)),
            unsafe_allow_html=True
        )
        speed_ph.markdown(
            build_needle_gauge("Speedometer", speed_show, speed_max, "km/h", speed_max * 0.82, speed_max * 0.35, speed_max * 0.68),
            unsafe_allow_html=True
        )

        if frame_idx % 3 == 0:
            graph_ph.plotly_chart(
                build_live_graph(st.session_state.history, current_idx=history_idx, current_rpm=max(rpm_now, 0), current_hp=hp_now, current_nm=nm_now),
                use_container_width=True,
                key=f"graph_{history_idx}_{frame_idx}"
            )

        render_engine_audio_once(rpm_now, float(in_rpm))

        if rpm_now <= 0:
            time.sleep(0.10)
        elif rpm_now < 1800:
            time.sleep(0.08)
        elif rpm_now < float(latest["RPM_HP"]):
            time.sleep(0.050)
        elif rpm_now < float(in_rpm):
            time.sleep(0.042)
        else:
            time.sleep(0.040)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    for i in range(6):
        tach_ph.markdown(build_needle_gauge("Tachometer", 1800, max(float(in_rpm) + 1500.0, 1500.0), "RPM", float(in_rpm), 1500.0, max(1800.0, float(in_rpm) * 0.92)), unsafe_allow_html=True)
        speed_ph.markdown(build_needle_gauge("Speedometer", 0, speed_max, "km/h", speed_max * 0.82, speed_max * 0.35, speed_max * 0.68), unsafe_allow_html=True)
        graph_ph.plotly_chart(build_live_graph(st.session_state.history, current_idx=history_idx, current_rpm=1800, current_hp=float(np.interp(1800, current_run["rpms"], current_run["hps"])), current_nm=float(np.interp(1800, current_run["rpms"], current_run["torques"]))), use_container_width=True, key=f"graph_idle_{i}")
        time.sleep(0.18)


if run_drag_btn and st.session_state.history:
    latest_drag = st.session_state.history[-1]
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.header("🏁 Drag Simulator")

    drag_left, drag_mid = st.columns(2)
    drag_tach_ph = drag_left.empty()
    drag_speed_ph = drag_mid.empty()
    drag_graph_ph = st.empty()

    # Precompute drag frames (tidak streaming hitung ulang)
    max_speed = max(120.0, 60.0 + latest_drag["Max_HP"] * 5.0)
    drag_total_time = float(latest_drag["T1000"]) if "T1000" in latest_drag else 32.8
    drag_frames = build_drag_frame_buffer(drag_total_time, max_speed, float(in_rpm), idle_rpm=1500.0, steps=90)

    drag_samples = []
    for idx, f in enumerate(drag_frames):
        rpm_now = float(f["rpm"])
        speed_now = float(f["speed"])
        dist_now = float(f["dist"])
        drag_samples.append((dist_now, speed_now, rpm_now))

        drag_tach_ph.markdown(
            build_needle_gauge("Tachometer", rpm_now, max(float(in_rpm) + 1500.0, 1500.0), "RPM", float(in_rpm), 1500.0, max(1800.0, float(in_rpm) * 0.92)),
            unsafe_allow_html=True
        )
        drag_speed_ph.markdown(
            build_needle_gauge("Speedometer", speed_now, max_speed, "km/h", max_speed * 0.82, max_speed * 0.35, max_speed * 0.68),
            unsafe_allow_html=True
        )

        if idx % 3 == 0:
            g = go.Figure()
            xs = [x[0] for x in drag_samples]
            ys = [x[1] for x in drag_samples]
            g.add_trace(go.Scatter(x=xs, y=ys, line=dict(width=4), showlegend=False))
            g.update_layout(
                template="plotly_dark",
                height=360,
                xaxis=dict(title="Distance (m)", showgrid=True, gridcolor="#333", range=[0, 1000]),
                yaxis=dict(title="Speed (km/h)", showgrid=True, gridcolor="#333", range=[0, max_speed * 1.1]),
                paper_bgcolor="#050505",
                plot_bgcolor="#050505",
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
            )
            drag_graph_ph.plotly_chart(g, use_container_width=True, key=f"drag_graph_{idx}")

        render_engine_audio_once(rpm_now, float(in_rpm))

        if rpm_now <= 0:
            time.sleep(0.08)
        elif rpm_now < 1800:
            time.sleep(0.06)
        else:
            time.sleep(max(drag_total_time / max(len(drag_frames), 1), 0.03))

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.write("### 📊 Drag Simulation Predictions")
    dist_100_idx = min(range(len(drag_samples)), key=lambda i: abs(drag_samples[i][0] - 100.0))
    dist_201_idx = min(range(len(drag_samples)), key=lambda i: abs(drag_samples[i][0] - 201.0))
    dist_402_idx = min(range(len(drag_samples)), key=lambda i: abs(drag_samples[i][0] - 402.0))
    drag_df = pd.DataFrame([{
        "Run": latest_drag["Run"],
        "0-100 km/h": round(max(2.8, 9.5 / ((latest_drag["Max_HP"] / max(latest_drag["CC"] + 60.0, 1.0)) ** 0.45)), 2),
        "201m": round(drag_samples[dist_201_idx][0] / max(drag_samples[dist_201_idx][1], 1.0) * 3.6, 2),
        "402m": round(drag_samples[dist_402_idx][0] / max(drag_samples[dist_402_idx][1], 1.0) * 3.6, 2),
        "1000m": round(drag_total_time, 2),
        "Top Speed": round(max_speed, 1),
    }])
    st.dataframe(drag_df.style.format({"0-100 km/h": "{:.2f}s", "201m": "{:.2f}", "402m": "{:.2f}", "1000m": "{:.2f}s", "Top Speed": "{:.1f} km/h"}), hide_index=True, use_container_width=True)

    df = pd.DataFrame(st.session_state.history)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.write("### 📊 Performance Dyno Result")
    df_perf = df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "Velocity"]].copy()
    st.dataframe(
        df_perf.style.format({"CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}", "Velocity": "{:.2f}"})
        .map(lambda v: style_state(v, "cr"), subset=["CR"])
        .map(lambda v: style_state(v, "vel"), subset=["Velocity"])
        .map(lambda v: style_state(v, "afr"), subset=["AFR"]),
        hide_index=True,
        use_container_width=True
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.write("### 🏁 Drag Simulation Predictions")
    df_drag = df[["Run", "T100", "T201", "T402", "T1000"]].rename(columns={"T100": "0-100 km/h", "T201": "201m", "T402": "402m", "T1000": "1000m"})
    st.dataframe(df_drag.style.format({"0-100 km/h": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s"}), hide_index=True, use_container_width=True)

    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")

    c1, c2, c3 = st.columns(3)
    lift_ratio = safe_div(latest["lift"], latest["v_in"], 0.0)
    valve_area_index = safe_div(curtain_area_mm2(latest["v_in"], latest["lift"], 2), area_circle_mm2(latest["venturi"]), 0.0)
    sig = param_signature(latest["CC"], latest["CR"], latest["AFR"], latest["Max_HP"], latest["RPM_HP"], latest["Max_Nm"], latest["Velocity"], latest["Velocity_Out"], latest["PistonSpeed"], latest["bore"], latest["stroke"], latest["v_in"], latest["v_out"], latest["lift"], latest["venturi"], latest["material"])
    cr_state = state_from_value(latest["CR"], 9.5, 13.8, 10.0, 12.8)
    vel_state = state_from_value(latest["Velocity"], 90.0, 99.9, 100.0, 110.0)

    with c1:
        st.subheader("🧐 1. Analisa Spek Mesin")
        analisa_mesin = choose_variant([
            f"Kapasitas nyata berada di **{latest['CC']:.2f} cc** dengan kompresi statis **{latest['CR']:.2f}:1**.",
            f"Displacement terukur **{latest['CC']:.2f} cc**. Rasio kompresi aktual terbaca **{latest['CR']:.2f}:1**.",
            f"Spek mesin mengarah ke **{latest['CC']:.2f} cc** dan CR **{latest['CR']:.2f}:1** dengan karakter kompresi {('ringan' if latest['CR'] < 11 else 'padat' if latest['CR'] < 13 else 'agresif')}.",
            f"Volume kerja **{latest['CC']:.2f} cc** dan CR **{latest['CR']:.2f}:1** menandakan build ini {('lebih aman' if cr_state == 'safe' else 'ideal' if cr_state == 'optimal' else 'berisiko')}."
        ], sig, latest["CC"], latest["CR"])
        st.markdown(f"- {analisa_mesin}", unsafe_allow_html=True)
        st.markdown(f"- Efisiensi lift terhadap klep in berada di **{(lift_ratio * 100):.1f}%** ({lift_ratio:.3f}).")
        st.markdown(f"- Indeks area klep vs venturi berada di **{valve_area_index:.3f}**.")
        st.markdown(f"- {color_tag('Status CR: ' + ('optimal' if cr_state == 'optimal' else 'aman' if cr_state == 'safe' else 'berisiko'), cr_state if cr_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)
        st.markdown(f"- {color_tag('Status Velocity: ' + ('optimal' if vel_state == 'optimal' else 'aman' if vel_state == 'safe' else 'berisiko'), vel_state if vel_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)

    with c2:
        st.subheader("📚 2. Saran Ahli (Teori)")
        if latest["Velocity"] > 115.0:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s sudah terlalu liar. Port mulai bekerja seperti sumbatan, VE justru turun di rpm atas.",
                f"Gas speed {latest['Velocity']:.2f} m/s menandakan choke flow. Nafas atas panjang di atas kertas, tapi habis di real flow.",
                f"Kecepatan aliran {latest['Velocity']:.2f} m/s melewati zona efisien. Campuran mulai pecah dan tenaga puncak tidak stabil."
            ], sig, latest["Velocity"])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)
        elif latest["Velocity"] < 90.0:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s masih terlalu lambat. Scavenging kurang hidup dan torsi bawah terasa kosong.",
                f"Gas speed {latest['Velocity']:.2f} m/s belum cukup untuk mengunci inersia udara. Respons awal masih bisa dipadatkan.",
                f"Aliran {latest['Velocity']:.2f} m/s berada di bawah jendela kerja ideal. Intake perlu dipadatkan untuk menaikkan momentum charge."
            ], sig, latest["Velocity"])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s berada di zona optimal. VE cenderung hidup di tengah sampai atas.",
                f"Gas speed {latest['Velocity']:.2f} m/s pas. Ini zona yang biasanya paling enak untuk powerband CVT.",
                f"Kecepatan aliran {latest['Velocity']:.2f} m/s sudah mendekati sweet spot. Mesin cenderung padat dan responsif."
            ], sig, latest["Velocity"])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)

        if lift_ratio < 0.24:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} terlalu kecil untuk ukuran klep {latest['v_in']} mm. Katup belum dimanfaatkan penuh.",
                f"Lift ratio {lift_ratio:.3f} menunjukkan cam masih terlalu jinak. Nafas akan tertahan oleh durasi buka yang pendek.",
                f"Efektivitas lift {lift_ratio:.3f} belum cukup agresif. Area buka klep belum sebanding dengan kebutuhan flow."
            ], sig, lift_ratio, latest["v_in"])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        elif 0.24 <= lift_ratio <= 0.33:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} sudah berada di area kerja yang sehat untuk head ini.",
                f"Lift ratio {lift_ratio:.3f} cukup ideal. Ini biasanya bikin flow enak tanpa terlalu mengorbankan durabilitas.",
                f"Efektivitas lift {lift_ratio:.3f} pas untuk karakter mesin yang ingin responsif namun tetap terkontrol."
            ], sig, lift_ratio, latest["v_in"])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} sudah agresif. Mekanik perlu cek stabilitas valve train dan per klep.",
                f"Lift ratio {lift_ratio:.3f} terlalu tinggi untuk sebagian setup harian. Friksi dan valve control perlu perhatian ekstra.",
                f"Rasio lift {lift_ratio:.3f} mendekati batas keras. Potensi valve floating mulai nyata saat rpm naik."
            ], sig, lift_ratio, latest["v_in"])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)

        if latest["PistonSpeed"] > 23.0:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s sudah terlalu dekat dengan batas aman untuk durasi panjang.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s menuntut oli dan pendinginan yang lebih serius.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masuk wilayah stres mekanik tinggi. Umur part akan lebih cepat terkikis."
            ], sig, latest["PistonSpeed"])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)
        elif latest["PistonSpeed"] > 20.0:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masih aman, tapi sudah tidak santai.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s berada di zona kerja keras namun masih bisa dipakai.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s cukup cepat. Setting oli dan per klep mulai penting."
            ], sig, latest["PistonSpeed"])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masih nyaman untuk karakter CVT.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s berada di zona aman untuk sesi panjang.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s relatif ideal dan tidak memaksa komponen berlebihan."
            ], sig, latest["PistonSpeed"])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)

    with c3:
        st.subheader("🛠️ 3. Solusi & Rekomendasi Part")
        rekomendasi_ditemukan = False
        if latest["Velocity"] > 115.0:
            msg = choose_variant([
                f"🔹 **Intake/TB:** Perbesar throttle body atau rapikan porting karena velocity {latest['Velocity']:.2f} m/s sudah terlalu padat.",
                f"🔹 **Manifold/Port:** Head mulai tersumbat. Buka jalur intake agar aliran tidak menabrak batas {latest['Velocity']:.2f} m/s.",
                f"🔹 **Intake:** Kombinasi TB dan port sekarang terlalu sempit untuk rpm atas. Perlu enlarge bertahap, jangan brutal."
            ], sig, latest["Velocity"], latest["venturi"])
            st.info(msg)
            rekomendasi_ditemukan = True
        elif latest["Velocity"] < 90.0:
            msg = choose_variant([
                f"🔹 **Manifold:** Pakai intake manifold yang sedikit lebih sempit atau lebih pendek untuk menaikkan velocity ke zona 100-110 m/s.",
                f"🔹 **Intake Runner:** Velocity terlalu rendah. Kecilkan volume runner agar momentum charge naik.",
                f"🔹 **Throttle Body:** TB terlalu lega untuk karakter ini. Sempitkan sedikit supaya respons bawah tidak ngempos."
            ], sig, latest["Velocity"], latest["venturi"])
            st.info(msg)
            rekomendasi_ditemukan = True

        if latest["CR"] > 13.2 and latest["material"] == "Casting":
            msg = choose_variant([
                f"🔹 **Piston:** Ganti ke forged piston karena CR {latest['CR']:.2f}:1 terlalu agresif untuk casting.",
                f"🔹 **Compression Safety:** Dengan CR {latest['CR']:.2f}:1, piston casting mulai rawan panas dan retak mikro.",
                f"🔹 **Top End:** Untuk kompresi {latest['CR']:.2f}:1, forged piston lebih aman daripada casting biasa."
            ], sig, latest["CR"], latest["material"])
            st.error(msg)
            rekomendasi_ditemukan = True
        elif latest["CR"] < 10.0:
            msg = choose_variant([
                f"🔹 **Kompresi:** CR {latest['CR']:.2f}:1 terlalu rendah. Naikkan volume head agar pembakaran lebih padat.",
                f"🔹 **Head Volume:** Ruang bakar masih terlalu besar. CR {latest['CR']:.2f}:1 perlu dinaikkan untuk mengisi torsi.",
                f"🔹 **Compression Build:** Turunkan volume head atau ubah dome piston karena kompresi masih terlalu jinak."
            ], sig, latest["CR"])
            st.info(msg)
            rekomendasi_ditemukan = True

        if lift_ratio < 0.26:
            target_lift = latest["v_in"] * 0.30
            msg = choose_variant([
                f"🔹 **Noken As:** Cari profil yang memberi lift minimal **{target_lift:.2f} mm**.",
                f"🔹 **Camshaft:** Lift sekarang belum cukup mengisi klep. Naikkan lift untuk mengejar curtain area.",
                f"🔹 **Noken As:** Durasi boleh ada, tapi lift masih terlalu jinak. Profil high-lift akan lebih cocok."
            ], sig, target_lift, latest["v_in"])
            st.info(msg)
            rekomendasi_ditemukan = True
        elif lift_ratio > 0.34:
            msg = choose_variant([
                f"🔹 **Noken As:** Lift terlalu tinggi. Cek per klep dan geometri rocker/valvetrain.",
                f"🔹 **Camshaft:** Profil sekarang agresif. Pastikan spring rate cukup supaya valve tidak floating.",
                f"🔹 **Valve Train:** Lift besar butuh per klep lebih keras dan setup clearance yang rapi."
            ], sig, lift_ratio)
            st.warning(msg)
            rekomendasi_ditemukan = True

        if latest["PistonSpeed"] > 22.0 or lift_ratio > 0.33:
            msg = choose_variant([
                f"🔹 **Per Klep:** Gunakan per klep racing/high tension untuk menjaga valve control di rpm tinggi.",
                f"🔹 **Valve Spring:** Spring standar terlalu lembek untuk kombinasi speed {latest['PistonSpeed']:.2f} m/s dan lift ratio {lift_ratio:.3f}.",
                f"🔹 **Klep Train:** Upgrade per klep wajib jika ingin rpm naik tanpa valve floating."
            ], sig, latest["PistonSpeed"], lift_ratio)
            st.warning(msg)
            rekomendasi_ditemukan = True

        if latest["AFR"] > 13.5:
            msg = choose_variant([
                f"🔹 **Sistem BBM:** AFR {latest['AFR']:.1f} terlalu kering. Tambah debit injektor atau seting ulang mapping.",
                f"🔹 **Fueling:** Campuran {latest['AFR']:.1f} cenderung miskin. Mesin bisa panas dan tenaga tidak stabil.",
                f"🔹 **Injector/BBM:** Tambah suplai bahan bakar karena AFR {latest['AFR']:.1f} sudah melewati area aman."
            ], sig, latest["AFR"])
            st.warning(msg)
            rekomendasi_ditemukan = True
        elif latest["AFR"] < 12.0:
            msg = choose_variant([
                f"🔹 **Sistem BBM:** AFR {latest['AFR']:.1f} terlalu basah. Bahan bakar kebanyakan, respons jadi berat.",
                f"🔹 **Fueling:** Campuran terlalu kaya. Kurangi debit supaya pembakaran lebih bersih.",
                f"🔹 **Injector/Spuyer:** AFR {latest['AFR']:.1f} perlu diringankan agar mesin tidak membuang tenaga."
            ], sig, latest["AFR"])
            st.info(msg)
            rekomendasi_ditemukan = True

        if latest["Velocity_Out"] > 118.0:
            msg = choose_variant([
                f"🔹 **Exhaust:** Jalur buang terlalu padat. Knalpot / leher perlu dibuka sedikit agar backpressure turun.",
                f"🔹 **Outlet Flow:** Velocity out {latest['Velocity_Out']:.2f} m/s menandakan exhaust terlalu menahan gas.",
                f"🔹 **Knalpot:** Buang gas sudah terlalu keras. Perbesar leher atau ubah diffuser bila perlu."
            ], sig, latest["Velocity_Out"])
            st.error(msg)
            rekomendasi_ditemukan = True
        elif latest["Velocity_Out"] < 92.0:
            msg = choose_variant([
                f"🔹 **Exhaust:** Buang gas terlalu lambat. Diameter leher bisa dipersempit sedikit untuk bantu scavenging.",
                f"🔹 **Outlet Flow:** Velocity out {latest['Velocity_Out']:.2f} m/s terlalu rendah untuk mengusir gas sisa.",
                f"🔹 **Knalpot:** Exhaust cenderung terlalu lega. Sedikit penyempitan bisa bantu mid-range."
            ], sig, latest["Velocity_Out"])
            st.info(msg)
            rekomendasi_ditemukan = True

        if not rekomendasi_ditemukan:
            msg = choose_variant([
                "✅ Setingan saat ini seimbang dan belum butuh part besar-besaran.",
                "✅ Kombinasi bore, lift, dan AFR sudah cukup rapi untuk karakter yang dipilih.",
                "✅ Tidak ada part mendesak. Tinggal fine tuning agar respons lebih tajam.",
                "✅ Paket tuning sudah saling mengisi; perbaikan kecil saja akan terasa di dyno."
            ], sig, latest["CC"], latest["CR"], latest["Velocity"], latest["AFR"])
            st.success(msg)

st.write("---")
st.error("⚠️ **DISCLAIMER:** Perhitungan hanya estimasi kalkulasi data, hasil nyata bergantung pada efisiensi volumetrik, suhu, kualitas part, dan setting lapangan.")
