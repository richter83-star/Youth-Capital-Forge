"""
Action and approval service for managing outbound marketing actions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import (
    Action, Approval, AuditLog, ActionStatusEnum, ApprovalStatusEnum,
    ActionTypeEnum, AuditLogEventEnum
)
from app.schemas import ActionCreate, ActionResponse, ApprovalCreate, ApprovalResponse


class SettingsService:
    """Service for managing system settings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        from app.models import Settings
        setting = self.db.query(Settings).filter(Settings.key == key).first()
        return setting.value if setting else default
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        from app.models import Settings
        setting = self.db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            self.db.add(setting)
        self.db.commit()
    
    def is_kill_switch_enabled(self) -> bool:
        """Check if the kill switch is enabled."""
        value = self.get_setting('KILL_SWITCH', 'false')
        return value.lower() == 'true'


class ActionService:
    """Service for managing actions and approvals."""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = SettingsService(db)
    
    def create_action(
        self,
        action_type: ActionTypeEnum,
        payload: Dict[str, Any],
        dry_run: bool = False,
        scheduled_for: Optional[datetime] = None,
        created_by: Optional[int] = None
    ) -> ActionResponse:
        """
        Create a new action.
        
        Args:
            action_type: Type of action (email, social, cms)
            payload: Action payload
            dry_run: Whether this is a dry run
            scheduled_for: When to execute
            created_by: User ID who created the action
        
        Returns:
            ActionResponse
        """
        action = Action(
            type=action_type,
            status=ActionStatusEnum.DRAFT,
            payload=payload,
            dry_run=dry_run,
            scheduled_for=scheduled_for,
            created_by=created_by
        )
        
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        
        # Log creation
        self._audit_log(
            event_type=AuditLogEventEnum.CREATED,
            entity_type='action',
            entity_id=action.id,
            actor='system',
            details={'type': action_type.value}
        )
        
        return ActionResponse.model_validate(action)
    
    def submit_action_for_approval(self, action_id: int) -> ActionResponse:
        """
        Submit an action for approval (draft -> pending_approval).
        
        Args:
            action_id: Action ID
        
        Returns:
            Updated ActionResponse
        """
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != ActionStatusEnum.DRAFT:
            raise ValueError(f"Can only submit draft actions, current status: {action.status}")
        
        action.status = ActionStatusEnum.PENDING_APPROVAL
        self.db.commit()
        self.db.refresh(action)
        
        # Log submission
        self._audit_log(
            event_type=AuditLogEventEnum.UPDATED,
            entity_type='action',
            entity_id=action.id,
            actor='system',
            details={'new_status': ActionStatusEnum.PENDING_APPROVAL.value}
        )
        
        return ActionResponse.model_validate(action)
    
    def approve_action(
        self,
        action_id: int,
        approved_by: int,
        note: Optional[str] = None
    ) -> ApprovalResponse:
        """
        Approve an action.
        
        Args:
            action_id: Action ID
            approved_by: User ID who approved
            note: Optional approval note
        
        Returns:
            ApprovalResponse
        """
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != ActionStatusEnum.PENDING_APPROVAL:
            raise ValueError(f"Can only approve pending actions, current status: {action.status}")
        
        # Create approval
        approval = Approval(
            action_id=action_id,
            status=ApprovalStatusEnum.APPROVED,
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
            note=note
        )
        
        # Update action status
        action.status = ActionStatusEnum.APPROVED
        
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        
        # Log approval
        self._audit_log(
            event_type=AuditLogEventEnum.APPROVED,
            entity_type='action',
            entity_id=action_id,
            actor=f"user_{approved_by}",
            details={'note': note}
        )
        
        return ApprovalResponse.model_validate(approval)
    
    def deny_action(
        self,
        action_id: int,
        approved_by: int,
        note: Optional[str] = None
    ) -> ApprovalResponse:
        """
        Deny an action.
        
        Args:
            action_id: Action ID
            approved_by: User ID who denied
            note: Optional denial note
        
        Returns:
            ApprovalResponse
        """
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != ActionStatusEnum.PENDING_APPROVAL:
            raise ValueError(f"Can only deny pending actions, current status: {action.status}")
        
        # Create approval
        approval = Approval(
            action_id=action_id,
            status=ApprovalStatusEnum.DENIED,
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
            note=note
        )
        
        # Update action status
        action.status = ActionStatusEnum.CANCELED
        
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        
        # Log denial
        self._audit_log(
            event_type=AuditLogEventEnum.DENIED,
            entity_type='action',
            entity_id=action_id,
            actor=f"user_{approved_by}",
            details={'note': note}
        )
        
        return ApprovalResponse.model_validate(approval)
    
    def get_action(self, action_id: int) -> Optional[ActionResponse]:
        """Get an action by ID."""
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if action:
            return ActionResponse.model_validate(action)
        return None
    
    def list_actions(
        self,
        status: Optional[ActionStatusEnum] = None,
        action_type: Optional[ActionTypeEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActionResponse]:
        """List actions with optional filters."""
        query = self.db.query(Action)
        
        if status:
            query = query.filter(Action.status == status)
        if action_type:
            query = query.filter(Action.type == action_type)
        
        actions = query.order_by(Action.created_at.desc()).offset(skip).limit(limit).all()
        return [ActionResponse.model_validate(action) for action in actions]
    
    def get_pending_actions(self) -> List[Action]:
        """Get all pending approval actions."""
        return self.db.query(Action).filter(
            Action.status == ActionStatusEnum.PENDING_APPROVAL
        ).all()
    
    def get_executable_actions(self) -> List[Action]:
        """Get all actions ready for execution."""
        return self.db.query(Action).filter(
            and_(
                Action.status == ActionStatusEnum.APPROVED,
                Action.scheduled_for <= datetime.utcnow()
            )
        ).all()
    
    def mark_executing(self, action_id: int) -> None:
        """Mark an action as executing."""
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if action:
            action.status = ActionStatusEnum.EXECUTING
            self.db.commit()
    
    def mark_succeeded(self, action_id: int, provider_message_id: Optional[str] = None) -> None:
        """Mark an action as succeeded."""
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if action:
            action.status = ActionStatusEnum.SUCCEEDED
            if provider_message_id:
                action.provider_message_id = provider_message_id
            self.db.commit()
            
            # Log success
            self._audit_log(
                event_type=AuditLogEventEnum.EXECUTED,
                entity_type='action',
                entity_id=action_id,
                actor='worker',
                details={'provider_message_id': provider_message_id}
            )
    
    def mark_failed(self, action_id: int, error_message: str) -> None:
        """Mark an action as failed."""
        action = self.db.query(Action).filter(Action.id == action_id).first()
        if action:
            action.status = ActionStatusEnum.FAILED
            self.db.commit()
            
            # Log failure
            self._audit_log(
                event_type=AuditLogEventEnum.FAILED,
                entity_type='action',
                entity_id=action_id,
                actor='worker',
                details={'error': error_message}
            )
    
    def _audit_log(
        self,
        event_type: AuditLogEventEnum,
        entity_type: str,
        entity_id: int,
        actor: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create an audit log entry."""
        log = AuditLog(
            timestamp=datetime.utcnow(),
            actor=actor,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {}
        )
        self.db.add(log)
        self.db.commit()
