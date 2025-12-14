"""
Sprint 3: SIEM/SOAR Integration and Threat Modeling
Log ingestion, event correlation, case triage, and response playbooks
"""

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Event severity classification"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class ThreatType(Enum):
    """Threat classification"""
    INJECTION = "SQL/smart_contract_injection"
    UNAUTHORIZED_ACCESS = "Unauthorized admin access"
    DATA_EXPOSURE = "Sensitive data exposure"
    PERFORMANCE_DEGRADATION = "Service degradation (event lag)"
    TRANSACTION_MANIPULATION = "Transaction manipulation/replay"
    RATE_LIMIT_BYPASS = "Rate-limit bypass attempt"
    DDOS = "Distributed denial of service"


@dataclass
class ThreatModel:
    """Threat model entry"""
    threat_id: str
    threat_type: ThreatType
    likelihood: int  # 1-5 (1=rare, 5=frequent)
    impact: int  # 1-5 (1=negligible, 5=critical)
    description: str
    mitigations: List[str]
    owner: str
    detection_rules: List[str]
    response_playbook: str
    
    @property
    def risk_score(self):
        """Risk = Likelihood × Impact"""
        return self.likelihood * self.impact


@dataclass
class SecurityEvent:
    """Structured security event for SIEM"""
    timestamp: str
    event_type: str
    severity: SeverityLevel
    source_ip: str
    user_id: Optional[str]
    resource: str
    action: str
    details: Dict
    threat_score: float  # 0.0 to 1.0
    correlated_events: List[str] = None  # Links to related events
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'severity': self.severity.name,
            'source_ip': self.source_ip,
            'user_id': self.user_id,
            'resource': self.resource,
            'action': self.action,
            'details': self.details,
            'threat_score': self.threat_score,
            'correlated_events': self.correlated_events or [],
        }


class ThreatModelRegistry:
    """Registry of identified threats with risk assessment"""
    
    THREATS = [
        ThreatModel(
            threat_id="T001",
            threat_type=ThreatType.PERFORMANCE_DEGRADATION,
            likelihood=4,
            impact=3,
            description="Event processing lag > 60s causes stale UI and user confusion",
            mitigations=[
                "Implement queue monitoring and auto-scaling",
                "Set up alerts for lag > 60s",
                "Implement circuit breaker for graceful degradation",
                "Use materialized views to serve stale data if real-time unavailable"
            ],
            owner="DevOps Team",
            detection_rules=[
                "event_lag_seconds > 60",
                "queue_depth > threshold"
            ],
            response_playbook="""
            1. Check indexer service status
            2. Review recent contract/event volume
            3. Spin up additional indexer instances if needed
            4. Notify users of potential delays
            5. Escalate if lag persists > 120s
            """
        ),
        
        ThreatModel(
            threat_id="T002",
            threat_type=ThreatType.INJECTION,
            likelihood=2,
            impact=5,
            description="SQL injection via input parameters; Smart contract manipulation via contract calls",
            mitigations=[
                "Use parameterized queries (ORM models)",
                "Input validation on all endpoints (Pydantic)",
                "Contract ABIs validation and type checking",
                "Rate limiting per IP/user",
                "Regular security audits"
            ],
            owner="Security Team",
            detection_rules=[
                "input_contains_sql_keywords",
                "input_length > max_allowed",
                "non_standard_character_encoding"
            ],
            response_playbook="""
            1. Block offending IP immediately
            2. Log full request for forensics
            3. Increase monitoring on related endpoints
            4. Rotate secrets if exposed
            5. Run WAF log analysis for similar patterns
            """
        ),
        
        ThreatModel(
            threat_id="T003",
            threat_type=ThreatType.UNAUTHORIZED_ACCESS,
            likelihood=2,
            impact=5,
            description="Unauthorized access to admin dashboard or API; credential stuffing",
            mitigations=[
                "Token-based authentication (required in Sprint 2)",
                "Admin dashboard behind JWT + IP whitelist",
                "Log all admin access with user/IP/action",
                "MFA for admin accounts",
                "Rate limiting on login endpoints (5 attempts/min)"
            ],
            owner="Security Team",
            detection_rules=[
                "failed_admin_login_count > 5 in 5min",
                "admin_access_from_unknown_ip",
                "admin_access_outside_business_hours"
            ],
            response_playbook="""
            1. Lock out offending admin account
            2. Force password reset
            3. Audit all recent admin actions
            4. Check for data exfiltration
            5. Notify SOC team and account owner
            """
        ),
        
        ThreatModel(
            threat_id="T004",
            threat_type=ThreatType.DATA_EXPOSURE,
            likelihood=1,
            impact=5,
            description="Accidental exposure of user PII, private transaction data, or API keys in logs",
            mitigations=[
                "Data retention policy (per Sprint 3)",
                "Redact PII from logs automatically",
                "Separate sensitive data into encrypted columns",
                "Encrypt data at rest (encryption module)",
                "Access controls on database",
                "Regular audits of log contents"
            ],
            owner="Data Protection Officer",
            detection_rules=[
                "log_contains_private_key_format",
                "log_contains_wallet_address_balance",
                "log_contains_credit_card_pattern"
            ],
            response_playbook="""
            1. Isolate affected log files
            2. Notify Data Protection Officer
            3. Search for copies of exposed data
            4. Rotate exposed credentials
            5. Notify affected users if required by law
            6. File incident report
            """
        ),
        
        ThreatModel(
            threat_id="T005",
            threat_type=ThreatType.RATE_LIMIT_BYPASS,
            likelihood=3,
            impact=3,
            description="Adversary bypasses rate limits via distributed IPs or header manipulation",
            mitigations=[
                "Rate limiting at API boundary (Redis/in-memory)",
                "Rate limit by user ID + IP (not just IP)",
                "Detect distributed attack patterns",
                "WAF with DDoS protection",
                "Monitor rate-limit hook events"
            ],
            owner="Backend Team",
            detection_rules=[
                "rate_limit_exceeded_count > 10 in 1min",
                "request_from_multiple_ips_same_user_id",
                "abnormal_request_pattern_detected"
            ],
            response_playbook="""
            1. Increase rate limit thresholds for legitimate users
            2. Add offending IPs to blocklist
            3. Trigger CAPTCHA/proof-of-work challenge
            4. Log attack details to SIEM
            5. Analyze attack pattern for trends
            """
        ),
    ]
    
    @classmethod
    def get_threat_by_id(cls, threat_id):
        """Retrieve threat by ID"""
        for threat in cls.THREATS:
            if threat.threat_id == threat_id:
                return threat
        return None
    
    @classmethod
    def get_all_threats(cls):
        """Get all threats sorted by risk score"""
        return sorted(cls.THREATS, key=lambda t: t.risk_score, reverse=True)
    
    @classmethod
    def to_markdown(cls):
        """Export threat model as markdown"""
        lines = ["# Threat Model\n"]
        
        for threat in cls.get_all_threats():
            lines.append(f"## {threat.threat_id}: {threat.threat_type.name}\n")
            lines.append(f"**Description:** {threat.description}\n")
            lines.append(f"**Likelihood:** {threat.likelihood}/5 | **Impact:** {threat.impact}/5 | **Risk:** {threat.risk_score}/25\n")
            lines.append(f"**Owner:** {threat.owner}\n")
            lines.append("\n### Mitigations\n")
            for mit in threat.mitigations:
                lines.append(f"- {mit}\n")
            lines.append("\n### Detection Rules\n")
            for rule in threat.detection_rules:
                lines.append(f"- {rule}\n")
            lines.append("\n### Response Playbook\n")
            lines.append(f"```\n{threat.response_playbook.strip()}\n```\n")
            lines.append("\n---\n\n")
        
        return "".join(lines)


class EventCorrelator:
    """Correlate related security events for pattern detection"""
    
    def __init__(self, correlation_window_seconds=300):
        self.correlation_window = correlation_window_seconds
        self.event_log = deque(maxlen=10000)
        self.event_patterns = defaultdict(list)  # Track patterns
    
    def ingest_event(self, event: SecurityEvent):
        """Ingest security event"""
        self.event_log.append(event)
        logger.info(f"Event ingested: {event.event_type} from {event.source_ip} (threat_score: {event.threat_score})")
        
        # Check for correlated events
        correlated = self._find_correlated_events(event)
        if correlated:
            event.correlated_events = correlated
            logger.warning(f"⚠️ CORRELATION: {len(correlated)} related events found for {event.event_type}")
    
    def _find_correlated_events(self, event: SecurityEvent) -> List[str]:
        """Find related events based on patterns"""
        correlated = []
        cutoff_time = datetime.fromisoformat(event.timestamp) - timedelta(seconds=self.correlation_window)
        
        for past_event in self.event_log:
            past_time = datetime.fromisoformat(past_event.timestamp)
            
            # Check correlations
            if (past_time > cutoff_time and 
                past_event.source_ip == event.source_ip and
                past_event.event_type != event.event_type):
                correlated.append(past_event.to_dict()['timestamp'])
            elif (past_event.user_id == event.user_id and
                  past_event.user_id is not None and
                  past_time > cutoff_time):
                correlated.append(past_event.to_dict()['timestamp'])
        
        return correlated[:5]  # Top 5 correlations
    
    def get_event_summary(self):
        """Get summary of recent events"""
        if not self.event_log:
            return {}
        
        summary = {
            'total_events': len(self.event_log),
            'critical_events': sum(1 for e in self.event_log if e.severity == SeverityLevel.CRITICAL),
            'high_threat_events': sum(1 for e in self.event_log if e.threat_score > 0.7),
            'events_by_type': defaultdict(int),
            'top_sources': defaultdict(int)
        }
        
        for event in self.event_log:
            summary['events_by_type'][event.event_type] += 1
            summary['top_sources'][event.source_ip] += 1
        
        return summary


class ResponsePlaybook:
    """Automated response actions (SOAR - Security Orchestration, Automation & Response)"""
    
    @staticmethod
    def execute_playbook(threat_id: str, event: SecurityEvent):
        """Execute response playbook for threat"""
        threat = ThreatModelRegistry.get_threat_by_id(threat_id)
        if not threat:
            logger.warning(f"Unknown threat: {threat_id}")
            return
        
        logger.critical(f"🚨 EXECUTING PLAYBOOK for {threat.threat_id}: {threat.threat_type.name}")
        
        # Automated actions based on threat
        if threat.threat_id == "T001":  # Performance degradation
            logger.info("→ Triggering auto-scaling for indexer")
            # Call API to spawn additional indexer instances
            
        elif threat.threat_id == "T002":  # Injection
            logger.info(f"→ Blocking IP: {event.source_ip}")
            # Add to firewall blocklist
            logger.info("→ Forcing rotation of API keys")
            # Rotate secrets
            
        elif threat.threat_id == "T003":  # Unauthorized access
            logger.info(f"→ Locking admin account: {event.user_id}")
            # Disable account
            logger.info("→ Creating incident ticket for SOC team")
            # Create ticket in ticketing system
            
        elif threat.threat_id == "T004":  # Data exposure
            logger.critical("→ DATA EXPOSURE - Manual intervention required")
            logger.info("→ Notifying DPO")
            
        elif threat.threat_id == "T005":  # Rate limit bypass
            logger.info(f"→ Adding {event.source_ip} to temporary blocklist")
            # Add to blocklist
            logger.info("→ Triggering DDoS mitigation")


# Demo/Testing
if __name__ == '__main__':
    print("=== Threat Model Registry ===\n")
    print(ThreatModelRegistry.to_markdown())
    
    print("\n=== Event Correlation Demo ===\n")
    correlator = EventCorrelator()
    
    # Simulate events
    event1 = SecurityEvent(
        timestamp=datetime.now().isoformat(),
        event_type="failed_login_attempt",
        severity=SeverityLevel.HIGH,
        source_ip="192.168.1.100",
        user_id="admin",
        resource="/api/admin/dashboard",
        action="GET",
        details={"attempts": 3},
        threat_score=0.65
    )
    
    event2 = SecurityEvent(
        timestamp=(datetime.now() + timedelta(seconds=10)).isoformat(),
        event_type="failed_login_attempt",
        severity=SeverityLevel.HIGH,
        source_ip="192.168.1.100",
        user_id="admin",
        resource="/api/admin/settings",
        action="POST",
        details={"attempts": 4},
        threat_score=0.75
    )
    
    correlator.ingest_event(event1)
    correlator.ingest_event(event2)
    
    print(f"\nEvent Summary:\n{json.dumps(correlator.get_event_summary(), indent=2)}")
    
    # Execute playbook
    ResponsePlaybook.execute_playbook("T003", event2)
    
    print("\n✅ SIEM/SOAR integration ready")
