"""
Optional Glances API integration for richer sensor data.
Falls back to psutil if Glances unavailable.
"""

import requests
from typing import Optional, Dict, Any


class GlancesClient:
    def __init__(self, host: str = "localhost", port: int = 61209, timeout: float = 2.0):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self._available: Optional[bool] = None
    
    def is_available(self) -> bool:
        """Check if Glances is running."""
        if self._available is None:
            try:
                # Try API v4 first (Glances 4.x), fallback to v3
                for api_path in ["/api/4/pluginslist", "/api/3/pluginslist"]:
                    try:
                        resp = requests.get(f"{self.base_url}{api_path}", timeout=self.timeout)
                        if resp.status_code == 200:
                            self._available = True
                            return True
                    except:
                        continue
                self._available = False
            except Exception:
                self._available = False
        return self._available
    
    def get_all_stats(self) -> Optional[Dict[str, Any]]:
        """Fetch complete system snapshot from Glances."""
        if not self.is_available():
            return None
        
        # Try v4 API first
        for api_path in ["/api/4/all", "/api/3/all"]:
            try:
                resp = requests.get(f"{self.base_url}{api_path}", timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
            except:
                continue
        return None
    
    def get_thermal_status(self) -> Optional[str]:
        """Generate status string from Glances data."""
        data = self.get_all_stats()
        if not data:
            return None
        
        try:
            # Handle both v3 and v4 API structures
            cpu = data.get("cpu", {}).get("total", 0)
            if isinstance(cpu, dict):
                cpu = cpu.get("total", 0)
            
            # Temperature handling
            temp = 0
            sensors = data.get("sensors", {}) or {}
            
            # v4 structure: sensors.temperatures array
            if isinstance(sensors, dict):
                temps_list = sensors.get("temperatures", [])
                if temps_list:
                    temp = max([t.get("value", t.get("current", 0)) for t in temps_list if isinstance(t.get("value", t.get("current")), (int, float))], default=0)
                
                # v3 structure: direct sensor keys
                if temp == 0:
                    for key, value in sensors.items():
                        if isinstance(value, (int, float)) and "temp" in key.lower():
                            temp = max(temp, value)
                        elif isinstance(value, dict):
                            current = value.get("value") or value.get("current")
                            if isinstance(current, (int, float)):
                                temp = max(temp, current)
            
            # Status thresholds
            if cpu > 90 or temp > 85:
                return f"CRITICAL: CPU {cpu:.1f}%, Temp {temp:.0f}°C — HALT renders immediately"
            elif cpu > 75 or temp > 75:
                return f"CAUTION: CPU {cpu:.1f}%, Temp {temp:.0f}°C — Queue carefully"
            return f"SAFE: CPU {cpu:.1f}%, Temp {temp:.0f}°C — Ready for production workloads"
            
        except Exception as e:
            return f"Glances parse error: {e}"
    
    def get_gpu_info(self) -> Optional[Dict]:
        """Get GPU stats if available."""
        data = self.get_all_stats()
        if not data:
            return None
        
        # Try multiple GPU sources
        gpu_data = data.get("gpu") or data.get("nvidia") or data.get("amdgpu")
        if not gpu_data:
            return None
        
        if isinstance(gpu_data, list):
            return {"gpus": gpu_data, "count": len(gpu_data)}
        return {"gpus": [gpu_data], "count": 1}
    
    def get_process_list(self, creative_only: bool = True) -> list:
        """Get process list from Glances."""
        data = self.get_all_stats()
        if not data:
            return []
        
        # Try v4 and v3 process structures
        processes = data.get("processlist") or data.get("processes", {}).get("list", [])
        if not creative_only:
            return processes
        
        creative_apps = [
            "blender", "unreal", "unity", "maya", "houdini", 
            "afterfx", "cinema", "c4d", "nuke", "resolve"
        ]
        
        filtered = []
        for proc in processes:
            name = (proc.get("name") or proc.get("cmdline", [""])[0]).lower()
            if any(app in name for app in creative_apps):
                filtered.append({
                    "name": proc.get("name", "unknown"),
                    "pid": proc.get("pid"),
                    "cpu": proc.get("cpu_percent") or proc.get("cpu", 0),
                    "memory": proc.get("memory_percent") or proc.get("memory", 0)
                })
        
        return filtered


def get_best_thermal_status() -> str:
    """Try Glances first, fall back to psutil."""
    glances = GlancesClient()
    status = glances.get_thermal_status()
    if status:
        return status + " (via Glances)"
    
    # Fall back to local psutil
    from .system_client import get_thermal_status as psutil_status
    return psutil_status()