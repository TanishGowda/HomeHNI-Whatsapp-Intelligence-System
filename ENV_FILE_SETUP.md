# Using .env File for Environment Variables

This guide explains how to use a `.env` file to store your environment variables, so you don't have to set them every time you open a new terminal session.

---

## Quick Setup

### Step 1: Install python-dotenv

The code now automatically loads environment variables from a `.env` file. First, install the required package:

```bash
pip install -r requirements.txt
```

This will install `python-dotenv` along with other dependencies.

### Step 2: Create Your .env File

1. **Copy the template:**
   - Copy `.env.example` to `.env`
   - On Windows: `copy .env.example .env`
   - On macOS/Linux: `cp .env.example .env`

2. **Edit the .env file:**
   - Open `.env` in a text editor
   - Replace all placeholder values with your actual credentials
   - **Never commit this file to Git** (it's already in `.gitignore`)

### Step 3: Fill in Your Credentials

Edit `.env` and replace the placeholder values:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-actual-auth-token-here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Hostinger FTP Configuration
HOSTINGER_FTP_HOST=ftp.yourdomain.com
HOSTINGER_FTP_USER=your-actual-ftp-username
HOSTINGER_FTP_PASSWORD=your-actual-ftp-password
HOSTINGER_FTP_PORT=21
HOSTINGER_FTP_DIR=/public_html/property-pdfs
HOSTINGER_BASE_URL=https://yourdomain.com/property-pdfs

# HomeHNI Onboarding Link (Optional)
HOMEHNI_ONBOARDING_LINK=https://your-actual-onboarding-link.com
```

### Step 4: Run Your Program

That's it! Now you can simply run:

```bash
python extract_messages.py
```

The program will automatically load all environment variables from the `.env` file.

---

## How It Works

The code now includes this at the top of `extract_messages.py`:

```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without it
    pass
```

This automatically loads variables from `.env` when the program starts, so you don't need to set them manually in each terminal session.

---

## Benefits

✅ **No need to set variables every time** - Just create `.env` once  
✅ **Secure** - `.env` is in `.gitignore`, so it won't be committed to Git  
✅ **Easy to manage** - All credentials in one place  
✅ **Works across platforms** - Same `.env` file works on Windows, macOS, and Linux  

---

## Security Notes

1. **Never commit `.env` to Git:**
   - The `.env` file is already in `.gitignore`
   - Only commit `.env.example` (the template)

2. **Keep `.env` private:**
   - Don't share your `.env` file with anyone
   - Don't upload it to cloud storage or email it

3. **Use different `.env` files for different environments:**
   - `.env.development` for testing
   - `.env.production` for production
   - Update your code to load the appropriate file if needed

---

## Troubleshooting

### Issue: Variables not loading

**Solution:**
1. Make sure `python-dotenv` is installed: `pip install python-dotenv`
2. Verify `.env` file exists in the same directory as `extract_messages.py`
3. Check that variable names match exactly (case-sensitive)
4. Ensure there are no spaces around the `=` sign: `KEY=value` not `KEY = value`

### Issue: Still asking for credentials

**Solution:**
1. Check that `.env` file is in the correct location (same folder as `extract_messages.py`)
2. Verify the file is named exactly `.env` (not `.env.txt` or `env`)
3. Restart your terminal/IDE after creating `.env`

### Issue: File not found

**Solution:**
- Make sure you're running the script from the project directory
- Check that `.env` exists: `ls .env` (macOS/Linux) or `dir .env` (Windows)

---

## Alternative: Manual Environment Variables

If you prefer not to use `.env` file, you can still set environment variables manually in your terminal (as before). The code will use those if `.env` is not available.

---

## File Structure

After setup, your project should look like:

```
Whatsapp automation/
├── .env                    # Your actual credentials (NOT in Git)
├── .env.example            # Template file (safe to commit)
├── .gitignore             # Ensures .env is not committed
├── extract_messages.py    # Main script (loads .env automatically)
├── requirements.txt       # Dependencies (includes python-dotenv)
├── sample.html            # HTML template
└── ... (other files)
```

---

**That's it! You're all set. Just create your `.env` file once and you're good to go!** 🎉

