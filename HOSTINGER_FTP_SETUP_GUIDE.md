# How to Get Hostinger FTP Credentials

This guide will walk you through the process of obtaining FTP credentials from your Hostinger hosting account and setting up the directory for PDF storage.

---

## Step 1: Log into Hostinger hPanel

1. **Visit Hostinger Website**
   - Go to: https://www.hostinger.com/
   - Click **"Log In"** (usually in the top right corner)

2. **Access hPanel**
   - After logging in, you'll see your hosting dashboard
   - Click on **"Manage"** or **"hPanel"** for your hosting account
   - This will open the Hostinger hPanel (control panel)

---

## Step 2: Navigate to FTP Accounts

1. **Find FTP Section**
   - In hPanel, look for the **"Files"** section
   - Click on **"FTP Accounts"** or **"FTP"**

2. **Alternative Path:**
   - Sometimes it's under: **"Advanced"** → **"FTP Accounts"**
   - Or: **"File Manager"** → **"FTP Accounts"**

---

## Step 3: Get or Create FTP Account

### Option A: Use Existing FTP Account

If you already have an FTP account set up:

1. **View FTP Accounts List**
   - You'll see a list of all FTP accounts
   - Each account shows:
     - **Username** (e.g., `username@yourdomain.com`)
     - **Directory** (e.g., `/public_html`)
     - **Status** (Active/Inactive)

2. **Get FTP Details**
   - Click on the FTP account you want to use
   - Or look for **"Change Password"** or **"Manage"** button
   - You'll see:
     - **FTP Host/Server**: Usually `ftp.yourdomain.com` or an IP address
     - **FTP Username**: The username (e.g., `username@yourdomain.com`)
     - **FTP Port**: Usually `21` (or `22` for SFTP)

3. **Get FTP Password**
   - If you don't remember the password, click **"Change Password"**
   - Set a new password and note it down
   - **⚠️ Important:** Keep this password secure!

### Option B: Create New FTP Account

If you need to create a new FTP account:

1. **Click "Create FTP Account" or "Add FTP Account"**

2. **Fill in the Details:**
   - **FTP Username**: Choose a username (e.g., `propertypdfs`)
   - **Directory**: Set to `/public_html/property-pdfs` (or your preferred path)
   - **Password**: Create a strong password
   - **Quota**: Leave as unlimited or set a limit

3. **Create the Account**
   - Click **"Create"** or **"Add"**
   - Note down the credentials shown

---

## Step 4: Get FTP Host/Server Address

1. **Find FTP Host Information**
   - In the FTP Accounts section, look for:
     - **"FTP Host"** or **"FTP Server"**
     - Usually displayed as: `ftp.yourdomain.com`
     - Or sometimes: `files.yourdomain.com`
     - Or an IP address like: `185.xxx.xxx.xxx`

2. **Alternative: Check Email**
   - Hostinger usually sends FTP details in the welcome email
   - Check your email for "Hosting Account Details" or "FTP Access Information"

3. **If Not Visible:**
   - Try using: `ftp.yourdomain.com` (replace with your actual domain)
   - Or check: **"Account Information"** section in hPanel

---

## Step 5: Determine FTP Port

1. **Standard FTP Port:**
   - Default port is **`21`** for regular FTP
   - This is what you'll use in most cases

2. **SFTP Port (if using SFTP):**
   - Port **`22`** is for SFTP (Secure FTP)
   - Only use this if you specifically set up SFTP

3. **Check in hPanel:**
   - FTP account details usually show the port
   - If not shown, use **`21`** as default

---

## Step 6: Set Up Directory Structure

### Step 6.1: Create Property-PDFs Directory

1. **Open File Manager**
   - In hPanel, go to: **"Files"** → **"File Manager"**
   - Or click **"File Manager"** directly

2. **Navigate to public_html**
   - Click on **`public_html`** folder
   - This is your website's root directory

3. **Create New Folder**
   - Click **"New Folder"** or **"Create Folder"**
   - Name it: `property-pdfs` (or any name you prefer)
   - Click **"Create"**

4. **Set Permissions (Important!)**
   - Right-click on the `property-pdfs` folder
   - Select **"Change Permissions"** or **"File Permissions"**
   - Set permissions to: **`755`** (or **`rwxr-xr-x`**)
   - This makes the folder publicly accessible
   - Click **"Save"** or **"Apply"**

### Step 6.2: Note the Directory Path

The directory path for your `.env` file should be:
- **`/public_html/property-pdfs`** (if folder is in public_html root)
- Or: **`/public_html/subfolder/property-pdfs`** (if in a subfolder)

**Important:** Always start with `/` and use forward slashes `/`, not backslashes `\`

---

## Step 7: Get Your Domain/Base URL

1. **Find Your Domain**
   - Your domain is the website address you're hosting
   - Example: `example.com` or `www.example.com`

2. **Construct Base URL**
   - Format: `https://yourdomain.com/property-pdfs`
   - Example: `https://example.com/property-pdfs`
   - Example: `https://www.example.com/property-pdfs`

3. **If Using Subdomain:**
   - Example: `https://files.example.com/property-pdfs`

4. **Test the URL:**
   - After uploading a test file, visit: `https://yourdomain.com/property-pdfs/test.pdf`
   - If you can access it, the URL is correct

---

## Step 8: Compile All Credentials

Now you should have all the information. Here's what to put in your `.env` file:

```env
# Hostinger FTP Configuration
HOSTINGER_FTP_HOST=ftp.yourdomain.com
HOSTINGER_FTP_USER=username@yourdomain.com
HOSTINGER_FTP_PASSWORD=your-ftp-password
HOSTINGER_FTP_PORT=21
HOSTINGER_FTP_DIR=/public_html/property-pdfs
HOSTINGER_BASE_URL=https://yourdomain.com/property-pdfs
```

**Replace with your actual values!**

---

## Quick Reference: Where to Find Each Value

| Variable | Where to Find | Example |
|----------|---------------|---------|
| `HOSTINGER_FTP_HOST` | FTP Accounts section → FTP Host/Server | `ftp.example.com` |
| `HOSTINGER_FTP_USER` | FTP Accounts section → Username | `user@example.com` |
| `HOSTINGER_FTP_PASSWORD` | Set when creating/changing password | `your-password-123` |
| `HOSTINGER_FTP_PORT` | FTP Accounts section → Port (default: 21) | `21` |
| `HOSTINGER_FTP_DIR` | Path you created in File Manager | `/public_html/property-pdfs` |
| `HOSTINGER_BASE_URL` | Your domain + folder path | `https://example.com/property-pdfs` |

---

## Visual Guide: hPanel Navigation

```
Hostinger hPanel
├── Files
│   ├── File Manager          ← Create property-pdfs folder here
│   └── FTP Accounts          ← Get FTP credentials here
│       ├── FTP Host          ← HOSTINGER_FTP_HOST
│       ├── Username          ← HOSTINGER_FTP_USER
│       ├── Password          ← HOSTINGER_FTP_PASSWORD (set/reset)
│       └── Port              ← HOSTINGER_FTP_PORT (usually 21)
└── Domains                   ← Get your domain name here
    └── Your Domain           ← Use for HOSTINGER_BASE_URL
```

---

## Testing Your FTP Connection

### Method 1: Test with File Manager

1. Upload a test PDF manually:
   - Go to File Manager
   - Navigate to `public_html/property-pdfs`
   - Upload a test file: `test.pdf`
   - Visit: `https://yourdomain.com/property-pdfs/test.pdf`
   - If you can see/download the file, everything is set up correctly!

### Method 2: Test with FTP Client

1. **Use an FTP Client** (like FileZilla, WinSCP, or Cyberduck):
   - **Host**: `ftp.yourdomain.com` (or your FTP host)
   - **Username**: `username@yourdomain.com`
   - **Password**: Your FTP password
   - **Port**: `21`
   - **Protocol**: FTP (not SFTP unless you set it up)

2. **Connect and Test:**
   - If connection succeeds, your credentials are correct
   - Navigate to `/public_html/property-pdfs`
   - Upload a test file
   - Check if it's accessible via URL

### Method 3: Test with Python Script

You can test your FTP connection with a simple Python script:

```python
import ftplib

ftp = ftplib.FTP()
ftp.connect('ftp.yourdomain.com', 21)  # Replace with your FTP host
ftp.login('username@yourdomain.com', 'your-password')  # Replace with your credentials
ftp.cwd('/public_html/property-pdfs')  # Navigate to your directory
print("FTP connection successful!")
ftp.quit()
```

---

## Common Issues and Solutions

### Issue: "FTP Host Not Found" or Connection Timeout

**Solutions:**
1. Verify FTP host is correct (try `ftp.yourdomain.com`)
2. Check if your domain is pointing to Hostinger nameservers
3. Try using the IP address instead of domain name
4. Check firewall settings (FTP uses port 21)

### Issue: "Login Failed" or "Invalid Credentials"

**Solutions:**
1. Double-check username format (usually includes `@yourdomain.com`)
2. Reset FTP password in hPanel
3. Ensure no extra spaces in username/password
4. Try creating a new FTP account

### Issue: "Permission Denied" when Uploading

**Solutions:**
1. Check folder permissions (should be 755)
2. Ensure FTP account has access to the directory
3. Verify directory path is correct (starts with `/`)
4. Try creating the folder again with correct permissions

### Issue: "Directory Not Found"

**Solutions:**
1. Verify directory path starts with `/` (e.g., `/public_html/property-pdfs`)
2. Ensure folder exists in File Manager
3. Check spelling of folder name
4. Try using absolute path from root

### Issue: PDF URL Not Accessible

**Solutions:**
1. Verify folder is in `public_html` (not outside)
2. Check folder permissions (755)
3. Test URL format: `https://yourdomain.com/property-pdfs/filename.pdf`
4. Ensure domain is properly configured
5. Check if SSL certificate is active (for HTTPS)

### Issue: "FTP Port 21 Blocked"

**Solutions:**
1. Check if your ISP blocks port 21
2. Try using SFTP (port 22) if available
3. Contact Hostinger support for alternative ports
4. Use Hostinger's web-based File Manager as alternative

---

## Security Best Practices

1. **Use Strong Passwords:**
   - Create a unique, strong password for FTP
   - Don't reuse passwords from other services

2. **Limit FTP Access:**
   - Create a dedicated FTP account only for this purpose
   - Restrict directory access to only what's needed (`/public_html/property-pdfs`)

3. **Keep Credentials Secure:**
   - Never share FTP credentials
   - Don't commit `.env` file to Git
   - Use environment variables or secure credential storage

4. **Regular Password Updates:**
   - Change FTP password periodically
   - Update `.env` file when password changes

---

## Alternative: Using Hostinger File Manager API

If FTP doesn't work for you, you can:
1. Use Hostinger's web-based File Manager
2. Manually upload PDFs through the web interface
3. Update the code to use Hostinger's API (if available) instead of FTP

However, FTP is the recommended method for automation.

---

## Getting Help

If you're still having trouble:

1. **Hostinger Support:**
   - Contact Hostinger support via live chat
   - They can help you find FTP credentials
   - They can verify your account setup

2. **Check Documentation:**
   - Hostinger Knowledge Base: https://support.hostinger.com/
   - Search for "FTP" or "File Manager"

3. **Verify Account Status:**
   - Ensure your hosting account is active
   - Check if there are any account restrictions

---

## Summary Checklist

Before running your program, ensure you have:

- [ ] FTP Host address (e.g., `ftp.yourdomain.com`)
- [ ] FTP Username (e.g., `user@yourdomain.com`)
- [ ] FTP Password (set and noted down)
- [ ] FTP Port (usually `21`)
- [ ] Created `property-pdfs` folder in `public_html`
- [ ] Set folder permissions to `755`
- [ ] Verified directory path (e.g., `/public_html/property-pdfs`)
- [ ] Confirmed your domain name
- [ ] Constructed base URL (e.g., `https://yourdomain.com/property-pdfs`)
- [ ] Tested FTP connection (optional but recommended)
- [ ] Added all values to `.env` file

---

**Once you have all these credentials, add them to your `.env` file and you're ready to go!** 🚀

