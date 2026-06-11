from typing import Any, Dict, Optional

async def record_audit_event_best_effort(
    *,
    audit_repo: Any,
    settings: Any,
    workspace_id: Optional[str],
    action: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    actor_user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> None:
    """
    Records an audit event in database mode, catching and swallowing any exceptions
    to preserve best-effort write behavior.
    """
    if settings.normalized_persistence_backend == "database":
        try:
            audit_repo.append_event(
                workspace_id=workspace_id,
                event_type=action,
                description=description,
                actor_user_id=actor_user_id,
                event_payload=metadata,
                metadata={"organization_id": organization_id} if organization_id else None,
            )
        except Exception:
            pass
