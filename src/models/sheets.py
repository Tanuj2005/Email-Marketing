from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union

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

# New models for web scraping
class ScrapeRequest(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Spreadsheet ID")
    range_name: str = Field(default="Sheet1", description="Range to read")
    url_column_name: str = Field(..., description="Name of the column containing website URLs")
    max_concurrent: Optional[int] = Field(default=5, description="Maximum concurrent scraping requests", ge=1, le=10)

class ScrapedWebsiteData(BaseModel):
    url: str
    original_url: str
    title: str
    description: str
    keywords: List[str]
    headings: Dict[str, List[str]]
    main_content: str
    contact_info: Dict[str, List[str]]
    social_links: List[str]
    business_info: Dict[str, Union[str, bool, int, float]]  # Allow mixed types
    technologies: List[str]
    success: bool
    scraped_at: str
    error: Optional[str] = None

class ScrapeResponse(BaseModel):
    spreadsheet_id: str
    spreadsheet_title: str
    url_column_name: str
    total_urls: int
    successful_scrapes: int
    failed_scrapes: int
    scraped_data: List[ScrapedWebsiteData]
    processing_time_seconds: float