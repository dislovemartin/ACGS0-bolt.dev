"""
Service Interfaces for ACGS-PGP Dependency Injection

Defines abstract interfaces for core services to enable loose coupling
and improve testability through dependency injection.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncContextManager, Dict, List, Optional


class ServiceInterface(ABC):
    """Base interface for all ACGS services."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""

    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup service resources."""


class DatabaseInterface(ABC):
    """Interface for database operations."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""

    @abstractmethod
    async def execute_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a database query."""

    @abstractmethod
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> int:
        """Execute a database command (INSERT, UPDATE, DELETE)."""

    @abstractmethod
    async def begin_transaction(self) -> AsyncContextManager:
        """Begin a database transaction."""

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""


class CacheInterface(ABC):
    """Interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check cache health."""


class AuthServiceInterface(ServiceInterface):
    """Interface for authentication service."""

    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials."""

    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate authentication token."""

    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user."""

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""


class ACServiceInterface(ServiceInterface):
    """Interface for Audit & Compliance service."""

    @abstractmethod
    async def create_principle(self, principle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new principle."""

    @abstractmethod
    async def get_principles(
        self, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get principles with optional filters."""

    @abstractmethod
    async def vote_on_principle(
        self, principle_id: str, vote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Vote on a principle."""

    @abstractmethod
    async def audit_compliance(
        self, target: str, criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform compliance audit."""


class GSServiceInterface(ServiceInterface):
    """Interface for Governance Synthesis service."""

    @abstractmethod
    async def synthesize_governance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize governance rules."""

    @abstractmethod
    async def analyze_principles(
        self, principles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze principles for synthesis."""

    @abstractmethod
    async def generate_policy(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate policy from requirements."""


class FVServiceInterface(ServiceInterface):
    """Interface for Formal Verification service."""

    @abstractmethod
    async def verify_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Verify policy correctness."""

    @abstractmethod
    async def check_consistency(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check policy consistency."""

    @abstractmethod
    async def validate_rules(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate rule syntax and semantics."""


class PGCServiceInterface(ServiceInterface):
    """Interface for Policy Governance & Compliance service."""

    @abstractmethod
    async def compile_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile policy for execution."""

    @abstractmethod
    async def evaluate_policy(
        self, policy_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate policy against context."""

    @abstractmethod
    async def enforce_policy(
        self, policy_id: str, action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enforce policy on action."""


class IntegrityServiceInterface(ServiceInterface):
    """Interface for Cryptographic Integrity service."""

    @abstractmethod
    async def sign_data(self, data: Dict[str, Any], key_id: str) -> Dict[str, Any]:
        """Sign data with cryptographic signature."""

    @abstractmethod
    async def verify_signature(
        self, data: Dict[str, Any], signature: str, key_id: str
    ) -> bool:
        """Verify cryptographic signature."""

    @abstractmethod
    async def generate_hash(self, data: Dict[str, Any]) -> str:
        """Generate cryptographic hash."""

    @abstractmethod
    async def verify_integrity(self, data: Dict[str, Any], expected_hash: str) -> bool:
        """Verify data integrity."""


class ECServiceInterface(ServiceInterface):
    """Interface for Executive Council service."""

    @abstractmethod
    async def monitor_system(self) -> Dict[str, Any]:
        """Monitor system health and performance."""

    @abstractmethod
    async def oversee_governance(
        self, governance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Oversee governance processes."""

    @abstractmethod
    async def generate_report(
        self, report_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate system reports."""


class EventBusInterface(ABC):
    """Interface for event bus operations."""

    @abstractmethod
    async def publish(
        self, event_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None
    ) -> bool:
        """Publish an event."""

    @abstractmethod
    async def subscribe(self, event_type: str, handler: callable) -> str:
        """Subscribe to events."""

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""

    @abstractmethod
    async def get_events(
        self, event_type: str = None, since: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get events from the bus."""


class MetricsInterface(ABC):
    """Interface for metrics collection."""

    @abstractmethod
    async def record_counter(
        self, name: str, value: int = 1, tags: Dict[str, str] = None
    ) -> None:
        """Record counter metric."""

    @abstractmethod
    async def record_gauge(
        self, name: str, value: float, tags: Dict[str, str] = None
    ) -> None:
        """Record gauge metric."""

    @abstractmethod
    async def record_histogram(
        self, name: str, value: float, tags: Dict[str, str] = None
    ) -> None:
        """Record histogram metric."""

    @abstractmethod
    async def record_timer(
        self, name: str, duration: float, tags: Dict[str, str] = None
    ) -> None:
        """Record timer metric."""

    @abstractmethod
    async def get_metrics(self, name: str = None) -> Dict[str, Any]:
        """Get collected metrics."""


class LoggingInterface(ABC):
    """Interface for structured logging."""

    @abstractmethod
    async def log(
        self, level: str, message: str, context: Dict[str, Any] = None
    ) -> None:
        """Log message with context."""

    @abstractmethod
    async def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with context."""

    @abstractmethod
    async def log_audit(
        self, action: str, user_id: str, resource: str, context: Dict[str, Any] = None
    ) -> None:
        """Log audit event."""

    @abstractmethod
    async def get_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get logs with filters."""


class ConfigurationInterface(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get configuration section."""

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source."""

    @abstractmethod
    def validate(self) -> List[str]:
        """Validate configuration."""
