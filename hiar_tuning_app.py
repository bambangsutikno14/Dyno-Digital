import base64
import hashlib
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown(
    """
<style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { font-size: 1.55rem; color: #00FF00; }
    .stMetric { background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    th, td { text-align: center !important; vertical-align: middle !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# DATABASE
# =========================================================
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

# =========================================================
# STATE
# =========================================================
if "dyno_history" not in st.session_state:
    st.session_state.dyno_history = []
if "drag_history" not in st.session_state:
    st.session_state.drag_history = []
if "mute_audio" not in st.session_state:
    st.session_state.mute_audio = False


# =========================================================
# HELPERS
# =========================================================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def safe_div(a, b, default=0.0):
    return a / b if abs(b) > 1e-12 else default


def sig_value(*values):
    parts = []
    for v in values:
        parts.append(f"{v:.4f}" if isinstance(v, float) else str(v))
    return int(hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest(), 16)


def choose_variant(options, *values):
    return options[sig_value(*values) % len(options)] if options else ""


def area_circle_mm2(d_mm):
    return math.pi * (d_mm / 2.0) ** 2


def curtain_area_mm2(valve_d_mm, lift_mm, n_valves):
    return math.pi * max(valve_d_mm, 0.1) * max(lift_mm, 0.1) * max(n_valves, 1)


def harmonic_mean(a, b):
    return (2.0 * a * b) / max(a + b, 1e-9)


def state_from_value(value, safe_low, safe_high, opt_low, opt_high):
    if opt_low <= value <= opt_high:
        return "optimal"
    if safe_low <= value <= safe_high:
        return "safe"
    return "risk"


def color_tag(text, level):
    palette = {"safe": "#3ba3ff", "optimal": "#39d353", "risk": "#ff4d4f"}
    return f"<span style='color:{palette.get(level, '#ffffff')}; font-weight:700'>{text}</span>"


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


def needle_gauge_html(label, value, max_value, unit, redline=None, optimal_low=None, optimal_high=None, size=360, tick_suffix=""):
    value = max(0.0, min(float(value), float(max_value)))
    redline = redline if redline is not None else max_value * 0.85
    optimal_low = optimal_low if optimal_low is not None else max_value * 0.45
    optimal_high = optimal_high if optimal_high is not None else max_value * 0.78
    pct = 0 if max_value <= 0 else value / max_value
    angle = -135 + pct * 270

    def tick_line(i):
        ang = -135 + i * 27
        x1 = 200 + 145 * math.cos(math.radians(ang))
        y1 = 200 + 145 * math.sin(math.radians(ang))
        x2 = 200 + 128 * math.cos(math.radians(ang))
        y2 = 200 + 128 * math.sin(math.radians(ang))
        return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#777" stroke-width="3"/>'

    ticks = "".join(tick_line(i) for i in range(11))
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
          {ticks}
          <text x="64" y="286" fill="#9aa4b2" font-size="16" font-family="Arial">0</text>
          <text x="110" y="150" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.25)}</text>
          <text x="190" y="105" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.50)}</text>
          <text x="272" y="150" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value*0.75)}</text>
          <text x="308" y="286" fill="#9aa4b2" font-size="16" font-family="Arial">{int(max_value)}</text>
          <g transform="rotate({angle:.1f} 200 200)" style="transition: transform 0.18s cubic-bezier(0.2, 0.9, 0.2, 1); filter:url(#glow);">
            <line x1="200" y1="205" x2="200" y2="78" stroke="#ff3b30" stroke-width="6" stroke-linecap="round"/>
            <line x1="200" y1="205" x2="200" y2="84" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
            <circle cx="200" cy="205" r="16" fill="#111" stroke="#d9d9d9" stroke-width="3"/>
          </g>
          <text x="200" y="248" text-anchor="middle" fill="#ffffff" font-size="38" font-family="Arial" font-weight="700">{value:.1f}</text>
          <text x="200" y="276" text-anchor="middle" fill="#8ab4ff" font-size="16" font-family="Arial">{unit}</text>
          <text x="200" y="308" text-anchor="middle" fill="#8f8f8f" font-size="15" font-family="Arial">safe {optimal_low:.0f}-{optimal_high:.0f} | redline {redline:.0f}</text>
        </svg>
      </div>
    </div>
    """


def render_audio_once(rpm_now, redline, muted=False, asset_names=None):
    if muted:
        return
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
        audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
        playback_rate = clamp(0.72 + (float(rpm_now) / max(float(redline), 1.0)) * 1.65, 0.72, 2.20)
        volume = clamp(0.18 + (float(rpm_now) / max(float(redline), 1.0)) * 0.42, 0.18, 0.60)
        html = f"""
        <html>
        <body style='margin:0; padding:0; background:transparent; overflow:hidden;'>
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
              a.onended = () => {{ a.pause(); a.currentTime = 0; }};
            }}
          </script>
        </body>
        </html>
        """
        components.html(html, height=0)
    except Exception:
        pass


def build_live_graph(history, current_idx=None, current_rpm=None, current_hp=None, current_nm=None):
    fig = go.Figure()
    colors = ["rgba(255, 0, 0, 1)", "rgba(0, 255, 0, 1)", "rgba(0, 0, 255, 1)", "rgba(255, 255, 0, 1)", "rgba(255, 0, 255, 1)", "rgba(0, 255, 255, 1)"]

    for i, r in enumerate(history):
        color = colors[i % len(colors)]
        opacity = 0.18 if i < len(history) - 1 else 0.92
        width = 2 if i < len(history) - 1 else 3
        dash = "dot" if i < len(history) - 1 else "solid"
        fig.add_trace(go.Scatter(x=r["rpms"], y=r["hps"], line=dict(color=color, width=width, dash=dash), opacity=opacity, showlegend=False))
        fig.add_trace(go.Scatter(x=r["rpms"], y=r["torques"], line=dict(color=color, width=max(width - 1, 1), dash="dot"), opacity=opacity, yaxis="y2", showlegend=False))

    if current_idx is not None and history:
        current = history[current_idx]
        color = colors[current_idx % len(colors)]
        live_pos = current.get("live_pos", len(current["rpms"]) - 1)
        live_pos = clamp(int(live_pos), 0, len(current["rpms"]) - 1)
        fig.add_trace(go.Scatter(x=current["rpms"][: live_pos + 1], y=current["hps"][: live_pos + 1], line=dict(color=color, width=5), showlegend=False))
        fig.add_trace(go.Scatter(x=[current_rpm], y=[current_hp], mode="markers", marker=dict(size=10, color="#FFFFFF", line=dict(color=color, width=3)), showlegend=False))
        fig.add_trace(go.Scatter(x=[current_rpm], y=[current_nm], mode="markers", marker=dict(size=8, color="#FFFFFF", line=dict(color=color, width=2)), yaxis="y2", showlegend=False))
        fig.add_vline(x=current_rpm, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.45)")

    fig.update_layout(
        template="plotly_dark",
        height=470,
        xaxis=dict(title="Engine RPM", showgrid=True, gridcolor="#333", dtick=1000),
        yaxis=dict(title="Power (HP)", showgrid=True, gridcolor="#333"),
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False),
        paper_bgcolor="#050505",
        plot_bgcolor="#050505",
        margin=dict(l=20, r=20, t=10, b=10),
        showlegend=False,
    )
    return fig


# =========================================================
# CORE CALCULATION
# =========================================================
def calculate_engine_metrics(cc, bore, stroke, cr, rpm_limit, valve_in, n_valve_in, valve_out, n_valve_out, lift, venturi, dur_in, dur_out, afr, material, drivetrain, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques, vel_in_list, vel_out_list, ve_list = [], [], [], [], []

    std_cc = (0.785398 * float(std["bore"]) ** 2 * float(std["stroke"])) / 1000.0
    std_cr = (std_cc + float(std["v_head"])) / float(std["v_head"])
    std_intake_area = harmonic_mean(area_circle_mm2(float(std["venturi"])) * 0.95, curtain_area_mm2(float(std["valve_in"]), float(std["lift_std"]), int(std["valves"])) * 0.80)
    std_exhaust_area = harmonic_mean(area_circle_mm2(float(std["venturi"])) * 0.82, curtain_area_mm2(float(std["valve_out"]), float(std["lift_std"]) * 0.92, max(int(std["valves"] / 2), 1)) * 0.78)
    std_lift_ratio = safe_div(float(std["lift_std"]), float(std["valve_in"]), 0.0)

    avg_dur = (float(dur_in) + float(dur_out)) / 2.0
    adj_peak_rpm = float(std["peak_rpm"]) + ((avg_dur - float(std["dur_std"])) * 42.0) + ((float(lift) - float(std["lift_std"])) * 165.0) + ((float(venturi) - float(std["venturi"])) * 26.0)
    adj_peak_rpm = clamp(adj_peak_rpm, 3500.0, float(rpm_limit) + 1200.0)

    drive_factor = 0.985 if drivetrain == "CVT" else 1.015
    material_factor = 1.0 if material == "Casting" else 1.02
    afr_target = 12.8
    cr_target = std_cr + 0.55

    for r in rpms:
        spread = clamp(1800.0 + abs(avg_dur - float(std["dur_std"])) * 10.0 + abs(float(lift) - float(std["lift_std"])) * 55.0 + abs(float(venturi) - float(std["venturi"])) * 18.0, 1200.0, 5200.0)
        ve = math.exp(-((r - adj_peak_rpm) / spread) ** 2)

        intake_curtain = curtain_area_mm2(float(valve_in), float(lift), int(n_valve_in))
        exhaust_curtain = curtain_area_mm2(float(valve_out), float(lift) * 0.92, max(int(n_valve_out), 1))
        tb_area = area_circle_mm2(float(venturi))
        intake_area = harmonic_mean(max(tb_area * 0.95, 1e-6), max(intake_curtain * 0.80, 1e-6))
        exhaust_area = harmonic_mean(max(tb_area * 0.82, 1e-6), max(exhaust_curtain * 0.78, 1e-6))
        flow_ratio_in = intake_area / max(std_intake_area, 1e-9)
        flow_ratio_out = exhaust_area / max(std_exhaust_area, 1e-9)

        lift_ratio = safe_div(float(lift), float(valve_in), 0.0)
        lift_ratio_delta = lift_ratio - std_lift_ratio

        afr_factor = clamp(1.0 - ((float(afr) - afr_target) ** 2) * 0.045, 0.72, 1.08)
        cr_factor = math.exp(-((float(cr) - cr_target) / 1.35) ** 2) / max(math.exp(-((std_cr - cr_target) / 1.35) ** 2), 1e-9)
        if float(cr) > 14.5:
            cr_factor *= max(0.18, 1.0 - ((float(cr) - 14.5) * 0.18))
        if float(cr) < 9.6:
            cr_factor *= max(0.55, 1.0 - ((9.6 - float(cr)) * 0.08))

        cam_factor = clamp(1.0 + (avg_dur - float(std["dur_std"])) * 0.0020 - ((avg_dur - float(std["dur_std"])) ** 2) * 0.0000014, 0.78, 1.22)
        lift_factor = clamp(1.0 + (lift_ratio_delta * 2.15) - (lift_ratio_delta ** 2) * 5.6, 0.72, 1.28)
        flow_factor = clamp((flow_ratio_in ** 0.43) * (flow_ratio_out ** 0.23), 0.68, 1.38)
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

        hp = float(std["hp_std"]) * (float(cc) / max(std_cc, 1e-9)) ** 0.92
        hp *= flow_factor * cam_factor * lift_factor * afr_factor * cr_factor * rpm_factor * material_factor * drive_factor
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

        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))
        vel_in_list.append(round(vel_in, 2))
        vel_out_list.append(round(vel_out, 2))
        ve_list.append(round(ve, 4))

    idx_hp = int(np.argmax(hps))
    idx_nm = int(np.argmax(torques))
    return {
        "rpms": rpms,
        "hps": hps,
        "torques": torques,
        "idx_hp": idx_hp,
        "idx_nm": idx_nm,
        "peak_hp": hps[idx_hp],
        "peak_nm": torques[idx_nm],
        "rpm_hp": int(rpms[idx_hp]),
        "rpm_nm": int(rpms[idx_nm]),
        "velocity_in": vel_in_list[idx_hp],
        "velocity_out": vel_out_list[idx_hp],
        "piston_speed": round((2.0 * float(stroke) * float(rpms[idx_hp])) / 60000.0, 2),
        "vel_in_list": vel_in_list,
        "vel_out_list": vel_out_list,
        "ve_list": ve_list,
    }


def drag_profile(hp_max, weight_total):
    pwr = max((hp_max / max(weight_total, 1e-9)) * 10.0, 0.25)
    t1000 = 32.8 / math.pow(pwr, 0.45)
    t402 = t1000 * 0.62
    t201 = t1000 * 0.36
    t100 = t1000 * 0.20

    def vmax_at(dist, tt):
        return clamp((dist / max(tt, 1e-6)) * 3.6 * 1.08, 0.0, 260.0)

    return {
        "total_time": t1000,
        "idle_time": clamp(1.0 + (pwr * 0.15), 1.0, 3.0),
        "segments": [
            ("0-100m", t100, vmax_at(100.0, t100)),
            ("0-201m", t201, vmax_at(201.0, t201)),
            ("0-402m", t402, vmax_at(402.0, t402)),
            ("0-1000m", t1000, vmax_at(1000.0, t1000)),
        ],
    }


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("1️⃣ MOTOR CONFIG")
    sel_merk = st.selectbox("Merk", list(DATABASE_REF.keys()))
    sel_sys = st.selectbox("Sistem Bahan Bakar", list(DATABASE_REF[sel_merk].keys()))
    sel_cc = st.selectbox("Kapasitas (CC)", list(DATABASE_REF[sel_merk][sel_sys].keys()))
    sel_model = st.selectbox("Model Motor", list(DATABASE_REF[sel_merk][sel_sys][sel_cc].keys()))
    std = DATABASE_REF[sel_merk][sel_sys][sel_cc][sel_model]

    st.header("2️⃣ ENGINE SIMULATION")
    with st.expander("🛠️ Engine Input", expanded=True):
        raw_label = st.text_input("Label Run", value=f"Run {len(st.session_state.dyno_history) + len(st.session_state.drag_history) + 1}")
        full_label = f"{raw_label} {sel_model.split(' ')[0]}"
        in_bore = st.number_input(f"Bore (std: {std['bore']})", value=float(std["bore"]), step=0.1)
        in_stroke = st.number_input(f"Stroke (std: {std['stroke']})", value=float(std["stroke"]), step=0.1)
        in_vhead = st.number_input(f"Vol Head (std: {std['v_head']})", value=float(std["v_head"]), step=0.1)
        in_rpm = st.number_input(f"Limit RPM (std: {std['limit_std']})", value=int(std["limit_std"]), step=100)
        in_v_in = st.number_input(f"Klep In (std: {std['valve_in']})", value=float(std["valve_in"]), step=0.1)
        default_in_idx = [1, 2, 4].index(std["valves"]) if std["valves"] in [1, 2, 4] else 1
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2, 4], index=default_in_idx)
        in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std["valve_out"]), step=0.1)
        out_default_idx = [1, 2, 4].index(max(min(std["valves"], 2), 1)) if max(min(std["valves"], 2), 1) in [1, 2, 4] else 1
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2, 4], index=out_default_idx)
        in_venturi = st.number_input(f"Venturi/TB (std: {std['venturi']})", value=float(std["venturi"]), step=0.5)
        in_v_lift = st.number_input(f"Lift (std: {std['lift_std']})", value=float(std["lift_std"]), step=0.1)
        in_dur_in = st.number_input(f"Durasi In (std: {std['dur_std']})", value=float(std["dur_std"]), step=1.0)
        in_dur_out = st.number_input(f"Durasi Out (std: {std['dur_std']})", value=float(std["dur_std"]), step=1.0)
        in_afr = st.number_input("AFR (Rasio Udara/BBM)", min_value=11.0, max_value=15.0, value=12.8, step=0.1)
        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])

    st.header("3️⃣ ACTION")
    run_dyno_btn = st.button("🚀 ANALYZE & RUN AXIS", use_container_width=True)
    with st.expander("🏁 Drag Simulator", expanded=True):
        drag_joki = st.number_input("Berat Joki Drag (kg)", value=60.0, step=1.0)
        run_drag_btn = st.button("🏁 RUN DRAG SIMULATOR", use_container_width=True)
    mute_audio = st.toggle("🔇 Mute Audio", value=st.session_state.mute_audio)
    st.session_state.mute_audio = mute_audio


# =========================================================
# MAIN DISPLAY
# =========================================================
st.title("📟 Hiar Lima Pendawa Tuning")

cc_calc = (0.785398 * float(in_bore) ** 2 * float(in_stroke)) / 1000.0
cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)

if not (run_dyno_btn or run_drag_btn) and not st.session_state.dyno_history and not st.session_state.drag_history:
    st.markdown("### 🎥 Standby Visual")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(needle_gauge_html("Tachometer", 0.0, 15.0, "x1000rpm", 9.0, 1.5, 8.8), unsafe_allow_html=True)
    with c2:
        st.markdown(needle_gauge_html("Speedometer", 0.0, 120.0, "km/h", 100.0, 20.0, 80.0), unsafe_allow_html=True)
    st.info("Klik **Analyze & Run Axis** untuk dyno satu kali, atau **Run Drag Simulator** untuk simulasi 0–1000m.")


# =========================================================
# DYNO AXIS RUN
# =========================================================
if run_dyno_btn:
    dyno = calculate_engine_metrics(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm,
        in_v_in, in_n_v_in, in_v_out, in_n_v_out,
        in_v_lift, in_venturi, in_dur_in, in_dur_out,
        in_afr, in_material, in_d_type, std,
    )

    hp_max = dyno["peak_hp"]
    nm_max = dyno["peak_nm"]
    pwr = max((hp_max / (float(std["weight_std"]) + 60.0)) * 10.0, 0.25)

    run = {
        "mode": "dyno",
        "Run": full_label,
        "CC": cc_calc,
        "CR": cr_calc,
        "AFR": in_afr,
        "Max_HP": hp_max,
        "RPM_HP": dyno["rpm_hp"],
        "Max_Nm": nm_max,
        "RPM_Nm": dyno["rpm_nm"],
        "Velocity": dyno["velocity_in"],
        "Velocity_Out": dyno["velocity_out"],
        "PistonSpeed": dyno["piston_speed"],
        "rpms": dyno["rpms"],
        "hps": dyno["hps"],
        "torques": dyno["torques"],
        "v_in": in_v_in,
        "v_out": in_v_out,
        "bore": in_bore,
        "stroke": in_stroke,
        "lift": in_v_lift,
        "venturi": in_venturi,
        "material": in_material,
        "live_pos": 0,
        "T100": 6.5 / math.pow(pwr, 0.45),
        "T201": 10.2 / math.pow(pwr, 0.45),
        "T402": 16.5 / math.pow(pwr, 0.45),
        "T1000": 32.8 / math.pow(pwr, 0.45),
    }
    st.session_state.dyno_history.append(run)
    latest = run

    st.markdown("### 🎥 Live Dyno Visual")
    g1, g2 = st.columns(2)
    tach_ph = g1.empty()
    speed_ph = g2.empty()
    graph_ph = st.empty()

    # 1) standby 0
    for _ in range(4):
        tach_ph.markdown(needle_gauge_html("Tachometer", 0.0, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", 0.0, 120.0, "km/h", 100.0, 20.0, 80.0), unsafe_allow_html=True)
        time.sleep(0.06)

    # 2) idle 1500-1800 rpm 1-5 detik (berdasarkan frame)
    idle_frames = list(np.linspace(1.5, 1.8, 25))
    warmup_frames = list(np.linspace(1.8, 3.2, 10))
    rise_frames = list(np.linspace(3.2, float(latest["RPM_HP"]) / 1000.0, 22))
    hold_frames = [float(latest["RPM_HP"]) / 1000.0] * 5
    sweep_frames = list(np.linspace(float(latest["RPM_HP"]) / 1000.0, float(in_rpm) / 1000.0, 14))
    limiter_bounce = []
    redline_k = float(in_rpm) / 1000.0
    for _ in range(4):
        limiter_bounce += [redline_k * 0.97, redline_k, redline_k * 1.01, redline_k * 0.985]
    down_frames = list(np.linspace(redline_k, 1.8, 10))
    idle_end_frames = [1.8] * 18   # idle 1-3 detik
    off_frames = list(np.linspace(1.8, 0.0, 8))

    anim_rpms_k = idle_frames + warmup_frames + rise_frames + hold_frames + sweep_frames + limiter_bounce + down_frames + idle_end_frames + off_frames

    for idx, rpm_k in enumerate(anim_rpms_k):
        rpm_now = max(float(rpm_k) * 1000.0, 0.0)
        live_pos = min(int((rpm_now / max(float(latest["rpms"][-1]), 1.0)) * (len(latest["rpms"]) - 1)), len(latest["rpms"]) - 1)
        latest["live_pos"] = live_pos
        hp_now = float(np.interp(rpm_now, latest["rpms"], latest["hps"]))
        nm_now = float(np.interp(rpm_now, latest["rpms"], latest["torques"]))

        speed_max = max(120.0, 60.0 + latest["Max_HP"] * 5.0)
        speed_now = clamp((rpm_now / max(float(latest["rpms"][-1]), 1.0)) * speed_max, 0.0, speed_max)

        tach_ph.markdown(needle_gauge_html("Tachometer", rpm_k, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", speed_now, speed_max, "km/h", speed_max * 0.82, speed_max * 0.35, speed_max * 0.68), unsafe_allow_html=True)

        live_graph = build_live_graph(st.session_state.dyno_history, current_idx=len(st.session_state.dyno_history) - 1, current_rpm=rpm_now, current_hp=hp_now, current_nm=nm_now)
        graph_ph.plotly_chart(live_graph, use_container_width=True, key=f"dyno_graph_{idx}")

        render_audio_once(rpm_now, float(in_rpm), muted=st.session_state.mute_audio)

        if rpm_now <= 0:
            time.sleep(0.10)
        elif rpm_now < 1800:
            time.sleep(0.07)
        elif rpm_now < float(latest["RPM_HP"]):
            time.sleep(0.045)
        elif rpm_now < float(in_rpm):
            time.sleep(0.040)
        else:
            time.sleep(0.040)

    # 3) idle 3 detik lalu off
    for _ in range(15):
        tach_ph.markdown(needle_gauge_html("Tachometer", 1.8, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", 0.0, max(120.0, 60.0 + latest["Max_HP"] * 5.0), "km/h", max(120.0, 60.0 + latest["Max_HP"] * 5.0) * 0.82, 20.0, 80.0), unsafe_allow_html=True)
        time.sleep(0.18)
    tach_ph.markdown(needle_gauge_html("Tachometer", 0.0, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
    speed_ph.markdown(needle_gauge_html("Speedometer", 0.0, max(120.0, 60.0 + latest["Max_HP"] * 5.0), "km/h", max(120.0, 60.0 + latest["Max_HP"] * 5.0) * 0.82, 20.0, 80.0), unsafe_allow_html=True)

    # 4) flowbench dan data baru tampil setelah run selesai
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Gas Speed In", f"{latest['Velocity']:.2f} m/s")
    with m2:
        st.metric("Gas Speed Out", f"{latest['Velocity_Out']:.2f} m/s")
    with m3:
        st.metric("Piston Speed", f"{latest['PistonSpeed']:.2f} m/s")
    with m4:
        st.metric("CC", f"{latest['CC']:.2f}")
    with m5:
        st.metric("CR", f"{latest['CR']:.2f}")

    st.markdown("### 📊 Performance Dyno Result")
    df_dyno = pd.DataFrame(st.session_state.dyno_history)
    df_perf = df_dyno[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "Velocity"]].copy()
    st.dataframe(
        df_perf.style
        .format({"CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}", "Velocity": "{:.2f}"})
        .map(lambda v: style_state(v, "cr"), subset=["CR"])
        .map(lambda v: style_state(v, "vel"), subset=["Velocity"])
        .map(lambda v: style_state(v, "afr"), subset=["AFR"]),
        hide_index=True,
        use_container_width=True,
    )

    # ringkas analisa saja, tidak mengganggu visual
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")
    c1, c2, c3 = st.columns(3)
    lift_ratio = safe_div(latest["lift"], latest["v_in"], 0.0)
    valve_area_index = safe_div(curtain_area_mm2(latest["v_in"], latest["lift"], 2), area_circle_mm2(latest["venturi"]), 0.0)
    cr_state = state_from_value(latest["CR"], 9.5, 13.8, 10.0, 12.8)
    vel_state = state_from_value(latest["Velocity"], 90.0, 99.9, 100.0, 110.0)
    with c1:
        st.markdown(f"- CC **{latest['CC']:.2f}** / CR **{latest['CR']:.2f}:1**")
        st.markdown(f"- Lift ratio **{lift_ratio:.3f}**")
        st.markdown(f"- {color_tag('CR ' + ('optimal' if cr_state == 'optimal' else 'safe' if cr_state == 'safe' else 'risk'), cr_state if cr_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)
    with c2:
        st.markdown(f"- Velocity **{latest['Velocity']:.2f} m/s**")
        st.markdown(f"- Exhaust velocity **{latest['Velocity_Out']:.2f} m/s**")
        st.markdown(f"- {color_tag('Velocity ' + ('optimal' if vel_state == 'optimal' else 'safe' if vel_state == 'safe' else 'risk'), vel_state if vel_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)
    with c3:
        st.markdown(f"- Valve area index **{valve_area_index:.3f}**")
        if latest["AFR"] > 13.5:
            st.warning("AFR terlalu kering, tambah bensin / injector.")
        elif latest["AFR"] < 12.0:
            st.info("AFR terlalu basah, kurangi fuel.")
        else:
            st.success("AFR sudah aman/optimal.")


# =========================================================
# DRAG SIMULATOR
# =========================================================
if run_drag_btn:
    dyno_like = calculate_engine_metrics(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm,
        in_v_in, in_n_v_in, in_v_out, in_n_v_out,
        in_v_lift, in_venturi, in_dur_in, in_dur_out,
        in_afr, in_material, in_d_type, std,
    )
    hp_max = dyno_like["peak_hp"]
    weight_total = float(std["weight_std"]) + float(drag_joki)
    prof = drag_profile(hp_max, weight_total)

    drag_run = {
        "mode": "drag",
        "Run": full_label,
        "CC": cc_calc,
        "HP": hp_max,
        "Weight": weight_total,
        "0-100m": prof["segments"][0][1],
        "0-201m": prof["segments"][1][1],
        "0-402m": prof["segments"][2][1],
        "0-1000m": prof["segments"][3][1],
        "Max Speed": max(x[2] for x in prof["segments"]),
        "segments": prof["segments"],
    }
    st.session_state.drag_history.append(drag_run)

    st.markdown("### 🏁 Drag Simulator")
    c1, c2 = st.columns(2)
    tach_ph = c1.empty()
    speed_ph = c2.empty()
    graph_ph = st.empty()

    # idle singkat sebelum start
    for _ in range(int(prof["idle_time"] * 10)):
        tach_ph.markdown(needle_gauge_html("Tachometer", 1.8, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", 0.0, max(120.0, drag_run["Max Speed"] * 1.15), "km/h", max(120.0, drag_run["Max Speed"]) * 0.82, 40.0, 110.0), unsafe_allow_html=True)
        time.sleep(0.11)

    n_frames = 90
    for i in range(n_frames + 1):
        p = i / n_frames
        dist = 1000.0 * p
        speed_now = drag_run["Max Speed"] * (1.0 - math.exp(-3.1 * p))
        speed_now = clamp(speed_now + 4.0 * math.sin(p * math.pi), 0.0, drag_run["Max Speed"])
        rpm_now = clamp(1800.0 + (float(in_rpm) - 1800.0) * (speed_now / max(drag_run["Max Speed"], 1e-9)) ** 0.95, 1800.0, float(in_rpm))
        hp_now = hp_max * (0.55 + 0.45 * p)
        nm_now = hp_now * 7127.0 / max(rpm_now, 1.0)

        tach_ph.markdown(needle_gauge_html("Tachometer", rpm_now / 1000.0, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", speed_now, max(120.0, drag_run["Max Speed"] * 1.15), "km/h", max(120.0, drag_run["Max Speed"]) * 0.82, 40.0, 110.0), unsafe_allow_html=True)

        graph = go.Figure()
        graph.add_trace(go.Scatter(x=[0, dist], y=[0, speed_now], line=dict(width=4), showlegend=False))
        graph.update_layout(
            template="plotly_dark",
            height=260,
            xaxis=dict(title="Distance (m)", range=[0, 1000], showgrid=True, gridcolor="#333"),
            yaxis=dict(title="Speed (km/h)", range=[0, max(120.0, drag_run["Max Speed"] * 1.15)], showgrid=True, gridcolor="#333"),
            paper_bgcolor="#050505",
            plot_bgcolor="#050505",
            margin=dict(l=20, r=20, t=15, b=15),
            showlegend=False,
        )
        if i % 2 == 0:
            graph_ph.plotly_chart(graph, use_container_width=True, key=f"drag_graph_{i}")

        render_audio_once(rpm_now, float(in_rpm), muted=st.session_state.mute_audio)
        time.sleep(max(prof["total_time"] / n_frames, 0.03))

    # final idle
    for _ in range(10):
        tach_ph.markdown(needle_gauge_html("Tachometer", 0.0, 15.0, "x1000rpm", float(in_rpm) / 1000.0, 1.5, 8.8), unsafe_allow_html=True)
        speed_ph.markdown(needle_gauge_html("Speedometer", 0.0, max(120.0, drag_run["Max Speed"] * 1.15), "km/h", max(120.0, drag_run["Max Speed"]) * 0.82, 40.0, 110.0), unsafe_allow_html=True)
        time.sleep(0.18)

    st.markdown("### 📊 Drag Simulation Result")
    drag_table = pd.DataFrame([{ "Run": drag_run["Run"], "100m": drag_run["0-100m"], "201m": drag_run["0-201m"], "402m": drag_run["0-402m"], "1000m": drag_run["0-1000m"], "Max Speed (km/h)": drag_run["Max Speed"] }])
    st.dataframe(drag_table.style.format({"100m": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s", "Max Speed (km/h)": "{:.1f}"}), hide_index=True, use_container_width=True)

    st.markdown("### 🧮 Segment Estimate")
    seg_df = pd.DataFrame([
        {"Segment": seg[0], "Time": seg[1], "Estimated Max Speed": seg[2]} for seg in drag_run["segments"]
    ])
    st.dataframe(seg_df.style.format({"Time": "{:.2f}s", "Estimated Max Speed": "{:.1f} km/h"}), hide_index=True, use_container_width=True)


# =========================================================
# TABLES FOR HISTORY
# =========================================================
if st.session_state.dyno_history and not run_dyno_btn:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.header("📊 Performance Dyno Result")
    df_dyno = pd.DataFrame(st.session_state.dyno_history)
    df_perf = df_dyno[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "Velocity"]].copy()
    st.dataframe(
        df_perf.style
        .format({"CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}", "Velocity": "{:.2f}"})
        .map(lambda v: style_state(v, "cr"), subset=["CR"])
        .map(lambda v: style_state(v, "vel"), subset=["Velocity"])
        .map(lambda v: style_state(v, "afr"), subset=["AFR"]),
        hide_index=True,
        use_container_width=True,
    )

if st.session_state.drag_history and not run_drag_btn:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.header("🏁 Drag Simulation Predictions")
    df_drag = pd.DataFrame(st.session_state.drag_history)
    df_drag = df_drag[["Run", "0-100m", "0-201m", "0-402m", "0-1000m", "Max Speed"]].rename(columns={"0-100m": "100m", "0-201m": "201m", "0-402m": "402m", "0-1000m": "1000m", "Max Speed": "Max Speed (km/h)"})
    st.dataframe(df_drag.style.format({"100m": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s", "Max Speed (km/h)": "{:.1f}"}), hide_index=True, use_container_width=True)

st.write("---")
st.error("⚠️ **DISCLAIMER:** Perhitungan hanya estimasi kalkulasi data, hasil nyata bergantung pada efisiensi volumetrik, suhu, kualitas part, dan setting lapangan.")
