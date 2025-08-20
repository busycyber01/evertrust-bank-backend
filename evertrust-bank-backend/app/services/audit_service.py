from app import db
from app.models import AuditLog
from datetime import datetime
import json

class AuditService:
    @staticmethod
    def log_event(user_id, action, entity, entity_id=None, metadata=None):
        """
        Log an audit event to the database
        
        Args:
            user_id: ID of the user performing the action
            action: Description of the action performed
            entity: Type of entity affected (e.g., 'account', 'transaction')
            entity_id: ID of the affected entity (optional)
            metadata: Additional context data (optional)
        
        Returns:
            AuditLog: The created audit log entry
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return audit_log
        except Exception as e:
            # If logging fails, we don't want to break the main operation
            # but we should at least log the error to console
            print(f"Audit logging failed: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def get_user_events(user_id, limit=50, offset=0):
        """
        Retrieve audit events for a specific user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of events to return
            offset: Number of events to skip for pagination
        
        Returns:
            List[AuditLog]: List of audit log entries
        """
        return AuditLog.query.filter_by(user_id=user_id)\
                            .order_by(AuditLog.created_at.desc())\
                            .limit(limit)\
                            .offset(offset)\
                            .all()

    @staticmethod
    def get_entity_events(entity, entity_id, limit=50):
        """
        Retrieve audit events for a specific entity
        
        Args:
            entity: Type of entity
            entity_id: ID of the entity
            limit: Maximum number of events to return
        
        Returns:
            List[AuditLog]: List of audit log entries
        """
        return AuditLog.query.filter_by(entity=entity, entity_id=entity_id)\
                            .order_by(AuditLog.created_at.desc())\
                            .limit(limit)\
                            .all()

    @staticmethod
    def export_events(user_id, start_date=None, end_date=None):
        """
        Export audit events to a JSON format
        
        Args:
            user_id: ID of the user
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
        
        Returns:
            str: JSON string of audit events
        """
        query = AuditLog.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        events = query.order_by(AuditLog.created_at.desc()).all()
        
        # Convert events to a serializable format
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'action': event.action,
                'entity': event.entity,
                'entity_id': event.entity_id,
                'metadata': event.metadata,
                'created_at': event.created_at.isoformat()
            })
        
        return json.dumps(events_data, indent=2)