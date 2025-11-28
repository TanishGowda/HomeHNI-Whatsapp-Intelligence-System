# HomeHNI WhatsApp Automation - Setup and Usage Guide

This guide provides step-by-step instructions for setting up and running the WhatsApp automation system that extracts property messages, generates webpages, converts them to PDFs, uploads to Hostinger, and sends them via WhatsApp.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Variables Setup](#environment-variables-setup)
4. [Hostinger FTP Configuration](#hostinger-ftp-configuration)
5. [Running the Program](#running-the-program)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.8 or higher** installed on your system
2. **WhatsApp chat export files** in folders (e.g., `HomeGroup/chat.txt`)
3. **OpenAI API Key** - Get from https://platform.openai.com/account/api-keys
4. **Twilio Account** with WhatsApp enabled:
   - Account SID
   - Auth Token
   - WhatsApp Business Number (format: `whatsapp:+1234567890`)
5. **Hostinger Hosting Account** with FTP access

---

## Installation

### Step 1: Install Python Dependencies

Open your terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

This will install:
- `openai` - For AI-powered message and image analysis
- `twilio` - For WhatsApp messaging
- `weasyprint` - For HTML-to-PDF conversion

**Note for Windows users:** If `weasyprint` installation fails, you may need to install additional dependencies. See the [Troubleshooting](#troubleshooting) section.

---

## Environment Variables Setup

You need to set environment variables for API keys and configuration. Choose the method based on your operating system:

### Windows PowerShell

```powershell
# OpenAI API Key
$Env:OPENAI_API_KEY = "sk-your-openai-api-key-here"

# Twilio Credentials
$Env:TWILIO_ACCOUNT_SID = "your-twilio-account-sid"
$Env:TWILIO_AUTH_TOKEN = "your-twilio-auth-token"
$Env:TWILIO_WHATSAPP_FROM = "whatsapp:+1234567890"

# Hostinger FTP Configuration
$Env:HOSTINGER_FTP_HOST = "ftp.yourdomain.com"
$Env:HOSTINGER_FTP_USER = "your-ftp-username"
$Env:HOSTINGER_FTP_PASSWORD = "your-ftp-password"
$Env:HOSTINGER_FTP_PORT = "21"
$Env:HOSTINGER_FTP_DIR = "/public_html/property-pdfs"
$Env:HOSTINGER_BASE_URL = "https://yourdomain.com/property-pdfs"

# Optional: HomeHNI Onboarding Link
$Env:HOMEHNI_ONBOARDING_LINK = "https://your-onboarding-link.com"
```

### Windows CMD

```cmd
set OPENAI_API_KEY=sk-your-openai-api-key-here
set TWILIO_ACCOUNT_SID=your-twilio-account-sid
set TWILIO_AUTH_TOKEN=your-twilio-auth-token
set TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
set HOSTINGER_FTP_HOST=ftp.yourdomain.com
set HOSTINGER_FTP_USER=your-ftp-username
set HOSTINGER_FTP_PASSWORD=your-ftp-password
set HOSTINGER_FTP_PORT=21
set HOSTINGER_FTP_DIR=/public_html/property-pdfs
set HOSTINGER_BASE_URL=https://yourdomain.com/property-pdfs
set HOMEHNI_ONBOARDING_LINK=https://your-onboarding-link.com
```

### macOS/Linux

```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
export TWILIO_ACCOUNT_SID="your-twilio-account-sid"
export TWILIO_AUTH_TOKEN="your-twilio-auth-token"
export TWILIO_WHATSAPP_FROM="whatsapp:+1234567890"
export HOSTINGER_FTP_HOST="ftp.yourdomain.com"
export HOSTINGER_FTP_USER="your-ftp-username"
export HOSTINGER_FTP_PASSWORD="your-ftp-password"
export HOSTINGER_FTP_PORT="21"
export HOSTINGER_FTP_DIR="/public_html/property-pdfs"
export HOSTINGER_BASE_URL="https://yourdomain.com/property-pdfs"
export HOMEHNI_ONBOARDING_LINK="https://your-onboarding-link.com"
```

**Important:** These environment variables are temporary and will be lost when you close the terminal. To make them permanent, you can:
- **Windows:** Add them to System Environment Variables
- **macOS/Linux:** Add them to `~/.bashrc` or `~/.zshrc`

---

## Hostinger FTP Configuration

### Step 1: Get FTP Credentials

1. Log into your **Hostinger hPanel**
2. Navigate to: **Files** → **FTP Accounts**
3. Note down or create an FTP account with:
   - **FTP Host**: Usually `ftp.yourdomain.com` or an IP address
   - **FTP Username**: Your FTP username
   - **FTP Password**: Your FTP password
   - **FTP Port**: Usually `21` (or `22` for SFTP)

### Step 2: Create PDF Storage Directory

1. Using Hostinger **File Manager** or an FTP client:
   - Navigate to your website's public directory (usually `public_html`)
   - Create a folder named `property-pdfs` (or any name you prefer)
   - Ensure this folder is publicly accessible (permissions: 755)

### Step 3: Set Environment Variables

Use the FTP credentials you obtained in Step 1 to set the environment variables as shown in the [Environment Variables Setup](#environment-variables-setup) section above.

**Example:**
- If your domain is `example.com`
- FTP host: `ftp.example.com`
- FTP directory: `/public_html/property-pdfs`
- Base URL: `https://example.com/property-pdfs`

---

## Running the Program

### Step 1: Prepare Your Data

Ensure you have:
- A folder containing `chat.txt` (e.g., `HomeGroup/chat.txt`)
- Media files in the same folder (if any)

### Step 2: Run the Program

Open your terminal/command prompt in the project directory and run:

```bash
python extract_messages.py
```

### Step 3: Follow the Prompts

The program will ask you for:

1. **Folder name**: Enter the folder name containing your WhatsApp chat (e.g., `HomeGroup`)
2. **Date**: Enter the date in `DD/MM/YYYY` or `DD/MM/YY` format (e.g., `28/10/2025` or `28/10/25`)

### Step 4: Wait for Processing

The program will:
1. ✅ Extract messages and media for the specified date
2. ✅ Display all extracted content in the terminal
3. ✅ Analyze messages using OpenAI to identify property listings
4. ✅ Analyze images using OpenAI Vision to identify property-related images
5. ✅ Generate HTML webpages for each property listing
6. ✅ Convert HTML files to PDFs
7. ✅ Upload PDFs to Hostinger via FTP
8. ✅ Send PDFs via WhatsApp to contact numbers found in messages
9. ✅ Send CTA (Call-to-Action) messages via WhatsApp

### Step 5: Check Results

After processing, you will see:
- **Generated HTML files**: `a.html`, `b.html`, `c.html`, etc.
- **Generated PDF files**: `a.pdf`, `b.pdf`, `c.pdf`, etc.
- **Terminal output** showing:
  - Number of messages and media extracted
  - Number of property listings identified
  - Number of webpages generated
  - Number of PDFs uploaded
  - WhatsApp sending summary

---

## What Happens When You Run the Program

### 1. Message Extraction
- Extracts all messages from `chat.txt` for the specified date
- Extracts all media files matching the date from the folder

### 2. Property Identification
- Uses OpenAI to identify messages from **sellers/agents/owners** offering properties
- **Excludes** buyer requests and inquiries
- **Only includes** messages with contact numbers
- Analyzes images to identify property-related content

### 3. Webpage Generation
- Generates professional HTML webpages using the `sample.html` template
- Each webpage is customized with property details from the message
- Files are saved as `a.html`, `b.html`, `c.html`, etc.

### 4. PDF Conversion
- Converts each HTML file to PDF using `weasyprint`
- PDFs are saved as `a.pdf`, `b.pdf`, `c.pdf`, etc.

### 5. FTP Upload
- Uploads each PDF to Hostinger via FTP
- PDFs are accessible at: `https://yourdomain.com/property-pdfs/filename.pdf`

### 6. WhatsApp Sending
- Extracts contact numbers from each property message
- Sends **two messages** to each contact:
  1. **First message**: PDF attachment with preview text
  2. **Second message**: CTA message with HomeHNI onboarding link

---

## Troubleshooting

### Issue: `weasyprint` Installation Fails (Windows)

**Solution:**
1. Install GTK+ runtime: Download from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. Or use alternative: `pip install pdfkit` and install `wkhtmltopdf`

### Issue: OpenAI API Key Invalid (401 Error)

**Solution:**
- Verify your API key is correct
- Check if the key has expired
- Get a new key from: https://platform.openai.com/account/api-keys
- Ensure the environment variable is set correctly

### Issue: FTP Upload Fails

**Possible causes:**
- Incorrect FTP credentials
- Directory doesn't exist
- Insufficient permissions

**Solution:**
1. Verify FTP credentials in Hostinger hPanel
2. Ensure the directory exists (create it manually if needed)
3. Check directory permissions (should be 755)
4. Try connecting with an FTP client to test credentials

### Issue: Twilio WhatsApp Send Fails

**Possible causes:**
- Invalid phone number format
- Number not opted in to WhatsApp
- Rate limit exceeded
- Invalid media URL

**Solution:**
1. Ensure phone numbers include country code (e.g., `+919876543210`)
2. Verify the recipient has opted in to receive WhatsApp messages
3. Wait a few minutes if rate limit is exceeded
4. Ensure PDF URL is publicly accessible

### Issue: PDF URL Not Accessible

**Solution:**
1. Verify `HOSTINGER_BASE_URL` is correct
2. Check that PDFs were uploaded successfully
3. Test the URL in a browser: `https://yourdomain.com/property-pdfs/a.pdf`
4. Ensure the `property-pdfs` folder has public read permissions

### Issue: No Property Messages Identified

**Possible causes:**
- Messages don't contain contact numbers
- Messages are from buyers (not sellers)
- Messages lack sufficient property details

**Solution:**
- The system only identifies messages from **sellers/agents/owners** offering properties
- Messages must contain a **contact number**
- Messages must have sufficient property details (location, type, specs, etc.)

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for message/image analysis | `sk-...` |
| `TWILIO_ACCOUNT_SID` | Yes* | Twilio Account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Yes* | Twilio Auth Token | `...` |
| `TWILIO_WHATSAPP_FROM` | Yes* | Your WhatsApp Business number | `whatsapp:+1234567890` |
| `HOSTINGER_FTP_HOST` | Yes* | FTP host address | `ftp.yourdomain.com` |
| `HOSTINGER_FTP_USER` | Yes* | FTP username | `username` |
| `HOSTINGER_FTP_PASSWORD` | Yes* | FTP password | `password` |
| `HOSTINGER_FTP_PORT` | No | FTP port (default: 21) | `21` |
| `HOSTINGER_FTP_DIR` | No | Remote directory path | `/public_html/property-pdfs` |
| `HOSTINGER_BASE_URL` | Yes* | Public URL for PDFs | `https://yourdomain.com/property-pdfs` |
| `HOMEHNI_ONBOARDING_LINK` | No | Onboarding link for CTA message | `https://...` |

*Required only if you want to use that feature (WhatsApp sending or FTP upload)

---

## Next Steps

1. **Set up your environment variables** (see [Environment Variables Setup](#environment-variables-setup))
2. **Configure Hostinger FTP** (see [Hostinger FTP Configuration](#hostinger-ftp-configuration))
3. **Run the program** (see [Running the Program](#running-the-program))
4. **Update the onboarding link** when ready by setting `HOMEHNI_ONBOARDING_LINK`

---

## Support

If you encounter any issues not covered in this guide:
1. Check the terminal output for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Review the [Troubleshooting](#troubleshooting) section

---

**Last Updated:** Implementation complete - Ready for testing!

