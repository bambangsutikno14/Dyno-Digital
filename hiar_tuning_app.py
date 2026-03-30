import streamlit as st
import numpy as np
import math
import time
import plotly.graph_objects as go

# --- 1. SETTING PAGE ---
st.set_page_config(page_title="Hiar Lima Pendawa Tuning", layout="wide")

# --- 2. DATABASE ---
DATABASE_MATIC = {
    "YAMAHA": {
        "NMAX 155 / Aerox 155": {"bore": 58.0, "stroke": 58.7, "v_head_std": 14.6, "vva": True, "weight": 127, "tire_circ": 1.55},
        "Mio Karbu / Soul 115": {"bore": 50.0, "stroke": 57.9, "v_head_std": 13.7, "vva": False, "weight": 94, "tire_circ": 1.45},
    },
    "HONDA": {
        "Vario 150 / PCX 150": {"bore": 57.3, "stroke": 57.9, "v_head_std": 15.6, "vva": False, "weight": 112, "tire_circ": 1.55},
        "BeAT FI / Scoopy": {"bore": 50.0, "stroke": 55.1, "v_head_std": 12.7, "vva": False, "weight": 90, "tire_circ": 1.40},
    }
}

# --- 3. LOGIKA ENGINE ---
def get_single_point(r, cc, stroke, vva, rpm_limit, cf=1.0):
    ve = 0.90 if vva and r > 6000 else 0.84
    ve_curve = ve * math.cos(math.radians((r - (rpm_limit*0.75)) / (rpm_limit*0.45) * 40))
    hp = (10.2 * cc * r * ve_curve) / 900000 * cf
    torque = (hp * 7127) / r
    # Speed estimation (Simulasi gigi 3/4 atau Rasio CVT akhir)
    speed = (r * 0.015) # Rasio kasar RPM ke KMH
    return round(hp, 2), round(torque, 2), round(speed, 1)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🏁 DYNO CONTROLLER")
    merk = st.selectbox("Pilih Merk", list(DATABASE_MATIC.keys()))
    motor = st.selectbox("Model", list(DATABASE_MATIC[merk].keys()))
    data_std = DATABASE_MATIC[merk][motor]
    
    st.write("---")
    bore_in = st.number_input("Bore (mm)", value=data_std['bore'], step=0.1)
    v_head_in = st.number_input("Vol Head (cc)", value=data_std['v_head_std'], step=0.1)
    rpm_limit = st.slider("Limit RPM", 5000, 14000, 10000)
    
    btn_run = st.button("🚀 START DYNO TEST")

# --- 5. MAIN PANEL (CINEMATIC) ---
st.title("📟 Hiar Lima Pendawa Tuning")

if btn_run:
    cc = (math.pi * (bore_in**2) * data_std['stroke']) / 4000
    
    # --- TEMPAT GAUGE & GRAFIK (Placeholder) ---
    col_gauge1, col_gauge2 = st.columns(2)
    with col_gauge1:
        rpm_placeholder = st.empty()
    with col_gauge2:
        speed_placeholder = st.empty()
    
    chart_placeholder = st.empty()
    
    # --- ANIMATION LOOP ---
    list_rpm = []
    list_hp = []
    list_torque = []
    
    # Simulasi Suara & Gerakan: Start dari 1000 RPM ke Limit
    for r in range(0, rpm_limit + 250, 250):
        if r < 1000: # Idle simulation
            current_hp, current_torque, current_speed = 0, 0, 0
        else:
            current_hp, current_torque, current_speed = get_single_point(r, cc, data_std['stroke'], data_std['vva'], rpm_limit)
        
        list_rpm.append(r)
        list_hp.append(current_hp)
        list_torque.append(current_torque)

        # 1. Update Takometer (RPM)
        fig_rpm = go.Figure(go.Indicator(
            mode = "gauge+number", value = r, title = {'text': "ENGINE RPM"},
            gauge = {'axis': {'range': [0, 14000]}, 'bar': {'color': "red" if r > rpm_limit*0.9 else "darkblue"}}
        ))
        fig_rpm.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        rpm_placeholder.plotly_chart(fig_rpm, use_container_width=True)

        # 2. Update Speedometer (KM/H)
        fig_spd = go.Figure(go.Indicator(
            mode = "gauge+number", value = current_speed, title = {'text': "SPEED KM/H"},
            gauge = {'axis': {'range': [0, 200]}, 'bar': {'color': "green"}}
        ))
        fig_spd.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        speed_placeholder.plotly_chart(fig_spd, use_container_width=True)

        # 3. Update Live Graph
        fig_live = go.Figure()
        fig_live.add_trace(go.Scatter(x=list_rpm, y=list_hp, name="Power (HP)", line=dict(color='red', width=4)))
        fig_live.add_trace(go.Scatter(x=list_rpm, y=list_torque, name="Torque (Nm)", line=dict(color='cyan', dash='dot'), yaxis="y2"))
        
        fig_live.update_layout(
            template="plotly_dark", height=450,
            xaxis=dict(range=[0, rpm_limit + 1000], title="RPM"),
            yaxis=dict(range=[0, max(list_hp)*1.2 if list_hp else 20], title="HP"),
            yaxis2=dict(range=[0, max(list_torque)*1.2 if list_torque else 20], overlaying="y", side="right", title="Nm"),
            legend=dict(orientation="h", y=1.1)
        )
        chart_placeholder.plotly_chart(fig_live, use_container_width=True)
        
        time.sleep(0.01) # Mengatur kecepatan animasi

    st.success(f"✅ Dyno Test Complete! Max Power: {max(list_hp)} HP")

else:
    st.info("💡 Pastikan 'Beban' sudah siap, lalu klik START untuk running mesin!")
