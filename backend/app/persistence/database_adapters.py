from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Workspace, Organization
from app.models.workspace import CompanyWorkspace
from app.persistence.interfaces import WorkspaceRepository

class DatabaseWorkspaceRepository(WorkspaceRepository):
    """
    SQLAlchemy-backed implementation of the WorkspaceRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session
        self.default_org_id = "org_default"

    def _ensure_default_org(self) -> None:
        """
        Ensure default organization exists in the database to satisfy ForeignKey constraints.
        Comments: Multi-tenant security boundaries will be implemented in a subsequent auth/RBAC PR.
        """
        org = self.session.query(Organization).filter_by(id=self.default_org_id).first()
        if not org:
            org = Organization(id=self.default_org_id, name="Default Organization")
            self.session.add(org)
            self.session.flush()

    def list_workspaces(self) -> List[CompanyWorkspace]:
        """
        List all active non-deleted workspaces.
        """
        workspaces = (
            self.session.query(Workspace)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .all()
        )
        return [
            CompanyWorkspace(
                id=w.id,
                companyName=w.name,
                createdAt=w.created_at.isoformat(),
                metadata=w.workspace_metadata or {}
            )
            for w in workspaces
        ]

    def get_workspace(self, workspace_id: str) -> Optional[CompanyWorkspace]:
        """
        Retrieve workspace by ID if it exists and is not deleted.
        """
        w = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not w:
            return None
        return CompanyWorkspace(
            id=w.id,
            companyName=w.name,
            createdAt=w.created_at.isoformat(),
            metadata=w.workspace_metadata or {}
        )

    def create_workspace(self, workspace_id: str, company_name: str, metadata: Optional[Dict[str, Any]] = None) -> CompanyWorkspace:
        """
        Create a new workspace, ensuring the default organization is present.
        """
        self._ensure_default_org()
        
        existing = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if existing:
            return CompanyWorkspace(
                id=existing.id,
                companyName=existing.name,
                createdAt=existing.created_at.isoformat(),
                metadata=existing.workspace_metadata or {}
            )

        new_workspace = Workspace(
            id=workspace_id,
            organization_id=self.default_org_id,
            name=company_name,
            status="active",
            workspace_metadata=metadata or {}
        )
        self.session.add(new_workspace)
        self.session.commit()
        return CompanyWorkspace(
            id=new_workspace.id,
            companyName=new_workspace.name,
            createdAt=new_workspace.created_at.isoformat(),
            metadata=new_workspace.workspace_metadata or {}
        )

    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Soft-delete workspace.
        """
        w = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not w:
            return False
        
        w.deleted_at = datetime.now(timezone.utc)
        w.status = "deleted"
        self.session.commit()
        return True

    def get_active_workspace(self) -> Optional[CompanyWorkspace]:
        """
        Returns the newest non-deleted workspace.
        """
        w = (
            self.session.query(Workspace)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .order_by(Workspace.created_at.desc())
            .first()
        )
        if not w:
            return None
        return CompanyWorkspace(
            id=w.id,
            companyName=w.name,
            createdAt=w.created_at.isoformat(),
            metadata=w.workspace_metadata or {}
        )
