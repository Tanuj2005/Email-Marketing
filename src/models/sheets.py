from pydantic import BaseModel, Field
from typing import List, Optional, Any

class SheetDataRequest(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Spreadsheet ID")
    range_name: str = Field(default="Sheet1", description="Range to read (e.g., 'Sheet1', 'A1:C10')")
    max_rows: Optional[int] = Field(default=None, description="Maximum number of rows to retrieve", ge=1, le=10000)

class SheetDataResponse(BaseModel):
    spreadsheet_id: str
    spreadsheet_title: str
    range: str
    values: List[List[Any]]
    row_count: int
    column_count: int

class SheetInfoResponse(BaseModel):
    spreadsheet_id: str
    title: str
    locale: str
    sheets: List[dict]

class ErrorResponse(BaseModel):
    error: str
    detail: str