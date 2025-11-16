"""
WhatsApp Message Extractor

This module extracts messages from a WhatsApp chat export file
for a specific date.
"""

import json
import os
import base64
from pathlib import Path
from datetime import datetime, date
import re
from typing import List, Dict, Optional


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
        "4. Include property specifications, pricing, location, and contact information\n\n"
        
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
        "1. Does it OFFER a property? (YES = include, NO = exclude)\n"
        "2. Does it ASK if a property is available? (YES = exclude immediately)\n"
        "3. Does it contain 'Looking to', 'Want to', 'Need', 'Required', 'Any [property] available'? "
        "(YES = exclude immediately)\n"
        "4. Does it state a budget with location preferences? (YES = exclude immediately)\n"
        "5. Does it describe what the person WANTS or NEEDS? (YES = exclude immediately)\n\n"
        
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
        "3. ONLY include messages with COMPLETE property information (property type + location + specifications/amenities/pricing/contact)\n"
        "4. EXCLUDE ALL buyer requests, buyer inquiries, buyer requirements, or messages asking if properties are available\n"
        "5. EXCLUDE messages that are vague, incomplete, or lack essential property details\n"
        "6. EXCLUDE casual conversations, technical discussions, or messages without property content\n"
        "7. PRESERVE the original message text character-by-character - do NOT modify, summarize, or rewrite\n"
        "8. If you identify a message as a buyer inquiry, DO NOT include it in the results, even if it contains property details\n"
        "9. Always respond with valid JSON matching the schema above\n"
        "10. If no seller messages meet the criteria, return {\"property_messages\": [], \"notes\": \"No seller property listings found\"}"
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
        
        return {
            "messages": messages,
            "media_files": media_files,
            "property_messages": property_messages,
            "property_images": property_images,
            "date": target_date,
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()

