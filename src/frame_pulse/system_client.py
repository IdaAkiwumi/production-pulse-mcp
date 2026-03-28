import psutil
import os
import re

def get_system_stats():
    """Get core system telemetry."""
    try:
        cpu = psutil.cpu_percent(interval=1)  # This needs 1 second to measure!
        mem = psutil.virtual_memory()
        
        stats = {
            'cpu': {'percent': cpu, 'cores': psutil.cpu_count()},
            'memory': {
                'percent': mem.percent,
                'used_gb': mem.used // (1024**3),
                'available_gb': mem.available // (1024**3)
            }
        }
        
        # Add temps if available
        temps = None
        if hasattr(psutil, 'sensors_temperatures'):
            try:
                raw_temps = psutil.sensors_temperatures()
                if raw_temps:
                    # Get max temp from any sensor
                    all_temps = []
                    for name, entries in raw_temps.items():
                        for t in entries:
                            if hasattr(t, 'current'):
                                all_temps.append(t.current)
                    if all_temps:
                        temps = max(all_temps)
            except:
                pass
        
        stats['max_temp'] = temps
        
        return stats
        
    except Exception as e:
        # Cloud/demo fallback
        import random
        return {
            'cpu': {'percent': random.randint(20, 45), 'cores': 8},
            'memory': {'percent': random.randint(30, 60)},
            'max_temp': random.randint(55, 75),
            '_demo_mode': True,
            '_error': str(e)
        }

def get_thermal_status():
    """Quick status check for MCP tools."""
    stats = get_system_stats()
    cpu = stats.get('cpu', {}).get('percent', 0)
    temp = stats.get('max_temp', 0) or 0
    
    # Demo mode detection
    if stats.get('_demo_mode'):
        return f"DEMO: CPU {cpu:.1f}%, Temp {temp:.0f}°C — Simulated for preview"
    
    # Real status with actual numbers
    if cpu > 90 or temp > 85:
        return f"CRITICAL: CPU {cpu:.1f}%, Temp {temp:.0f}°C — HALT renders immediately"
    elif cpu > 75 or temp > 75:
        return f"CAUTION: CPU {cpu:.1f}%, Temp {temp:.0f}°C — Queue carefully"
    
    return f"SAFE: CPU {cpu:.1f}%, Temp {temp:.0f}°C — Ready for production workloads"