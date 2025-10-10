# Fantasy NBA Advisor - Deployment Guide

## Single App for All Environments

Use `app.py` for:
- ✅ Local development
- ✅ Docker deployment  
- ✅ Streamlit Cloud deployment

## Streamlit Cloud Setup

**Main file:** `app.py`

**Requirements:** `requirements.txt` (or `requirements_streamlit.txt` for lighter deployment)

**Environment Detection:** Automatic
- Detects Streamlit Cloud environment
- Uses appropriate import strategy
- Handles API keys correctly

## Local Development

**Run locally:**
```bash
streamlit run app.py --server.port=8504
```

**With environment API key:**
- Set `GROQ_API_KEY` in `.env` file
- App will use it automatically for local development
- Users can still override with their own key

## Docker Deployment

**Run with Docker:**
```bash
docker-compose up
```

**Port:** 8504 (as configured)

## API Key Handling

**Local Development:**
- Uses `.env` file API key if available
- Shows success message: "🔑 Using API key from environment"
- Users can override by entering their own key

**Streamlit Cloud:**
- Users must enter their own API keys
- No environment variables used for security

**Both:**
- User input always takes precedence
- Secure password input field
- Clear instructions for getting free API keys