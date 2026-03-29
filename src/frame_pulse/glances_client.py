# src/frame_pulse/glances_client.py
import requests

def get_glances_stats(host="localhost", port=61208):
    """Alternative data source if Glances is running."""
    try:
        resp = requests.get(f"http://{host}:{port}/api/3/all", timeout=2)
        data = resp.json()
        return {
            'cpu': data.get('cpu', {}).get('total', 0),
            'mem': data.get('mem', {}).get('percent', 0),
            'temp': max([t.get('current', 0) for t in data.get('sensors', {}).get('temperature', [])]) if data.get('sensors') else 0
        }
    except:
        return None  # Fall back to psutil