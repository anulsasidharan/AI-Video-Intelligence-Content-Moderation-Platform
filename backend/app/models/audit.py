import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"


class AuditStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class AccessAuditLog(Base, UUIDMixin, TimestampMixin):
    """Records every login and logout attempt for compliance and security review."""

    __tablename__ = "access_audit_logs"

    # Who — nullable because failed login may reference a non-existent user
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # What
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus, name="audit_status_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Where / How
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
