"""Test script to verify credentials and test Hostinger base URL."""
import os
from dotenv import load_dotenv
import ftplib
import requests

# Load environment variables
load_dotenv()

print("=" * 80)
print("CREDENTIALS VERIFICATION")
print("=" * 80)

# Check OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
print(f"\n1. OpenAI API Key:")
if openai_key and openai_key != "sk-your-openai-api-key-here":
    print(f"   Status: OK (Key length: {len(openai_key)} chars)")
    print(f"   Starts with: {openai_key[:10]}...")
else:
    print("   Status: NOT SET or using placeholder")

# Check Twilio
print(f"\n2. Twilio Credentials:")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")

if twilio_sid and twilio_sid != "your-twilio-account-sid-here":
    print(f"   Account SID: OK ({twilio_sid[:10]}...)")
else:
    print("   Account SID: NOT SET")

if twilio_token and twilio_token != "your-twilio-auth-token-here":
    print(f"   Auth Token: OK ({len(twilio_token)} chars)")
else:
    print("   Auth Token: NOT SET")

if twilio_from:
    print(f"   WhatsApp From: {twilio_from}")
    if twilio_from.startswith("whatsapp:"):
        print("   Format: OK")
    else:
        print("   Format: Should start with 'whatsapp:'")
else:
    print("   WhatsApp From: NOT SET")

# Check Hostinger FTP
print(f"\n3. Hostinger FTP Credentials:")
ftp_host = os.getenv("HOSTINGER_FTP_HOST")
ftp_user = os.getenv("HOSTINGER_FTP_USER")
ftp_password = os.getenv("HOSTINGER_FTP_PASSWORD")
ftp_port = os.getenv("HOSTINGER_FTP_PORT", "21")
ftp_dir = os.getenv("HOSTINGER_FTP_DIR")
base_url = os.getenv("HOSTINGER_BASE_URL")

if ftp_host:
    print(f"   FTP Host: {ftp_host}")
else:
    print("   FTP Host: NOT SET")

if ftp_user:
    print(f"   FTP User: {ftp_user}")
else:
    print("   FTP User: NOT SET")

if ftp_password:
    print(f"   FTP Password: OK (set)")
else:
    print("   FTP Password: NOT SET")

print(f"   FTP Port: {ftp_port}")
print(f"   FTP Directory: {ftp_dir}")

if base_url:
    print(f"   Base URL: {base_url}")
else:
    print("   Base URL: NOT SET")

# Test FTP Connection
print(f"\n4. Testing FTP Connection:")
if all([ftp_host, ftp_user, ftp_password]):
    try:
        ftp = ftplib.FTP()
        ftp.connect(ftp_host, int(ftp_port))
        ftp.login(ftp_user, ftp_password)
        print("   Status: SUCCESS - Connected to FTP server")
        
        # Try to change to directory
        if ftp_dir:
            try:
                ftp.cwd(ftp_dir)
                print(f"   Directory Access: SUCCESS - Can access {ftp_dir}")
            except ftplib.error_perm as e:
                print(f"   Directory Access: FAILED - {e}")
                print(f"   Note: Directory might not exist or permissions issue")
        
        ftp.quit()
    except Exception as e:
        print(f"   Status: FAILED - {e}")
else:
    print("   Status: SKIPPED - Missing FTP credentials")

# Test Base URL
print(f"\n5. Testing Base URL:")
if base_url:
    try:
        response = requests.get(base_url, timeout=10, allow_redirects=True)
        print(f"   URL: {base_url}")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   Status: SUCCESS - URL is accessible and returns content")
        elif response.status_code == 403:
            print("   Status: PARTIAL - URL exists but access forbidden (might need authentication)")
        elif response.status_code == 404:
            print("   Status: FAILED - Directory not found (check if property-pdfs folder exists)")
        else:
            print(f"   Status: UNEXPECTED - Got status code {response.status_code}")
        
        # Try accessing a test file
        test_url = f"{base_url.rstrip('/')}/test.pdf"
        test_response = requests.get(test_url, timeout=5)
        if test_response.status_code == 404:
            print(f"   Test File Check: Directory exists (404 for test.pdf is expected)")
        elif test_response.status_code == 200:
            print(f"   Test File Check: Found test.pdf (unexpected)")
        else:
            print(f"   Test File Check: Status {test_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"   Status: FAILED - Cannot connect to {base_url}")
        print("   Possible issues:")
        print("   - Domain not pointing to Hostinger")
        print("   - DNS not propagated")
        print("   - Server down")
    except requests.exceptions.Timeout:
        print(f"   Status: FAILED - Connection timeout")
    except Exception as e:
        print(f"   Status: ERROR - {e}")
else:
    print("   Status: SKIPPED - Base URL not set")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

