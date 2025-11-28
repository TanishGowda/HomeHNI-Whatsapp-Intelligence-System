"""
WhatsApp Message Extractor

This module extracts messages from a WhatsApp chat export file
for a specific date.
"""

import json
import os
import base64
import time
from pathlib import Path
from datetime import datetime, date
import re
from typing import List, Dict, Optional
import ftplib

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # override=True ensures .env file values take precedence over existing env vars
except ImportError:
    # python-dotenv not installed, continue without it
    pass


def parse_whatsapp_date(date_str: str) -> Optional[date]:
    """
    Parse a date string in DD/MM/YYYY or DD/MM/YY format.
    
    Supports both 2-digit and 4-digit years for consistency with WhatsApp export format.
    
    Args:
        date_str: Date string in DD/MM/YYYY or DD/MM/YY format
        
    Returns:
        date object or None if parsing fails
    """
    date_str = date_str.strip()
    
    # Try 4-digit year format first: DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        pass
    
    # Try 2-digit year format: DD/MM/YY (matches WhatsApp export format)
    try:
        return datetime.strptime(date_str, "%d/%m/%y").date()
    except ValueError:
        pass
    
    return None


def parse_whatsapp_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse a WhatsApp timestamp string.
    
    Supports the actual WhatsApp export format:
    - [DD/MM/YY, H:MM:SS AM/PM] (with brackets, 2-digit year, includes seconds)
    
    Args:
        timestamp_str: Timestamp string from WhatsApp message (with or without brackets)
        
    Returns:
        datetime object or None if parsing fails
    """
    # Remove brackets if present
    timestamp_str = timestamp_str.strip().strip('[]')
    
    # Try format: "DD/MM/YY, H:MM:SS AM/PM" (2-digit year, with seconds)
    # Handle both single and double digit hours
    try:
        dt = datetime.strptime(timestamp_str.strip(), "%d/%m/%y, %I:%M:%S %p")
        return dt
    except ValueError:
        pass
    
    # Try with lowercase am/pm
    try:
        dt = datetime.strptime(timestamp_str.strip().lower(), "%d/%m/%y, %I:%M:%S %p")
        return dt
    except ValueError:
        pass
    
    # Fallback: Try without seconds (for compatibility)
    try:
        dt = datetime.strptime(timestamp_str.strip(), "%d/%m/%y, %I:%M %p")
        return dt
    except ValueError:
        pass
    
    # Fallback: Try 4-digit year format (for backward compatibility)
    try:
        dt = datetime.strptime(timestamp_str.strip(), "%d/%m/%Y, %I:%M:%S %p")
        return dt
    except ValueError:
        pass
    
    return None


def is_system_message(line: str) -> bool:
    """
    Check if a line is a WhatsApp system message.
    
    System messages typically don't match the standard message pattern
    or contain encryption notices, group updates, etc.
    
    Args:
        line: A line from the chat file
        
    Returns:
        True if it's a system message, False otherwise
    """
    # Remove zero-width characters and strip
    line_clean = line.strip().lstrip('\u200e')  # Remove left-to-right mark
    
    # System messages don't match the standard message pattern
    # Pattern: [DD/MM/YY, H:MM:SS AM/PM] Sender: Message
    message_pattern = r'^\[?\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)\]?\s+.+?:'
    
    if not re.match(message_pattern, line_clean, re.IGNORECASE):
        return True
    
    # Check for common system message keywords
    system_keywords = [
        'encryption',
        'security code',
        'group created',
        'left the group',
        'joined the group',
        'changed the subject',
        'changed this group',
        'removed',
        'added',
        'you were added',
        'messages and calls are end-to-end encrypted',
        'created this group',
        'image omitted',
        'document omitted',
        'video omitted',
        'audio omitted',
        'sticker omitted',
        'gif omitted'
    ]
    
    line_lower = line_clean.lower()
    return any(keyword in line_lower for keyword in system_keywords)


def parse_message_line(line: str) -> Optional[Dict]:
    """
    Parse a single line from WhatsApp chat export.
    
    Expected format: [DD/MM/YY, H:MM:SS AM/PM] Sender: Message
    
    Args:
        line: A line from the chat file
        
    Returns:
        Dictionary with 'datetime', 'sender', and 'text' keys,
        or None if the line cannot be parsed
    """
    # Remove zero-width characters and strip
    line_clean = line.strip().lstrip('\u200e')  # Remove left-to-right mark
    
    if not line_clean:
        return None
    
    if is_system_message(line_clean):
        return None
    
    # Pattern to match: [DD/MM/YY, H:MM:SS AM/PM] Sender: Message
    # The timestamp is in brackets, followed by space, then sender and message
    # Format: [DD/MM/YY, H:MM:SS AM/PM] Sender: Message
    # Handle optional zero-width characters and flexible spacing
    pattern = r'^\[(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm))\]\s+(.+?):\s+(.+)$'
    
    match = re.match(pattern, line_clean, re.IGNORECASE)
    if not match:
        return None
    
    timestamp_str = match.group(1)
    sender = match.group(2).strip()
    text = match.group(3).strip()
    
    # Remove any remaining zero-width characters from sender and text
    sender = sender.replace('\u200e', '').strip()
    text = text.replace('\u200e', '').strip()
    
    # Parse the timestamp
    dt = parse_whatsapp_timestamp(timestamp_str)
    if dt is None:
        return None
    
    return {
        "datetime": dt,
        "sender": sender,
        "text": text
    }


def extract_messages_for_date(chat_file_path: str, target_date: date) -> List[Dict]:
    """
    Extract messages from a WhatsApp chat file for a specific date.
    
    Args:
        chat_file_path: Path to the WhatsApp chat export file (chat.txt)
        target_date: The date to filter messages for
        
    Returns:
        List of message dictionaries, each containing:
        {
            "datetime": datetime,
            "sender": str,
            "text": str
        }
    """
    file_path = Path(chat_file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Chat file not found: {chat_file_path}")
    
    messages = []
    
    # Read the file with UTF-8 encoding, handling potential encoding issues
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Split into lines, but handle multi-line messages
    lines = content.split('\n')
    current_message = None
    
    for line in lines:
        # Try to parse as a new message
        parsed = parse_message_line(line)
        
        if parsed is not None:
            # This is a new message line
            # Save previous message if it matches the target date
            if current_message is not None:
                msg_date = current_message["datetime"].date()
                if msg_date == target_date:
                    messages.append(current_message)
            
            # Start tracking this new message
            current_message = parsed
        elif current_message is not None:
            # This is a continuation of the previous message (multi-line)
            # Append to the text of the current message
            if line.strip():
                current_message["text"] += "\n" + line.strip()
    
    # Don't forget the last message
    if current_message is not None:
        msg_date = current_message["datetime"].date()
        if msg_date == target_date:
            messages.append(current_message)
    
    return messages


def extract_media_files_for_date(folder_path: str, target_date: date) -> List[Dict]:
    """
    Extract media files from a folder that match a specific date.
    
    Media files are expected to have dates in the filename format:
    ID-MEDIATYPE-YYYY-MM-DD-HH-MM-SS.ext
    
    Args:
        folder_path: Path to the folder containing media files
        target_date: The date to filter media files for
        
    Returns:
        List of media file dictionaries, each containing:
        {
            "filename": str,
            "filepath": Path,
            "media_type": str,  # PHOTO, VIDEO, DOCUMENT, etc.
            "datetime": datetime,
            "extension": str
        }
    """
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    media_files = []
    
    # Pattern to match: ID-MEDIATYPE-YYYY-MM-DD-HH-MM-SS.ext
    # Example: 00000004-PHOTO-2025-10-28-11-32-12.jpg
    pattern = r'^(\d+)-([A-Z_]+)-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\.(.+)$'
    
    # Common media file extensions
    media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', 
                       '.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', 
                       '.pptx', '.zip', '.rar', '.mp3', '.wav', '.ogg'}
    
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in media_extensions:
            filename = file_path.name
            match = re.match(pattern, filename, re.IGNORECASE)
            
            if match:
                try:
                    year = int(match.group(3))
                    month = int(match.group(4))
                    day = int(match.group(5))
                    hour = int(match.group(6))
                    minute = int(match.group(7))
                    second = int(match.group(8))
                    
                    file_date = date(year, month, day)
                    file_datetime = datetime(year, month, day, hour, minute, second)
                    
                    # Check if the file date matches the target date
                    if file_date == target_date:
                        media_files.append({
                            "filename": filename,
                            "filepath": file_path,
                            "media_type": match.group(2),
                            "datetime": file_datetime,
                            "extension": match.group(9)
                        })
                except (ValueError, IndexError):
                    # Skip files that don't match the expected format
                    continue
    
    # Sort by datetime
    media_files.sort(key=lambda x: x["datetime"])
    
    return media_files


def display_extracted_content(messages: List[Dict], media_files: List[Dict], target_date: date):
    """
    Display all extracted messages and media files in the terminal.
    
    Args:
        messages: List of message dictionaries
        media_files: List of media file dictionaries
        target_date: The target date for filtering
    """
    print("\n" + "="*80)
    print(f"EXTRACTION RESULTS FOR {target_date.strftime('%d/%m/%Y')}")
    print("="*80)
    
    # Display messages
    print(f"\n📨 MESSAGES ({len(messages)} found):")
    print("-"*80)
    
    if messages:
        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] [{msg['datetime'].strftime('%H:%M:%S')}] {msg['sender']}:")
            print(f"    {msg['text']}")
    else:
        print("    No messages found for this date.")
    
    # Display media files
    print(f"\n\n📎 MEDIA FILES ({len(media_files)} found):")
    print("-"*80)
    
    if media_files:
        # Group by media type
        by_type = {}
        for media in media_files:
            media_type = media['media_type']
            if media_type not in by_type:
                by_type[media_type] = []
            by_type[media_type].append(media)
        
        for media_type in sorted(by_type.keys()):
            files = by_type[media_type]
            print(f"\n  {media_type} ({len(files)} file(s)):")
            for media in files:
                time_str = media['datetime'].strftime('%H:%M:%S')
                size = media['filepath'].stat().st_size
                size_kb = size / 1024
                if size_kb < 1024:
                    size_str = f"{size_kb:.1f} KB"
                else:
                    size_str = f"{size_kb/1024:.1f} MB"
                print(f"    • [{time_str}] {media['filename']} ({size_str})")
    else:
        print("    No media files found for this date.")
    
    print("\n" + "="*80)
    print(f"TOTAL: {len(messages)} message(s) and {len(media_files)} media file(s)")
    print("="*80 + "\n")


def identify_property_related_messages(messages: List[Dict]) -> Optional[List[Dict]]:
    """Identify property-related WhatsApp messages using OpenAI."""
    if not messages:
        return []

    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI analysis skipped: OPENAI_API_KEY environment variable is not set.")
        print("   To enable property analysis, set your API key:")
        print("   Windows PowerShell: $Env:OPENAI_API_KEY = 'sk-your-key-here'")
        print("   Windows CMD: set OPENAI_API_KEY=sk-your-key-here")
        print("   macOS/Linux: export OPENAI_API_KEY='sk-your-key-here'")
        print("   Get your API key from: https://platform.openai.com/account/api-keys")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI analysis skipped: openai package not installed. Run 'pip install openai'.")
        return None
    
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an expert real-estate content analyst. Your ABSOLUTE PRIMARY task is to identify ONLY messages "
        "from PROPERTY SELLERS, AGENTS, or OWNERS who are OFFERING properties for sale or lease.\n\n"
        
        "🚨 CRITICAL RULE - MANDATORY EXCLUSION:\n"
        "If a message contains ANY of these buyer indicators, you MUST EXCLUDE it from results:\n"
        "- 'Looking to buy', 'Want to buy', 'Looking for', 'Seeking', 'Need', 'Required', 'Want to lease', "
        "'Looking to lease', 'Any [property] available', 'Any [property] for lease', 'Any [property] for sale'\n"
        "- 'Budget: X' followed by location/preferences (buyer stating their budget)\n"
        "- 'Purpose: Investment' when combined with location preferences (buyer seeking)\n"
        "- Messages asking 'Any [property type] available in [location]' (buyer inquiry)\n"
        "- Messages describing what the person WANTS, NEEDS, or is LOOKING FOR (buyer requirements)\n"
        "- Messages asking others to share properties or details (buyer inquiries)\n\n"
        
        "✅ ONLY INCLUDE messages that:\n"
        "1. Are from SELLERS/AGENTS/OWNERS OFFERING a specific property\n"
        "2. Contain the phrase 'for Sale', 'for Lease', 'for Rent', 'Available', 'Selling', 'Leasing', "
        "'Offering' in the context of OFFERING a property (not asking if one is available)\n"
        "3. Describe a SPECIFIC property with details (not asking about availability)\n"
        "4. MANDATORY: MUST contain a CONTACT NUMBER (phone number) - messages without contact numbers must be EXCLUDED\n"
        "5. Include property specifications, pricing, location, and contact information\n\n"
        
        "❌ ALWAYS EXCLUDE messages that:\n"
        "1. Ask 'Any [property] available' or 'Any [property] for lease/sale' (buyer inquiry)\n"
        "2. Start with 'Looking to buy', 'Want to buy', 'Looking for', 'Need', 'Required'\n"
        "3. State a budget followed by location preferences (buyer stating requirements)\n"
        "4. Describe what the person WANTS or NEEDS (buyer requirements)\n"
        "5. Ask others to share properties or contact them with property details (buyer inquiry)\n\n"
        
        "MANDATORY EXCLUSION EXAMPLES (DO NOT INCLUDE THESE):\n"
        "❌ 'Any big commercial building available for lease in Nallagandla or Tellapur road. "
        "For shopping mall full building required, like R.S Brothers/ Chandana brothers.' "
        "(BUYER - asking if any building is available)\n"
        "❌ 'Budget: 20 crores( total budget). Looking to buy land. Location: from TUKKUGUDA surrounding "
        "areas to Kalwakurthy. Purpose: Investment. Zone: Residential. Pls reach out on 77940 54285' "
        "(BUYER - stating budget and looking to buy)\n"
        "❌ 'Required 6 cabins, 1 spacious cabin for MD. Location: Near Jubilee enclave. Pls share details' "
        "(BUYER requirement)\n"
        "❌ 'Looking for 2BHK apartment in Gachibowli. Budget: 85 Lakhs' (BUYER inquiry)\n"
        "❌ 'Need office space. Required: 15-20 members working space' (BUYER need)\n\n"
        
        "INCLUSION EXAMPLES (ONLY INCLUDE THESE - from sellers/agents):\n"
        "✅ 'Office Space for Lease!!! 6 cabins available, 1 spacious cabin for MD, 1 conference hall, "
        "15-20 members working space, Min 6 car parkings, Location: Near Jubilee enclave near hitech city. "
        "Pls share details on 77940 54285' (SELLER - offering office space)\n"
        "✅ '2BHK Apartment for Sale in Gachibowli. 1200 sqft, Ready to move, 3rd floor, 2 covered parking, "
        "Price: 85 Lakhs, Contact: 9876543210' (SELLER - offering apartment)\n"
        "✅ 'Land for Sale: 2 acres in Kompally, Clear title, Near highway, 50L per acre, Call for details' "
        "(SELLER - offering land)\n"
        "✅ 'Commercial Property Available for Lease in Hitech City. 5000 sqft, Ground floor, "
        "Contact: 9876543210' (SELLER - offering property)\n\n"
        
        "VALIDATION CHECKLIST - Before including a message, verify:\n"
        "1. Does it OFFER a property? (YES = continue, NO = exclude)\n"
        "2. Does it ASK if a property is available? (YES = exclude immediately)\n"
        "3. Does it contain 'Looking to', 'Want to', 'Need', 'Required', 'Any [property] available'? "
        "(YES = exclude immediately)\n"
        "4. Does it state a budget with location preferences? (YES = exclude immediately)\n"
        "5. Does it describe what the person WANTS or NEEDS? (YES = exclude immediately)\n"
        "6. MANDATORY: Does it contain a CONTACT NUMBER (phone number)? (NO = exclude immediately, even if all other criteria are met)\n\n"
        
        "OUTPUT FORMAT:\n"
        "Return a JSON object with this exact structure:\n"
        "{\n"
        "  \"property_messages\": [\n"
        "    {\n"
        "      \"index\": int,           // Original message index\n"
        "      \"sender\": str,          // Sender name\n"
        "      \"time\": str,            // Time in HH:MM:SS format\n"
        "      \"text\": str,            // Complete original message text (preserve exactly)\n"
        "      \"reason\": str           // Detailed explanation (50-100 words) of why this message "
        "contains sufficient property information to create a webpage, including what specific details "
        "are present (property type, location, specs, pricing, amenities, contact info, etc.)\n"
        "    }\n"
        "  ],\n"
        "  \"notes\": str                // Optional summary or observations\n"
        "}\n\n"
        
        "ABSOLUTE MANDATORY RULES:\n"
        "1. FIRST CHECK: If message contains 'Any [property] available', 'Looking to', 'Want to', 'Need', "
        "'Required', 'Looking for', 'Seeking', 'Budget: X' with location, or 'Purpose: Investment' with location "
        "→ EXCLUDE IMMEDIATELY (this is a buyer message)\n"
        "2. ONLY include messages that OFFER a specific property (contain 'for Sale', 'for Lease', 'Available', "
        "'Selling', 'Leasing' in offering context, NOT in inquiry context)\n"
        "3. MANDATORY REQUIREMENT: ONLY include messages that contain a CONTACT NUMBER (phone number). "
        "Messages without a contact number must be EXCLUDED, even if they have all other property details.\n"
        "4. Contact number patterns to look for: 10-digit phone numbers, numbers with country codes, "
        "numbers written as 'Call: X', 'Contact: X', 'Phone: X', 'Reach out on X', 'Pls share details on X', etc.\n"
        "5. ONLY include messages with COMPLETE property information (property type + location + specifications/amenities/pricing + CONTACT NUMBER)\n"
        "6. EXCLUDE ALL buyer requests, buyer inquiries, buyer requirements, or messages asking if properties are available\n"
        "7. EXCLUDE messages that are vague, incomplete, or lack essential property details\n"
        "8. EXCLUDE messages without contact numbers (even if they have property details)\n"
        "9. EXCLUDE casual conversations, technical discussions, or messages without property content\n"
        "10. PRESERVE the original message text character-by-character - do NOT modify, summarize, or rewrite\n"
        "11. If you identify a message as a buyer inquiry, DO NOT include it in the results, even if it contains property details\n"
        "12. Always respond with valid JSON matching the schema above\n"
        "13. If no seller messages with contact numbers meet the criteria, return {\"property_messages\": [], \"notes\": \"No seller property listings with contact numbers found\"}"
    )

    payload = [
        {
            "index": idx + 1,
            "sender": msg["sender"],
            "time_24h": msg["datetime"].strftime("%H:%M:%S"),
            "text": msg["text"],
        }
        for idx, msg in enumerate(messages)
    ]

    user_content = json.dumps({"messages": payload}, ensure_ascii=False, indent=2)

    try:
        # Try GPT-5 first, fallback to GPT-4o if not available
        try:
            response = client.chat.completions.create(
                model="gpt-5",  # Latest model (if available)
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Identify property-related messages in the following JSON payload. "
                            "Remember to respond with strictly valid JSON.\n\n" + user_content
                        ),
                    },
                ],
            )
        except Exception as gpt5_error:
            # Fallback to GPT-4o if GPT-5 is not available
            if "model" in str(gpt5_error).lower() or "not found" in str(gpt5_error).lower():
                response = client.chat.completions.create(
                    model="gpt-4o",  # Fallback to GPT-4o (latest confirmed model)
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": (
                                "Identify property-related messages in the following JSON payload. "
                                "Remember to respond with strictly valid JSON.\n\n" + user_content
                            ),
                        },
                    ],
                )
            else:
                raise
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            print("❌ OpenAI API authentication failed: Invalid API key.")
            print("   Please verify your OPENAI_API_KEY is correct and has not expired.")
            print("   Get a new key from: https://platform.openai.com/account/api-keys")
        elif "429" in error_msg or "rate_limit" in error_msg.lower():
            print("❌ OpenAI API rate limit exceeded. Please try again later.")
        elif "insufficient_quota" in error_msg.lower():
            print("❌ OpenAI API quota exceeded. Please check your account billing.")
        else:
            print(f"❌ OpenAI analysis failed: {exc}")
        return None

    try:
        content = response.choices[0].message.content if response.choices else "{}"
    except (AttributeError, IndexError):
        print("OpenAI analysis failed: unexpected response format.")
        return None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"OpenAI analysis failed: unable to parse JSON response ({exc}).")
        return None

    property_messages = parsed.get("property_messages", [])

    # Ensure structure integrity
    cleaned = []
    for item in property_messages:
        if not isinstance(item, dict):
            continue
        index = item.get("index")
        text = item.get("text")
        if index is None or text is None:
            continue
        cleaned.append(
            {
                "index": index,
                "sender": item.get("sender", ""),
                "time": item.get("time", ""),
                "text": text,
                "reason": item.get("reason", ""),
            }
        )

    return cleaned


def identify_property_related_images(media_files: List[Dict]) -> Optional[List[Dict]]:
    """
    Identify property-related images using OpenAI Vision API.
    
    Analyzes all image files from the media_files list and identifies those
    containing detailed property-related content suitable for webpage creation.
    
    Args:
        media_files: List of media file dictionaries from extract_media_files_for_date
        
    Returns:
        Optional[List[Dict]]: List of property-related image dictionaries, or None if analysis fails
    """
    if not media_files:
        return []
    
    # Filter only image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    image_files = [
        media for media in media_files 
        if Path(media['filename']).suffix.lower() in image_extensions
    ]
    
    if not image_files:
        return []
    
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI image analysis skipped: OPENAI_API_KEY environment variable is not set.")
        print("   To enable image analysis, set your API key:")
        print("   Windows PowerShell: $Env:OPENAI_API_KEY = 'sk-your-key-here'")
        print("   Windows CMD: set OPENAI_API_KEY=sk-your-key-here")
        print("   macOS/Linux: export OPENAI_API_KEY='sk-your-key-here'")
        print("   Get your API key from: https://platform.openai.com/account/api-keys")
        return None
    
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI image analysis skipped: openai package not installed. Run 'pip install openai'.")
        return None
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = (
        "You are an expert real-estate visual content analyst specializing in identifying property-related "
        "images from SELLERS, AGENTS, or OWNERS that contain sufficient detail to create professional "
        "property listing webpages. Your CRITICAL task is to identify images that represent properties "
        "AVAILABLE FOR SALE OR LEASE, not images from buyers seeking properties.\n\n"
        
        "CRITICAL DISTINCTION:\n"
        "✅ INCLUDE: Images showing properties being OFFERED for sale/lease (property listings, "
        "brochures, floor plans, property photos, availability documents)\n"
        "❌ EXCLUDE: Images from buyers (requirement documents, buyer wish lists, screenshots of "
        "what buyers are looking for, buyer inquiry forms)\n\n"
        
        "CRITICAL CRITERIA - An image must:\n"
        "1. Represent a property AVAILABLE FOR SALE OR LEASE (from seller/agent/owner perspective)\n"
        "2. Contain ENOUGH VISUAL DETAIL to build a webpage\n"
        "3. Show one or more of the following:\n"
        "   - Property Exteriors: Building facades, apartment complexes, office buildings, commercial spaces, "
        "land plots with clear boundaries (properties being offered)\n"
        "   - Property Interiors: Rooms, kitchens, bathrooms, living spaces, office cabins, conference halls, "
        "commercial showrooms with visible features (available properties)\n"
        "   - Property Listing Documents: Brochures, floor plans, site plans, layout diagrams, RERA certificates, "
        "property documents with visible text showing property details, pricing, availability\n"
        "   - Location/Area Views: Neighborhood views, nearby landmarks, connectivity features, area maps "
        "(for properties being offered)\n"
        "   - Amenities: Parking areas, elevators, swimming pools, gyms, gardens, security features, "
        "common areas, clubhouses (of available properties)\n"
        "   - Property Details in Text: Images containing text with property specifications, pricing, "
        "location details, contact information, project names, builder details, 'for sale', 'for lease', "
        "'available' keywords\n\n"
        
        "EXAMPLES OF GOOD IMAGES (include these - seller/agent property listings):\n"
        "- Photos of apartment interiors showing rooms, kitchen, bathroom (properties for sale/lease)\n"
        "- Building exteriors showing the complete property structure (available properties)\n"
        "- Floor plans or layout diagrams with dimensions and room details (property listings)\n"
        "- Property brochures with text containing specifications, pricing, location, 'for sale/lease' "
        "(seller marketing materials)\n"
        "- Office spaces showing cabins, conference rooms, work areas (available for lease)\n"
        "- Land plots with clear boundaries and location markers (land for sale)\n"
        "- RERA certificates or property documents showing property details (seller documents)\n\n"
        
        "EXAMPLES OF IMAGES TO EXCLUDE:\n"
        "- Screenshots of buyer requirements or wish lists\n"
        "- Images showing what buyers are looking for (buyer perspective)\n"
        "- Buyer inquiry forms or requirement documents\n"
        "- Screenshots of error messages or system interfaces\n"
        "- Casual photos without property context\n"
        "- Generic images without property-specific content\n"
        "- Blurry or unclear images where property details cannot be discerned\n"
        "- Images that are too generic or lack property-specific information\n\n"
        
        "OUTPUT FORMAT:\n"
        "Return a JSON object with this exact structure:\n"
        "{\n"
        "  \"property_images\": [\n"
        "    {\n"
        "      \"filename\": str,        // Original filename\n"
        "      \"time\": str,            // Time in HH:MM:SS format\n"
        "      \"reason\": str           // Detailed explanation (50-100 words) of what property "
        "information is visible in the image and why it contains sufficient detail to create a webpage. "
        "Describe specific visible elements (property type, features, amenities, text content, etc.)\n"
        "    }\n"
        "  ],\n"
        "  \"notes\": str                // Optional summary or observations\n"
        "}\n\n"
        
        "STRICT RULES:\n"
        "1. ONLY include images representing properties AVAILABLE FOR SALE OR LEASE (from seller/agent/owner)\n"
        "2. EXCLUDE images from buyers (requirement documents, buyer wish lists, buyer inquiries)\n"
        "3. ONLY include images with CLEAR and DETAILED property content suitable for webpage creation\n"
        "4. EXCLUDE generic, unclear, or non-property-related images\n"
        "5. Provide detailed reasons (50-100 words) explaining why this is a seller property image and what property information is visible\n"
        "6. Always respond with valid JSON matching the schema above\n"
        "7. If no images meet the criteria, return {\"property_images\": [], \"notes\": \"No seller property images with sufficient details found\"}"
    )
    
    property_images = []
    
    # Process images in batches to avoid token limits
    batch_size = 5  # Process 5 images at a time
    
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i + batch_size]
        
        # Prepare image content for API
        image_contents = []
        for media in batch:
            try:
                file_path = media['filepath']
                # Read and encode image
                with open(file_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Determine MIME type
                ext = file_path.suffix.lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(ext, 'image/jpeg')
                
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                })
            except Exception as e:
                print(f"Warning: Could not process image {media['filename']}: {e}")
                continue
        
        if not image_contents:
            continue
        
        # Create user message with image references
        # Create a mapping of image index to filename for the API
        image_info = []
        for idx, media in enumerate(batch):
            image_info.append(f"Image {idx + 1}: {media['filename']} (Time: {media['datetime'].strftime('%H:%M:%S')})")
        
        user_content_parts = [
            {
                "type": "text",
                "text": (
                    f"Analyze the following {len(batch)} image(s) and identify which ones contain "
                    "detailed property-related content suitable for creating a property listing webpage. "
                    "For each property-related image, provide the EXACT filename (as shown below) and a detailed reason.\n\n"
                    "Image filenames and times (in order):\n" +
                    "\n".join(image_info) +
                    "\n\nIMPORTANT: When returning results, use the EXACT filename as shown above for each image."
                )
            }
        ] + image_contents
        
        try:
            # Try GPT-5 first, fallback to GPT-4o if not available
            try:
                response = client.chat.completions.create(
                    model="gpt-5",  # Latest model with vision (if available)
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content_parts}
                    ],
                    max_tokens=2000
                )
            except Exception as gpt5_error:
                # Fallback to GPT-4o if GPT-5 is not available
                if "model" in str(gpt5_error).lower() or "not found" in str(gpt5_error).lower():
                    response = client.chat.completions.create(
                        model="gpt-4o",  # Fallback to GPT-4o (latest confirmed model with vision)
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content_parts}
                        ],
                        max_tokens=2000
                    )
                else:
                    raise
        except Exception as exc:
            error_msg = str(exc)
            if "401" in error_msg or "invalid_api_key" in error_msg.lower():
                print(f"❌ OpenAI image analysis failed: Invalid API key.")
                print("   Please verify your OPENAI_API_KEY is correct and has not expired.")
                print("   Get a new key from: https://platform.openai.com/account/api-keys")
                break  # Stop processing remaining batches
            elif "429" in error_msg or "rate_limit" in error_msg.lower():
                print(f"⚠️  OpenAI API rate limit exceeded for image batch. Continuing with remaining images...")
                continue
            elif "insufficient_quota" in error_msg.lower():
                print(f"❌ OpenAI API quota exceeded. Cannot process images.")
                break
            else:
                print(f"⚠️  OpenAI image analysis failed for batch: {exc}")
                continue
        
        try:
            content = response.choices[0].message.content if response.choices else "{}"
        except (AttributeError, IndexError):
            print("OpenAI image analysis failed: unexpected response format.")
            continue
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            print(f"OpenAI image analysis failed: unable to parse JSON response ({exc}).")
            continue
        
        batch_results = parsed.get("property_images", [])
        
        # Match results back to original media files
        for result in batch_results:
            filename = result.get("filename", "")
            matching_media = next(
                (m for m in batch if m['filename'] == filename),
                None
            )
            if matching_media:
                property_images.append({
                    "filename": filename,
                    "filepath": matching_media['filepath'],
                    "time": matching_media['datetime'].strftime('%H:%M:%S'),
                    "media_type": matching_media.get('media_type', 'PHOTO'),
                    "reason": result.get("reason", "")
                })
    
    return property_images


def generate_html_webpage(message: Dict, template_path: str, output_path: str) -> Optional[str]:
    """
    Generate an HTML webpage for a property message using OpenAI.
    
    Args:
        message: Property message dictionary with index, sender, time, text, reason
        template_path: Path to the sample.html template file
        output_path: Path where the generated HTML should be saved
        
    Returns:
        Generated HTML content as string, or None if generation fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"⚠️  HTML generation skipped for message #{message.get('index')}: OPENAI_API_KEY not set.")
        return None
    
    try:
        from openai import OpenAI
    except ImportError:
        print(f"⚠️  HTML generation skipped for message #{message.get('index')}: openai package not installed.")
        return None
    
    client = OpenAI(api_key=api_key)
    
    # Read the template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return None
    
    system_prompt = (
        "You are an expert web developer specializing in creating property listing webpages. "
        "Your task is to update the provided HTML template with property information from a WhatsApp message, "
        "while STRICTLY maintaining the template's structure, theme, and styling.\n\n"
        
        "CRITICAL RULES - TEMPLATE PRESERVATION:\n"
        "1. PRESERVE the exact HTML structure, CSS classes, and layout of the template\n"
        "2. KEEP all CSS styles exactly as provided - do NOT modify colors, fonts, spacing, or design elements\n"
        "3. MAINTAIN the red and white color scheme (--primary-red: #C21807, --dark-red: #9F1205, etc.)\n"
        "4. KEEP the same section structure: Header → Hero → Image Gallery → Details Grid → Footer\n"
        "5. PRESERVE all CSS variables, animations, and responsive breakpoints\n"
        "6. KEEP the footer brand 'WWW.HOMEHNI.COM' unchanged\n\n"
        
        "CONTENT POPULATION - What to Update:\n"
        "1. Header: Update property-type-badge with actual property type (e.g., 'APARTMENT / FLAT', 'OFFICE SPACE', 'LAND', etc.)\n"
        "2. Hero Section:\n"
        "   - property-title: Extract property name/title from message\n"
        "   - property-subtitle: Extract society/project/builder name\n"
        "   - property-location: Extract and format location details\n"
        "3. Image Gallery: Use 'apple.avif' for all 4 images (keep same image 4 times)\n"
        "4. Features Section:\n"
        "   - tags-container: Extract property features (BHK, Sq Ft, Furnishing, etc.) and create appropriate tags\n"
        "   - description: If message has additional details, create a brief description paragraph\n"
        "5. Price Card: Extract and display price in the format '₹ X,XX,XX,XXX'\n"
        "6. Contact Card: Extract phone numbers and email addresses from the message\n\n"
        
        "ADDITIONAL CONTENT - When to Add:\n"
        "If the message contains useful additional information that doesn't fit existing sections, you may:\n"
        "1. Add more tags to the tags-container (e.g., 'Ready to Move', 'RERA Approved', 'Parking Available')\n"
        "2. Expand the description section with additional property details\n"
        "3. Add more contact items if multiple phone numbers are provided\n"
        "4. Add amenities or features as new tags\n\n"
        "HOWEVER, when adding content:\n"
        "- Use ONLY existing CSS classes and structure\n"
        "- Do NOT create new CSS classes or modify existing styles\n"
        "- Follow the same visual pattern as the template\n"
        "- Keep the same spacing and layout proportions\n\n"
        
        "STRICT PROHIBITIONS:\n"
        "1. DO NOT modify CSS colors, fonts, or styling variables\n"
        "2. DO NOT change the HTML structure or add new sections\n"
        "3. DO NOT remove or modify CSS classes\n"
        "4. DO NOT change the responsive breakpoints or media queries\n"
        "5. DO NOT alter the header, footer, or overall layout structure\n"
        "6. DO NOT use different image sources - always use 'apple.avif'\n\n"
        
        "EXTRACTION GUIDELINES:\n"
        "- Extract property type from keywords: 'apartment', 'flat', 'office', 'land', 'commercial', 'residential', etc.\n"
        "- Extract location from phrases like 'in [location]', 'at [location]', 'near [location]'\n"
        "- Extract size from patterns: 'X sqft', 'X sqm', 'X BHK', 'X acres', etc.\n"
        "- Extract price from: '₹ X', 'Rs X', 'X Lakhs', 'X Crores', 'Price: X', etc.\n"
        "- Extract contact from: phone numbers (10 digits), email addresses\n"
        "- Extract features: 'furnished', 'semi-furnished', 'unfurnished', 'parking', 'elevator', etc.\n\n"
        
        "OUTPUT FORMAT:\n"
        "- Return ONLY the complete, valid HTML code\n"
        "- No explanations, no markdown code blocks, just pure HTML\n"
        "- Ensure all HTML is properly formatted and valid\n"
        "- Preserve all original CSS and structure\n"
    )
    
    user_prompt = (
        f"Update the following HTML template with property information from this WhatsApp message:\n\n"
        f"MESSAGE TEXT:\n{message.get('text', '')}\n\n"
        f"HTML TEMPLATE:\n{template_html}\n\n"
        f"Generate the updated HTML webpage that accurately represents this property listing. "
        f"Use 'apple.avif' for all 4 property images. Return ONLY the complete HTML code."
    )
    
    try:
        # Try GPT-5 first, fallback to GPT-4o if not available
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent output
            )
        except Exception as gpt5_error:
            if "model" in str(gpt5_error).lower() or "not found" in str(gpt5_error).lower():
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
            else:
                raise
        
        html_content = response.choices[0].message.content.strip()
        
        # Clean up the HTML if it's wrapped in markdown code blocks
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        elif html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()
        
        # Save to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return html_content
        except Exception as e:
            print(f"❌ Error saving HTML to {output_path}: {e}")
            return None
            
    except Exception as exc:
        print(f"❌ HTML generation failed for message #{message.get('index')}: {exc}")
        return None


def convert_html_to_pdf(html_file_path: str, pdf_file_path: str) -> bool:
    """
    Convert an HTML file to PDF using playwright (headless browser).
    Optimized to fit content in 2 pages with proper alignment.
    Works on Windows, macOS, and Linux.
    
    Args:
        html_file_path: Path to the HTML file
        pdf_file_path: Path where the PDF should be saved
        
    Returns:
        True if conversion successful, False otherwise
    """
    # Try playwright first (best for Windows)
    try:
        from playwright.sync_api import sync_playwright
        use_playwright = True
    except ImportError:
        use_playwright = False
        # Fallback to weasyprint if available (for Linux/macOS)
        try:
            from weasyprint import HTML
            use_weasyprint = True
        except ImportError:
            use_weasyprint = False
    
    if not use_playwright and not use_weasyprint:
        print("⚠️  No PDF library found. Install one of the following:")
        print("   - playwright (recommended for Windows): pip install playwright && playwright install chromium")
        print("   - weasyprint (Linux/macOS): pip install weasyprint")
        return False
    
    try:
        html_path = Path(html_file_path)
        if not html_path.exists():
            print(f"❌ HTML file not found: {html_file_path}")
            return False
        
        # Use absolute path for file:// URL
        abs_html_path = html_path.resolve()
        file_url = f"file:///{abs_html_path.as_posix()}"
        
        if use_playwright:
            # Use Playwright with headless Chrome (works on Windows)
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(file_url, wait_until="networkidle")
                
                # Inject CSS to optimize for 2-page PDF layout
                page.add_style_tag(content="""
                    @media print {
                        body {
                            font-size: 12px !important;
                            line-height: 1.4 !important;
                        }
                        .hero-section {
                            padding: 30px 20px !important;
                            min-height: 200px !important;
                        }
                        .property-title {
                            font-size: 32px !important;
                            margin-bottom: 10px !important;
                        }
                        .property-subtitle {
                            font-size: 18px !important;
                            margin-bottom: 10px !important;
                        }
                        .property-location {
                            font-size: 16px !important;
                        }
                        .image-gallery {
                            grid-template-columns: repeat(2, 1fr) !important;
                            gap: 10px !important;
                            margin-bottom: 20px !important;
                        }
                        .gallery-item {
                            aspect-ratio: 4/3 !important;
                        }
                        .details-grid {
                            gap: 20px !important;
                            margin-bottom: 20px !important;
                        }
                        .features-section, .price-card, .contact-card {
                            padding: 20px !important;
                        }
                        .section-title {
                            font-size: 20px !important;
                            margin-bottom: 15px !important;
                        }
                        .tag {
                            padding: 8px 16px !important;
                            font-size: 12px !important;
                        }
                        .description {
                            font-size: 14px !important;
                            line-height: 1.5 !important;
                            margin-top: 15px !important;
                        }
                        .price-value {
                            font-size: 36px !important;
                        }
                        .contact-title {
                            font-size: 18px !important;
                            margin-bottom: 15px !important;
                        }
                        .contact-item {
                            padding: 10px !important;
                        }
                        .contact-item strong, .contact-item span {
                            font-size: 14px !important;
                        }
                        .footer {
                            padding: 20px !important;
                            margin-top: 20px !important;
                        }
                        .footer-brand {
                            font-size: 24px !important;
                        }
                        .container {
                            padding: 20px !important;
                        }
                    }
                """)
                
                # Generate PDF optimized for 2 pages
                page.pdf(
                    path=pdf_file_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "0.8cm", "right": "0.8cm", "bottom": "0.8cm", "left": "0.8cm"},
                    prefer_css_page_size=False,
                    scale=0.95  # Slightly scale down to ensure content fits
                )
                browser.close()
        else:
            # Fallback to weasyprint (for Linux/macOS)
            HTML(filename=str(html_path)).write_pdf(pdf_file_path)
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "executable doesn't exist" in error_msg.lower() or "chromium" in error_msg.lower():
            print(f"❌ Playwright browser not installed. Run: playwright install chromium")
        else:
            print(f"❌ PDF conversion failed for {html_file_path}: {e}")
        return False


def upload_file_to_hostinger(file_path: str, subdirectory: str = None) -> Optional[str]:
    """
    Upload a file to Hostinger via FTP and return the public URL.
    
    Args:
        file_path: Path to the local file to upload
        subdirectory: Optional subdirectory (e.g., "propertypages" for HTML, "propertypdfs" for PDF)
        
    Returns:
        Public URL of the uploaded file, or None if upload fails
    """
    # Get FTP credentials from environment variables
    ftp_host = os.getenv("HOSTINGER_FTP_HOST")
    ftp_user = os.getenv("HOSTINGER_FTP_USER")
    ftp_password = os.getenv("HOSTINGER_FTP_PASSWORD")
    ftp_port = int(os.getenv("HOSTINGER_FTP_PORT", "21"))
    
    # Determine directory - prioritize HOSTINGER_FTP_DIR from .env file
    local_path = Path(file_path)
    
    # Get base URL from .env file
    base_url = os.getenv("HOSTINGER_BASE_URL", "").rstrip('/')
    
    # Check if HOSTINGER_FTP_DIR is set in .env (user's preference)
    env_ftp_dir = os.getenv("HOSTINGER_FTP_DIR")
    
    if env_ftp_dir:
        # Use the directory from .env file (respects user's configuration)
        ftp_dir = env_ftp_dir
        # Use HOSTINGER_BASE_URL directly if set, otherwise construct from FTP host
        if base_url:
            public_url_base = base_url
        else:
            # Extract domain from FTP host and construct URL
            domain = (ftp_host or '').replace('ftp.', '')
            public_url_base = f"https://{domain}{env_ftp_dir}" if domain else None
    elif subdirectory:
        # Fallback: construct path if HOSTINGER_FTP_DIR not set
        ftp_dir = f"/public_html/{subdirectory}"
        if base_url:
            public_url_base = f"{base_url}/{subdirectory}"
        else:
            public_url_base = f"https://{os.getenv('HOSTINGER_FTP_HOST', '').replace('ftp.', '')}/{subdirectory}"
    else:
        # Default fallback
        ftp_dir = "/public_html/propertypages"
        if base_url:
            public_url_base = base_url
        else:
            public_url_base = f"https://{os.getenv('HOSTINGER_FTP_HOST', '').replace('ftp.', '')}"
    
    if not all([ftp_host, ftp_user, ftp_password]):
        print(f"⚠️  Hostinger FTP credentials not configured. Skipping upload for {file_path}")
        print("   Required environment variables:")
        print("   - HOSTINGER_FTP_HOST")
        print("   - HOSTINGER_FTP_USER")
        print("   - HOSTINGER_FTP_PASSWORD")
        print("   - HOSTINGER_FTP_PORT (optional, default: 21)")
        print("   - HOSTINGER_FTP_DIR (for HTML and PDF, optional, default: /public_html/propertypages)")
        print("   - HOSTINGER_BASE_URL")
        return None
    
    if not local_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        # Connect to FTP server
        ftp = ftplib.FTP()
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_password)
        
        # Change to the target directory
        try:
            ftp.cwd(ftp_dir)
        except ftplib.error_perm:
            # Directory might not exist, try to create it
            print(f"⚠️  Directory {ftp_dir} not found. Attempting to create...")
            # Try to create directory (this may fail if permissions don't allow)
            try:
                parts = ftp_dir.strip('/').split('/')
                current_path = ''
                for part in parts:
                    current_path += '/' + part
                    try:
                        ftp.cwd(current_path)
                    except ftplib.error_perm:
                        ftp.mkd(current_path)
                        ftp.cwd(current_path)
            except Exception as e:
                print(f"❌ Could not create directory {ftp_dir}: {e}")
                ftp.quit()
                return None
        
        # Upload the file
        filename = local_path.name
        with open(local_path, 'rb') as fobj:
            ftp.storbinary(f'STOR {filename}', fobj)
        
        ftp.quit()
        
        # Construct the public URL
        public_url = f"{public_url_base.rstrip('/')}/{filename}"
        print(f"✅ Successfully uploaded {filename} to Hostinger")
        return public_url
        
    except ftplib.error_perm as e:
        print(f"❌ FTP permission error: {e}")
        return None
    except ftplib.error_temp as e:
        print(f"❌ FTP temporary error: {e}")
        return None
    except Exception as e:
        print(f"❌ FTP upload failed for {file_path}: {e}")
        return None


def upload_pdf_to_hostinger(pdf_file_path: str) -> Optional[str]:
    """
    Backwards-compatible wrapper to upload a PDF using the generic uploader.
    """
    return upload_file_to_hostinger(pdf_file_path)


def extract_contact_numbers(message_text: str) -> List[str]:
    """
    Extract contact phone numbers from a message text.
    
    Supports various formats:
    - 10-digit numbers
    - Numbers with country codes
    - Numbers written as "Call: X", "Contact: X", "Phone: X", etc.
    - Numbers in "Reach out on X", "Pls share details on X" format
    
    Args:
        message_text: The message text to extract phone numbers from
        
    Returns:
        List of valid phone numbers (normalized to include country code if needed)
    """
    phone_numbers = []
    
    # Pattern to match various phone number formats
    # Matches: 10-digit numbers, numbers with spaces/dashes, country codes
    patterns = [
        # 10-digit Indian numbers (most common)
        r'\b(\d{10})\b',
        # Numbers with country code +91
        r'\+91[\s-]?(\d{10})',
        # Numbers written as "Call: X", "Contact: X", "Phone: X"
        r'(?:Call|Contact|Phone|Reach out|share details|details on)[\s:]+(\d{10,12})',
        # Numbers with spaces or dashes: 123 456 7890 or 123-456-7890
        r'\b(\d{3}[\s-]?\d{3}[\s-]?\d{4})\b',
        # Numbers in parentheses or brackets
        r'[\(\[{](\d{10,12})[\)\]}]',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message_text, re.IGNORECASE)
        for match in matches:
            # Clean the number (remove spaces, dashes)
            cleaned = re.sub(r'[\s\-]', '', str(match))
            # Validate it's a reasonable length (10-12 digits)
            if len(cleaned) >= 10 and len(cleaned) <= 12:
                # Normalize to include country code if it's a 10-digit number
                if len(cleaned) == 10:
                    # Assume Indian number, add +91
                    normalized = f"+91{cleaned}"
                elif cleaned.startswith('91') and len(cleaned) == 12:
                    normalized = f"+{cleaned}"
                elif cleaned.startswith('+91'):
                    normalized = cleaned
                else:
                    normalized = cleaned
                
                # Avoid duplicates
                if normalized not in phone_numbers:
                    phone_numbers.append(normalized)
    
    return phone_numbers


def send_whatsapp_pdf(phone_number: str, pdf_url: str, message_text: str = "") -> bool:
    """
    Send a PDF file via WhatsApp using Twilio API.
    
    Args:
        phone_number: Recipient phone number (with country code, e.g., +919876543210)
        pdf_url: Public URL of the PDF file to send
        message_text: Optional text message to send along with the PDF
        
    Returns:
        True if sent successfully, False otherwise
    """
    # Get Twilio credentials from environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    
    if not account_sid or not auth_token or not from_number:
        print(f"⚠️  Twilio credentials not configured. Skipping WhatsApp send to {phone_number}")
        return False
    
    try:
        from twilio.rest import Client
    except ImportError:
        print(f"⚠️  Twilio package not installed. Run 'pip install twilio'. Skipping WhatsApp send.")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Format phone number for WhatsApp (ensure it starts with whatsapp:)
        if not phone_number.startswith("whatsapp:"):
            whatsapp_number = f"whatsapp:{phone_number}"
        else:
            whatsapp_number = phone_number
        
        if not from_number.startswith("whatsapp:"):
            from_whatsapp = f"whatsapp:{from_number}"
        else:
            from_whatsapp = from_number
        
        # Prepare message text
        if not message_text:
            message_text = "Hello! Here is your property listing preview."
        
        # Send message with PDF attachment
        message = client.messages.create(
            body=message_text,
            from_=from_whatsapp,
            to=whatsapp_number,
            media_url=[pdf_url]
        )
        
        return True
        
    except Exception as exc:
        error_msg = str(exc)
        if "21211" in error_msg or "invalid" in error_msg.lower():
            print(f"❌ Invalid phone number: {phone_number}")
        elif "21608" in error_msg or "rate limit" in error_msg.lower():
            print(f"⚠️  Rate limit exceeded. Please try again later.")
        elif "21614" in error_msg:
            print(f"❌ Unsubscribed number: {phone_number}")
        elif "media" in error_msg.lower() or "url" in error_msg.lower():
            print(f"⚠️  Media URL issue. Ensure PDF URL is accessible: {pdf_url}")
        else:
            print(f"❌ WhatsApp send failed to {phone_number}: {exc}")
        return False


def send_whatsapp_cta_message(phone_number: str, onboarding_link: str = "") -> bool:
    """
    Send the call-to-action message via WhatsApp.
    
    Args:
        phone_number: Recipient phone number (with country code, e.g., +919876543210)
        onboarding_link: HomeHNI onboarding link (if empty, uses placeholder)
        
    Returns:
        True if sent successfully, False otherwise
    """
    # Get Twilio credentials from environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    
    if not account_sid or not auth_token or not from_number:
        print(f"⚠️  Twilio credentials not configured. Skipping CTA message to {phone_number}")
        return False
    
    try:
        from twilio.rest import Client
    except ImportError:
        print(f"⚠️  Twilio package not installed. Run 'pip install twilio'. Skipping WhatsApp send.")
        return False
    
    # Use placeholder if link not provided
    if not onboarding_link:
        onboarding_link = "<link>"  # Placeholder - user will provide later
    
    cta_message = (
        "Hello from HomeHNI, this is how your property posting will look on our platform, "
        f"click on this link, to get started with your journey of posting properties through HomeHNI!!! {onboarding_link}"
    )
    
    try:
        client = Client(account_sid, auth_token)
        
        # Format phone number for WhatsApp
        if not phone_number.startswith("whatsapp:"):
            whatsapp_number = f"whatsapp:{phone_number}"
        else:
            whatsapp_number = phone_number
        
        if not from_number.startswith("whatsapp:"):
            from_whatsapp = f"whatsapp:{from_number}"
        else:
            from_whatsapp = from_number
        
        # Send CTA message
        message = client.messages.create(
            body=cta_message,
            from_=from_whatsapp,
            to=whatsapp_number
        )
        
        return True
        
    except Exception as exc:
        error_msg = str(exc)
        if "21211" in error_msg or "invalid" in error_msg.lower():
            print(f"❌ Invalid phone number: {phone_number}")
        elif "21608" in error_msg or "rate limit" in error_msg.lower():
            print(f"⚠️  Rate limit exceeded. Please try again later.")
        elif "21614" in error_msg:
            print(f"❌ Unsubscribed number: {phone_number}")
        else:
            print(f"❌ CTA message send failed to {phone_number}: {exc}")
        return False


def send_webpages_via_whatsapp(property_messages: Optional[List[Dict]], generated_files: List[Dict], onboarding_link: str = ""):
    """
    Send generated HTML and PDF links via WhatsApp to contact numbers in property messages.
    Sends 3 messages in sequence:
    1. HTML preview link
    2. PDF link
    3. CTA message with onboarding link
    
    Args:
        property_messages: List of property message dictionaries
        generated_files: List of dictionaries with 'html_file', 'html_url', 'pdf_file', and 'pdf_url' keys
        onboarding_link: HomeHNI onboarding link (optional, uses placeholder if not provided)
    """
    if not property_messages or not generated_files:
        print("\n⚠️  No property messages or generated files to send via WhatsApp.")
        return
    
    print(f"\n{'='*80}")
    print(f"SENDING PROPERTY PREVIEW LINKS VIA WHATSAPP (3 MESSAGES PER PROPERTY)")
    print(f"{'='*80}\n")
    
    # Check Twilio configuration
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    
    if not account_sid or not auth_token or not from_number:
        print("⚠️  Twilio WhatsApp not configured. Skipping WhatsApp sending.")
        print("   To enable WhatsApp sending, set the following environment variables:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_WHATSAPP_FROM (your WhatsApp Business number)")
        return
    
    successful_html_sends = 0
    failed_html_sends = 0
    successful_pdf_sends = 0
    failed_pdf_sends = 0
    successful_cta_sends = 0
    failed_cta_sends = 0
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
    except ImportError:
        print("⚠️  Twilio package not installed. Run 'pip install twilio'. Skipping WhatsApp send.")
        return
    
    for idx, message in enumerate(property_messages):
        if idx >= len(generated_files):
            break
        
        file_info = generated_files[idx]
        html_url = file_info.get('html_url')
        pdf_url = file_info.get('pdf_url')
        html_file = file_info.get('html_file', 'Unknown')
        message_text = message.get('text', '')
        
        # Extract contact numbers from the message
        contact_numbers = extract_contact_numbers(message_text)
        
        if not contact_numbers:
            print(f"⚠️  No contact number found in message #{message.get('index')}. Skipping {html_file}")
            failed_html_sends += 1
            failed_pdf_sends += 1
            failed_cta_sends += 1
            continue
        
        if not html_url:
            print(f"⚠️  No HTML URL available for {html_file}. Skipping WhatsApp send.")
            failed_html_sends += 1
            failed_pdf_sends += 1
            failed_cta_sends += 1
            continue
        
        # Send to each contact number found in the message
        for phone_number in contact_numbers:
            print(f"\nSending to {phone_number}...")
            
            # Format phone numbers for WhatsApp
            if not phone_number.startswith("whatsapp:"):
                whatsapp_number = f"whatsapp:{phone_number}"
            else:
                whatsapp_number = phone_number

            if not from_number.startswith("whatsapp:"):
                from_whatsapp = f"whatsapp:{from_number}"
            else:
                from_whatsapp = from_number
            
            # Step 1: Send HTML preview link as first message
            print(f"  → Sending HTML preview link...")
            try:
                html_body = f"Hello! Here is your property listing preview: {html_url}"
                client.messages.create(
                    body=html_body,
                    from_=from_whatsapp,
                    to=whatsapp_number,
                )
                print(f"  ✅ HTML preview link sent successfully")
                successful_html_sends += 1
            except Exception as exc:
                print(f"  ❌ HTML preview link send failed: {exc}")
                failed_html_sends += 1
                # Continue to try PDF and CTA even if HTML fails
                failed_pdf_sends += 1
                failed_cta_sends += 1
                continue

            # Delay between messages
            time.sleep(2)

            # Step 2: Send PDF link as second message
            if pdf_url:
                print(f"  → Sending PDF link...")
                try:
                    pdf_body = f"Here is the PDF version of your property listing: {pdf_url}"
                    client.messages.create(
                        body=pdf_body,
                        from_=from_whatsapp,
                        to=whatsapp_number,
                    )
                    print(f"  ✅ PDF link sent successfully")
                    successful_pdf_sends += 1
                except Exception as exc:
                    print(f"  ❌ PDF link send failed: {exc}")
                    failed_pdf_sends += 1
            else:
                print(f"  ⚠️  No PDF URL available. Skipping PDF message.")
                failed_pdf_sends += 1

            # Delay between messages
            time.sleep(2)

            # Step 3: Send CTA message as third message
            print(f"  → Sending CTA message...")
            cta_success = send_whatsapp_cta_message(phone_number, onboarding_link)
            
            if cta_success:
                print(f"  ✅ CTA message sent successfully")
                successful_cta_sends += 1
            else:
                print(f"  ❌ CTA message failed")
                failed_cta_sends += 1
            
            # Delay between different recipients to avoid rate limiting
            time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"WHATSAPP SENDING SUMMARY:")
    print(f"  HTML Preview Messages:")
    print(f"    Successful: {successful_html_sends}")
    print(f"    Failed: {failed_html_sends}")
    print(f"  PDF Messages:")
    print(f"    Successful: {successful_pdf_sends}")
    print(f"    Failed: {failed_pdf_sends}")
    print(f"  CTA Messages:")
    print(f"    Successful: {successful_cta_sends}")
    print(f"    Failed: {failed_cta_sends}")
    print(f"{'='*80}\n")


def _build_safe_filename(message: Dict, used_names: set) -> str:
    """
    Build a unique, filesystem-safe base filename for a property message.
    
    Format (best-effort):
        <sender>_<time>_<index>
    
    Where:
        - sender: message sender name (spaces -> -, non-alnum removed)
        - time  : message time (HH-MM-SS or HH-MM) with ':' replaced by '-'
        - index : original message index in the chat
    
    A numeric suffix is appended if the name already exists in used_names.
    """
    sender = (message.get("sender") or "property").strip()
    # Take only first line of sender in case of weird values
    sender = sender.splitlines()[0]
    
    time_str = (message.get("time") or "").strip()
    time_safe = time_str.replace(":", "-").replace(" ", "_")
    
    index = message.get("index")
    index_part = f"{index}" if index is not None else ""
    
    parts = [sender, time_safe, index_part]
    # Join non-empty parts with underscore
    base = "_".join([p for p in parts if p])
    if not base:
        base = "property"
    
    # Lowercase and keep only safe chars
    base = base.lower()
    base = re.sub(r"[^a-z0-9_\-]+", "-", base)
    # Collapse multiple dashes/underscores
    base = re.sub(r"[-_]+", "-", base).strip("-_")
    
    if not base:
        base = "property"
    
    original_base = base
    counter = 1
    while base in used_names:
        base = f"{original_base}-{counter}"
        counter += 1
    
    used_names.add(base)
    return base


def generate_webpages_for_properties(property_messages: Optional[List[Dict]], template_path: str = "sample.html"):
    """
    Generate HTML webpages and PDFs for each identified property message.
    Uploads both HTML and PDF files to Hostinger and returns their public URLs.
    
    Args:
        property_messages: List of property message dictionaries
        template_path: Path to the sample.html template file
        
    Returns:
        List of dictionaries with 'html_file', 'html_url', 'pdf_file', and 'pdf_url' keys
    """
    if not property_messages:
        print("\n⚠️  No property messages to generate webpages for.")
        return []
    
    print(f"\n{'='*80}")
    print(f"GENERATING HTML WEBPAGES AND PDFs FOR {len(property_messages)} PROPERTY LISTING(S)")
    print(f"{'='*80}\n")
    
    generated_files = []
    used_names: set = set()
    
    for idx, message in enumerate(property_messages):
        # Build a unique, descriptive filename per message
        base_name = _build_safe_filename(message, used_names)
        html_path = f"{base_name}.html"
        pdf_path = f"{base_name}.pdf"
        
        print(f"\nProcessing message #{message.get('index')}...")
        
        # Step 1: Generate HTML webpage
        print(f"  → Generating HTML: {html_path}")
        html_content = generate_html_webpage(message, template_path, html_path)
        
        if not html_content:
            print(f"  ❌ Failed to generate {html_path}. Skipping PDF conversion and upload.")
            continue
        
        print(f"  ✅ Successfully generated {html_path}")
        
        # Step 2: Convert HTML to PDF
        print(f"  → Converting HTML to PDF: {pdf_path}")
        pdf_success = convert_html_to_pdf(html_path, pdf_path)
        
        if not pdf_success:
            print(f"  ⚠️  PDF conversion failed. Continuing with HTML upload only.")
            pdf_path = None
        
        # Step 3: Upload HTML to Hostinger
        print(f"  → Uploading HTML to Hostinger...")
        html_url = upload_file_to_hostinger(html_path, "propertypages")
        
        if html_url:
            print(f"  ✅ Successfully uploaded HTML. URL: {html_url}")
        else:
            print(f"  ⚠️  HTML upload failed. HTML link will not be sent via WhatsApp.")
        
        # Step 4: Upload PDF to Hostinger (if conversion was successful)
        pdf_url = None
        if pdf_path and Path(pdf_path).exists():
            print(f"  → Uploading PDF to Hostinger...")
            pdf_url = upload_file_to_hostinger(pdf_path, "propertypages")
            
            if pdf_url:
                print(f"  ✅ Successfully uploaded PDF. URL: {pdf_url}")
            else:
                print(f"  ⚠️  PDF upload failed. PDF link will not be sent via WhatsApp.")
        
        generated_files.append({
            'html_file': html_path,
            'html_url': html_url,
            'pdf_file': pdf_path if pdf_path and Path(pdf_path).exists() else None,
            'pdf_url': pdf_url,
        })
        
        # Small delay between requests to avoid rate limiting
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print(f"GENERATION SUMMARY:")
    print(f"  HTML files generated: {len([f for f in generated_files if f['html_file']])}")
    print(f"  HTML files uploaded: {len([f for f in generated_files if f['html_url']])}")
    print(f"  PDF files generated: {len([f for f in generated_files if f['pdf_file']])}")
    print(f"  PDF files uploaded: {len([f for f in generated_files if f['pdf_url']])}")
    print(f"{'='*80}\n")
    
    return generated_files


def display_property_analysis(property_messages: Optional[List[Dict]], property_images: Optional[List[Dict]] = None):
    """Pretty-print the OpenAI property message and image analysis."""
    print("\n" + "#" * 80)
    print("PROPERTY CONTENT IDENTIFICATION (SUITABLE FOR WEBPAGE CREATION)")
    print("#" * 80)

    # Display property messages
    print(f"\n📨 PROPERTY-RELATED MESSAGES:")
    print("-" * 80)
    
    if property_messages is None:
        print("    Message analysis skipped or failed. See messages above for details.")
    else:
        count = len(property_messages)
        print(f"    Identified {count} property-related message(s) with sufficient detail for webpage creation.\n")
        
        if count == 0:
            print("    No property-related messages with sufficient detail were identified for this date.")
        else:
            for idx, entry in enumerate(property_messages, 1):
                print(f"\n    [{idx}] Message #{entry.get('index')} ({entry.get('time', 'N/A')}) - {entry.get('sender', '').strip()}")
                print(f"        Text  : {entry.get('text', '').strip()}")
                if entry.get('reason'):
                    print(f"        Reason: {entry['reason'].strip()}")
    
    # Display property images
    print(f"\n\n🖼️  PROPERTY-RELATED IMAGES:")
    print("-" * 80)
    
    if property_images is None:
        print("    Image analysis skipped or failed. See messages above for details.")
    else:
        img_count = len(property_images)
        print(f"    Identified {img_count} property-related image(s) with sufficient detail for webpage creation.\n")
        
        if img_count == 0:
            print("    No property-related images with sufficient detail were identified for this date.")
        else:
            for idx, entry in enumerate(property_images, 1):
                print(f"\n    [{idx}] {entry.get('filename', 'Unknown')} ({entry.get('time', 'N/A')})")
                size = entry.get('filepath', Path()).stat().st_size if isinstance(entry.get('filepath'), Path) else 0
                size_kb = size / 1024 if size > 0 else 0
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                print(f"        Size  : {size_str}")
                if entry.get('reason'):
                    print(f"        Reason: {entry['reason'].strip()}")
    
    # Summary
    msg_count = len(property_messages) if property_messages else 0
    img_count = len(property_images) if property_images else 0
    total = msg_count + img_count
    
    print(f"\n" + "-" * 80)
    print(f"TOTAL PROPERTY CONTENT ITEMS: {total} ({msg_count} message(s) + {img_count} image(s))")
    print("#" * 80 + "\n")


def main():
    """
    Main entry point for the CLI.
    Prompts user for folder name and date, then extracts messages and media.
    """
    # Prompt for folder name
    folder_input = input("Enter folder name (e.g., HomeGroup): ").strip()
    
    if not folder_input:
        print("Error: Folder name cannot be empty.")
        return
    
    folder_path = Path(folder_input)
    
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: Folder not found: {folder_path.absolute()}")
        print("Please ensure the folder exists in the current directory.")
        return
    
    # Prompt for date
    date_input = input("Enter date to extract (DD/MM/YYYY or DD/MM/YY): ").strip()
    
    # Parse the date
    target_date = parse_whatsapp_date(date_input)
    if target_date is None:
        print(f"Error: Invalid date format. Expected DD/MM/YYYY or DD/MM/YY, got: {date_input}")
        return
    
    # Chat file path
    chat_file = folder_path / "chat.txt"
    
    if not chat_file.exists():
        print(f"Error: Chat file not found at {chat_file.absolute()}")
        print("Please ensure chat.txt exists in the specified folder.")
        return
    
    try:
        # Extract messages for the target date
        print(f"\nExtracting messages from {chat_file.name}...")
        messages = extract_messages_for_date(str(chat_file), target_date)
        
        # Extract media files for the target date
        print(f"Scanning media files in {folder_path.name}...")
        media_files = extract_media_files_for_date(str(folder_path), target_date)
        
        # Display all extracted content
        display_extracted_content(messages, media_files, target_date)

        # Run property-related message analysis via OpenAI
        print("\nAnalyzing messages for property-related content...")
        property_messages = identify_property_related_messages(messages)
        
        # Run property-related image analysis via OpenAI
        print("Analyzing images for property-related content...")
        property_images = identify_property_related_images(media_files)
        
        # Display combined analysis
        display_property_analysis(property_messages, property_images)
        
        # Generate HTML webpages and PDFs for each property message
        if property_messages:
            template_path = Path("sample.html")
            if template_path.exists():
                generated_files = generate_webpages_for_properties(property_messages, str(template_path))
                
                # Send PDFs via WhatsApp
                if generated_files:
                    # Get onboarding link from environment variable (optional)
                    onboarding_link = os.getenv("HOMEHNI_ONBOARDING_LINK", "")
                    send_webpages_via_whatsapp(property_messages, generated_files, onboarding_link)
            else:
                print(f"\n⚠️  Template file 'sample.html' not found. Skipping webpage generation.")
                generated_files = []
        else:
            generated_files = []
        
        return {
            "messages": messages,
            "media_files": media_files,
            "property_messages": property_messages,
            "property_images": property_images,
            "generated_webpages": generated_files,
            "date": target_date,
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()

