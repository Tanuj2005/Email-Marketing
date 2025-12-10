from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from ..utils.oauth import oauth_manager
from ..utils.sheets import sheets_service
from ..utils.scraper import scraper_service
from ..utils.gemini_service import gemini_service
from ..utils.gmail_service import gmail_service
from ..utils.config import FRONTEND_URL, SESSION_COOKIE_NAME, SESSION_COOKIE_MAX_AGE
from ..models.sheets import (
    SheetDataRequest, SheetDataResponse, SheetInfoResponse,
    ScrapeRequest, ScrapeResponse, ScrapedWebsiteData,
    EmailCampaignRequest, EmailCampaignResponse,
)
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_session(request: Request) -> str:
    """Dependency to get current session ID"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="No session found")
    return session_id

# ... existing endpoints remain the same ...

# Keep all existing endpoints below...
@router.get("/login")
async def login():
    """Generate OAuth authorization URL"""
    try:
        auth_url, state = oauth_manager.generate_auth_url()
        return JSONResponse({
            "auth_url": auth_url,
            "state": state
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@router.get("/callback")
async def oauth_callback(request: Request, response: Response):
    """Handle OAuth callback and create session"""
    try:
        # Get query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        # Check for OAuth errors
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state parameter")
        
        # Validate CSRF state
        if not oauth_manager.validate_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Exchange code for tokens
        tokens = await oauth_manager.exchange_code_for_tokens(code)
        
        # Get user info
        user_info = await oauth_manager.get_user_info(tokens['access_token'])
        user_email = user_info['email']
        
        # Store tokens and create session
        session_id = await oauth_manager.store_tokens_and_create_session(tokens, user_email)
        
        # Create secure session cookie
        response = RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            max_age=SESSION_COOKIE_MAX_AGE,
            httponly=True,
            secure=False,  # Set to False for localhost development
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(url=f"{FRONTEND_URL}/error?message={str(e)}")

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    try:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id:
            # Invalidate session in database using the proper method
            from ..utils.database import db
            await db.deactivate_session(session_id)
        
        # Clear cookie
        response = JSONResponse({"message": "Logged out successfully"})
        response.delete_cookie(key=SESSION_COOKIE_NAME)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info from session"""
    try:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id:
            raise HTTPException(status_code=401, detail="No session found")
        
        session_info = await oauth_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        return {
            "user_id": session_info['user_id'],
            "email": session_info['email'],
            "session_id": session_info['session_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")

@router.post("/sheets/data", response_model=SheetDataResponse)
async def get_sheet_data(
    request_data: SheetDataRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Retrieve data from Google Sheets
    
    This endpoint fetches data from a Google Spreadsheet using the user's access token.
    The access token is automatically refreshed if it has expired.
    """
    try:
        # Get valid access token (will refresh if needed)
        access_token = await oauth_manager.get_valid_access_token(session_id)
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Unable to get valid access token. Please re-authenticate."
            )
        
        # Fetch sheet data
        sheet_data = await sheets_service.get_sheet_data(
            access_token=access_token,
            spreadsheet_id=request_data.spreadsheet_id,
            range_name=request_data.range_name,
            max_rows=request_data.max_rows
        )
        
        return SheetDataResponse(**sheet_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sheet data: {str(e)}")

@router.get("/sheets/{spreadsheet_id}/info", response_model=SheetInfoResponse)
async def get_sheet_info(
    spreadsheet_id: str,
    session_id: str = Depends(get_current_session)
):
    """
    Get information about a Google Spreadsheet
    
    This endpoint fetches metadata about a Google Spreadsheet including
    title, sheets, and basic properties.
    """
    try:
        # Get valid access token (will refresh if needed)
        access_token = await oauth_manager.get_valid_access_token(session_id)
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Unable to get valid access token. Please re-authenticate."
            )
        
        # Fetch sheet info
        sheet_info = await sheets_service.get_sheet_info(
            access_token=access_token,
            spreadsheet_id=spreadsheet_id
        )
        
        return SheetInfoResponse(**sheet_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sheet info: {str(e)}")

# New scraping endpoints
@router.post("/sheets/scrape", response_model=ScrapeResponse)
async def scrape_websites_from_sheet(
    request_data: ScrapeRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Scrape websites from URLs in a Google Sheet column
    
    This endpoint:
    1. Fetches data from the specified Google Sheet
    2. Extracts URLs from the specified column
    3. Scrapes each website concurrently
    4. Returns structured data from all websites
    """
    try:
        start_time = time.time()
        
        # Get valid access token
        access_token = await oauth_manager.get_valid_access_token(session_id)
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Unable to get valid access token. Please re-authenticate."
            )
        
        # Fetch sheet data
        sheet_data = await sheets_service.get_sheet_data(
            access_token=access_token,
            spreadsheet_id=request_data.spreadsheet_id,
            range_name=request_data.range_name
        )
        
        if not sheet_data.get("values"):
            raise HTTPException(status_code=400, detail="No data found in the specified range")
        
        # Find the column index for the URL column
        headers = sheet_data["values"][0] if sheet_data["values"] else []
        url_column_index = None
        
        for i, header in enumerate(headers):
            if str(header).strip().lower() == request_data.url_column_name.strip().lower():
                url_column_index = i
                break
        
        if url_column_index is None:
            raise HTTPException(
                status_code=400, 
                detail=f"Column '{request_data.url_column_name}' not found. Available columns: {headers}"
            )
        
        # Extract URLs from the specified column
        urls = []
        for row_index, row in enumerate(sheet_data["values"][1:], start=1):  # Skip header row
            if url_column_index < len(row) and row[url_column_index]:
                url = str(row[url_column_index]).strip()
                if url:
                    urls.append(url)
        
        if not urls:
            raise HTTPException(
                status_code=400, 
                detail=f"No URLs found in column '{request_data.url_column_name}'"
            )
        
        # Scrape all websites
        scraped_results = await scraper_service.scrape_multiple_websites(
            urls=urls,
            max_concurrent=request_data.max_concurrent
        )
        
        # Convert to response format
        scraped_data = []
        successful_scrapes = 0
        failed_scrapes = 0
        
        for result in scraped_results:
            scraped_data.append(ScrapedWebsiteData(**result))
            if result.get("success"):
                successful_scrapes += 1
            else:
                failed_scrapes += 1
        
        processing_time = time.time() - start_time
        
        return ScrapeResponse(
            spreadsheet_id=request_data.spreadsheet_id,
            spreadsheet_title=sheet_data.get("spreadsheet_title", "Unknown"),
            url_column_name=request_data.url_column_name,
            total_urls=len(urls),
            successful_scrapes=successful_scrapes,
            failed_scrapes=failed_scrapes,
            scraped_data=scraped_data,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape websites: {str(e)}")

@router.post("/scrape/single")
async def scrape_single_website(
    url: str,
    session_id: str = Depends(get_current_session)
):
    """
    Scrape a single website
    
    This endpoint scrapes a single website and returns structured data.
    Useful for testing or one-off scraping.
    """
    try:
        # Verify user is authenticated
        access_token = await oauth_manager.get_valid_access_token(session_id)
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Unable to get valid access token. Please re-authenticate."
            )
        
        # Scrape the website
        scraped_result = await scraper_service.scrape_website(url)
        
        return ScrapedWebsiteData(**scraped_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape website: {str(e)}")
    


@router.post("/campaign/send", response_model=EmailCampaignResponse)
async def send_email_campaign(
    request_data: EmailCampaignRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Complete email campaign workflow:
    1. Fetch contacts from Google Sheets (email_id, company_name, website_link)
    2. Scrape each website for business information
    3. Generate personalized emails using Gemini AI
    4. Send emails via Gmail API
    
    This is the main endpoint for running a hyper-personalized email campaign.
    """
    try:
        start_time = time.time()
        logger.info(f"Starting email campaign for spreadsheet: {request_data.spreadsheet_id}")
        
        # Step 1: Get valid access token
        access_token = await oauth_manager.get_valid_access_token(session_id)
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Unable to get valid access token. Please re-authenticate."
            )
        
        # Step 2: Fetch sheet data
        logger.info("Fetching contact data from Google Sheets...")
        sheet_data = await sheets_service.get_sheet_data(
            access_token=access_token,
            spreadsheet_id=request_data.spreadsheet_id,
            range_name=request_data.range_name
        )
        
        if not sheet_data.get("values") or len(sheet_data["values"]) < 2:
            raise HTTPException(
                status_code=400, 
                detail="No data found in the specified range or missing header row"
            )
        
        # Step 3: Parse headers and extract contact data
        headers = sheet_data["values"][0]
        logger.info(f"Sheet headers: {headers}")
        
        # Find column indices
        email_col_idx = None
        company_col_idx = None
        website_col_idx = None
        
        for i, header in enumerate(headers):
            header_lower = str(header).strip().lower()
            if header_lower == request_data.email_column.lower():
                email_col_idx = i
            elif header_lower == request_data.company_column.lower():
                company_col_idx = i
            elif header_lower == request_data.website_column.lower():
                website_col_idx = i
        
        if email_col_idx is None or company_col_idx is None or website_col_idx is None:
            raise HTTPException(
                status_code=400,
                detail=f"Required columns not found. Available: {headers}. Looking for: {request_data.email_column}, {request_data.company_column}, {request_data.website_column}"
            )
        
        # Extract contact data
        contacts = []
        for row_idx, row in enumerate(sheet_data["values"][1:], start=2):
            if len(row) > max(email_col_idx, company_col_idx, website_col_idx):
                email = str(row[email_col_idx]).strip() if row[email_col_idx] else None
                company = str(row[company_col_idx]).strip() if row[company_col_idx] else None
                website = str(row[website_col_idx]).strip() if row[website_col_idx] else None
                
                if email and company and website:
                    contacts.append({
                        "email": email,
                        "company_name": company,
                        "website_url": website,
                        "row_number": row_idx
                    })
        
        if not contacts:
            raise HTTPException(
                status_code=400,
                detail="No valid contacts found with all required fields (email, company, website)"
            )
        
        logger.info(f"Found {len(contacts)} valid contacts")
        
        # Step 4: Scrape websites
        logger.info("Scraping websites...")
        urls_to_scrape = [contact["website_url"] for contact in contacts]
        scraped_results = await scraper_service.scrape_multiple_websites(
            urls=urls_to_scrape,
            max_concurrent=request_data.max_concurrent_scrapes
        )
        
        # Match scraped data with contacts
        for i, contact in enumerate(contacts):
            contact["website_data"] = scraped_results[i]
        
        # Step 5: Generate personalized emails using Gemini AI
        logger.info("Generating personalized emails with AI...")
        email_generation_tasks = []
        
        for contact in contacts:
            if contact["website_data"].get("success"):
                email_data = await gemini_service.generate_personalized_email(
                    recipient_email=contact["email"],
                    company_name=contact["company_name"],
                    website_data=contact["website_data"],
                    email_purpose=request_data.campaign_purpose
                )
                contact["email_content"] = email_data
            else:
                # Fallback email if scraping failed
                contact["email_content"] = {
                    "subject": f"Exploring partnership opportunities with {contact['company_name']}",
                    "body": f"Hi,\n\nI came across {contact['company_name']} and would love to discuss potential collaboration opportunities.\n\nWould you be open to a brief conversation?\n\nBest regards",
                    "generated_successfully": False,
                    "error": "Website scraping failed"
                }
        
        logger.info(f"Generated {len(contacts)} personalized emails")
        
        # Step 6: Send emails via Gmail
        logger.info("Sending emails...")
        emails_to_send = []
        
        for contact in contacts:
            emails_to_send.append({
                "to": contact["email"],
                "subject": contact["email_content"]["subject"],
                "body": contact["email_content"]["body"]
            })
        
        send_results = await gmail_service.send_bulk_emails(
            access_token=access_token,
            emails=emails_to_send,
            max_concurrent=request_data.max_concurrent_emails,
            delay_between_batches=request_data.delay_between_emails
        )
        
        # Step 7: Compile detailed results
        detailed_results = []
        
        for i, contact in enumerate(contacts):
            send_result = send_results["results"][i]
            
            detailed_results.append({
                "row_number": contact["row_number"],
                "email": contact["email"],
                "company_name": contact["company_name"],
                "website_url": contact["website_url"],
                "website_scraped": contact["website_data"].get("success", False),
                "email_generated": contact["email_content"].get("generated_successfully", False),
                "email_sent": send_result.get("success", False),
                "subject": contact["email_content"]["subject"],
                "message_id": send_result.get("message_id"),
                "error": send_result.get("error") or contact["website_data"].get("error")
            })
        
        processing_time = time.time() - start_time
        
        logger.info(f"Campaign completed in {processing_time:.2f}s. Success: {send_results['successful']}, Failed: {send_results['failed']}")
        
        return EmailCampaignResponse(
            spreadsheet_id=request_data.spreadsheet_id,
            spreadsheet_title=sheet_data.get("spreadsheet_title", "Unknown"),
            campaign_purpose=request_data.campaign_purpose,
            total_contacts=len(contacts),
            emails_generated=len([c for c in contacts if c["email_content"].get("generated_successfully")]),
            emails_sent_successfully=send_results["successful"],
            emails_failed=send_results["failed"],
            processing_time_seconds=round(processing_time, 2),
            detailed_results=detailed_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in email campaign: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute email campaign: {str(e)}"
        )


