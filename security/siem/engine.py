"""
SIEM/SOAR Integration for DonCoin DAO
Security Information and Event Management with automated response.
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import SIEM_CONFIG, LOGS_DIR


class EventCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    ADMIN_ACTION = "admin_action"
    SECURITY_ALERT = "security_alert"
    RATE_LIMIT = "rate_limit"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class CaseSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class SecurityEvent:
    """Represents a security-relevant event"""
    event_id: str
    timestamp: datetime
    category: EventCategory
    source_ip: str
    user: Optional[str]
    action: str
    resource: str
    outcome: str  # 'success', 'failure', 'blocked'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "source_ip": self.source_ip,
            "user": self.user,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "details": self.details
        }


@dataclass
class SecurityCase:
    """Represents a security incident/case for investigation"""
    case_id: str
    title: str
    description: str
    severity: CaseSeverity
    status: CaseStatus
    created_at: datetime
    events: List[str] = field(default_factory=list)  # Event IDs
    assignee: Optional[str] = None
    resolution: Optional[str] = None
    closed_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "events": self.events,
            "assignee": self.assignee,
            "resolution": self.resolution,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None
        }


class CorrelationRule:
    """Rule for correlating multiple events into a case"""
    
    def __init__(
        self,
        name: str,
        pattern: str,
        severity: CaseSeverity,
        action: str,
        window_seconds: int = 300,
        threshold: int = 5
    ):
        self.name = name
        self.pattern = pattern
        self.severity = severity
        self.action = action
        self.window_seconds = window_seconds
        self.threshold = threshold
    
    def matches(self, event: SecurityEvent) -> bool:
        """Check if event matches this rule's pattern"""
        # Simple pattern matching for demo
        if "failed login" in self.pattern.lower():
            return (
                event.category == EventCategory.AUTHENTICATION and
                event.outcome == "failure"
            )
        elif "rate limit" in self.pattern.lower():
            return event.category == EventCategory.RATE_LIMIT
        return False


class SIEMEngine:
    """
    SIEM Engine for log collection, normalization, and correlation.
    """
    
    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.cases: Dict[str, SecurityCase] = {}
        self.event_counter = 0
        self.case_counter = 0
        
        # Event buffers for correlation
        self.event_buffers: Dict[str, List[SecurityEvent]] = defaultdict(list)
        
        # Load correlation rules from config
        self.correlation_rules = self._load_correlation_rules()
        
        # Response playbooks
        self.playbooks: Dict[str, Callable] = {}
        self._register_default_playbooks()
    
    def _load_correlation_rules(self) -> List[CorrelationRule]:
        """Load correlation rules from config"""
        rules = []
        for rule_config in SIEM_CONFIG.get('correlation_rules', []):
            rules.append(CorrelationRule(
                name=rule_config['name'],
                pattern=rule_config['pattern'],
                severity=CaseSeverity(rule_config.get('severity', 'medium')),
                action=rule_config.get('action', 'alert')
            ))
        return rules
    
    def _register_default_playbooks(self):
        """Register default response playbooks"""
        self.playbooks['block_ip'] = self._playbook_block_ip
        self.playbooks['alert'] = self._playbook_alert
        self.playbooks['escalate'] = self._playbook_escalate
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        self.event_counter += 1
        return f"EVT-{datetime.utcnow().strftime('%Y%m%d')}-{self.event_counter:06d}"
    
    def _generate_case_id(self) -> str:
        """Generate unique case ID"""
        self.case_counter += 1
        return f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{self.case_counter:04d}"
    
    def ingest_event(
        self,
        category: EventCategory,
        source_ip: str,
        action: str,
        resource: str,
        outcome: str,
        user: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """Ingest a new security event"""
        event = SecurityEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            category=category,
            source_ip=source_ip,
            user=user,
            action=action,
            resource=resource,
            outcome=outcome,
            details=details or {}
        )
        
        # Store event
        self.events.append(event)
        
        # Write to log file
        self._write_event_log(event)
        
        # Process through correlation engine
        self._correlate_event(event)
        
        return event
    
    def _write_event_log(self, event: SecurityEvent):
        """Write event to SIEM log file"""
        log_file = Path(SIEM_CONFIG['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def _correlate_event(self, event: SecurityEvent):
        """Correlate event against rules"""
        for rule in self.correlation_rules:
            if rule.matches(event):
                # Add to buffer for this rule
                buffer_key = f"{rule.name}:{event.source_ip}"
                self.event_buffers[buffer_key].append(event)
                
                # Clean old events from buffer
                cutoff = datetime.utcnow() - timedelta(seconds=rule.window_seconds)
                self.event_buffers[buffer_key] = [
                    e for e in self.event_buffers[buffer_key]
                    if e.timestamp > cutoff
                ]
                
                # Check threshold
                if len(self.event_buffers[buffer_key]) >= rule.threshold:
                    self._trigger_correlation(rule, self.event_buffers[buffer_key])
                    self.event_buffers[buffer_key] = []  # Clear buffer
    
    def _trigger_correlation(self, rule: CorrelationRule, events: List[SecurityEvent]):
        """Trigger correlation match - create case and execute playbook"""
        # Create case
        case = SecurityCase(
            case_id=self._generate_case_id(),
            title=rule.name,
            description=f"Correlation rule '{rule.name}' matched with {len(events)} events",
            severity=rule.severity,
            status=CaseStatus.NEW,
            created_at=datetime.utcnow(),
            events=[e.event_id for e in events]
        )
        
        self.cases[case.case_id] = case
        
        # Execute playbook
        if rule.action in self.playbooks:
            self.playbooks[rule.action](case, events)
        
        return case
    
    # =============================================================================
    # PLAYBOOKS (SOAR)
    # =============================================================================
    
    def _playbook_block_ip(self, case: SecurityCase, events: List[SecurityEvent]):
        """Playbook: Block source IP"""
        if not events:
            return
        
        source_ip = events[0].source_ip
        
        # Import here to avoid circular imports
        from middleware.rate_limiter import rate_limiter
        import asyncio
        
        # Block for 15 minutes
        asyncio.create_task(rate_limiter.block_ip(source_ip, 900))
        
        case.resolution = f"IP {source_ip} blocked for 15 minutes"
        case.status = CaseStatus.CONTAINED
        
        # Log playbook execution
        self.ingest_event(
            category=EventCategory.SECURITY_ALERT,
            source_ip=source_ip,
            action="playbook_executed",
            resource="block_ip",
            outcome="success",
            details={"case_id": case.case_id, "blocked_duration": 900}
        )
    
    def _playbook_alert(self, case: SecurityCase, events: List[SecurityEvent]):
        """Playbook: Send alert"""
        from monitoring.alerting import alert_manager
        
        # The alerting system will handle notification
        # Just update case status
        case.status = CaseStatus.INVESTIGATING
        
        # Log playbook execution
        if events:
            self.ingest_event(
                category=EventCategory.SECURITY_ALERT,
                source_ip=events[0].source_ip if events else "system",
                action="playbook_executed",
                resource="alert",
                outcome="success",
                details={"case_id": case.case_id}
            )
    
    def _playbook_escalate(self, case: SecurityCase, events: List[SecurityEvent]):
        """Playbook: Escalate to on-call"""
        case.status = CaseStatus.INVESTIGATING
        case.assignee = "on-call-security"
        
        # In production, this would page/notify on-call
        # Log playbook execution
        if events:
            self.ingest_event(
                category=EventCategory.SECURITY_ALERT,
                source_ip=events[0].source_ip if events else "system",
                action="playbook_executed",
                resource="escalate",
                outcome="success",
                details={"case_id": case.case_id, "assignee": "on-call-security"}
            )
    
    # =============================================================================
    # CASE MANAGEMENT
    # =============================================================================
    
    def update_case(
        self,
        case_id: str,
        status: Optional[CaseStatus] = None,
        assignee: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> Optional[SecurityCase]:
        """Update a security case"""
        case = self.cases.get(case_id)
        if not case:
            return None
        
        if status:
            case.status = status
            if status in [CaseStatus.RESOLVED, CaseStatus.FALSE_POSITIVE]:
                case.closed_at = datetime.utcnow()
        
        if assignee:
            case.assignee = assignee
        
        if resolution:
            case.resolution = resolution
        
        return case
    
    def get_open_cases(self) -> List[Dict[str, Any]]:
        """Get all open cases"""
        open_statuses = [CaseStatus.NEW, CaseStatus.INVESTIGATING, CaseStatus.CONTAINED]
        return [
            case.to_dict() for case in self.cases.values()
            if case.status in open_statuses
        ]
    
    def get_case_summary(self) -> Dict[str, Any]:
        """Get summary of case statistics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        return {
            "total_cases": len(self.cases),
            "open_cases": sum(1 for c in self.cases.values() 
                              if c.status not in [CaseStatus.RESOLVED, CaseStatus.FALSE_POSITIVE]),
            "critical_open": sum(1 for c in self.cases.values()
                                  if c.severity == CaseSeverity.CRITICAL and
                                  c.status not in [CaseStatus.RESOLVED, CaseStatus.FALSE_POSITIVE]),
            "new_last_24h": sum(1 for c in self.cases.values() if c.created_at > last_24h),
            "resolved_last_24h": sum(1 for c in self.cases.values() 
                                      if c.closed_at and c.closed_at > last_24h)
        }
    
    def search_events(
        self,
        category: Optional[EventCategory] = None,
        source_ip: Optional[str] = None,
        user: Optional[str] = None,
        outcome: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search security events"""
        results = []
        
        for event in reversed(self.events):  # Most recent first
            if category and event.category != category:
                continue
            if source_ip and event.source_ip != source_ip:
                continue
            if user and event.user != user:
                continue
            if outcome and event.outcome != outcome:
                continue
            if since and event.timestamp < since:
                continue
            if until and event.timestamp > until:
                continue
            
            results.append(event.to_dict())
            if len(results) >= limit:
                break
        
        return results


# Global SIEM instance
siem_engine = SIEMEngine()


# =============================================================================
# HELPER FUNCTIONS FOR LOG INGESTION
# =============================================================================

def log_auth_attempt(
    source_ip: str,
    username: str,
    success: bool,
    details: Optional[Dict[str, Any]] = None
):
    """Log authentication attempt"""
    siem_engine.ingest_event(
        category=EventCategory.AUTHENTICATION,
        source_ip=source_ip,
        user=username,
        action="login",
        resource="/auth/login",
        outcome="success" if success else "failure",
        details=details or {}
    )


def log_admin_action(
    source_ip: str,
    username: str,
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log admin action"""
    siem_engine.ingest_event(
        category=EventCategory.ADMIN_ACTION,
        source_ip=source_ip,
        user=username,
        action=action,
        resource=resource,
        outcome="success",
        details=details or {}
    )


def log_rate_limit_violation(
    source_ip: str,
    endpoint: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log rate limit violation"""
    siem_engine.ingest_event(
        category=EventCategory.RATE_LIMIT,
        source_ip=source_ip,
        user=None,
        action="rate_limit_exceeded",
        resource=endpoint,
        outcome="blocked",
        details=details or {}
    )


def log_suspicious_activity(
    source_ip: str,
    user: Optional[str],
    activity_type: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log suspicious activity"""
    siem_engine.ingest_event(
        category=EventCategory.SUSPICIOUS_ACTIVITY,
        source_ip=source_ip,
        user=user,
        action=activity_type,
        resource="system",
        outcome="flagged",
        details=details or {}
    )
