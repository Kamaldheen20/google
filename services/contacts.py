"""
Google Contacts Service
Provides integration with Google People API for contact management
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class ContactsService:
    """Google People API Service for Contacts"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('people', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Contacts")
    
    def list_connections(self, max_results: int = 100,
                         page_token: str = None) -> Dict[str, Any]:
        """List all contacts"""
        self._ensure_service()
        
        try:
            result = self.service.people().connections().list(
                resourceName='people/me',
                pageSize=max_results,
                pageToken=page_token,
                personFields='names,emailAddresses,phoneNumbers,organizations'
            ).execute()
            
            connections = result.get('connections', [])
            
            contacts = []
            for person in connections:
                contact = {'resourceName': person.get('resourceName')}
                
                # Names
                if 'names' in person and person['names']:
                    contact['display_name'] = person['names'][0].get('displayName')
                    contact['given_name'] = person['names'][0].get('givenName')
                    contact['family_name'] = person['names'][0].get('familyName')
                
                # Email
                if 'emailAddresses' in person and person['emailAddresses']:
                    contact['email'] = person['emailAddresses'][0].get('value')
                
                # Phone
                if 'phoneNumbers' in person and person['phoneNumbers']:
                    contact['phone'] = person['phoneNumbers'][0].get('value')
                
                # Organization
                if 'organizations' in person and person['organizations']:
                    contact['company'] = person['organizations'][0].get('name')
                    contact['title'] = person['organizations'][0].get('title')
                
                contacts.append(contact)
            
            return {
                "success": True,
                "contacts": contacts,
                "next_page_token": result.get('nextPageToken'),
                "total": len(contacts)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_contacts(self, query: str,
                        max_results: int = 50) -> Dict[str, Any]:
        """Search contacts"""
        self._ensure_service()
        
        try:
            result = self.service.people().searchContacts(
                query=query,
                pageSize=max_results,
                personFields='names,emailAddresses,phoneNumbers'
            ).execute()
            
            results = result.get('results', [])
            
            contacts = []
            for r in results:
                person = r.get('person', {})
                contact = {}
                
                if 'names' in person and person['names']:
                    contact['name'] = person['names'][0].get('displayName')
                if 'emailAddresses' in person and person['emailAddresses']:
                    contact['email'] = person['emailAddresses'][0].get('value')
                if 'phoneNumbers' in person and person['phoneNumbers']:
                    contact['phone'] = person['phoneNumbers'][0].get('value')
                
                contacts.append(contact)
            
            return {
                "success": True,
                "contacts": contacts,
                "total": len(contacts)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_contact(self, resource_name: str) -> Dict[str, Any]:
        """Get a specific contact"""
        self._ensure_service()
        
        try:
            result = self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,organizations,addresses'
            ).execute()
            
            return {
                "success": True,
                "contact": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_contact(self, name: str,
                       email: str = None,
                       phone: str = None) -> Dict[str, Any]:
        """Create a new contact"""
        self._ensure_service()
        
        try:
            body = {
                'names': [{'displayName': name}],
                'emailAddresses': [{'value': email}] if email else [],
                'phoneNumbers': [{'value': phone}] if phone else []
            }
            
            result = self.service.people().createContact(
                body=body,
                personFields='names,emailAddresses,phoneNumbers'
            ).execute()
            
            return {
                "success": True,
                "resource_name": result.get('resourceName'),
                "name": name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_contact(self, resource_name: str,
                       name: str = None,
                       email: str = None,
                       phone: str = None) -> Dict[str, Any]:
        """Update a contact"""
        self._ensure_service()
        
        try:
            # Get current contact
            current = self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers'
            ).execute()
            
            # Build update
            body = {
                'resourceName': resource_name,
                'etag': current.get('etag')
            }
            
            if name:
                body['names'] = [{'displayName': name}]
            if email:
                body['emailAddresses'] = [{'value': email}]
            if phone:
                body['phoneNumbers'] = [{'value': phone}]
            
            result = self.service.people().updateContact(
                resourceName=resource_name,
                body=body,
                updatePersonFields='names,emailAddresses,phoneNumbers'
            ).execute()
            
            return {
                "success": True,
                "resource_name": result.get('resourceName'),
                "updated": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_contact(self, resource_name: str) -> Dict[str, Any]:
        """Delete a contact"""
        self._ensure_service()
        
        try:
            self.service.people().deleteContact(
                resourceName=resource_name
            ).execute()
            
            return {
                "success": True,
                "resource_name": resource_name,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def list_contacts(user_id: str, max_results: int = 100) -> Dict[str, Any]:
    """List all contacts"""
    service = ContactsService(user_id)
    return service.list_connections(max_results)


def search_contacts(user_id: str, query: str,
                    max_results: int = 50) -> Dict[str, Any]:
    """Search contacts"""
    service = ContactsService(user_id)
    return service.search_contacts(query, max_results)


def create_contact(user_id: str, name: str,
                   email: str = None, phone: str = None) -> Dict[str, Any]:
    """Create a new contact"""
    service = ContactsService(user_id)
    return service.create_contact(name, email, phone)
