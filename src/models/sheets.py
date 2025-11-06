from pydantic import BaseModel, Field, EmailStr
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

# Scraping models
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
    business_info: Dict[str, Union[str, bool, int, float]]
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

# Email Campaign models
class EmailCampaignRequest(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Spreadsheet ID containing contact data")
    range_name: str = Field(default="Sheet1", description="Sheet range to read")
    email_column: str = Field(default="email_id", description="Column name for email addresses")
    company_column: str = Field(default="company_name", description="Column name for company names")
    website_column: str = Field(default="website_link", description="Column name for website URLs")
    campaign_purpose: str = Field(default="business outreach", description="Purpose of the email campaign")
    max_concurrent_scrapes: int = Field(default=5, ge=1, le=10)
    max_concurrent_emails: int = Field(default=3, ge=1, le=5)
    delay_between_emails: float = Field(default=1.0, ge=0.5, le=5.0)

class EmailGenerationResult(BaseModel):
    recipient_email: EmailStr
    company_name: str
    subject: str
    body: str
    generated_successfully: bool
    error: Optional[str] = None

class EmailSendResult(BaseModel):
    recipient_email: EmailStr
    company_name: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class EmailCampaignResponse(BaseModel):
    spreadsheet_id: str
    spreadsheet_title: str
    campaign_purpose: str
    total_contacts: int
    emails_generated: int
    emails_sent_successfully: int
    emails_failed: int
    processing_time_seconds: float
    detailed_results: List[Dict[str, Any]]