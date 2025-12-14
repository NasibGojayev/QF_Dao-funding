"""
Alerting System for DonCoin DAO
Configurable alerts based on KPI thresholds.
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import ALERT_CONFIG, MONITORING_KPIS, LOGS_DIR
from monitoring.metrics import metrics_collector


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Represents an alert instance"""
    alert_id: str
    name: str
    kpi: str
    severity: AlertSeverity
    status: AlertStatus
    value: float
    threshold: float
    message: str
    fired_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    
    def to_dict(self):
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "kpi": self.kpi,
            "severity": self.severity.value,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "fired_at": self.fired_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
        }


class AlertManager:
    """
    Manages alert rules, firing, and notification.
    """
    
    def __init__(self):
        self.rules = ALERT_CONFIG.get('rules', [])
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.cooldowns: Dict[str, datetime] = {}  # rule_name -> last_fired
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default notification handlers"""
        self.notification_handlers['log'] = self._notify_log
        
        if ALERT_CONFIG['channels']['email']['enabled']:
            self.notification_handlers['email'] = self._notify_email
        
        if ALERT_CONFIG['channels']['webhook']['enabled']:
            self.notification_handlers['webhook'] = self._notify_webhook
    
    def _generate_alert_id(self, rule_name: str) -> str:
        """Generate unique alert ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"{rule_name.lower().replace(' ', '_')}_{timestamp}"
    
    def _evaluate_condition(self, condition: str, value: float) -> bool:
        """Evaluate alert condition"""
        # Simple condition parser for expressions like "value > 60"
        condition = condition.replace("value", str(value))
        try:
            return eval(condition)
        except:
            return False
    
    def _check_cooldown(self, rule_name: str, cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period"""
        if rule_name not in self.cooldowns:
            return False
        
        last_fired = self.cooldowns[rule_name]
        cooldown_end = last_fired + timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() < cooldown_end
    
    async def check_rules(self):
        """Check all alert rules and fire if conditions met"""
        for rule in self.rules:
            rule_name = rule['name']
            kpi = rule['kpi']
            condition = rule['condition']
            severity = AlertSeverity(rule['severity'])
            cooldown = rule.get('cooldown_minutes', 5)
            
            # Get current KPI value
            current_value = metrics_collector.get_gauge(kpi)
            
            # Evaluate condition
            should_fire = self._evaluate_condition(condition, current_value)
            
            # Check if already firing
            is_firing = rule_name in self.active_alerts
            
            if should_fire and not is_firing:
                # Check cooldown
                if self._check_cooldown(rule_name, cooldown):
                    continue
                
                # Fire new alert
                await self._fire_alert(rule, current_value)
            
            elif not should_fire and is_firing:
                # Resolve alert
                await self._resolve_alert(rule_name)
    
    async def _fire_alert(self, rule: dict, value: float):
        """Fire a new alert"""
        alert = Alert(
            alert_id=self._generate_alert_id(rule['name']),
            name=rule['name'],
            kpi=rule['kpi'],
            severity=AlertSeverity(rule['severity']),
            status=AlertStatus.FIRING,
            value=value,
            threshold=float(rule['condition'].split()[-1]),  # Extract threshold from condition
            message=f"{rule['name']}: {rule['kpi']} is {value} ({rule['condition']})",
            fired_at=datetime.utcnow()
        )
        
        self.active_alerts[rule['name']] = alert
        self.cooldowns[rule['name']] = datetime.utcnow()
        
        # Send notifications
        await self._send_notifications(alert)
    
    async def _resolve_alert(self, rule_name: str):
        """Resolve an active alert"""
        if rule_name not in self.active_alerts:
            return
        
        alert = self.active_alerts[rule_name]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[rule_name]
        
        # Notify resolution
        await self._send_notifications(alert)
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications via all enabled channels"""
        for channel_name, handler in self.notification_handlers.items():
            try:
                await handler(alert) if asyncio.iscoroutinefunction(handler) else handler(alert)
            except Exception as e:
                print(f"Failed to send {channel_name} notification: {e}")
    
    def _notify_log(self, alert: Alert):
        """Log alert to file"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "alert",
            **alert.to_dict()
        }
        
        log_file = LOGS_DIR / "alerts.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    async def _notify_email(self, alert: Alert):
        """Send email notification"""
        config = ALERT_CONFIG['channels']['email']
        
        subject = f"[{alert.severity.value.upper()}] {alert.name}"
        body = f"""
        Alert: {alert.name}
        Status: {alert.status.value}
        KPI: {alert.kpi}
        Value: {alert.value}
        Threshold: {alert.threshold}
        Time: {alert.fired_at.isoformat()}
        
        {alert.message}
        """
        
        msg = MIMEMultipart()
        msg['From'] = config['smtp_user']
        msg['To'] = ', '.join(config['recipients'])
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
            server.starttls()
            server.login(config['smtp_user'], config['smtp_password'])
            server.sendmail(config['smtp_user'], config['recipients'], msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Email notification failed: {e}")
    
    async def _notify_webhook(self, alert: Alert):
        """Send webhook notification"""
        import httpx
        
        config = ALERT_CONFIG['channels']['webhook']
        payload = {
            "alert": alert.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    config['url'],
                    json=payload,
                    timeout=10.0
                )
        except Exception as e:
            print(f"Webhook notification failed: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                return True
        return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        return [alert.to_dict() for alert in sorted(
            self.alert_history,
            key=lambda x: x.fired_at,
            reverse=True
        )[:limit]]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        return {
            "active_count": len(self.active_alerts),
            "critical_count": sum(1 for a in self.active_alerts.values() 
                                   if a.severity == AlertSeverity.CRITICAL),
            "warning_count": sum(1 for a in self.active_alerts.values() 
                                  if a.severity == AlertSeverity.WARNING),
            "unacknowledged_count": sum(1 for a in self.active_alerts.values() 
                                         if not a.acknowledged),
            "last_24h_total": sum(1 for a in self.alert_history 
                                   if a.fired_at > datetime.utcnow() - timedelta(hours=24))
        }


# Global alert manager
alert_manager = AlertManager()


# =============================================================================
# BACKGROUND ALERT CHECKER
# =============================================================================

async def alert_checker_loop(interval_seconds: int = 30):
    """Background task to periodically check alert rules"""
    while True:
        try:
            await alert_manager.check_rules()
        except Exception as e:
            print(f"Alert checker error: {e}")
        
        await asyncio.sleep(interval_seconds)


def simulate_alert_test():
    """Simulate an alert for testing"""
    # Set a high value to trigger alert
    from monitoring.metrics import metrics_collector
    
    # Simulate high event lag
    metrics_collector.record_gauge("event_processing_lag", 75.0)
    
    # Manually check rules
    import asyncio
    asyncio.run(alert_manager.check_rules())
    
    return alert_manager.get_active_alerts()
