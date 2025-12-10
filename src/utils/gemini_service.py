import google.generativeai as genai
from typing import Dict, Any, Optional
import logging
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Sender/Company Configuration - Update these with your actual details
SENDER_CONFIG = {
    "sender_name": "John Smith",  # Your name
    "sender_title": "Founder & CEO",  # Your title
    "company_name": "GrowthPulse Marketing",  # Your company name
    "company_description": "AI-powered email marketing and lead generation",  # What you do
    "company_website": "https://growthpulse.io",  # Your website
    "value_proposition": "We help B2B companies increase their email response rates by 3x using AI-driven personalization and data-backed outreach strategies.",
    "services": [
        "AI-Powered Email Campaigns",
        "Lead Generation & Qualification", 
        "Marketing Automation",
        "Conversion Rate Optimization"
    ]
}

class GeminiAIService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.sender_config = SENDER_CONFIG
    
    async def generate_personalized_email(
        self,
        recipient_email: str,
        company_name: str,
        website_data: Dict[str, Any],
        email_purpose: str = "business outreach",
        sender_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate a hyper-personalized email using Gemini AI
        
        Args:
            recipient_email: Recipient's email address
            company_name: Company name
            website_data: Scraped website data containing business information
            email_purpose: Purpose of the email (default: "business outreach")
            sender_config: Optional sender configuration override
            
        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        try:
            # Use provided sender config or default
            sender = sender_config or self.sender_config
            
            # Extract key information from scraped data
            website_title = website_data.get('title', '')
            website_description = website_data.get('description', '')
            main_content = website_data.get('main_content', '')[:1000]  # Limit content
            business_info = website_data.get('business_info', {})
            services_info = "services section present" if business_info.get('has_services_section') else "no services section"
            
            # Format sender services
            sender_services = ", ".join(sender.get('services', ['marketing services']))
            
            # Create a detailed prompt for Gemini
            prompt = f"""
You are an expert email marketing copywriter specializing in B2B outreach. Generate a highly personalized, engaging email that feels authentic and human-written.

=== SENDER INFORMATION (This is who is sending the email) ===
- Sender Name: {sender.get('sender_name', 'Alex')}
- Sender Title: {sender.get('sender_title', 'Founder')}
- Sender Company: {sender.get('company_name', 'Our Agency')}
- What We Do: {sender.get('company_description', 'Marketing services')}
- Our Services: {sender_services}
- Our Value Proposition: {sender.get('value_proposition', 'We help businesses grow')}

=== RECIPIENT INFORMATION (This is who we are emailing) ===
- Recipient Company: {company_name}
- Website Title: {website_title}
- Company Description: {website_description}
- Key Business Info: {services_info}

=== WEBSITE CONTENT INSIGHTS ===
{main_content}

=== EMAIL REQUIREMENTS ===
1. Purpose: {email_purpose}
2. Tone: Professional yet conversational and warm
3. Length: 150-200 words maximum
4. Personalization: Reference specific details from their website to show genuine research
5. Value Proposition: Focus on how {sender.get('company_name', 'we')} can help their specific business needs
6. Call-to-Action: Clear, non-pushy invitation to connect
7. Subject Line: Attention-grabbing, personalized, under 60 characters

=== CRITICAL INSTRUCTIONS ===
- Use the ACTUAL sender name "{sender.get('sender_name', 'Alex')}" in the signature - DO NOT use placeholders like [Your Name]
- Use the ACTUAL company name "{sender.get('company_name', 'Our Agency')}" - DO NOT use placeholders like [Company Name]
- DO NOT include any placeholders, brackets, or fields to fill in
- DO NOT use generic templates or obvious AI language
- DO reference specific aspects of their business from the website content
- DO show genuine understanding of their industry/services
- DO make it feel like a human took time to research their company
- DO NOT be overly salesy or pushy
- DO NOT use phrases like "I hope this email finds you well" or other clichés
- DO NOT mention that you scraped their website or used AI
- DO NOT include website URLs in the signature (just name and title)
- Focus on building a relationship, not making a sale

=== OUTPUT FORMAT ===
Subject: [Your subject line here]

Body:
[Email body - start directly with the greeting, no "Body:" label in output]

[Sign off with actual name: {sender.get('sender_name', 'Alex')}]
[Title: {sender.get('sender_title', 'Founder')}]
[Company: {sender.get('company_name', 'Our Agency')}]

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
                if line.lower().startswith('subject:'):
                    subject = line.split(':', 1)[1].strip() if ':' in line else line.replace('Subject', '').strip()
                elif line.lower().startswith('body:'):
                    body_started = True
                elif body_started or (subject and not line.lower().startswith('subject:')):
                    if not body_started and subject:
                        body_started = True
                    if body_started:
                        body_lines.append(line)
            
            body = '\n'.join(body_lines).strip()
            
            # Clean up any remaining placeholders (safety net)
            placeholders_to_remove = [
                '[Your Name]', '[My Name]', '[Name]',
                '[Your Title]', '[My Title]', '[Title]',
                '[Your Company]', '[My Company]', '[Company Name]', '[My Agency Name]', '[Agency Name]',
                '[Your Website]', '[My Website]', '[Website]',
                '[Recipient Name]', '[Their Name]',
                '[Your Email]', '[My Email]', '[Email]'
            ]
            
            for placeholder in placeholders_to_remove:
                if placeholder.lower() in body.lower():
                    # Replace with actual values
                    if 'name' in placeholder.lower() and 'recipient' not in placeholder.lower():
                        body = body.replace(placeholder, sender.get('sender_name', ''))
                    elif 'title' in placeholder.lower():
                        body = body.replace(placeholder, sender.get('sender_title', ''))
                    elif 'company' in placeholder.lower() or 'agency' in placeholder.lower():
                        body = body.replace(placeholder, sender.get('company_name', ''))
                    elif 'website' in placeholder.lower():
                        body = body.replace(placeholder, '')  # Remove website placeholders
                    elif 'recipient' in placeholder.lower():
                        body = body.replace(placeholder, '')  # Remove recipient name placeholder
                    else:
                        body = body.replace(placeholder, '')
            
            # Clean up empty lines and extra whitespace
            body = '\n'.join(line for line in body.split('\n') if line.strip() or line == '')
            body = body.strip()
            
            # Fallback if parsing fails
            if not subject:
                subject = f"Quick thought about {company_name}'s growth"
            if not body:
                body = email_text
            
            return {
                "subject": subject,
                "body": body,
                "generated_successfully": True
            }
            
        except Exception as e:
            logger.error(f"Error generating email with Gemini: {str(e)}")
            # Return a fallback email with actual sender info
            sender = sender_config or self.sender_config
            return {
                "subject": f"Quick question about {company_name}",
                "body": f"""Hi,

I came across {company_name} and was impressed by what you're doing. I'd love to explore how we might work together.

Would you be open to a brief conversation?

Best regards,
{sender.get('sender_name', 'Alex')}
{sender.get('sender_title', 'Founder')}
{sender.get('company_name', 'Our Company')}""",
                "generated_successfully": False,
                "error": str(e)
            }
    
    async def generate_multiple_emails(
        self,
        recipients: list[Dict[str, Any]],
        email_purpose: str = "business outreach",
        sender_config: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        Generate personalized emails for multiple recipients
        
        Args:
            recipients: List of dicts with 'email', 'company_name', and 'website_data'
            email_purpose: Purpose of the email campaign
            sender_config: Optional sender configuration override
            
        Returns:
            List of generated email data
        """
        results = []
        
        for recipient in recipients:
            email_data = await self.generate_personalized_email(
                recipient_email=recipient.get('email'),
                company_name=recipient.get('company_name'),
                website_data=recipient.get('website_data', {}),
                email_purpose=email_purpose,
                sender_config=sender_config
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