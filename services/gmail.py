"""
Gmail Service
Provides integration with Gmail API for sending, reading, and managing emails
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email import encoders
import re

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class GmailService:
    """Gmail API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('gmail', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Gmail")
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[str] = None, 
                   bcc: Optional[str] = None,
                   html: bool = False) -> Dict[str, Any]:
        """Send an email"""
        self._ensure_service()
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        if html:
            message.attach(MIMEText(body, 'html'))
        else:
            message.attach(MIMEText(body, 'plain'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": result['id'],
                "thread_id": result.get('threadId'),
                "label_ids": result.get('labelIds', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_emails(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """Read emails matching a query"""
        self._ensure_service()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                emails.append(self._parse_email(email_data))
            
            return {
                "success": True,
                "emails": emails,
                "total": len(emails)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_email(self, email_data: Dict) -> Dict[str, Any]:
        """Parse email data into a readable format"""
        headers = {h['name']: h['value'] for h in email_data.get('payload', {}).get('headers', [])}
        
        return {
            "id": email_data['id'],
            "thread_id": email_data.get('threadId'),
            "subject": headers.get('Subject', '(No subject)'),
            "from": headers.get('From'),
            "to": headers.get('To'),
            "cc": headers.get('Cc'),
            "date": headers.get('Date'),
            "snippet": email_data.get('snippet'),
            "label_ids": email_data.get('labelIds', [])
        }
    
    def search_emails(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search emails with advanced query"""
        self._ensure_service()
        
        try:
            # Gmail search operators
            search_operators = {
                "from": f"from:{query}",
                "to": f"to:{query}",
                "subject": f"subject:{query}",
                "has": f"has:{query}",
                "label": f"label:{query}",
                "after": f"after:{query}",
                "before": f"before:{query}",
                "is": f"is:{query}"
            }
            
            # Use direct query if it looks like an email
            if '@' in query:
                search_query = f"from:{query} OR to:{query}"
            else:
                search_query = query
            
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'To', 'Date']
                ).execute()
                
                emails.append(self._parse_email(email_data))
            
            return {
                "success": True,
                "emails": emails,
                "query": search_query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_unread_count(self, label: str = "INBOX") -> Dict[str, Any]:
        """Get count of unread emails"""
        self._ensure_service()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=f"is:unread label:{label}",
                maxResults=1
            ).execute()
            
            total_results = results.get('resultSizeEstimate', 0)
            
            return {
                "success": True,
                "unread_count": total_results,
                "label": label
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_label(self, name: str, query: str = None) -> Dict[str, Any]:
        """Create a new label"""
        self._ensure_service()
        
        try:
            label = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            if query:
                label['filter'] = {
                    'query': query
                }
            
            result = self.service.users().labels().create(
                userId='me',
                body=label
            ).execute()
            
            return {
                "success": True,
                "label_id": result['id'],
                "label_name": result['name']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_labels(self) -> Dict[str, Any]:
        """Get all labels"""
        self._ensure_service()
        
        try:
            results = self.service.users().labels().list(userId='me').execute()
            
            return {
                "success": True,
                "labels": results.get('labels', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_email(self, message_id: str) -> Dict[str, Any]:
        """Delete an email (move to trash)"""
        self._ensure_service()
        
        try:
            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            
            return {
                "success": True,
                "message_id": message_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_send_emails(self, recipients: List[Dict[str, str]], 
                          subject: str, body: str) -> Dict[str, Any]:
        """Send the same email to multiple recipients"""
        results = []
        
        for recipient in recipients:
            result = self.send_email(
                to=recipient['email'],
                subject=subject,
                body=body,
                cc=recipient.get('cc'),
                bcc=recipient.get('bcc')
            )
            results.append({
                "email": recipient['email'],
                "result": result
            })
        
        successful = sum(1 for r in results if r['result']['success'])
        
        return {
            "success": True,
            "sent": successful,
            "total": len(recipients),
            "results": results
        }


# Convenience functions
def send_email(user_id: str, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
    """Send an email"""
    service = GmailService(user_id)
    return service.send_email(to, subject, body, **kwargs)


def read_emails(user_id: str, query: str = "", max_results: int = 10) -> Dict[str, Any]:
    """Read emails"""
    service = GmailService(user_id)
    return service.read_emails(query, max_results)
