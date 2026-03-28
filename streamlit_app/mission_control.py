import streamlit as st
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from frame_pulse.system_client import get_thermal_status
from frame_pulse.render_guard import find_render_processes, emergency_throttle

st.set_page_config(page_title="Frame Pulse | Studio Telemetry", layout="wide", page_icon="🎬")

st.title("🎬 Frame Pulse")
st.caption("Hardware-aware mission control for creative workstations")

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("System Status")
    
    try:
        thermal = get_thermal_status()
        status = thermal.split(":")[0] if ":" in thermal else "UNKNOWN"
        
        match = re.search(r'CPU\s+(\d+\.?\d*)%', thermal)
        cpu_val = float(match.group(1)) if match else 0.0
        
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            delta = "normal" if "SAFE" in status else "inverse"
            st.metric("Status", status, delta_color=delta)
        with mcol2:
            st.metric("CPU", f"{cpu_val:.1f}%")
        
        mcol3, mcol4 = st.columns(2)
        with mcol3:
            mode = "🟡 Demo" if "DEMO" in thermal else "🟢 Active"
            st.metric("Server", mode)
        with mcol4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        if "CRITICAL" in status:
            st.error(f"🔥 {thermal}")
        elif "CAUTION" in status:
            st.warning(f"⚠️ {thermal}")
        elif "DEMO" in thermal:
            st.info(f"ℹ️ {thermal}")
        else:
            st.success(f"✅ {thermal}")

    except Exception as e:
        st.error(f"Status error: {e}")

with right_col:
    st.subheader("🎨 Active Creative Apps")
    
    try:
        processes = find_render_processes()
        
        if not processes:
            st.info("No creative apps detected — start Blender, Unreal, or Maya")
        else:
            for p in processes:
                with st.container(border=True):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{p['name']}**")
                        st.caption(f"PID `{p['pid']}` | CPU {p['cpu']:.1f}% | RAM {p['memory']:.1f}%")
                    with cols[1]:
                        if st.button("⏸️ Cool", key=f"throttle_{p['pid']}", use_container_width=True):
                            result = emergency_throttle(p['pid'])
                            st.toast(result)
                            st.rerun()
    except Exception as e:
        st.error(f"Apps error: {e}")

st.divider()
st.caption("Built with Python, MCP, and Streamlit")