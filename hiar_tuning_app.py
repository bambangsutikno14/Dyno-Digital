import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd
import time

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

st.markdown("""
<style>
    th, td { text-align: center !important; vertical-align: middle !important; }
    div[data-testid="stDataFrame"] { display: flex; justify-content: center; }
    .main { background-color: #050505; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
DATABASE_REF = {
    "YAMAHA": {
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head": 13.7, "valve_in": 23.0, "valve_out": 19.0, "venturi": 24, "hp_std": 8.78, "peak_rpm": 8000, "limit_std": 9000, "weight_std": 92, "f_ratio": 3.10},
    }
}

# --- 3. SESSION ---
for k, v in {
    "history": [],
    "bore": 50.0,
    "cc": 113.7,
    "vhead": 13.7,
    "last_changed": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- CORE FUNCTION ---
def calculate_ultimate(cc, bore, stroke, cr, rpm_limit, valve_in, valve_out, venturi, dur_in, dur_out, afr, std):
    rpms = np.arange(2000, rpm_limit + 100, 100)
    hps, torques = [], []

    for r in rpms:
        hp = (cc * r) / 100000
        hps.append(hp)
        torques.append((hp * 7127) / r)

    return rpms, hps, torques, 0, 0

def calc_cc(bore, stroke):
    return (math.pi * bore**2 * stroke) / 4000

def calc_bore(cc, stroke):
    return math.sqrt((cc * 4000) / (math.pi * stroke))

def smooth(prev, target):
    return prev + (target - prev) * 0.15

def simulate_drag(rpms, hps, weight, final_ratio, tire):
    dt = 0.02
    speed = 0
    dist = 0
    t = 0
    out = []

    for i in range(len(rpms)):
        rpm = rpms[i]
        hp = hps[i]

        power = hp * 745.7

        drag = 0.5 * 1.2 * 0.6 * speed**2

        cvt = final_ratio * (1.2 - min(rpm / 12000, 0.4))

        wheel_rpm = rpm / max(cvt, 0.5)
        circ = math.pi * (tire / 1000)
        speed_real = (wheel_rpm * circ) / 60

        force = power / max(speed, 1)
        force = min(force, weight * 9.8 * 0.9)

        acc = (force - drag) / weight

        speed += acc * dt
        dist += speed * dt
        t += dt

        out.append({
            "time": t,
            "distance": dist,
            "speed": speed * 3.6,
            "rpm": rpm,
            "hp": hp
        })

        if dist >= 402:
            break

    return out

def gauge(title, val, maxv):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={"text": title},
        gauge={"axis": {"range": [0, maxv]}}
    ))
    fig.update_layout(height=250)
    return fig

def plot_curve(rpms, hps, torques, cur=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rpms, y=hps, name="HP"))
    fig.add_trace(go.Scatter(x=rpms, y=torques, name="Nm"))
    if cur:
        i = np.argmin(np.abs(rpms - cur))
        fig.add_scatter(x=[rpms[i]], y=[hps[i]], mode="markers")
    return fig

# --- SIDEBAR ---
with st.sidebar:

    std = DATABASE_REF["YAMAHA"]["Mio Karbu / Soul 115"]

    stroke = st.number_input("Stroke", value=std["stroke"])

    def on_bore():
        if st.session_state.last_changed != "bore":
            st.session_state.last_changed = "bore"
            st.session_state.cc = calc_cc(st.session_state.bore, stroke)

    def on_cc():
        if st.session_state.last_changed != "cc":
            st.session_state.last_changed = "cc"
            st.session_state.bore = calc_bore(st.session_state.cc, stroke)

    st.number_input("Bore", key="bore", on_change=on_bore)
    st.number_input("CC", key="cc", on_change=on_cc)
    st.number_input("Vol Head", key="vhead")

    rpm_limit = st.number_input("Limit RPM", value=9000)
    weight = st.number_input("Total Weight", value=150)
    f_ratio = st.number_input("Final Ratio", value=std["f_ratio"])
    tire = st.number_input("Tire Diameter (mm)", value=350)

    sim_button = st.button("START DYNO")

# --- MAIN ---
st.title("DYNO + DRAG SIMULATOR")

cc = st.session_state.cc
bore = st.session_state.bore
vhead = st.session_state.vhead

cr = (cc + vhead) / vhead

rpms, hps, torques, _, _ = calculate_ultimate(
    cc, bore, stroke, cr, rpm_limit,
    std["valve_in"], std["valve_out"], std["venturi"],
    240, 240, 13.0, std
)

max_hp = max(hps)

col1, col2, col3 = st.columns(3)
tach = col1.empty()
speedo = col2.empty()
power = col3.empty()

graph = st.empty()

if sim_button:

    drag = simulate_drag(rpms, hps, weight, f_ratio, tire)

    t100 = t201 = t402 = None

    for d in drag:
        if d["distance"] >= 100 and not t100:
            t100 = d["time"]
        if d["distance"] >= 201 and not t201:
            t201 = d["time"]
        if d["distance"] >= 402:
            t402 = d["time"]
            break

    c1, c2, c3 = st.columns(3)
    c1.metric("0-100m", round(t100,2))
    c2.metric("201m", round(t201,2))
    c3.metric("402m", round(t402,2))

    rpm_s = speed_s = hp_s = 0

    for d in drag:

        rpm_s = smooth(rpm_s, d["rpm"])
        speed_s = smooth(speed_s, d["speed"])
        hp_s = smooth(hp_s, d["hp"])

        tach.plotly_chart(gauge("RPM", rpm_s, rpm_limit), use_container_width=True)
        speedo.plotly_chart(gauge("KMH", speed_s, 200), use_container_width=True)
        power.plotly_chart(gauge("HP", hp_s, max_hp * 1.2), use_container_width=True)

        fig = plot_curve(rpms, hps, torques, rpm_s)
        graph.plotly_chart(fig, use_container_width=True)

        st.progress(min(d["distance"] / 402, 1.0))

        time.sleep(0.02)
