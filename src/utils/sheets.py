import httpx
from typing import List, Dict, Any, Optional
from .config import GOOGLE_SHEETS_API_BASE
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    
    async def get_sheet_data(self, access_token: str, spreadsheet_id: str, 
                           range_name: str = "Sheet1", max_rows: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve data from Google Sheets
        
        Args:
            access_token: Valid Google access token
            spreadsheet_id: The ID of the Google Spreadsheet
            range_name: The range to read (default: "Sheet1")
            max_rows: Maximum number of rows to retrieve
        
        Returns:
            Dictionary containing sheet data and metadata
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Build the API URL with proper range formatting
            if max_rows and ":" not in range_name:
                # If max_rows is specified and range_name is just a sheet name, create proper range
                range_name = f"{range_name}!A1:Z{max_rows}"
            elif max_rows and "!" not in range_name:
                # If range_name contains : but no sheet name, add default sheet
                range_name = f"Sheet1!{range_name}"
            elif "!" not in range_name and ":" not in range_name:
                # If just sheet name without range, use the sheet name as-is
                range_name = f"{range_name}!A:Z"
            
            url = f"{GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}/values/{range_name}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Get spreadsheet metadata
                metadata_url = f"{GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}"
                metadata_response = await client.get(
                    metadata_url, 
                    headers=headers,
                    params={"fields": "properties.title,sheets.properties"}
                )
                metadata_response.raise_for_status()
                metadata = metadata_response.json()
                
                values = data.get("values", [])
                
                # Apply max_rows limit if specified and not already limited by range
                if max_rows and len(values) > max_rows:
                    values = values[:max_rows]
                
                return {
                    "spreadsheet_id": spreadsheet_id,
                    "spreadsheet_title": metadata.get("properties", {}).get("title", "Unknown"),
                    "range": data.get("range", range_name),
                    "values": values,
                    "row_count": len(values),
                    "column_count": len(values[0]) if values else 0
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Access token expired or invalid")
            elif e.response.status_code == 403:
                raise Exception("Access forbidden - check spreadsheet permissions")
            elif e.response.status_code == 404:
                raise Exception("Spreadsheet not found")
            else:
                raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching sheet data: {e}")
            raise Exception(f"Failed to fetch sheet data: {str(e)}")
    
    # ...existing get_sheet_info method remains unchanged...
    async def get_sheet_info(self, access_token: str, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Get basic information about the spreadsheet
        
        Args:
            access_token: Valid Google access token
            spreadsheet_id: The ID of the Google Spreadsheet
        
        Returns:
            Dictionary containing spreadsheet metadata
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"{GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url, 
                    headers=headers,
                    params={"fields": "properties,sheets.properties"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                sheets_info = []
                for sheet in data.get("sheets", []):
                    sheet_props = sheet.get("properties", {})
                    sheets_info.append({
                        "sheet_id": sheet_props.get("sheetId"),
                        "title": sheet_props.get("title"),
                        "sheet_type": sheet_props.get("sheetType", "GRID"),
                        "row_count": sheet_props.get("gridProperties", {}).get("rowCount", 0),
                        "column_count": sheet_props.get("gridProperties", {}).get("columnCount", 0)
                    })
                
                return {
                    "spreadsheet_id": spreadsheet_id,
                    "title": data.get("properties", {}).get("title", "Unknown"),
                    "locale": data.get("properties", {}).get("locale", "en_US"),
                    "sheets": sheets_info
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Access token expired or invalid")
            elif e.response.status_code == 403:
                raise Exception("Access forbidden - check spreadsheet permissions")
            elif e.response.status_code == 404:
                raise Exception("Spreadsheet not found")
            else:
                raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching sheet info: {e}")
            raise Exception(f"Failed to fetch sheet info: {str(e)}")

sheets_service = GoogleSheetsService()