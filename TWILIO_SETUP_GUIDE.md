# How to Get Twilio Credentials for WhatsApp

This guide will walk you through the process of setting up a Twilio account and obtaining the required credentials for WhatsApp messaging.

---

## Step 1: Create a Twilio Account

1. **Visit Twilio Website**
   - Go to: https://www.twilio.com/
   - Click **"Sign Up"** or **"Get Started"** (usually in the top right corner)

2. **Sign Up Process**
   - Enter your email address
   - Create a password
   - Verify your email address
   - Complete the sign-up form with your details

3. **Account Verification**
   - Twilio may ask for phone number verification
   - Follow the prompts to verify your phone number

---

## Step 2: Get Your Account SID and Auth Token

Once you're logged into your Twilio Console:

1. **Navigate to Dashboard**
   - After logging in, you'll be on the Twilio Console Dashboard
   - The dashboard shows your account information

2. **Find Account SID**
   - Look for **"Account SID"** on the dashboard
   - It starts with `AC` followed by 32 characters
   - Example: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (replace x's with your actual SID)
   - **Copy this value** - this is your `TWILIO_ACCOUNT_SID`

3. **Find Auth Token**
   - On the same dashboard, look for **"Auth Token"**
   - Click the **eye icon** or **"View"** button to reveal it
   - It's a 32-character string
   - Example: `your_auth_token_here_32_chars`
   - **Copy this value** - this is your `TWILIO_AUTH_TOKEN`

   **⚠️ Important:** Keep your Auth Token secret! Never share it publicly.

---

## Step 3: Set Up WhatsApp on Twilio

Twilio offers WhatsApp messaging through their WhatsApp Sandbox (for testing) and WhatsApp Business API (for production).

### Option A: WhatsApp Sandbox (For Testing - FREE)

The WhatsApp Sandbox allows you to test WhatsApp messaging for free, but with limitations:
- You can only send messages to verified phone numbers
- Limited to testing purposes
- No production use

**Steps to Set Up WhatsApp Sandbox:**

1. **Navigate to WhatsApp in Console**
   - In your Twilio Console, go to: **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Or go to: **Messaging** → **Settings** → **WhatsApp Sandbox**

2. **Join the Sandbox**
   - You'll see a WhatsApp number and a join code
   - Example: `join <code-word>`
   - Send this message to the provided WhatsApp number from your phone
   - Example: Send `join example-code` to `+1 415 523 8886`

3. **Get Your Sandbox Number**
   - After joining, you'll see your sandbox WhatsApp number
   - Format: `whatsapp:+14155238886` (or similar)
   - **Copy this value** - this is your `TWILIO_WHATSAPP_FROM`

4. **Add Recipients (For Testing)**
   - Recipients must also join the sandbox by sending the join code
   - Or you can add them manually in the Twilio Console

### Option B: WhatsApp Business API (For Production - PAID)

For production use, you need to:
1. Apply for WhatsApp Business API access
2. Get approval from Twilio
3. Set up your WhatsApp Business Profile
4. Get your approved WhatsApp Business number

**Steps to Set Up WhatsApp Business API:**

1. **Navigate to WhatsApp in Console**
   - Go to: **Messaging** → **Settings** → **WhatsApp Senders**

2. **Apply for WhatsApp Business API**
   - Click **"Get Started"** or **"Apply"**
   - Fill out the application form with:
     - Business information
     - Use case description
     - Expected message volume
   - Submit for review

3. **Wait for Approval**
   - Twilio will review your application
   - This can take a few days to weeks
   - You'll receive an email when approved

4. **Get Your WhatsApp Business Number**
   - Once approved, you'll receive a WhatsApp Business number
   - Format: `whatsapp:+1234567890`
   - **Copy this value** - this is your `TWILIO_WHATSAPP_FROM`

---

## Step 4: Set Up Your Environment Variables

Once you have all three credentials, set them as environment variables:

### Windows PowerShell:
```powershell
$Env:TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$Env:TWILIO_AUTH_TOKEN = "your_auth_token_here"
$Env:TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
```

### Windows CMD:
```cmd
set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set TWILIO_AUTH_TOKEN=your_auth_token_here
set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### macOS/Linux:
```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
```

**Replace the example values with your actual credentials!**

---

## Quick Reference: Where to Find Credentials in Twilio Console

1. **Account SID and Auth Token:**
   - Location: **Console Dashboard** (home page)
   - Look for: "Account Info" section
   - Account SID: Starts with `AC`
   - Auth Token: Click "View" to reveal

2. **WhatsApp Number (Sandbox):**
   - Location: **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Or: **Messaging** → **Settings** → **WhatsApp Sandbox**
   - Format: `whatsapp:+14155238886`

3. **WhatsApp Number (Business API):**
   - Location: **Messaging** → **Settings** → **WhatsApp Senders**
   - Format: `whatsapp:+1234567890`

---

## Important Notes

### WhatsApp Sandbox Limitations:
- ✅ **Free to use** for testing
- ✅ **Quick setup** (minutes)
- ❌ **Limited recipients** (must join sandbox)
- ❌ **Not for production** use
- ❌ **Limited message volume**

### WhatsApp Business API:
- ✅ **Production ready**
- ✅ **No recipient limitations**
- ✅ **Higher message volumes**
- ❌ **Requires approval** (can take time)
- ❌ **Paid service** (pay per message)

### Phone Number Format:
- Always use the format: `whatsapp:+1234567890`
- Include the `whatsapp:` prefix
- Include country code (e.g., `+1` for US, `+91` for India)
- No spaces or dashes

---

## Testing Your Setup

After setting up your credentials, you can test if everything works:

1. **Verify Environment Variables:**
   ```bash
   # Windows PowerShell
   echo $Env:TWILIO_ACCOUNT_SID
   echo $Env:TWILIO_AUTH_TOKEN
   echo $Env:TWILIO_WHATSAPP_FROM
   
   # macOS/Linux
   echo $TWILIO_ACCOUNT_SID
   echo $TWILIO_AUTH_TOKEN
   echo $TWILIO_WHATSAPP_FROM
   ```

2. **Run Your Program:**
   ```bash
   python extract_messages.py
   ```

3. **Check Twilio Console:**
   - Go to **Monitor** → **Logs** → **Messaging**
   - You should see message attempts and their status

---

## Troubleshooting

### Issue: "Invalid Account SID"
- **Solution:** Verify you copied the entire Account SID (starts with `AC`)
- Check for extra spaces or characters

### Issue: "Invalid Auth Token"
- **Solution:** Make sure you clicked "View" to reveal the full token
- Verify no spaces were copied
- Regenerate the token if needed (Console → Account → Auth Tokens)

### Issue: "Invalid WhatsApp Number"
- **Solution:** Ensure the number includes `whatsapp:` prefix
- Format: `whatsapp:+1234567890`
- Verify the number is active in your Twilio account

### Issue: "Unsubscribed Number" (21614 error)
- **Solution:** For Sandbox, the recipient must join the sandbox first
- Send the join code to the sandbox number from the recipient's phone
- Or add the number manually in Twilio Console

### Issue: "Rate Limit Exceeded"
- **Solution:** Wait a few minutes before sending more messages
- Check your Twilio account limits
- Consider upgrading your account for higher limits

---

## Additional Resources

- **Twilio Console:** https://console.twilio.com/
- **Twilio WhatsApp Documentation:** https://www.twilio.com/docs/whatsapp
- **Twilio WhatsApp Sandbox Guide:** https://www.twilio.com/docs/whatsapp/sandbox
- **Twilio Support:** https://support.twilio.com/

---

## Security Best Practices

1. **Never commit credentials to Git:**
   - Use environment variables (as shown above)
   - Add `.env` files to `.gitignore` if using them

2. **Rotate Auth Tokens regularly:**
   - Go to: Console → Account → Auth Tokens
   - Create new tokens and update your environment variables

3. **Use separate accounts for testing and production:**
   - Keep sandbox credentials separate from production

4. **Monitor usage:**
   - Check Twilio Console regularly for unexpected activity
   - Set up billing alerts

---

**Last Updated:** Ready for use!

