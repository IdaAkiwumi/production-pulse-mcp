"""
Alert integrations for Frame Pulse MCP.
Not called directly by MCP tools — used by Streamlit or scheduled jobs.
"""

import os
import json
import asyncio
from typing import Optional
from dataclasses import dataclass

@dataclass
class AlertConfig:
    discord_webhook: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    thermal_threshold: float = 85.0  # CPU % to trigger alert

class AlertManager:
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or self._load_from_env()
        self._last_alert_time = 0
        self._cooldown_seconds = 300  # 5 min between alerts
    
    def _load_from_env(self) -> AlertConfig:
        """Load credentials from environment variables."""
        return AlertConfig(
            discord_webhook=os.getenv("DISCORD_WEBHOOK_URL"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            thermal_threshold=float(os.getenv("THERMAL_THRESHOLD", "85.0"))
        )
    
    async def send_discord(self, message: str, status: str = "info"):
        """Send alert to Discord webhook."""
        if not self.config.discord_webhook:
            return "Discord not configured"
        
        color_map = {
            "info": 0x3498db,      # Blue
            "warning": 0xf39c12,   # Orange
            "critical": 0xe74c3c   # Red
        }
        
        payload = {
            "embeds": [{
                "title": "🎬 Frame Pulse Alert",
                "description": message,
                "color": color_map.get(status, 0x3498db),
                "footer": {"text": "Frame Pulse MCP • Creative Workstation Monitor"}
            }]
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.discord_webhook,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 204:
                        return "Discord alert sent"
                    return f"Discord error: {resp.status}"
        except Exception as e:
            return f"Discord failed: {e}"
    
    async def send_telegram(self, message: str):
        """Send alert via Telegram Bot API."""
        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            return "Telegram not configured"
        
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.config.telegram_chat_id,
            "text": f"🎬 *Frame Pulse Alert*\n\n{message}",
            "parse_mode": "Markdown"
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    if result.get("ok"):
                        return "Telegram alert sent"
                    return f"Telegram error: {result}"
        except Exception as e:
            return f"Telegram failed: {e}"
    
    async def check_and_alert(self, thermal_status: str):
        """Smart alerting with cooldown to prevent spam."""
        import time
        
        # Check if we should alert
        is_critical = "CRITICAL" in thermal_status
        is_caution = "CAUTION" in thermal_status
        
        if not (is_critical or is_caution):
            return None  # Safe state, no alert needed
        
        # Cooldown check
        current_time = time.time()
        if current_time - self._last_alert_time < self._cooldown_seconds:
            return "Alert on cooldown"
        
        self._last_alert_time = current_time
        
        # Determine severity
        status = "critical" if is_critical else "warning"
        
        # Send to all configured channels
        results = []
        
        if self.config.discord_webhook:
            result = await self.send_discord(thermal_status, status)
            results.append(result)
        
        if self.config.telegram_bot_token:
            result = await self.send_telegram(thermal_status)
            results.append(result)
        
        return " | ".join(results) if results else "No alerts configured"

# Singleton for reuse
_default_manager: Optional[AlertManager] = None

def get_alert_manager() -> AlertManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = AlertManager()
    return _default_manager

# Convenience function for synchronous contexts
def send_alert_sync(message: str, status: str = "info"):
    """Fire-and-forget alert for non-async code."""
    manager = get_alert_manager()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, schedule task
            asyncio.create_task(manager.send_discord(message, status))
        else:
            # New event loop
            loop.run_until_complete(manager.send_discord(message, status))
    except Exception as e:
        return f"Alert failed: {e}"