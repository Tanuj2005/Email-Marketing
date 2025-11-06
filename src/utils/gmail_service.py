import httpx
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.gmail_api_base = "https://gmail.googleapis.com/gmail/v1/users/me"
    
    async def send_email(
        self,
        access_token: str,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send an email using Gmail API
        
        Args:
            access_token: Valid Google access token with Gmail send scope
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_email: Sender email (optional, defaults to authenticated user)
            
        Returns:
            Dictionary with send result
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            if from_email:
                message['From'] = from_email
            message['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "raw": raw_message
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.gmail_api_base}/messages/send",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "message_id": result.get('id'),
                    "thread_id": result.get('threadId'),
                    "to": to_email,
                    "subject": subject
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending email to {to_email}: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "to": to_email,
                "subject": subject
            }
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email,
                "subject": subject
            }
    
    async def send_bulk_emails(
        self,
        access_token: str,
        emails: List[Dict[str, str]],
        max_concurrent: int = 3,
        delay_between_batches: float = 1.0
    ) -> Dict[str, any]:
        """
        Send multiple emails with rate limiting
        
        Args:
            access_token: Valid Google access token
            emails: List of dicts with 'to', 'subject', 'body'
            max_concurrent: Maximum concurrent send operations
            delay_between_batches: Delay in seconds between batches
            
        Returns:
            Dictionary with send statistics and results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def send_with_semaphore(email_data: Dict[str, str]) -> Dict[str, any]:
            async with semaphore:
                result = await self.send_email(
                    access_token=access_token,
                    to_email=email_data['to'],
                    subject=email_data['subject'],
                    body=email_data['body'],
                    from_email=email_data.get('from')
                )
                # Add delay to respect rate limits
                await asyncio.sleep(delay_between_batches)
                return result
        
        # Send all emails concurrently with rate limiting
        tasks = [send_with_semaphore(email) for email in emails]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        failed = 0
        detailed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                detailed_results.append({
                    "to": emails[i]['to'],
                    "success": False,
                    "error": str(result)
                })
            elif result.get('success'):
                successful += 1
                detailed_results.append(result)
            else:
                failed += 1
                detailed_results.append(result)
        
        return {
            "total_emails": len(emails),
            "successful": successful,
            "failed": failed,
            "results": detailed_results
        }

gmail_service = GmailService()