"""
Google Sheets Service
Provides integration with Google Sheets API for spreadsheet management
"""

from typing import Optional, List, Dict, Any
import re

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class SheetsService:
    """Google Sheets API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('sheets', 'v4', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Sheets")
    
    def create_spreadsheet(self, title: str,
                          sheet_name: str = "Sheet1") -> Dict[str, Any]:
        """Create a new spreadsheet"""
        self._ensure_service()
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': sheet_name
                    }
                }]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            
            return {
                "success": True,
                "spreadsheet_id": result['spreadsheetId'],
                "title": result['properties']['title'],
                "url": result['spreadsheetUrl']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_spreadsheet(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Get spreadsheet metadata"""
        self._ensure_service()
        
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            return {
                "success": True,
                "spreadsheet_id": result['spreadsheetId'],
                "title": result['properties']['title'],
                "sheets": [s['properties'] for s in result.get('sheets', [])]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_range(self, spreadsheet_id: str,
                   range_: str,
                   value_render: str = 'UNFORMATTED_VALUE') -> Dict[str, Any]:
        """Read data from a range"""
        self._ensure_service()
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueRenderOption=value_render
            ).execute()
            
            values = result.get('values', [])
            
            return {
                "success": True,
                "range": range_,
                "values": values,
                "row_count": len(values),
                "column_count": len(values[0]) if values else 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_range(self, spreadsheet_id: str,
                    range_: str,
                    values: List[List[Any]],
                    input_option: str = 'RAW') -> Dict[str, Any]:
        """Write data to a range"""
        self._ensure_service()
        
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption=input_option,
                body=body
            ).execute()
            
            return {
                "success": True,
                "updated_cells": result.get('updatedCells'),
                "updated_range": result.get('updatedRange')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def append_row(self, spreadsheet_id: str,
                   range_: str,
                   values: List[Any]) -> Dict[str, Any]:
        """Append a row to the sheet"""
        self._ensure_service()
        
        try:
            body = {
                'values': [values]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return {
                "success": True,
                "updated_range": result.get('updates', {}).get('updatedRange')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_range(self, spreadsheet_id: str,
                    range_: str) -> Dict[str, Any]:
        """Clear a range"""
        self._ensure_service()
        
        try:
            result = self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_
            ).execute()
            
            return {
                "success": True,
                "cleared_range": result.get('clearedRange')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_update(self, spreadsheet_id: str,
                    requests: List[Dict]) -> Dict[str, Any]:
        """Batch update spreadsheet"""
        self._ensure_service()
        
        try:
            body = {'requests': requests}
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return {
                "success": True,
                "replies": result.get('replies', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_cell(self, spreadsheet_id: str,
                    sheet_name: str,
                    row: int,
                    col: int,
                    value: Any) -> Dict[str, Any]:
        """Update a single cell"""
        self._ensure_service()
        
        range_ = f"{sheet_name}!{self._col_letter(col)}{row}"
        return self.write_range(spreadsheet_id, range_, [[value]])
    
    def _col_letter(self, col: int) -> str:
        """Convert column number to letter"""
        result = ""
        while col > 0:
            col -= 1
            result = chr(col % 26 + 65) + result
            col //= 26
        return result
    
    def read_all(self, spreadsheet_id: str,
                sheet_name: str = None) -> Dict[str, Any]:
        """Read all data from a sheet"""
        self._ensure_service()
        
        try:
            # Get sheet name if not provided
            if sheet_name is None:
                spreadsheet = self.get_spreadsheet(spreadsheet_id)
                if spreadsheet['success']:
                    sheet_name = spreadsheet['sheets'][0]['title']
                else:
                    return spreadsheet
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            
            return {
                "success": True,
                "sheet_name": sheet_name,
                "values": result.get('values', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_from_data(self, title: str,
                        data: List[List[Any]],
                        headers: List[str] = None) -> Dict[str, Any]:
        """Create spreadsheet from data"""
        self._ensure_service()
        
        try:
            # Create spreadsheet
            result = self.create_spreadsheet(title)
            if not result['success']:
                return result
            
            spreadsheet_id = result['spreadsheet_id']
            
            # Prepare values
            values = data
            if headers:
                values = [headers] + data
            
            # Write data
            write_result = self.write_range(
                spreadsheet_id,
                'A1',
                values
            )
            
            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "url": result['url'],
                "cells_written": write_result.get('updatedCells', 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def find_replace(self, spreadsheet_id: str,
                    find: str,
                    replace: str,
                    all_sheets: bool = True) -> Dict[str, Any]:
        """Find and replace text"""
        self._ensure_service()
        
        request = {
            'findReplace': {
                'find': find,
                'replacement': replace,
                'allSheets': all_sheets
            }
        }
        
        return self.batch_update(spreadsheet_id, [request])
    
    def add_formula(self, spreadsheet_id: str,
                   range_: str,
                   formula: str) -> Dict[str, Any]:
        """Add a formula to a cell/range"""
        self._ensure_service()
        
        return self.write_range(spreadsheet_id, range_, [[formula]], input_option='USER_ENTERED')
    
    def get_chart(self, spreadsheet_id: str,
                 sheet_id: int,
                 chart_id: int) -> Dict[str, Any]:
        """Get chart metadata"""
        self._ensure_service()
        
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['sheetId'] == sheet_id:
                    charts = sheet.get('charts', [])
                    for chart in charts:
                        if chart['chartId'] == chart_id:
                            return {
                                "success": True,
                                "chart": chart
                            }
            
            return {
                "success": False,
                "error": "Chart not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def share_spreadsheet(self, spreadsheet_id: str,
                         email: str,
                         role: str = 'reader') -> Dict[str, Any]:
        """Share spreadsheet with someone"""
        self._ensure_service()
        
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [{
                    'addPermission': permission
                }]}
            ).execute()
            
            return {
                "success": True,
                "shared_with": email
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def create_spreadsheet(user_id: str, title: str) -> Dict[str, Any]:
    """Create a new spreadsheet"""
    service = SheetsService(user_id)
    return service.create_spreadsheet(title)


def read_range(user_id: str, spreadsheet_id: str, range_: str) -> Dict[str, Any]:
    """Read data from a range"""
    service = SheetsService(user_id)
    return service.read_range(spreadsheet_id, range_)


def write_range(user_id: str, spreadsheet_id: str, range_: str, values: List[List[Any]]) -> Dict[str, Any]:
    """Write data to a range"""
    service = SheetsService(user_id)
    return service.write_range(spreadsheet_id, range_, values)
