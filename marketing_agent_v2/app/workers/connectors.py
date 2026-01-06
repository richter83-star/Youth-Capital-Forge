"""
Execution connectors for different action types.
"""

import logging
import os
from typing import Dict, Any
from abc import ABC, abstractmethod
from app.models import ActionTypeEnum

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for execution connectors."""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            payload: Action payload
            dry_run: Whether this is a dry run
        
        Returns:
            Result dictionary with provider_message_id if applicable
        """
        pass


class EmailConnector(BaseConnector):
    """Connector for email actions."""
    
    def execute(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Execute email action."""
        recipient = payload.get('recipient')
        subject = payload.get('subject')
        body = payload.get('body')
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send email to {recipient}: {subject}")
            return {
                'status': 'success',
                'provider_message_id': f"dry_run_{id(payload)}",
                'message': 'Email would be sent (dry run)'
            }
        
        # Check for SendGrid
        sendgrid_key = os.getenv('SENDGRID_API_KEY')
        if sendgrid_key:
            return self._send_via_sendgrid(recipient, subject, body)
        else:
            # Mock mode
            logger.info(f"[MOCK] Sending email to {recipient}: {subject}")
            return {
                'status': 'success',
                'provider_message_id': f"mock_{id(payload)}",
                'message': 'Email sent (mock mode)'
            }
    
    def _send_via_sendgrid(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email='noreply@marketing.local',
                to_emails=recipient,
                subject=subject,
                plain_text_content=body
            )
            
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            response = sg.send(message)
            
            logger.info(f"Email sent via SendGrid: {response.status_code}")
            
            return {
                'status': 'success',
                'provider_message_id': response.headers.get('X-Message-Id'),
                'message': 'Email sent via SendGrid'
            }
        
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            raise


class SocialConnector(BaseConnector):
    """Connector for social media actions."""
    
    def execute(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Execute social media action."""
        platform = payload.get('platform')
        content = payload.get('content')
        
        if dry_run:
            logger.info(f"[DRY RUN] Would post to {platform}: {content[:100]}")
            return {
                'status': 'success',
                'provider_message_id': f"dry_run_{id(payload)}",
                'message': f'Post would be sent to {platform} (dry run)'
            }
        
        # Check for Buffer
        buffer_token = os.getenv('BUFFER_TOKEN')
        if buffer_token:
            return self._post_via_buffer(platform, content, payload.get('media_urls'))
        else:
            # Mock mode
            logger.info(f"[MOCK] Posting to {platform}: {content[:100]}")
            return {
                'status': 'success',
                'provider_message_id': f"mock_{id(payload)}",
                'message': f'Post sent to {platform} (mock mode)'
            }
    
    def _post_via_buffer(self, platform: str, content: str, media_urls: list = None) -> Dict[str, Any]:
        """Post to social media via Buffer."""
        try:
            import requests
            
            url = "https://api.bufferapp.com/1/updates/create.json"
            params = {
                'access_token': os.getenv('BUFFER_TOKEN')
            }
            
            data = {
                'profile_ids': [f"buffer_profile_{platform}"],
                'text': content,
                'media': {'link': media_urls[0]} if media_urls else None
            }
            
            response = requests.post(url, params=params, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Posted to {platform} via Buffer")
            
            return {
                'status': 'success',
                'provider_message_id': result.get('updates', [{}])[0].get('id'),
                'message': f'Post sent to {platform} via Buffer'
            }
        
        except Exception as e:
            logger.error(f"Error posting to {platform} via Buffer: {e}")
            raise


class CMSConnector(BaseConnector):
    """Connector for CMS publishing actions."""
    
    def execute(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Execute CMS publishing action."""
        title = payload.get('title')
        content = payload.get('content')
        
        if dry_run:
            logger.info(f"[DRY RUN] Would publish to CMS: {title}")
            return {
                'status': 'success',
                'provider_message_id': f"dry_run_{id(payload)}",
                'message': 'Post would be published to CMS (dry run)'
            }
        
        # Check for CMS webhook
        cms_webhook = os.getenv('CMS_WEBHOOK_URL')
        if cms_webhook:
            return self._publish_via_webhook(cms_webhook, payload)
        else:
            # Mock mode
            logger.info(f"[MOCK] Publishing to CMS: {title}")
            return {
                'status': 'success',
                'provider_message_id': f"mock_{id(payload)}",
                'message': 'Post published to CMS (mock mode)'
            }
    
    def _publish_via_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to CMS via webhook."""
        try:
            import requests
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info("Published to CMS via webhook")
            
            return {
                'status': 'success',
                'provider_message_id': response.headers.get('X-Message-Id', f"webhook_{id(payload)}"),
                'message': 'Post published to CMS via webhook'
            }
        
        except Exception as e:
            logger.error(f"Error publishing to CMS: {e}")
            raise


def get_connector(action_type: ActionTypeEnum) -> BaseConnector:
    """Get the appropriate connector for an action type."""
    if action_type == ActionTypeEnum.EMAIL:
        return EmailConnector()
    elif action_type == ActionTypeEnum.SOCIAL:
        return SocialConnector()
    elif action_type == ActionTypeEnum.CMS:
        return CMSConnector()
    else:
        raise ValueError(f"Unknown action type: {action_type}")
