import streamlit as st
import psutil
import time

st.set_page_config(page_title="Production Pulse | Studio Telemetry", layout="wide", page_icon="🎬")

st.title("🎬 Production Pulse")
st.caption("Mission Control for AI-Augmented Creative Workflows")

# Real-time metrics
col1, col2, col3, col4 = st.columns(4)

cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory()
disk = psutil.disk_usage('/')

with col1:
    st.metric("CPU Load", f"{cpu}%", delta="High" if cpu > 80 else "Normal", 
              delta_color="inverse")
with col2:
    st.metric("Memory", f"{mem.percent}%", f"{mem.available/1024**3:.1f}GB free")
with col3:
    st.metric("Disk", f"{disk.percent}%", f"{disk.free/1024**3:.1f}GB free")
with col4:
    st.metric("MCP Status", "🟢 Active", "Agent Connected")

# Thermal warning
if hasattr(psutil, "sensors_temperatures"):
    temps = psutil.sensors_temperatures()
    if temps and 'coretemp' in temps:
        max_temp = max([t.current for t in temps['coretemp']])
        if max_temp > 80:
            st.error(f"🔥 Thermal Warning: {max_temp}°C - Consider pausing renders")
        elif max_temp > 70:
            st.warning(f"⚠️ Elevated Temp: {max_temp}°C")

# Creative process monitor
st.divider()
st.subheader("🎨 Active Production Processes")

creative_apps = ['blender', 'unreal', 'unity', 'maya', 'houdini', 'afterfx', 'cinema']
active_renders = []

for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
    try:
        if any(app in proc.info['name'].lower() for app in creative_apps):
            active_renders.append(proc.info)
    except:
        continue

if active_renders:
    for render in active_renders:
        with st.container():
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**{render['name']}** (PID: {render['pid']})")
            cols[1].progress(min(render['cpu_percent']/100, 1.0), text=f"CPU {render['cpu_percent']:.0f}%")
            cols[2].write(f"RAM: {render['memory_percent']:.1f}%")
            if cols[3].button("⏸️ Throttle", key=f"throttle_{render['pid']}"):
                try:
                    psutil.Process(render['pid']).nice(19)
                    st.success("Throttled!")
                except:
                    st.error("Permission denied")
else:
    st.info("No creative applications currently running")

st.divider()
st.caption("💡 **For Recruiters:** This dashboard demonstrates real-time system telemetry integration with LLM agent control via MCP.")