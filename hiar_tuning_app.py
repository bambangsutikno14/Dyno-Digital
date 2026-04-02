import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd
import hashlib

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

# --- 3. HELPERS ---
def clamp(value, low, high):
    return max(low, min(high, value))


def safe_div(a, b, default=0.0):
    return a / b if abs(b) > 1e-12 else default


def param_signature(*values):
    parts = []
    for v in values:
        if isinstance(v, float):
            parts.append(f"{v:.4f}")
        else:
            parts.append(str(v))
    raw = "|".join(parts).encode("utf-8")
    return int(hashlib.sha1(raw).hexdigest(), 16)


def choose_variant(options, *signature_values):
    if not options:
        return ""
    idx = param_signature(*signature_values) % len(options)
    return options[idx]


def color_tag(text, level):
    palette = {
        "safe": "#3ba3ff",      # biru
        "optimal": "#39d353",   # hijau
        "risk": "#ff4d4f"       # merah
    }
    return f"<span style='color:{palette.get(level, '#ffffff')}; font-weight:700'>{text}</span>"


def state_from_value(value, safe_low, safe_high, opt_low, opt_high):
    if opt_low <= value <= opt_high:
        return "optimal"
    if safe_low <= value <= safe_high:
        return "safe"
    return "risk"


def style_state(val, kind):
    if kind == "cr":
        if val <= 0:
            return "color:#ff4d4f; font-weight:700"
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


def display_state_label(value, kind, label_safe, label_opt, label_risk, safe_low, safe_high, opt_low, opt_high):
    state = state_from_value(value, safe_low, safe_high, opt_low, opt_high)
    if state == "optimal":
        return color_tag(f"{label_opt}", "optimal")
    if state == "safe":
        return color_tag(f"{label_safe}", "safe")
    return color_tag(f"{label_risk}", "risk")


def area_circle_mm2(diameter_mm):
    return math.pi * (diameter_mm / 2.0) ** 2


def curtain_area_mm2(valve_d_mm, lift_mm, n_valves):
    return math.pi * max(valve_d_mm, 0.1) * max(lift_mm, 0.1) * max(n_valves, 1)


def harmonic_mean(a, b):
    return (2.0 * a * b) / max(a + b, 1e-9)


# --- 4. CORE CALCULATION (REVISED: lebih sensitif, tetap stabil) ---
def calculate_axis_v22(cc, bore, stroke, cr, rpm_limit, v_in, n_v_in, v_out, n_v_out, v_lift, venturi, dur_in, dur_out, afr, material, d_type, std):
    rpms = np.arange(1000, int(rpm_limit) + 100, 100)
    hps, torques = [], []
    pspeeds, vel_in_list, vel_out_list = [], [], []
    ve_list = []

    std_cc = (0.785398 * float(std['bore']) ** 2 * float(std['stroke'])) / 1000.0
    std_cr = (std_cc + float(std['v_head'])) / float(std['v_head'])
    std_avg_dur = float(std['dur_std'])
    std_lift_ratio = safe_div(float(std['lift_std']), float(std['valve_in']), 0.0)

    std_intake_curtain = curtain_area_mm2(float(std['valve_in']), float(std['lift_std']), int(std['valves']))
    std_exhaust_curtain = curtain_area_mm2(float(std['valve_out']), float(std['lift_std']) * 0.92, max(int(std['valves'] / 2), 1))
    std_tb_area = area_circle_mm2(float(std['venturi']))

    std_intake_area = harmonic_mean(std_tb_area * 0.95, std_intake_curtain * 0.80)
    std_exhaust_area = harmonic_mean(std_tb_area * 0.82, std_exhaust_curtain * 0.78)

    # faktor dasar drivetrain: tetap kecil agar output tidak liar, tapi tetap sensitif terhadap CVT / rantai
    drive_factor = 0.985 if d_type == "CVT" else 1.015
    material_factor = 1.0 if material == "Casting" else 1.02
    afr_target = 12.8

    # timing / puncak rpm bergeser sangat halus mengikuti durasi, lift, dan flow
    dur_delta = float(dur_in) - std_avg_dur
    lift_delta = float(v_lift) - float(std['lift_std'])
    flow_delta = float(venturi) - float(std['venturi'])
    adj_peak_rpm = float(std['peak_rpm']) + (dur_delta * 42.0) + (lift_delta * 165.0) + (flow_delta * 26.0)
    adj_peak_rpm = clamp(adj_peak_rpm, 3500.0, float(rpm_limit) + 1200.0)

    # basis hp dibentuk dari data standar agar hasil tidak terlalu jauh dari dyno referensi
    # lalu diperbaiki oleh faktor flow, CR, AFR, lift, timing, rpm, dan thermal/friction penalty
    for r in rpms:
        # --- VE curve ---
        spread = 1800.0 + abs(dur_delta) * 10.0 + abs(lift_delta) * 55.0 + abs(flow_delta) * 18.0
        spread = clamp(spread, 1200.0, 5200.0)
        ve = math.exp(-((r - adj_peak_rpm) / spread) ** 2)

        # displacement factor (sangat lembut supaya stok tetap dekat hp_std)
        cc_factor = (float(cc) / max(std_cc, 1e-9)) ** 0.92

        # area / flow factor: semakin mismatch antara TB dan curtain, semakin besar penalti
        intake_curtain = curtain_area_mm2(float(v_in), float(v_lift), int(n_v_in))
        exhaust_curtain = curtain_area_mm2(float(v_out), float(v_lift) * 0.92, max(int(n_v_out), 1))
        tb_area = area_circle_mm2(float(venturi))
        intake_area = harmonic_mean(max(tb_area * 0.95, 1e-6), max(intake_curtain * 0.80, 1e-6))
        exhaust_area = harmonic_mean(max(tb_area * 0.82, 1e-6), max(exhaust_curtain * 0.78, 1e-6))
        flow_ratio_in = intake_area / max(std_intake_area, 1e-9)
        flow_ratio_out = exhaust_area / max(std_exhaust_area, 1e-9)

        # lift ratio vs valve diameter
        lift_ratio = safe_div(float(v_lift), float(v_in), 0.0)
        lift_ratio_std = max(std_lift_ratio, 1e-6)
        lift_ratio_delta = lift_ratio - lift_ratio_std

        # curve factors yang tetap 1 di setelan standar, tapi sensitif saat berubah
        cam_factor = clamp(1.0 + (dur_delta * 0.0020) - (dur_delta ** 2) * 0.0000014, 0.78, 1.22)
        lift_factor = clamp(1.0 + (lift_ratio_delta * 2.15) - (lift_ratio_delta ** 2) * 5.6, 0.72, 1.28)
        flow_factor = clamp((flow_ratio_in ** 0.43) * (flow_ratio_out ** 0.23), 0.68, 1.38)

        # AFR factor: paling stabil di 12.8; terlalu miskin / kaya akan menurunkan HP
        afr_delta = float(afr) - afr_target
        afr_factor = clamp(1.0 - (afr_delta ** 2) * 0.045, 0.72, 1.08)

        # CR factor: puncak halus di sekitar CR stok + sedikit advance; terlalu tinggi akan drop
        cr_target = std_cr + 0.55
        cr_factor = math.exp(-((float(cr) - cr_target) / 1.35) ** 2)
        cr_ref = math.exp(-((std_cr - cr_target) / 1.35) ** 2)
        cr_factor = safe_div(cr_factor, cr_ref, 1.0)
        if float(cr) > 14.5:
            cr_factor *= max(0.18, 1.0 - ((float(cr) - 14.5) * 0.18))
        if float(cr) < 9.6:
            cr_factor *= max(0.55, 1.0 - ((9.6 - float(cr)) * 0.08))

        # rpm factor: peak di area adjust peak rpm, lalu turun jika terlalu jauh
        rpm_factor = math.exp(-((r - adj_peak_rpm) / (spread * 0.95)) ** 2)

        # piston speed penalty
        ps_speed = (2.0 * float(stroke) * float(r)) / 60000.0
        friction_loss = clamp((r / float(rpm_limit)) ** 2 * 0.08 + (ps_speed / 28.0) ** 2 * 0.05, 0.00, 0.28)

        # velocity yang dipakai untuk analisa & dyno (dikondisikan agar mirip skala hasil axis dyno)
        disp_m3 = float(cc) / 1_000_000.0
        q_m3s = disp_m3 * (r / 2.0) / 60.0 * ve
        vel_in = safe_div(q_m3s, max(intake_area / 1_000_000.0, 1e-9), 0.0) * 5.55
        vel_out = safe_div(q_m3s, max(exhaust_area / 1_000_000.0, 1e-9), 0.0) * 6.95

        # velocity penalty / bonus: target optimal 100-110 m/s
        if vel_in < 90.0:
            ve *= clamp(0.74 + (vel_in / 150.0), 0.74, 0.98)
        elif 100.0 <= vel_in <= 110.0:
            ve *= 1.06
        elif vel_in > 110.0:
            ve *= clamp((110.0 / vel_in) ** 1.12, 0.70, 1.00)
        else:
            ve *= 1.0

        if vel_out < 92.0:
            ve *= clamp(0.80 + (vel_out / 220.0), 0.80, 0.99)
        elif 102.0 <= vel_out <= 115.0:
            ve *= 1.05
        elif vel_out > 115.0:
            ve *= clamp((115.0 / vel_out) ** 1.05, 0.72, 1.00)

        # kalau lift terlalu kecil untuk diameter klep, penalti cukup terasa
        if lift_ratio < 0.24:
            ve *= 0.88
        elif lift_ratio > 0.34:
            ve *= 0.94

        # kalau manifold terlalu kecil / terlalu besar terhadap flow, penalti tambahan
        if flow_ratio_in < 0.85:
            ve *= 0.90 + (flow_ratio_in * 0.10)
        elif flow_ratio_in > 1.45:
            ve *= 0.95

        # baseline hp dibangun dari hp_std agar stok tidak melenceng jauh
        hp = float(std['hp_std'])
        hp *= cc_factor * flow_factor * cam_factor * lift_factor * afr_factor * cr_factor * rpm_factor * material_factor * drive_factor
        hp *= (0.78 + 0.42 * ve)
        hp *= (1.0 - friction_loss)

        # batas fisika tambahan supaya hasil ekstrem tetap turun secara wajar
        if ps_speed > 23.0:
            hp *= max(0.68, 1.0 - ((ps_speed - 23.0) * 0.03))
        if float(cr) > 13.8 and material == "Casting":
            hp *= max(0.74, 1.0 - ((float(cr) - 13.8) * 0.06))
        if float(afr) < 12.0:
            hp *= max(0.82, 1.0 - ((12.0 - float(afr)) * 0.04))
        if float(afr) > 13.4:
            hp *= max(0.82, 1.0 - ((float(afr) - 13.4) * 0.04))

        # simpan hasil
        ve_list.append(round(ve, 4))
        pspeeds.append(round(ps_speed, 2))
        vel_in_list.append(round(vel_in, 2))
        vel_out_list.append(round(vel_out, 2))
        hps.append(round(hp, 2))
        torques.append(round((hp * 7127.0) / r if r > 0 else 0, 2))

    idx_hp = int(np.argmax(hps))
    idx_nm = int(np.argmax(torques))

    peak_gsin = vel_in_list[idx_hp]
    peak_gsout = vel_out_list[idx_hp]
    peak_pspeed = pspeeds[idx_hp]

    return rpms, hps, torques, peak_pspeed, peak_gsin, peak_gsout, vel_in_list, vel_out_list, ve_list, idx_hp, idx_nm


# --- 5. SIDEBAR ---
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
        default_in_idx = [1, 2, 4].index(std['valves']) if std['valves'] in [1, 2, 4] else 1
        in_n_v_in = st.selectbox("Jml Klep In", [1, 2, 4], index=default_in_idx)
        in_v_out = st.number_input(f"Klep Out (std: {std['valve_out']})", value=float(std['valve_out']), step=0.1)
        out_default_idx = [1, 2, 4].index(max(min(std['valves'], 2), 1)) if max(min(std['valves'], 2), 1) in [1, 2, 4] else 1
        in_n_v_out = st.selectbox("Jml Klep Out", [1, 2, 4], index=out_default_idx)

        in_venturi = st.number_input(f"Venturi/TB (std: {std['venturi']})", value=float(std['venturi']), step=0.5)
        in_v_lift = st.number_input(f"Lift (std: {std['lift_std']})", value=float(std['lift_std']), step=0.1)
        in_dur_in = st.number_input(f"Durasi In (std: {std['dur_std']})", value=float(std['dur_std']), step=1.0)
        in_dur_out = st.number_input(f"Durasi Out (std: {std['dur_std']})", value=float(std['dur_std']), step=1.0)

        in_afr = st.number_input("AFR (Rasio Udara/BBM)", min_value=11.0, max_value=15.0, value=12.8, step=0.1)

        in_material = st.selectbox("Piston", ["Casting", "Forged"])
        in_d_type = st.selectbox("Penggerak", ["CVT", "Rantai"])

    cc_calc = (0.785398 * float(in_bore) ** 2 * float(in_stroke)) / 1000.0
    cc_placeholder.success(f"CC: {cc_calc:.2f}")
    in_joki = st.number_input("Berat Joki (kg)", value=60.0)
    run_btn = st.button("🚀 ANALYZE & RUN AXIS")


# --- 6. MAIN DISPLAY ---
st.title("📟 Hiar Lima Pendawa Tuning")

if run_btn:
    cr_calc = (cc_calc + float(in_vhead)) / float(in_vhead)
    rpms, hps, torques, peak_pspeed, peak_gsin, peak_gsout, vel_in_list, vel_out_list, ve_list, idx_hp, idx_nm = calculate_axis_v22(
        cc_calc, in_bore, in_stroke, cr_calc, in_rpm, in_v_in, in_n_v_in,
        in_v_out, in_n_v_out, in_v_lift, in_venturi, in_dur_in, in_dur_out,
        in_afr, in_material, in_d_type, std
    )

    hp_max = max(hps)
    nm_max = max(torques)

    # power-to-weight untuk drag prediction; tetap sederhana tapi lebih sensitif
    pwr = (hp_max / (float(std['weight_std']) + float(in_joki))) * 10.0
    pwr = max(pwr, 0.25)

    v_state = state_from_value(peak_gsin, 90.0, 99.9, 100.0, 110.0)
    cr_state = state_from_value(cr_calc, max(9.0, (cc_calc + in_vhead) / in_vhead - 0.5), max(13.8, (cc_calc + in_vhead) / in_vhead + 0.2), 10.0, 12.8)

    st.session_state.history.append({
        "Run": full_label,
        "CC": cc_calc,
        "CR": cr_calc,
        "AFR": in_afr,
        "Max_HP": hp_max,
        "RPM_HP": rpms[idx_hp],
        "Max_Nm": nm_max,
        "RPM_Nm": rpms[idx_nm],
        "Velocity": peak_gsin,
        "Velocity_Out": peak_gsout,
        "PistonSpeed": peak_pspeed,
        "gsin": peak_gsin,
        "gsout": peak_gsout,
        "pspeed": peak_pspeed,
        "rpms": rpms,
        "hps": hps,
        "torques": torques,
        "vel_in_list": vel_in_list,
        "vel_out_list": vel_out_list,
        "ve_list": ve_list,
        "v_in": in_v_in,
        "v_out": in_v_out,
        "bore": in_bore,
        "stroke": in_stroke,
        "lift": in_v_lift,
        "venturi": in_venturi,
        "material": in_material,
        "cr_state": cr_state,
        "vel_state": v_state,
        "T100": 6.5 / math.pow(pwr, 0.45),
        "T201": 10.2 / math.pow(pwr, 0.45),
        "T402": 16.5 / math.pow(pwr, 0.45),
        "T1000": 32.8 / math.pow(pwr, 0.45)
    })

if st.session_state.history:
    latest = st.session_state.history[-1]

    st.header("🌪️ Flowbench & Physical Analysis")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Gas Speed In", f"{latest['gsin']:.2f} m/s")
    with m2:
        st.metric("Gas Speed Out", f"{latest['gsout']:.2f} m/s")
    with m3:
        st.metric("Piston Speed", f"{latest['pspeed']:.2f} m/s")
    with m4:
        st.metric("Flow In (est)", f"{round((latest['v_in'] / 25.4) ** 2 * 146, 1)} CFM")
    with m5:
        st.metric("Flow Out (est)", f"{round((latest['v_out'] / 25.4) ** 2 * 146, 1)} CFM")

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
        idx_hp = int(np.argmax(r['hps']))
        idx_nm = int(np.argmax(r['torques']))
        fig.add_annotation(x=r['rpms'][idx_hp], y=r['hps'][idx_hp], text=f"Peak: {r['hps'][idx_hp]}HP@{r['rpms'][idx_hp]}", showarrow=True, arrowhead=1, bgcolor=bg_color, font=dict(color="white", size=11))
        fig.add_annotation(x=r['rpms'][idx_nm], y=r['torques'][idx_nm], text=f"Peak: {r['torques'][idx_nm]}Nm@{r['rpms'][idx_nm]}", showarrow=True, arrowhead=1, bgcolor=bg_color, font=dict(color="white", size=11), yref="y2")

    fig.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        xaxis=dict(title="Engine RPM", showgrid=True, gridcolor="#333", dtick=1000),
        yaxis=dict(title="Power (HP)", showgrid=True, gridcolor="#333"),
        yaxis2=dict(overlaying="y", side="right", title="Torque (Nm)", showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLES ---
    df = pd.DataFrame(st.session_state.history)
    st.write("### 📊 Performance Dyno Result")
    df_perf = df[["Run", "CC", "CR", "AFR", "Max_HP", "RPM_HP", "Max_Nm", "RPM_Nm", "Velocity"]].copy()
    st.dataframe(
        df_perf.style
        .format({"CC": "{:.2f}", "CR": "{:.2f}", "AFR": "{:.2f}", "Max_HP": "{:.2f}", "Max_Nm": "{:.2f}", "Velocity": "{:.2f}"})
        .map(lambda v: style_state(v, "cr"), subset=["CR"])
        .map(lambda v: style_state(v, "vel"), subset=["Velocity"])
        .map(lambda v: style_state(v, "afr"), subset=["AFR"]),
        hide_index=True,
        use_container_width=True
    )

    st.write("### 🏁 Drag Simulation Predictions")
    df_drag = df[["Run", "T100", "T201", "T402", "T1000"]].rename(columns={"T100": "100m", "T201": "201m", "T402": "402m", "T1000": "1000m"})
    st.dataframe(df_drag.style.format({
        "100m": "{:.2f}s", "201m": "{:.2f}s", "402m": "{:.2f}s", "1000m": "{:.2f}s"
    }), hide_index=True, use_container_width=True)

    # --- PERUBAHAN: ANALISA DINAMIS lebih sensitif & lebih banyak opsi jawaban ---
    st.divider()
    st.header("🏁 Axis Expert Physics Analysis")

    c1, c2, c3 = st.columns(3)

    lift_ratio = safe_div(latest['lift'], latest['v_in'], 0.0)
    valve_area_index = safe_div(curtain_area_mm2(latest['v_in'], latest['lift'], 2), area_circle_mm2(latest['venturi']), 0.0)
    sig = param_signature(
        latest['CC'], latest['CR'], latest['AFR'], latest['Max_HP'], latest['RPM_HP'], latest['Max_Nm'],
        latest['Velocity'], latest['Velocity_Out'], latest['PistonSpeed'], latest['bore'], latest['stroke'],
        latest['v_in'], latest['v_out'], latest['lift'], latest['venturi'], latest['material']
    )

    # thresholds yang bisa dibaca manusia
    cr_state = state_from_value(latest['CR'], 9.5, 13.8, 10.0, 12.8)
    vel_state = state_from_value(latest['Velocity'], 90.0, 99.9, 100.0, 110.0)
    piston_state = state_from_value(latest['PistonSpeed'], 0.0, 21.0, 0.0, 20.0)  # green ketika masih aman dan tidak tinggi
    lift_state = state_from_value(lift_ratio * 100.0, 24.0, 33.0, 28.0, 32.0)

    with c1:
        st.subheader("🧐 1. Analisa Spek Mesin")
        analisa_mesin = choose_variant([
            f"Kapasitas nyata berada di **{latest['CC']:.2f} cc** dengan kompresi statis **{latest['CR']:.2f}:1**.",
            f"Displacement terukur **{latest['CC']:.2f} cc**. Rasio kompresi aktual terbaca **{latest['CR']:.2f}:1**.",
            f"Spek mesin mengarah ke **{latest['CC']:.2f} cc** dan CR **{latest['CR']:.2f}:1** dengan karakter kompresi {('ringan' if latest['CR'] < 11 else 'padat' if latest['CR'] < 13 else 'agresif') }.",
            f"Volume kerja **{latest['CC']:.2f} cc** dan CR **{latest['CR']:.2f}:1** menandakan build ini {('lebih aman' if cr_state == 'safe' else 'ideal' if cr_state == 'optimal' else 'berisiko')}."
        ], sig, latest['CC'], latest['CR'])
        st.markdown(f"- {analisa_mesin}", unsafe_allow_html=True)
        st.markdown(f"- Efisiensi lift terhadap klep in berada di **{(lift_ratio * 100):.1f}%** ({lift_ratio:.3f}).")
        st.markdown(f"- Indeks area klep vs venturi berada di **{valve_area_index:.3f}**.")
        st.markdown(f"- {color_tag('Status CR: ' + ('optimal' if cr_state == 'optimal' else 'aman' if cr_state == 'safe' else 'berisiko'), cr_state if cr_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)
        st.markdown(f"- {color_tag('Status Velocity: ' + ('optimal' if vel_state == 'optimal' else 'aman' if vel_state == 'safe' else 'berisiko'), vel_state if vel_state in ['safe', 'optimal'] else 'risk')}", unsafe_allow_html=True)

    with c2:
        st.subheader("📚 2. Saran Ahli (Teori)")

        if latest['Velocity'] > 115.0:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s sudah terlalu liar. Port mulai bekerja seperti sumbatan, VE justru turun di rpm atas.",
                f"Gas speed {latest['Velocity']:.2f} m/s menandakan choke flow. Nafas atas panjang di atas kertas, tapi habis di real flow.",
                f"Kecepatan aliran {latest['Velocity']:.2f} m/s melewati zona efisien. Campuran mulai pecah dan tenaga puncak tidak stabil."
            ], sig, latest['Velocity'])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)
        elif latest['Velocity'] < 90.0:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s masih terlalu lambat. Scavenging kurang hidup dan torsi bawah terasa kosong.",
                f"Gas speed {latest['Velocity']:.2f} m/s belum cukup untuk mengunci inersia udara. Respons awal masih bisa dipadatkan.",
                f"Aliran {latest['Velocity']:.2f} m/s berada di bawah jendela kerja ideal. Intake perlu dipadatkan untuk menaikkan momentum charge."
            ], sig, latest['Velocity'])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Velocity {latest['Velocity']:.2f} m/s berada di zona optimal. VE cenderung hidup di tengah sampai atas.",
                f"Gas speed {latest['Velocity']:.2f} m/s pas. Ini zona yang biasanya paling enak untuk powerband CVT.",
                f"Kecepatan aliran {latest['Velocity']:.2f} m/s sudah mendekati sweet spot. Mesin cenderung padat dan responsif."
            ], sig, latest['Velocity'])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)

        if lift_ratio < 0.24:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} terlalu kecil untuk ukuran klep {latest['v_in']} mm. Katup belum dimanfaatkan penuh.",
                f"Lift ratio {lift_ratio:.3f} menunjukkan cam masih terlalu jinak. Nafas akan tertahan oleh durasi buka yang pendek.",
                f"Efektivitas lift {lift_ratio:.3f} belum cukup agresif. Area buka klep belum sebanding dengan kebutuhan flow."
            ], sig, lift_ratio, latest['v_in'])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        elif 0.24 <= lift_ratio <= 0.33:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} sudah berada di area kerja yang sehat untuk head ini.",
                f"Lift ratio {lift_ratio:.3f} cukup ideal. Ini biasanya bikin flow enak tanpa terlalu mengorbankan durabilitas.",
                f"Efektivitas lift {lift_ratio:.3f} pas untuk karakter mesin yang ingin responsif namun tetap terkontrol."
            ], sig, lift_ratio, latest['v_in'])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Rasio lift {lift_ratio:.3f} sudah agresif. Mekanik perlu cek stabilitas valve train dan per klep.",
                f"Lift ratio {lift_ratio:.3f} terlalu tinggi untuk sebagian setup harian. Friksi dan valve control perlu perhatian ekstra.",
                f"Rasio lift {lift_ratio:.3f} mendekati batas keras. Potensi valve floating mulai nyata saat rpm naik.",
            ], sig, lift_ratio, latest['v_in'])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)

        if latest['PistonSpeed'] > 23.0:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s sudah terlalu dekat dengan batas aman untuk durasi panjang.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s menuntut oli dan pendinginan yang lebih serius.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masuk wilayah stres mekanik tinggi. Umur part akan lebih cepat terkikis."
            ], sig, latest['PistonSpeed'])
            st.markdown(f"<span style='color:#ff4d4f'>{msg}</span>", unsafe_allow_html=True)
        elif latest['PistonSpeed'] > 20.0:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masih aman, tapi sudah tidak santai.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s berada di zona kerja keras namun masih bisa dipakai.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s cukup cepat. Setting oli dan per klep mulai penting."
            ], sig, latest['PistonSpeed'])
            st.markdown(f"<span style='color:#3ba3ff'>{msg}</span>", unsafe_allow_html=True)
        else:
            msg = choose_variant([
                f"Piston speed {latest['PistonSpeed']:.2f} m/s masih nyaman untuk karakter CVT.",
                f"Kecepatan piston {latest['PistonSpeed']:.2f} m/s berada di zona aman untuk sesi panjang.",
                f"Piston speed {latest['PistonSpeed']:.2f} m/s relatif ideal dan tidak memaksa komponen berlebihan."
            ], sig, latest['PistonSpeed'])
            st.markdown(f"<span style='color:#39d353'>{msg}</span>", unsafe_allow_html=True)

    with c3:
        st.subheader("🛠️ 3. Solusi & Rekomendasi Part")
        rekomendasi_ditemukan = False

        # Manifold / TB / porting
        if latest['Velocity'] > 115.0:
            msg = choose_variant([
                f"🔹 **Intake/TB:** Perbesar throttle body atau rapikan porting karena velocity {latest['Velocity']:.2f} m/s sudah terlalu padat.",
                f"🔹 **Manifold/Port:** Head mulai tersumbat. Buka jalur intake agar aliran tidak menabrak batas {latest['Velocity']:.2f} m/s.",
                f"🔹 **Intake:** Kombinasi TB dan port sekarang terlalu sempit untuk rpm atas. Perlu enlarge bertahap, jangan brutal."
            ], sig, latest['Velocity'], latest['venturi'])
            st.info(msg)
            rekomendasi_ditemukan = True
        elif latest['Velocity'] < 90.0:
            msg = choose_variant([
                f"🔹 **Manifold:** Pakai intake manifold yang sedikit lebih sempit atau lebih pendek untuk menaikkan velocity ke zona 100-110 m/s.",
                f"🔹 **Intake Runner:** Velocity terlalu rendah. Kecilkan volume runner agar momentum charge naik.",
                f"🔹 **Throttle Body:** TB terlalu lega untuk karakter ini. Sempitkan sedikit supaya respons bawah tidak ngempos."
            ], sig, latest['Velocity'], latest['venturi'])
            st.info(msg)
            rekomendasi_ditemukan = True

        # Piston / CR
        if latest['CR'] > 13.2 and latest['material'] == "Casting":
            msg = choose_variant([
                f"🔹 **Piston:** Ganti ke forged piston karena CR {latest['CR']:.2f}:1 terlalu agresif untuk casting.",
                f"🔹 **Compression Safety:** Dengan CR {latest['CR']:.2f}:1, piston casting mulai rawan panas dan retak mikro.",
                f"🔹 **Top End:** Untuk kompresi {latest['CR']:.2f}:1, forged piston lebih aman daripada casting biasa."
            ], sig, latest['CR'], latest['material'])
            st.error(msg)
            rekomendasi_ditemukan = True
        elif latest['CR'] < 10.0:
            msg = choose_variant([
                f"🔹 **Kompresi:** CR {latest['CR']:.2f}:1 terlalu rendah. Naikkan volume head agar pembakaran lebih padat.",
                f"🔹 **Head Volume:** Ruang bakar masih terlalu besar. CR {latest['CR']:.2f}:1 perlu dinaikkan untuk mengisi torsi.",
                f"🔹 **Compression Build:** Turunkan volume head atau ubah dome piston karena kompresi masih terlalu jinak."
            ], sig, latest['CR'])
            st.info(msg)
            rekomendasi_ditemukan = True

        # Cam / lift
        if lift_ratio < 0.26:
            target_lift = latest['v_in'] * 0.30
            msg = choose_variant([
                f"🔹 **Noken As:** Cari profil yang memberi lift minimal **{target_lift:.2f} mm**.",
                f"🔹 **Camshaft:** Lift sekarang belum cukup mengisi klep. Naikkan lift untuk mengejar curtain area.",
                f"🔹 **Noken As:** Durasi boleh ada, tapi lift masih terlalu jinak. Profil high-lift akan lebih cocok."
            ], sig, target_lift, latest['v_in'])
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

        # Per klep
        if latest['PistonSpeed'] > 22.0 or lift_ratio > 0.33:
            msg = choose_variant([
                f"🔹 **Per Klep:** Gunakan per klep racing/high tension untuk menjaga valve control di rpm tinggi.",
                f"🔹 **Valve Spring:** Spring standar terlalu lembek untuk kombinasi speed {latest['PistonSpeed']:.2f} m/s dan lift ratio {lift_ratio:.3f}.",
                f"🔹 **Klep Train:** Upgrade per klep wajib jika ingin rpm naik tanpa valve floating."
            ], sig, latest['PistonSpeed'], lift_ratio)
            st.warning(msg)
            rekomendasi_ditemukan = True

        # AFR / BBM
        if latest['AFR'] > 13.5:
            msg = choose_variant([
                f"🔹 **Sistem BBM:** AFR {latest['AFR']:.1f} terlalu kering. Tambah debit injektor atau seting ulang mapping.",
                f"🔹 **Fueling:** Campuran {latest['AFR']:.1f} cenderung miskin. Mesin bisa panas dan tenaga tidak stabil.",
                f"🔹 **Injector/BBM:** Tambah suplai bahan bakar karena AFR {latest['AFR']:.1f} sudah melewati area aman."
            ], sig, latest['AFR'])
            st.warning(msg)
            rekomendasi_ditemukan = True
        elif latest['AFR'] < 12.0:
            msg = choose_variant([
                f"🔹 **Sistem BBM:** AFR {latest['AFR']:.1f} terlalu basah. Bahan bakar kebanyakan, respons jadi berat.",
                f"🔹 **Fueling:** Campuran terlalu kaya. Kurangi debit supaya pembakaran lebih bersih.",
                f"🔹 **Injector/Spuyer:** AFR {latest['AFR']:.1f} perlu diringankan agar mesin tidak membuang tenaga."
            ], sig, latest['AFR'])
            st.info(msg)
            rekomendasi_ditemukan = True

        # Exhaust balance
        if latest['Velocity_Out'] > 118.0:
            msg = choose_variant([
                f"🔹 **Exhaust:** Jalur buang terlalu padat. Knalpot / leher perlu dibuka sedikit agar backpressure turun.",
                f"🔹 **Outlet Flow:** Velocity out {latest['Velocity_Out']:.2f} m/s menandakan exhaust terlalu menahan gas.",
                f"🔹 **Knalpot:** Buang gas sudah terlalu keras. Perbesar leher atau ubah diffuser bila perlu."
            ], sig, latest['Velocity_Out'])
            st.error(msg)
            rekomendasi_ditemukan = True
        elif latest['Velocity_Out'] < 92.0:
            msg = choose_variant([
                f"🔹 **Exhaust:** Buang gas terlalu lambat. Diameter leher bisa dipersempit sedikit untuk bantu scavenging.",
                f"🔹 **Outlet Flow:** Velocity out {latest['Velocity_Out']:.2f} m/s terlalu rendah untuk mengusir gas sisa.",
                f"🔹 **Knalpot:** Exhaust cenderung terlalu lega. Sedikit penyempitan bisa bantu mid-range."
            ], sig, latest['Velocity_Out'])
            st.info(msg)
            rekomendasi_ditemukan = True

        # kalau belum ada rekomendasi, tetap beri jawaban yang berbeda bergantung signature
        if not rekomendasi_ditemukan:
            msg = choose_variant([
                "✅ Setingan saat ini seimbang dan belum butuh part besar-besaran.",
                "✅ Kombinasi bore, lift, dan AFR sudah cukup rapi untuk karakter yang dipilih.",
                "✅ Tidak ada part mendesak. Tinggal fine tuning agar respons lebih tajam.",
                "✅ Paket tuning sudah saling mengisi; perbaikan kecil saja akan terasa di dyno."
            ], sig, latest['CC'], latest['CR'], latest['Velocity'], latest['AFR'])
            st.success(msg)

st.write("---")
st.error("⚠️ **DISCLAIMER:** Perhitungan hanya estimasi kalkulasi data, hasil nyata bergantung pada efisiensi volumetrik, suhu, kualitas part, dan setting lapangan.")
