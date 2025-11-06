import google.generativeai as genai
from typing import Dict, Any, Optional
import logging
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_personalized_email(
        self,
        recipient_email: str,
        company_name: str,
        website_data: Dict[str, Any],
        email_purpose: str = "business outreach"
    ) -> Dict[str, str]:
        """
        Generate a hyper-personalized email using Gemini AI
        
        Args:
            recipient_email: Recipient's email address
            company_name: Company name
            website_data: Scraped website data containing business information
            email_purpose: Purpose of the email (default: "business outreach")
            
        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        try:
            # Extract key information from scraped data
            website_title = website_data.get('title', '')
            website_description = website_data.get('description', '')
            main_content = website_data.get('main_content', '')[:1000]  # Limit content
            business_info = website_data.get('business_info', {})
            services_info = "services section present" if business_info.get('has_services_section') else "no services section"
            
            # Create a detailed prompt for Gemini
            prompt = f"""
You are an expert email marketing copywriter specializing in B2B outreach. Generate a highly personalized, engaging email that feels authentic and human-written.

RECIPIENT INFORMATION:
- Email: {recipient_email}
- Company: {company_name}
- Website Title: {website_title}
- Company Description: {website_description}
- Key Business Info: {services_info}

WEBSITE CONTENT INSIGHTS:
{main_content}

EMAIL REQUIREMENTS:
1. Purpose: {email_purpose}
2. Tone: Professional yet conversational and warm
3. Length: 150-250 words maximum
4. Personalization: Reference specific details from their website to show genuine research
5. Value Proposition: Focus on how we can help their specific business needs
6. Call-to-Action: Clear, non-pushy invitation to connect
7. Subject Line: Attention-grabbing, personalized, under 60 characters

IMPORTANT GUIDELINES:
- DO NOT use generic templates or obvious AI language
- DO reference specific aspects of their business from the website content
- DO show genuine understanding of their industry/services
- DO make it feel like a human took time to research their company
- DO NOT be overly salesy or pushy
- DO NOT use phrases like "I hope this email finds you well" or other clichés
- DO NOT mention that you scraped their website
- Focus on building a relationship, not making a sale

OUTPUT FORMAT:
Subject: [Your subject line here]

Body:
[Your email body here]

Generate the email now:
"""

            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            email_text = response.text
            
            # Parse the response to extract subject and body
            lines = email_text.strip().split('\n')
            subject = ""
            body_lines = []
            body_started = False
            
            for line in lines:
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('Body:'):
                    body_started = True
                elif body_started:
                    body_lines.append(line)
            
            body = '\n'.join(body_lines).strip()
            
            # Fallback if parsing fails
            if not subject:
                subject = f"Thoughts on enhancing {company_name}'s digital presence"
            if not body:
                body = email_text
            
            return {
                "subject": subject,
                "body": body,
                "generated_successfully": True
            }
            
        except Exception as e:
            logger.error(f"Error generating email with Gemini: {str(e)}")
            # Return a fallback email
            return {
                "subject": f"Quick question about {company_name}",
                "body": f"Hi,\n\nI came across {company_name} and was impressed by what you're doing. I'd love to explore how we might work together.\n\nWould you be open to a brief conversation?\n\nBest regards",
                "generated_successfully": False,
                "error": str(e)
            }
    
    async def generate_multiple_emails(
        self,
        recipients: list[Dict[str, Any]],
        email_purpose: str = "business outreach"
    ) -> list[Dict[str, Any]]:
        """
        Generate personalized emails for multiple recipients
        
        Args:
            recipients: List of dicts with 'email', 'company_name', and 'website_data'
            email_purpose: Purpose of the email campaign
            
        Returns:
            List of generated email data
        """
        results = []
        
        for recipient in recipients:
            email_data = await self.generate_personalized_email(
                recipient_email=recipient.get('email'),
                company_name=recipient.get('company_name'),
                website_data=recipient.get('website_data', {}),
                email_purpose=email_purpose
            )
            
            results.append({
                "recipient_email": recipient.get('email'),
                "company_name": recipient.get('company_name'),
                "subject": email_data.get('subject'),
                "body": email_data.get('body'),
                "generated_successfully": email_data.get('generated_successfully', False)
            })
        
        return results

gemini_service = GeminiAIService()