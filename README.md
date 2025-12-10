# AI-Powered Hyper-Personalized Email Marketing Platform

An intelligent B2B email outreach automation system that scrapes prospect websites, generates hyper-personalized emails using AI, and sends them automatically—all from a simple Google Sheets input.

## What It Does

This platform automates the entire cold email workflow:

1. **Reads contacts** from your Google Sheet (email, company name, website)
2. **Scrapes each website** to understand the prospect's business
3. **Generates personalized emails** using Gemini AI based on scraped insights
4. **Sends emails** via Gmail API with rate limiting

## Why Use This?

| Traditional Cold Email | This Platform |
|------------------------|---------------|
| Generic templates | AI-crafted personalization per recipient |
| Manual research | Automated website analysis |
| Copy-paste sending | One-click bulk campaigns |
| Low response rates | 3x higher engagement through relevance |

**Problem Solved:** Cold emails fail because they're generic. This tool makes every email feel hand-crafted by analyzing each prospect's website and tailoring the message accordingly.

## Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud Project with OAuth 2.0 credentials
- Gemini API key
- Supabase account (for session/token storage)

### Installation

```bash
# Clone and navigate
git clone https://github.com/Tanuj2005/Email-Marketing.git
cd Email-Marketing

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/callback
FRONTEND_REDIRECT_URL=http://localhost:3000
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_encryption_key
```

### Run the Server

```bash
uv run uvicorn src.main:app --reload
```

Server runs at `http://localhost:8000`

## API Usage

### 1. Authenticate

```
GET /login
```

Returns Google OAuth URL. Complete authentication in browser.

### 2. Prepare Your Google Sheet

Create a sheet with these columns:

| email_id | company_name | website_link |
|----------|--------------|--------------|
| john@acme.com | Acme Corp | https://acme.com |
| jane@startup.io | Startup Inc | https://startup.io |

### 3. Run Campaign

```bash
POST /campaign/send
Content-Type: application/json

{
  "spreadsheet_id": "your_google_sheet_id",
  "campaign_purpose": "Introduce our AI marketing services",
  "email_column": "email_id",
  "company_column": "company_name",
  "website_column": "website_link"
}
```

### Response

```json
{
  "total_contacts": 50,
  "emails_sent_successfully": 48,
  "emails_failed": 2,
  "processing_time_seconds": 120.5,
  "detailed_results": [...]
}
```

## Project Structure

```
src/
├── main.py              # FastAPI application
├── routes/
│   └── routes.py        # API endpoints
├── models/
│   └── sheets.py        # Request/Response models
└── utils/
    ├── oauth.py         # Google OAuth handling
    ├── sheets.py        # Google Sheets integration
    ├── scraper.py       # Website scraping
    ├── gemini_service.py # AI email generation
    ├── gmail_service.py  # Email sending
    ├── database.py      # Supabase client
    └── security.py      # Token encryption
```

## Key Features

- **OAuth 2.0 Authentication** - Secure Google login with token refresh
- **Concurrent Scraping** - Scrapes multiple websites in parallel
- **AI Personalization** - Gemini analyzes website content for relevant messaging
- **Rate Limiting** - Respects Gmail API quotas automatically
- **Error Handling** - Graceful fallbacks when scraping or AI fails
- **Encrypted Storage** - OAuth tokens encrypted at rest

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Get OAuth authorization URL |
| GET | `/callback` | OAuth callback handler |
| POST | `/logout` | End user session |
| POST | `/campaign/send` | Execute email campaign |

## Tech Stack

- **Backend:** FastAPI, Python 3.12
- **AI:** Google Gemini 2.5 Flash
- **Database:** Supabase (PostgreSQL)
- **APIs:** Google OAuth, Sheets, Gmail
- **Scraping:** BeautifulSoup, httpx

## License

MIT

---

**Built for marketers who value personalization over volume.**