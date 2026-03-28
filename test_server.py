import sys
sys.path.insert(0, 'src')
from production_pulse.server import get_thermal_status, find_render_processes

print("Testing get_thermal_status(): - test_server.py:5")
print(get_thermal_status())

print("\nTesting find_render_processes(): - test_server.py:8")
print(find_render_processes())