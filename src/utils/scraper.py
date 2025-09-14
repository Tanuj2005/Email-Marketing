import httpx
import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class WebScraperService:
    def __init__(self):
        self.session_timeout = 30
        self.max_content_length = 1000000  # 1MB limit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single website and extract key information
        
        Args:
            url: The website URL to scrape
            
        Returns:
            Dictionary containing scraped data
        """
        try:
            # Validate and clean URL
            cleaned_url = self._clean_url(url)
            if not cleaned_url:
                return {"url": url, "error": "Invalid URL format", "success": False}

            async with httpx.AsyncClient(timeout=self.session_timeout, headers=self.headers) as client:
                response = await client.get(cleaned_url, follow_redirects=True)
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_content_length:
                    return {"url": url, "error": "Content too large", "success": False}
                
                response.raise_for_status()
                
                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract structured data
                scraped_data = {
                    "url": cleaned_url,
                    "original_url": url,
                    "title": self._extract_title(soup),
                    "description": self._extract_description(soup),
                    "keywords": self._extract_keywords(soup),
                    "headings": self._extract_headings(soup),
                    "main_content": self._extract_main_content(soup),
                    "contact_info": self._extract_contact_info(soup),
                    "social_links": self._extract_social_links(soup),
                    "business_info": self._extract_business_info(soup),
                    "technologies": self._extract_technologies(soup),
                    "success": True,
                    "scraped_at": self._get_current_timestamp()
                }
                
                return scraped_data
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping {url}")
            return {"url": url, "error": "Request timeout", "success": False}
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
            return {"url": url, "error": f"HTTP {e.response.status_code}", "success": False}
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"url": url, "error": str(e), "success": False}

    async def scrape_multiple_websites(self, urls: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple websites concurrently
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of dictionaries containing scraped data
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.scrape_website(url)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate URL"""
        if not url or not isinstance(url, str):
            return None
            
        url = url.strip()
        if not url:
            return None
            
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return url
        except Exception:
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title = soup.find('title')
        return title.get_text().strip() if title else ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        description = soup.find('meta', attrs={'name': 'description'}) or \
                     soup.find('meta', attrs={'property': 'og:description'})
        return description.get('content', '').strip() if description else ""

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract meta keywords"""
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            return [k.strip() for k in keywords.get('content', '').split(',') if k.strip()]
        return []

    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract headings (H1-H6)"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            if h_tags:
                headings[f'h{i}'] = [h.get_text().strip() for h in h_tags[:5]]  # Limit to 5 per level
        return headings

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Remove script, style, and other non-content elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = soup.find('main') or soup.find('article') or \
                      soup.find('div', class_=re.compile(r'content|main', re.I)) or \
                      soup.find('body')
        
        if main_content:
            text = main_content.get_text()
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            # Limit content length
            return text[:2000] if text else ""
        return ""

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract contact information"""
        contact_info = {"emails": [], "phones": []}
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        contact_info["emails"] = list(set(emails))[:5]  # Limit and deduplicate
        
        # Extract phone numbers
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        contact_info["phones"] = list(set([''.join(phone) for phone in phones]))[:5]
        
        return contact_info

    def _extract_social_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract social media links"""
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 
                         'youtube.com', 'tiktok.com', 'pinterest.com']
        
        social_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(domain in href.lower() for domain in social_domains):
                social_links.append(href)
        
        return list(set(social_links))[:10]  # Limit and deduplicate

    def _extract_business_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract business-specific information"""
        business_info = {}
        
        # Look for schema.org structured data
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and data.get('@type') in ['Organization', 'LocalBusiness']:
                    business_info['name'] = data.get('name', '')
                    business_info['description'] = data.get('description', '')
                    business_info['industry'] = data.get('@type', '')
            except:
                pass
        
        # Look for common business indicators
        text_lower = soup.get_text().lower()
        if any(word in text_lower for word in ['about us', 'our company', 'our mission']):
            business_info['has_about_section'] = True
            
        if any(word in text_lower for word in ['services', 'products', 'solutions']):
            business_info['has_services_section'] = True
            
        return business_info

    def _extract_technologies(self, soup: BeautifulSoup) -> List[str]:
        """Extract technologies used on the website"""
        technologies = []
        
        # Check for common frameworks and libraries
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script['src'].lower()
            if 'jquery' in src:
                technologies.append('jQuery')
            elif 'react' in src:
                technologies.append('React')
            elif 'angular' in src:
                technologies.append('Angular')
            elif 'vue' in src:
                technologies.append('Vue.js')
        
        # Check meta tags for generator
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator:
            technologies.append(generator.get('content', ''))
        
        return list(set(technologies))

    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

scraper_service = WebScraperService()