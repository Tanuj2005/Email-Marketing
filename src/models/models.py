from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any, Dict, Union

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