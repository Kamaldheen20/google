"""
Google Translate Service
Provides integration with Google Translate API for text translation
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class TranslateService:
    """Google Translate API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('translate', 'v2', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Translate")
    
    def translate(self, text: str,
                  target_language: str,
                  source_language: str = None) -> Dict[str, Any]:
        """Translate text"""
        self._ensure_service()
        
        try:
            body = {
                'q': text,
                'target': target_language,
                'format': 'text'
            }
            
            if source_language:
                body['source'] = source_language
            
            result = self.service.translations().list(
                q=text,
                target=target_language
            ).execute()
            
            translated_text = result['translations'][0]['translatedText']
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "source_language": result['translations'][0].get('detectedSourceLanguage', source_language),
                "target_language": target_language
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def translate_batch(self, texts: List[str],
                       target_language: str,
                       source_language: str = None) -> Dict[str, Any]:
        """Translate multiple texts"""
        self._ensure_service()
        
        try:
            result = self.service.translations().list(
                q=texts,
                target=target_language
            ).execute()
            
            translations = result.get('translations', [])
            
            return {
                "success": True,
                "translations": [
                    {
                        "original": texts[i],
                        "translated": t['translatedText'],
                        "detected_language": t.get('detectedSourceLanguage')
                    }
                    for i, t in enumerate(translations)
                ],
                "target_language": target_language
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text"""
        self._ensure_service()
        
        try:
            result = self.service.detections().list(q=text).execute()
            
            detection = result['detections'][0][0]
            
            return {
                "success": True,
                "text": text,
                "language": detection['language'],
                "confidence": detection['confidence']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_languages(self, target_language: str = 'en') -> Dict[str, Any]:
        """List supported languages"""
        self._ensure_service()
        
        try:
            result = self.service.languages().list(target=target_language).execute()
            
            languages = result.get('languages', [])
            
            return {
                "success": True,
                "languages": [
                    {
                        "language": lang['language'],
                        "name": lang.get('name')
                    }
                    for lang in languages
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def translate(user_id: str, text: str, target_language: str,
              source_language: str = None) -> Dict[str, Any]:
    """Translate text"""
    service = TranslateService(user_id)
    return service.translate(text, target_language, source_language)


def translate_batch(user_id: str, texts: List[str], target_language: str,
                    source_language: str = None) -> Dict[str, Any]:
    """Translate multiple texts"""
    service = TranslateService(user_id)
    return service.translate_batch(texts, target_language, source_language)
