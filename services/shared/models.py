# ACGS Federated Service Models
import os
import sys

# Handle imports for both service context and alembic context
Base = None

try:
    # Try relative import first (when used as a module)
    from .database import Base
except ImportError:
    try:
        # Try importing from the database.py file directly (for alembic)
        sys.path.insert(0, os.path.dirname(__file__))
        import database as db_module

        Base = db_module.Base
    except ImportError:
        try:
            # Last resort: try importing from database directory
            from database import Base
        except ImportError:
            # Final fallback: create Base directly
            from sqlalchemy.orm import declarative_base

            Base = declarative_base()

# Ensure Base is not None - this is critical for model definitions
if Base is None:
    print("WARNING: Base is None, creating fallback declarative_base")
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

# Verify Base is properly initialized
if not hasattr(Base, "metadata"):
    print("ERROR: Base does not have metadata attribute")
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()
import enum
import uuid  # For generating UUIDs
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (  # For PostgreSQL specific JSONB, UUID, and ARRAY types
    ARRAY,
    JSONB,
    UUID,
)
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(
        String(255), nullable=False
    )  # Increased length for stronger hashes
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    # Roles: e.g., "system_admin", "principle_author", "policy_auditor", "service_account", "user"
    role = Column(String(50), default="user", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    # Relationships for created_by in other models
    created_principles = relationship(
        "Principle",
        back_populates="created_by_user",
        foreign_keys="Principle.created_by_user_id",
    )
    created_policy_templates = relationship(
        "PolicyTemplate",
        back_populates="created_by_user",
        foreign_keys="PolicyTemplate.created_by_user_id",
    )
    created_policies = relationship(
        "Policy",
        back_populates="created_by_user",
        foreign_keys="Policy.created_by_user_id",
    )
    audit_logs_as_actor = relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jti = Column(
        String(36), unique=True, index=True, nullable=False
    )  # JWT ID (standard UUID length)
    token = Column(
        String(512), nullable=False, index=True
    )  # The actual refresh token string, if storing it directly (hashed recommended)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class Principle(Base):
    __tablename__ = "principles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Actual constitutional text
    version = Column(Integer, default=1, nullable=False)
    # Status: e.g., "draft", "active", "archived", "under_review", "deprecated"
    status = Column(String(50), default="draft", nullable=False, index=True)

    # Enhanced Phase 1 Constitutional Fields
    priority_weight = Column(
        Float,
        nullable=True,
        comment="Priority weight for principle prioritization (0.0 to 1.0)",
    )
    scope = Column(
        JSONB,
        nullable=True,
        comment="JSON array defining contexts where principle applies",
    )
    normative_statement = Column(
        Text,
        nullable=True,
        comment="Structured normative statement for constitutional interpretation",
    )
    constraints = Column(
        JSONB,
        nullable=True,
        comment="JSON object defining formal constraints and requirements",
    )
    rationale = Column(
        Text,
        nullable=True,
        comment="Detailed rationale and justification for the principle",
    )
    keywords = Column(
        JSONB,
        nullable=True,
        comment="JSON array of keywords for principle categorization",
    )
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Category classification (e.g., Safety, Privacy, Fairness)",
    )
    validation_criteria_nl = Column(
        Text, nullable=True, comment="Natural language validation criteria for testing"
    )
    constitutional_metadata = Column(
        JSONB, nullable=True, comment="Metadata for constitutional compliance tracking"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_principles")


class PolicyRule(Base):
    __tablename__ = "policy_rules"  # Corresponds to Datalog rules in Integrity Service

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(
        String(255), index=True, nullable=True
    )  # Optional: a human-readable name for the rule, not necessarily unique
    datalog_content = Column(
        Text, nullable=False, unique=True
    )  # Assuming datalog content should be unique for a given version
    version = Column(Integer, default=1, nullable=False)

    # Link to the overarching Policy object this rule belongs to/is derived from (if any)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    policy = relationship("Policy", back_populates="rules")

    # Incremental compilation tracking (Task 8)
    compilation_hash = Column(
        String(64), nullable=True, index=True
    )  # SHA-256 hash for change detection
    last_compiled_at = Column(DateTime(timezone=True), nullable=True)
    compilation_status = Column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, compiled, failed
    compilation_metrics = Column(
        JSONB, nullable=True
    )  # Performance metrics for compilation

    # Policy version tracking for incremental compilation
    policy_versions = relationship(
        "PolicyVersion", back_populates="policy_rule", cascade="all, delete-orphan"
    )

    source_principle_ids = Column(
        JSONB, nullable=True
    )  # e.g., [1, 2, 3] - IDs from Principle table

    # Status: "pending_synthesis", "synthesized", "pending_verification", "verified_passed", "verified_failed", "active", "inactive", "archived"
    status = Column(String(50), default="pending_synthesis", nullable=False, index=True)

    # Verification details
    verification_status = Column(
        String(50), default="not_verified", nullable=False, index=True
    )  # "not_verified", "pending", "passed", "failed", "error"
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_feedback = Column(
        JSONB, nullable=True
    )  # E.g., counter-example, report summary from FV service

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Optional: IDs from external systems if this rule was synthesized or verified by a specific run/job
    synthesized_by_gs_run_id = Column(String(100), nullable=True)
    verified_by_fv_run_id = Column(String(100), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Using UUID for audit logs
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    service_name = Column(
        String(100), nullable=False, index=True
    )  # e.g., "auth_service", "gs_service"
    event_type = Column(
        String(100), nullable=False, index=True
    )  # e.g., "USER_LOGIN", "POLICY_RULE_CREATED"

    actor_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # User performing action
    # Or if User.id is UUID:
    # actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor = relationship("User", back_populates="audit_logs_as_actor")

    # Entity being acted upon (optional and polymorphic)
    # Consider a more robust polymorphic relationship if many entity types need linking
    # Or keep it simple with string identifiers.
    entity_type = Column(
        String(100), nullable=True, index=True
    )  # e.g., "Principle", "PolicyRule", "User"
    entity_id_int = Column(
        Integer, nullable=True, index=True
    )  # If entity has integer PK
    entity_id_uuid = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # If entity has UUID PK
    entity_id_str = Column(
        String(255), nullable=True, index=True
    )  # If entity has string PK or for general refs

    description = Column(Text, nullable=True)  # Human-readable summary
    details = Column(
        JSONB, nullable=True
    )  # Structured details of the event (e.g., changes made, request payload)

    # For tamper evidence (optional, can be complex to manage)
    # previous_hash = Column(String(64), nullable=True) # Hash of the previous log entry for this stream/entity
    # current_hash = Column(String(64), nullable=True, index=True, unique=True) # Hash of this log entry's content


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Template content (e.g., Datalog with placeholders like {{param_name}})
    template_content = Column(Text, nullable=False)
    # JSON schema describing customizable parameters and their types/constraints
    parameters_schema = Column(JSONB, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    status = Column(
        String(50), default="draft", nullable=False, index=True
    )  # "draft", "active", "deprecated"

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_policy_templates")

    # Policies instantiated from this template
    generated_policies = relationship("Policy", back_populates="template")


class PolicyVersion(Base):
    """Policy version tracking for incremental compilation (Task 8)"""

    __tablename__ = "policy_versions"

    id = Column(Integer, primary_key=True, index=True)
    policy_rule_id = Column(Integer, ForeignKey("policy_rules.id"), nullable=False)
    policy_rule = relationship("PolicyRule", back_populates="policy_versions")

    version_number = Column(Integer, nullable=False)
    content_hash = Column(
        String(64), nullable=False, index=True
    )  # SHA-256 hash of policy content
    compilation_hash = Column(
        String(64), nullable=True, index=True
    )  # Hash of compiled output

    # Compilation metadata
    compilation_status = Column(
        String(50), nullable=False, default="pending", index=True
    )
    compilation_time_ms = Column(
        Float, nullable=True
    )  # Compilation time in milliseconds
    compilation_strategy = Column(
        String(50), nullable=True
    )  # full, incremental, partial, optimized

    # Version control and rollback support
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    is_rollback_point = Column(Boolean, default=False, nullable=False)
    rollback_reason = Column(Text, nullable=True)

    # Constitutional amendment integration
    amendment_id = Column(Integer, ForeignKey("ac_amendments.id"), nullable=True)
    amendment = relationship("ACAmendment")

    # Deployment tracking
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deployment_status = Column(
        String(50), default="pending", nullable=False, index=True
    )
    deployment_metrics = Column(JSONB, nullable=True)

    # Backward compatibility tracking (3-version requirement)
    compatible_versions = Column(
        JSONB, nullable=True
    )  # List of compatible version numbers
    breaking_changes = Column(
        JSONB, nullable=True
    )  # List of breaking changes from previous version

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User")


class Policy(Base):
    __tablename__ = (
        "policies"  # A high-level policy object, potentially composed of multiple rules
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(255), index=True, nullable=False, unique=True
    )  # Policy name should be unique
    description = Column(Text, nullable=True)
    # Overall policy intent or summary, if not directly executable content like PolicyRule
    # This 'content' could be natural language, or a structured representation.
    # If this Policy directly translates to a single rule, its content might be similar to PolicyRule.datalog_content.
    # However, a Policy could also be a collection of PolicyRules.
    # For now, let's assume 'content' here is a textual description or high-level definition.
    # The actual enforceable rules are in PolicyRule.
    high_level_content = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    # Status: "draft", "active", "archived", "under_review", "deprecated"
    status = Column(
        String(50), default="draft", nullable=False, index=True
    )  # Corrected from index=true

    template_id = Column(Integer, ForeignKey("policy_templates.id"), nullable=True)
    template = relationship("PolicyTemplate", back_populates="generated_policies")

    # Parameters used if this policy was instantiated from a template
    customization_parameters = Column(JSONB, nullable=True)
    # Links to AC principles this policy is derived from or aims to uphold
    source_principle_ids = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_policies")

    # Relationship to the actual Datalog rules that implement this policy
    rules = relationship(
        "PolicyRule", back_populates="policy", cascade="all, delete-orphan"
    )

    # For version history (simplified: link to previous version)
    # previous_version_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    # For a full version history, a separate versioning table or pattern might be better.


# Constitutional Council and AC Enhancement Models


class ACMetaRule(Base):
    """Meta-rules (R) component of the Artificial Constitution AC=⟨P,R,M,V⟩"""

    __tablename__ = "ac_meta_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(
        String(100), nullable=False, index=True
    )  # e.g., "amendment_procedure", "voting_threshold", "stakeholder_role"
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # JSON structure defining the meta-governance rule
    rule_definition = Column(
        JSONB, nullable=False
    )  # e.g., {"threshold": 0.67, "stakeholder_roles": ["admin", "policy_manager"]}

    # Governance parameters
    threshold = Column(
        String(50), nullable=True
    )  # e.g., "0.67", "simple_majority", "unanimous"
    stakeholder_roles = Column(
        JSONB, nullable=True
    )  # List of roles that can participate
    decision_mechanism = Column(
        String(100), nullable=True
    )  # e.g., "supermajority_vote", "consensus", "expert_panel"

    status = Column(
        String(50), default="active", nullable=False, index=True
    )  # "active", "deprecated", "proposed"
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User")


class ACAmendment(Base):
    """Amendment proposals and voting for the Artificial Constitution"""

    __tablename__ = "ac_amendments"

    id = Column(Integer, primary_key=True, index=True)
    principle_id = Column(Integer, ForeignKey("principles.id"), nullable=False)
    principle = relationship("Principle")

    amendment_type = Column(
        String(50), nullable=False, index=True
    )  # "modify", "add", "remove", "status_change"
    proposed_changes = Column(Text, nullable=False)  # Description of proposed changes
    justification = Column(Text, nullable=True)  # Rationale for the amendment

    # Amendment content
    proposed_content = Column(Text, nullable=True)  # New content if modifying/adding
    proposed_status = Column(String(50), nullable=True)  # New status if changing status

    # Workflow status
    status = Column(
        String(50), default="proposed", nullable=False, index=True
    )  # "proposed", "under_review", "voting", "approved", "rejected", "implemented"

    # Voting and approval
    voting_started_at = Column(DateTime(timezone=True), nullable=True)
    voting_ends_at = Column(DateTime(timezone=True), nullable=True)
    votes_for = Column(Integer, default=0, nullable=False)
    votes_against = Column(Integer, default=0, nullable=False)
    votes_abstain = Column(Integer, default=0, nullable=False)
    required_threshold = Column(String(50), nullable=True)  # From applicable meta-rule

    # Public consultation
    consultation_period_days = Column(Integer, nullable=True)
    public_comment_enabled = Column(Boolean, default=True, nullable=False)
    stakeholder_groups = Column(JSONB, nullable=True)  # Groups invited to participate

    # Co-evolution and scalability fields
    urgency_level = Column(
        String(20), nullable=False, default="normal", index=True
    )  # "normal", "rapid", "emergency"
    co_evolution_context = Column(
        JSONB, nullable=True
    )  # Context for rapid co-evolution scenarios
    expected_impact = Column(
        String(20), nullable=True, index=True
    )  # "low", "medium", "high", "critical"
    rapid_processing_requested = Column(Boolean, default=False, nullable=False)
    constitutional_significance = Column(
        String(20), nullable=False, default="normal"
    )  # "normal", "significant", "fundamental"

    # Optimistic locking and versioning
    version = Column(Integer, default=1, nullable=False)  # For optimistic locking
    workflow_state = Column(
        String(50), nullable=False, default="proposed", index=True
    )  # State machine tracking
    state_transitions = Column(JSONB, nullable=True)  # History of state transitions
    processing_metrics = Column(
        JSONB, nullable=True
    )  # Performance metrics for co-evolution tracking

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    proposed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposed_by_user = relationship("User")

    # Relationships
    votes = relationship(
        "ACAmendmentVote", back_populates="amendment", cascade="all, delete-orphan"
    )
    comments = relationship(
        "ACAmendmentComment", back_populates="amendment", cascade="all, delete-orphan"
    )


class ACAmendmentVote(Base):
    """Individual votes on AC amendments by Constitutional Council members"""

    __tablename__ = "ac_amendment_votes"

    id = Column(Integer, primary_key=True, index=True)
    amendment_id = Column(Integer, ForeignKey("ac_amendments.id"), nullable=False)
    amendment = relationship("ACAmendment", back_populates="votes")

    voter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voter = relationship("User")

    vote = Column(String(20), nullable=False, index=True)  # "for", "against", "abstain"
    reasoning = Column(Text, nullable=True)  # Optional explanation of vote

    voted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ACAmendmentComment(Base):
    """Public comments and feedback on AC amendments"""

    __tablename__ = "ac_amendment_comments"

    id = Column(Integer, primary_key=True, index=True)
    amendment_id = Column(Integer, ForeignKey("ac_amendments.id"), nullable=False)
    amendment = relationship("ACAmendment", back_populates="comments")

    commenter_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Nullable for anonymous comments
    commenter = relationship("User")

    commenter_name = Column(String(255), nullable=True)  # For anonymous commenters
    commenter_email = Column(String(255), nullable=True)  # For anonymous commenters
    stakeholder_group = Column(
        String(100), nullable=True
    )  # e.g., "citizen", "expert", "affected_party"

    comment_text = Column(Text, nullable=False)
    sentiment = Column(
        String(20), nullable=True, index=True
    )  # "support", "oppose", "neutral"

    is_public = Column(Boolean, default=True, nullable=False)
    is_moderated = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Create ACPrinciple as an alias for Principle for backward compatibility
ACPrinciple = Principle
# Create ConstitutionalPrinciple as an alias for Principle for backward compatibility
ConstitutionalPrinciple = Principle


class ACConflictResolution(Base):
    """Conflict Resolution Mapping (M) component of the Artificial Constitution"""

    __tablename__ = "ac_conflict_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    conflict_type = Column(
        String(100), nullable=False, index=True
    )  # e.g., "principle_contradiction", "practical_incompatibility"

    # Principles involved in the conflict
    principle_ids = Column(JSONB, nullable=False)  # List of principle IDs
    context = Column(String(255), nullable=True)  # e.g., "data_retention_vs_privacy"

    # Conflict analysis
    conflict_description = Column(Text, nullable=False)
    severity = Column(
        String(20), nullable=False, index=True
    )  # "low", "medium", "high", "critical"

    # Resolution strategy
    resolution_strategy = Column(
        String(100), nullable=False
    )  # e.g., "principle_priority_based", "contextual_balancing", "meta_rule_override"
    resolution_details = Column(
        JSONB, nullable=True
    )  # Structured resolution information
    precedence_order = Column(
        JSONB, nullable=True
    )  # Priority order of principles for this context

    # Status and lifecycle
    status = Column(
        String(50), default="identified", nullable=False, index=True
    )  # "identified", "analyzed", "resolved", "monitoring"
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    identified_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    identified_by_user = relationship("User")


# --- Phase 3: Appeal and Dispute Resolution Models ---


class Appeal(Base):
    """Appeal model for challenging algorithmic decisions - Phase 3 democratic governance"""

    __tablename__ = "appeals"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String, nullable=False, index=True)
    appeal_reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    requested_remedy = Column(Text, nullable=False)
    appellant_contact = Column(String, nullable=True)

    status = Column(
        String, default="pending", nullable=False, index=True
    )  # pending, under_review, resolved, rejected
    resolution = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    submitted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_reviewer_id = Column(String, nullable=True, index=True)
    escalation_level = Column(
        Integer, default=1, nullable=False, index=True
    )  # 1=ombudsperson, 2=technical, 3=council_subcommittee, 4=full_council

    def __repr__(self):
    # requires: Valid input parameters
    # ensures: Correct function execution
    # sha256: func_hash
        return f"<Appeal(id={self.id}, decision_id='{self.decision_id}', status='{self.status}', level={self.escalation_level})>"


class DisputeResolution(Base):
    """Dispute resolution process model for appeals - Phase 3 democratic governance"""

    __tablename__ = "dispute_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    appeal_id = Column(Integer, ForeignKey("appeals.id"), nullable=False, index=True)
    appeal = relationship("Appeal")

    resolution_method = Column(
        String, nullable=False, index=True
    )  # ombudsperson, technical_review, council_subcommittee, full_council
    panel_composition = Column(ARRAY(String), nullable=True)
    timeline_days = Column(Integer, default=30, nullable=False)

    status = Column(
        String, default="initiated", nullable=False, index=True
    )  # initiated, in_progress, completed, escalated
    findings = Column(Text, nullable=True)
    recommendations = Column(ARRAY(String), nullable=True)
    final_decision = Column(Text, nullable=True)

    initiated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    panel_members = Column(ARRAY(String), nullable=True)

    def __repr__(self):
    # requires: Valid input parameters
    # ensures: Correct function execution
    # sha256: func_hash
        return f"<DisputeResolution(id={self.id}, appeal_id={self.appeal_id}, method='{self.resolution_method}', status='{self.status}')>"


# Indexes for appeal and dispute resolution queries
Index("ix_appeal_decision_status", Appeal.decision_id, Appeal.status)
Index("ix_appeal_submitted_level", Appeal.submitted_at, Appeal.escalation_level)
Index(
    "ix_dispute_appeal_method",
    DisputeResolution.appeal_id,
    DisputeResolution.resolution_method,
)
Index(
    "ix_dispute_initiated_status",
    DisputeResolution.initiated_at,
    DisputeResolution.status,
)


# Example of how models might be related if a Policy is a collection of PolicyRules:
# In Policy model:
# rules = relationship("PolicyRule", back_populates="policy_group")
# In PolicyRule model:
# policy_group_id = Column(Integer, ForeignKey("policies.id"))
# policy_group = relationship("Policy", back_populates="rules")
# The current setup with policy_id in PolicyRule and rules in Policy achieves this.


# ===== FEDERATED EVALUATION FRAMEWORK MODELS =====


class PlatformTypeEnum(enum.Enum):
    """Supported platform types for federated evaluation."""

    CLOUD_OPENAI = "cloud_openai"
    CLOUD_ANTHROPIC = "cloud_anthropic"
    CLOUD_COHERE = "cloud_cohere"
    CLOUD_GROQ = "cloud_groq"
    LOCAL_OLLAMA = "local_ollama"
    ACGS_INTERNAL = "acgs_internal"


class EvaluationStatusEnum(enum.Enum):
    """Status of federated evaluation tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatusEnum(enum.Enum):
    """Status of federated nodes."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class AggregationMethodEnum(enum.Enum):
    """Aggregation methods for federated results."""

    FEDERATED_AVERAGING = "federated_averaging"
    SECURE_SUM = "secure_sum"
    DIFFERENTIAL_PRIVATE = "differential_private"
    BYZANTINE_ROBUST = "byzantine_robust"


class FederatedNode(Base):
    """Federated evaluation node registration and management."""

    __tablename__ = "federated_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, nullable=False, index=True)
    platform_type = Column(Enum(PlatformTypeEnum), nullable=False, index=True)

    # Connection details
    endpoint_url = Column(String(500), nullable=False)
    api_key_hash = Column(String(255), nullable=True)  # Hashed API key for security

    # Node capabilities and metadata
    capabilities = Column(
        JSONB, nullable=True
    )  # {"models": ["gpt-4"], "max_tokens": 4096}
    configuration = Column(JSONB, nullable=True)  # Node-specific configuration

    # Status and health
    status = Column(
        Enum(NodeStatusEnum), default=NodeStatusEnum.ACTIVE, nullable=False, index=True
    )
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    health_score = Column(Float, default=1.0, nullable=False)  # 0.0 to 1.0

    # Performance metrics
    total_evaluations = Column(Integer, default=0, nullable=False)
    successful_evaluations = Column(Integer, default=0, nullable=False)
    failed_evaluations = Column(Integer, default=0, nullable=False)
    average_response_time_ms = Column(Float, default=0.0, nullable=False)

    # MAB integration
    mab_template_preferences = Column(
        JSONB, nullable=True
    )  # Template performance history
    prompt_optimization_history = Column(JSONB, nullable=True)  # MAB optimization data

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    evaluations = relationship(
        "FederatedEvaluation",
        back_populates="nodes",
        secondary="evaluation_node_assignments",
    )


class FederatedEvaluation(Base):
    """Federated evaluation task tracking."""

    __tablename__ = "federated_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)

    # Evaluation content
    policy_content = Column(Text, nullable=False)
    evaluation_criteria = Column(JSONB, nullable=False)
    target_platforms = Column(ARRAY(String), nullable=False)

    # Privacy and security
    privacy_requirements = Column(
        JSONB, nullable=True
    )  # {"epsilon": 1.0, "mechanism": "laplace"}
    privacy_budget_used = Column(Float, default=0.0, nullable=False)

    # MAB integration
    mab_context = Column(JSONB, nullable=True)  # MAB optimization context
    selected_template_id = Column(String(100), nullable=True)  # MAB-selected template

    # Status and timing
    status = Column(
        Enum(EvaluationStatusEnum),
        default=EvaluationStatusEnum.PENDING,
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_completion_time = Column(DateTime(timezone=True), nullable=True)

    # Results and metrics
    aggregated_results = Column(JSONB, nullable=True)  # Final aggregated results
    aggregation_method = Column(Enum(AggregationMethodEnum), nullable=True)
    participant_count = Column(Integer, default=0, nullable=False)
    byzantine_nodes_detected = Column(Integer, default=0, nullable=False)

    # Performance metrics
    total_execution_time_ms = Column(Float, nullable=True)
    cross_platform_consistency_score = Column(Float, nullable=True)  # 0.0 to 1.0

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # User tracking
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_by_user = relationship("User")

    # Relationships
    nodes = relationship(
        "FederatedNode",
        back_populates="evaluations",
        secondary="evaluation_node_assignments",
    )
    node_results = relationship(
        "EvaluationNodeResult",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class EvaluationNodeAssignment(Base):
    """Many-to-many relationship between evaluations and nodes."""

    __tablename__ = "evaluation_node_assignments"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(
        Integer, ForeignKey("federated_evaluations.id"), nullable=False
    )
    node_id = Column(Integer, ForeignKey("federated_nodes.id"), nullable=False)

    # Assignment details
    assigned_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    priority = Column(Integer, default=1, nullable=False)  # 1=high, 2=medium, 3=low

    # Status tracking
    status = Column(
        String(50), default="assigned", nullable=False, index=True
    )  # assigned, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class EvaluationNodeResult(Base):
    """Individual node results for federated evaluations."""

    __tablename__ = "evaluation_node_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(
        Integer, ForeignKey("federated_evaluations.id"), nullable=False
    )
    node_id = Column(Integer, ForeignKey("federated_nodes.id"), nullable=False)

    # Result data
    raw_response = Column(JSONB, nullable=True)  # Raw response from the node
    processed_metrics = Column(JSONB, nullable=True)  # Processed evaluation metrics

    # Performance metrics
    policy_compliance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    execution_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # 0.0 to 1.0
    consistency_score = Column(Float, nullable=True)  # 0.0 to 1.0
    privacy_score = Column(Float, nullable=True)  # 0.0 to 1.0

    # Quality indicators
    is_byzantine = Column(
        Boolean, default=False, nullable=False
    )  # Detected as Byzantine
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    validation_passed = Column(Boolean, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    evaluation = relationship("FederatedEvaluation", back_populates="node_results")
    node = relationship("FederatedNode")


class SecureAggregationSession(Base):
    """Secure aggregation session tracking."""

    __tablename__ = "secure_aggregation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    evaluation_id = Column(
        Integer, ForeignKey("federated_evaluations.id"), nullable=False
    )

    # Aggregation configuration
    aggregation_method = Column(Enum(AggregationMethodEnum), nullable=False)
    participant_nodes = Column(ARRAY(String), nullable=False)
    minimum_participants = Column(Integer, default=2, nullable=False)

    # Cryptographic details
    encryption_scheme = Column(
        String(100), nullable=True
    )  # e.g., "homomorphic", "secret_sharing"
    key_exchange_completed = Column(Boolean, default=False, nullable=False)
    verification_hashes = Column(JSONB, nullable=True)

    # Privacy parameters
    privacy_epsilon = Column(Float, nullable=True)  # Differential privacy parameter
    privacy_delta = Column(Float, nullable=True)  # Differential privacy parameter
    noise_mechanism = Column(String(50), nullable=True)  # "laplace", "gaussian"

    # Session status
    status = Column(
        String(50), default="initializing", nullable=False, index=True
    )  # initializing, collecting, aggregating, completed, failed
    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results
    aggregated_data = Column(JSONB, nullable=True)  # Final aggregated results
    privacy_budget_consumed = Column(Float, default=0.0, nullable=False)
    byzantine_nodes_detected = Column(Integer, default=0, nullable=False)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Relationships
    evaluation = relationship("FederatedEvaluation")
    shares = relationship(
        "SecureShare", back_populates="session", cascade="all, delete-orphan"
    )


class SecureShare(Base):
    """Secure shares for cryptographic aggregation."""

    __tablename__ = "secure_shares"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(100), unique=True, nullable=False, index=True)
    session_id = Column(
        Integer, ForeignKey("secure_aggregation_sessions.id"), nullable=False
    )
    node_id = Column(Integer, ForeignKey("federated_nodes.id"), nullable=False)

    # Share data
    encrypted_value = Column(Text, nullable=False)  # Encrypted share value
    verification_hash = Column(String(255), nullable=False)  # Hash for verification
    share_index = Column(Integer, nullable=False)  # Index in secret sharing scheme

    # Metadata
    encryption_metadata = Column(JSONB, nullable=True)  # Encryption parameters
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session = relationship("SecureAggregationSession", back_populates="shares")
    node = relationship("FederatedNode")


class PrivacyMetric(Base):
    """Privacy metrics tracking for federated evaluations."""

    __tablename__ = "privacy_metrics"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(
        Integer, ForeignKey("federated_evaluations.id"), nullable=False
    )
    node_id = Column(
        Integer, ForeignKey("federated_nodes.id"), nullable=True
    )  # Null for aggregated metrics

    # Privacy measurements
    epsilon_consumed = Column(
        Float, nullable=True
    )  # Differential privacy budget consumed
    delta_consumed = Column(Float, nullable=True)  # Differential privacy delta consumed
    privacy_score = Column(Float, nullable=True)  # Overall privacy score (0.0 to 1.0)

    # Specific privacy metrics
    data_minimization_score = Column(Float, nullable=True)  # How well data is minimized
    anonymization_level = Column(
        Float, nullable=True
    )  # Level of anonymization achieved
    inference_resistance = Column(
        Float, nullable=True
    )  # Resistance to inference attacks

    # Privacy mechanisms applied
    mechanisms_applied = Column(JSONB, nullable=True)  # List of privacy mechanisms used
    noise_parameters = Column(JSONB, nullable=True)  # Parameters for noise addition

    # Compliance tracking
    gdpr_compliant = Column(Boolean, nullable=True)
    ccpa_compliant = Column(Boolean, nullable=True)
    hipaa_compliant = Column(Boolean, nullable=True)

    # Timestamps
    measured_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    evaluation = relationship("FederatedEvaluation")
    node = relationship("FederatedNode")


class ConstitutionalValidation(Base):
    """Constitutional compliance validation for federated evaluations."""

    __tablename__ = "constitutional_validations"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(
        Integer, ForeignKey("federated_evaluations.id"), nullable=False
    )

    # Constitutional compliance
    principle_ids_validated = Column(
        ARRAY(Integer), nullable=True
    )  # AC principle IDs checked
    compliance_score = Column(
        Float, nullable=True
    )  # Overall compliance score (0.0 to 1.0)
    constitutional_violations = Column(JSONB, nullable=True)  # Detected violations

    # Validation details
    validation_method = Column(
        String(100), nullable=True
    )  # "automated", "human_review", "hybrid"
    validation_timestamp = Column(DateTime, nullable=True)
    validation_metadata = Column(JSON, nullable=True)
    validator_confidence = Column(
        Float, nullable=True
    )  # Confidence in validation (0.0 to 1.0)

    # Cross-platform consistency
    consistency_across_platforms = Column(
        Float, nullable=True
    )  # Consistency score across platforms
    platform_specific_issues = Column(
        JSONB, nullable=True
    )  # Platform-specific compliance issues

    # Integration with Constitutional Council
    council_review_required = Column(Boolean, default=False, nullable=False)
    council_decision = Column(
        String(100), nullable=True
    )  # "approved", "rejected", "conditional"
    council_feedback = Column(Text, nullable=True)

    # Timestamps
    validated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    council_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    evaluation = relationship("FederatedEvaluation")


# --- Constitutional Violation Detection Models ---


class ConstitutionalViolation(Base):
    """Model for tracking constitutional principle violations."""

    __tablename__ = "constitutional_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    violation_type = Column(
        String(100), nullable=False, index=True
    )  # principle_violation, synthesis_failure, enforcement_breach, stakeholder_conflict
    severity = Column(
        String(20), nullable=False, index=True
    )  # low, medium, high, critical
    principle_id = Column(Integer, ForeignKey("principles.id"), nullable=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)

    # Violation details
    violation_description = Column(Text, nullable=False)
    detection_method = Column(
        String(100), nullable=False
    )  # automated, manual, escalated
    fidelity_score = Column(
        Numeric(5, 4), nullable=True
    )  # Constitutional fidelity score at time of violation
    distance_score = Column(
        Numeric(5, 4), nullable=True
    )  # Constitutional distance score

    # Context and metadata
    context_data = Column(JSON, nullable=True)  # Additional context about the violation
    detection_metadata = Column(
        JSON, nullable=True
    )  # Metadata from detection algorithms

    # Status tracking
    status = Column(
        String(50), default="detected", nullable=False, index=True
    )  # detected, investigating, resolved, escalated
    resolution_status = Column(
        String(50), nullable=True
    )  # auto_resolved, manual_resolved, escalated, dismissed
    resolution_description = Column(Text, nullable=True)

    # Escalation tracking
    escalated = Column(Boolean, default=False, nullable=False, index=True)
    escalation_level = Column(
        String(50), nullable=True
    )  # policy_manager, constitutional_council, emergency_response
    escalated_at = Column(DateTime, nullable=True)
    escalated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Audit trail
    detected_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    detected_by = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # User who detected (if manual)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_violation_type_severity", "violation_type", "severity"),
        Index("idx_violation_status_detected", "status", "detected_at"),
        Index("idx_violation_escalated", "escalated", "escalation_level"),
        Index("idx_violation_principle_policy", "principle_id", "policy_id"),
    )


class ViolationAlert(Base):
    """Model for tracking violation alerts and notifications."""

    __tablename__ = "violation_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    violation_id = Column(
        UUID(as_uuid=True), ForeignKey("constitutional_violations.id"), nullable=False
    )

    # Alert configuration
    alert_type = Column(
        String(50), nullable=False, index=True
    )  # threshold, escalation, notification
    alert_level = Column(String(20), nullable=False, index=True)  # green, amber, red
    threshold_value = Column(
        Numeric(5, 4), nullable=True
    )  # Threshold that triggered the alert

    # Alert content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recommended_actions = Column(JSON, nullable=True)  # List of recommended actions

    # Notification tracking
    notification_channels = Column(
        JSON, nullable=True
    )  # List of channels used for notification
    notification_status = Column(
        String(50), default="pending", nullable=False
    )  # pending, sent, failed, acknowledged
    notification_attempts = Column(Integer, default=0, nullable=False)
    last_notification_attempt = Column(DateTime, nullable=True)

    # Response tracking
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    response_actions = Column(JSON, nullable=True)  # Actions taken in response to alert

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_alert_type_level", "alert_type", "alert_level"),
        Index("idx_alert_status_created", "notification_status", "created_at"),
        Index("idx_alert_acknowledged", "acknowledged", "acknowledged_at"),
    )


class ViolationThreshold(Base):
    """Model for configurable violation detection thresholds."""

    __tablename__ = "violation_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    threshold_name = Column(String(100), unique=True, nullable=False, index=True)
    threshold_type = Column(
        String(50), nullable=False, index=True
    )  # fidelity_score, violation_count, severity_based

    # Threshold values
    green_threshold = Column(
        Numeric(5, 4), nullable=False
    )  # Normal operation threshold
    amber_threshold = Column(Numeric(5, 4), nullable=False)  # Warning threshold
    red_threshold = Column(Numeric(5, 4), nullable=False)  # Critical threshold

    # Configuration
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)  # Additional configuration parameters

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class ViolationEscalation(Base):
    """Model for tracking violation escalation workflows."""

    __tablename__ = "violation_escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    violation_id = Column(
        UUID(as_uuid=True), ForeignKey("constitutional_violations.id"), nullable=False
    )

    # Escalation details
    escalation_type = Column(
        String(50), nullable=False, index=True
    )  # automatic, manual, threshold_based
    escalation_level = Column(
        String(50), nullable=False, index=True
    )  # policy_manager, constitutional_council, emergency_response
    escalation_reason = Column(Text, nullable=False)

    # Escalation configuration
    trigger_conditions = Column(
        JSON, nullable=True
    )  # Conditions that triggered escalation
    escalation_rules = Column(JSON, nullable=True)  # Rules applied for escalation

    # Assignment and notification
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_role = Column(String(50), nullable=True)  # Role required for handling
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_channels = Column(JSON, nullable=True)

    # Status tracking
    status = Column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, assigned, in_progress, resolved, timeout
    response_time_seconds = Column(Integer, nullable=True)  # Time to first response
    resolution_time_seconds = Column(Integer, nullable=True)  # Time to resolution

    # Response details
    response_actions = Column(JSON, nullable=True)  # Actions taken in response
    resolution_summary = Column(Text, nullable=True)

    # Audit trail
    escalated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    escalated_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_escalation_type_level", "escalation_type", "escalation_level"),
        Index("idx_escalation_status_escalated", "status", "escalated_at"),
        Index("idx_escalation_assigned", "assigned_to", "assigned_role"),
    )


# --- Task 13: Cross-Domain Principle Testing Framework Models ---


class DomainContext(Base):
    """Domain-specific context metadata for cross-domain principle testing"""

    __tablename__ = "domain_contexts"

    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(
        String(100), unique=True, nullable=False, index=True
    )  # e.g., "healthcare", "finance", "education"
    domain_description = Column(Text, nullable=True)

    # Regulatory framework information
    regulatory_frameworks = Column(
        JSONB, nullable=True
    )  # List of applicable regulations
    compliance_requirements = Column(
        JSONB, nullable=True
    )  # Specific compliance requirements
    cultural_contexts = Column(
        JSONB, nullable=True
    )  # Cultural and social context factors

    # Domain-specific constraints
    domain_constraints = Column(
        JSONB, nullable=True
    )  # Technical and operational constraints
    risk_factors = Column(JSONB, nullable=True)  # Domain-specific risk factors
    stakeholder_groups = Column(JSONB, nullable=True)  # Relevant stakeholder groups

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)


class CrossDomainTestScenario(Base):
    """Test scenarios for cross-domain principle validation"""

    __tablename__ = "cross_domain_test_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String(255), nullable=False, index=True)
    scenario_description = Column(Text, nullable=True)

    # Domain associations
    primary_domain_id = Column(
        Integer, ForeignKey("domain_contexts.id"), nullable=False, index=True
    )
    secondary_domains = Column(JSONB, nullable=True)  # List of secondary domain IDs

    # Test configuration
    test_type = Column(
        String(50), nullable=False, index=True
    )  # e.g., "consistency", "adaptation", "conflict_detection"
    test_parameters = Column(JSONB, nullable=True)  # Configurable test parameters
    expected_outcomes = Column(JSONB, nullable=True)  # Expected test results

    # Principle associations
    principle_ids = Column(JSONB, nullable=False)  # List of principle IDs to test
    principle_adaptations = Column(
        JSONB, nullable=True
    )  # Domain-specific principle adaptations

    # Status and results
    status = Column(
        String(50), default="pending", nullable=False, index=True
    )  # "pending", "running", "completed", "failed"
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    accuracy_score = Column(Float, nullable=True)  # Test accuracy (0.0 to 1.0)
    consistency_score = Column(Float, nullable=True)  # Cross-domain consistency score

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class CrossDomainTestResult(Base):
    """Results from cross-domain principle testing"""

    __tablename__ = "cross_domain_test_results"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("cross_domain_test_scenarios.id"),
        nullable=False,
        index=True,
    )
    test_run_id = Column(
        String(100), nullable=False, index=True
    )  # Unique identifier for test run

    # Test execution details
    domain_id = Column(
        Integer, ForeignKey("domain_contexts.id"), nullable=False, index=True
    )
    principle_id = Column(
        Integer, ForeignKey("principles.id"), nullable=False, index=True
    )
    test_type = Column(String(50), nullable=False, index=True)

    # Results
    is_consistent = Column(Boolean, nullable=False)
    consistency_score = Column(Float, nullable=False)  # 0.0 to 1.0
    adaptation_required = Column(Boolean, nullable=False)
    adaptation_suggestions = Column(JSONB, nullable=True)  # Suggested adaptations

    # Detailed analysis
    validation_details = Column(JSONB, nullable=True)  # Detailed validation results
    conflict_detected = Column(Boolean, default=False, nullable=False)
    conflict_details = Column(JSONB, nullable=True)  # Details of any conflicts found

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)

    # Metadata
    executed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    executed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class ResearchDataExport(Base):
    """Anonymized research data exports for external validation"""

    __tablename__ = "research_data_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_name = Column(String(255), nullable=False, index=True)
    export_description = Column(Text, nullable=True)

    # Data scope
    domain_ids = Column(JSONB, nullable=False)  # List of domain IDs included
    principle_ids = Column(JSONB, nullable=False)  # List of principle IDs included
    date_range_start = Column(DateTime(timezone=True), nullable=False)
    date_range_end = Column(DateTime(timezone=True), nullable=False)

    # Anonymization details
    anonymization_method = Column(
        String(100), nullable=False
    )  # e.g., "k_anonymity", "differential_privacy"
    anonymization_parameters = Column(JSONB, nullable=True)  # Anonymization parameters
    privacy_budget_used = Column(Float, nullable=True)  # Privacy budget consumed

    # Export data
    export_data = Column(JSONB, nullable=False)  # Anonymized research data
    statistical_summary = Column(JSONB, nullable=True)  # Statistical summary of data

    # Cryptographic integrity
    data_hash = Column(
        String(64), nullable=False, index=True
    )  # SHA3-256 hash of export data
    pgp_signature = Column(Text, nullable=True)  # PGP signature for integrity
    signed_by_key_id = Column(String(100), nullable=True)  # Key ID used for signing

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    export_format = Column(
        String(50), default="json", nullable=False
    )  # "json", "csv", "parquet"
    file_size_bytes = Column(Integer, nullable=True)


# Indexes for performance optimization
Index(
    "ix_federated_node_platform_status",
    FederatedNode.platform_type,
    FederatedNode.status,
)
Index(
    "ix_federated_evaluation_status_created",
    FederatedEvaluation.status,
    FederatedEvaluation.created_at,
)
Index(
    "ix_evaluation_node_result_evaluation_node",
    EvaluationNodeResult.evaluation_id,
    EvaluationNodeResult.node_id,
)
Index(
    "ix_secure_aggregation_session_status",
    SecureAggregationSession.status,
    SecureAggregationSession.started_at,
)
Index(
    "ix_privacy_metric_evaluation_measured",
    PrivacyMetric.evaluation_id,
    PrivacyMetric.measured_at,
)
Index(
    "ix_constitutional_validation_evaluation",
    ConstitutionalValidation.evaluation_id,
    ConstitutionalValidation.validated_at,
)

# Task 13: Cross-Domain Testing Framework Indexes
Index(
    "ix_domain_context_name_active", DomainContext.domain_name, DomainContext.is_active
)
Index(
    "ix_cross_domain_scenario_domain_status",
    CrossDomainTestScenario.primary_domain_id,
    CrossDomainTestScenario.status,
)
Index(
    "ix_cross_domain_result_scenario_domain",
    CrossDomainTestResult.scenario_id,
    CrossDomainTestResult.domain_id,
)
Index(
    "ix_cross_domain_result_principle_executed",
    CrossDomainTestResult.principle_id,
    CrossDomainTestResult.executed_at,
)
Index(
    "ix_research_export_created_domains",
    ResearchDataExport.created_at,
    ResearchDataExport.domain_ids,
)
