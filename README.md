# WhatsApp Message Extractor

A Python module that extracts and filters messages from WhatsApp chat exports for a specific date. This is part of a larger automation system that processes WhatsApp group messages and generates webpages.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [File Structure](#file-structure)
- [Usage](#usage)
- [Step-by-Step Execution Guide](#step-by-step-execution-guide)
- [API Documentation](#api-documentation)
- [WhatsApp Export Format](#whatsapp-export-format)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

## 🎯 Overview

This module powers an automation pipeline that:
1. Extracts messages from WhatsApp chat exports
2. Filters messages by date
3. Identifies property-related messages with OpenAI
4. (Future) Generates HTML webpages
5. (Future) Uploads to Hostinger via FTP/GitHub

**Current Implementation**: Steps 1–3 (message & media extraction + property classifier).

## ✨ Features

- ✅ Interactive CLI that prompts for folder and date
- ✅ Displays both messages and associated media for the selected day
- ✅ Handles multi-line messages correctly
- ✅ Automatically filters out WhatsApp system messages
- ✅ Robust error handling and encoding support
- ✅ Returns structured Python objects for easy integration
- ✅ Property-awareness powered by OpenAI with concise justifications (optional)
- ✅ Clean, modular, production-ready code

## 📦 Prerequisites

Before using this module, ensure you have:

1. **Python 3.10 or higher**
   - Check your version: `python --version` or `python3 --version`

2. **WhatsApp Chat Export File**
   - Export your WhatsApp group chat as a `.txt` file
   - Instructions: Open WhatsApp → Select Group → Menu (⋮) → More → Export Chat → Without Media

3. **OpenAI Access (optional but recommended)**
   - Create an API key at [platform.openai.com](https://platform.openai.com/)
   - Set the environment variable `OPENAI_API_KEY`
   - Install the Python SDK: `pip install openai`

4. **Basic Terminal/Command Line Knowledge**

## 🔧 Installation

### Step 1: Verify Python Installation

Open your terminal (PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
python --version
```

You should see Python 3.10 or higher. If not, download from [python.org](https://www.python.org/downloads/).

### Step 2: Download the Module

1. Navigate to your project directory:
   ```bash
   cd "C:\Whatsapp automation"
   ```

2. Ensure `extract_messages.py` is in this directory.

### Step 3: Prepare Your Chat File

1. Export your WhatsApp chat (see Prerequisites above)
2. Save the exported file as `chat.txt` in the same directory as `extract_messages.py`

**Directory structure should look like:**
```
Whatsapp automation/
├── extract_messages.py            # Main module file
├── README.md                      # This documentation file
└── HomeGroup/                     # Example exported folder (name varies)
    ├── chat.txt                   # WhatsApp chat export (required)
    ├── 00000004-PHOTO-....jpg     # Media files (photos/videos/docs)
    └── ...
```

### Step 4: Verify Setup

List files in your directory:
```bash
# Windows PowerShell
dir

# Windows CMD
dir

# Mac/Linux
ls
```

You should see both `extract_messages.py` and `chat.txt`.

## 📁 File Structure

```
Whatsapp automation/
├── extract_messages.py            # Main module file
├── README.md                      # This documentation file
└── HomeGroup/                     # Example exported folder (name varies)
    ├── chat.txt                   # WhatsApp chat export (required)
    ├── 00000004-PHOTO-....jpg     # Media files (photos/videos/docs)
    └── ...
```

## 🚀 Usage

### Basic Execution

Run the script from the command line:

```bash
python extract_messages.py
```

The script will:
1. Prompt you to enter the exported folder name (e.g., `HomeGroup`)
2. Prompt you to enter the target date
3. Load `chat.txt` inside that folder and parse messages
4. Scan media files (images, videos, docs) in the same folder
5. Display all messages and media for the date
6. (Optional) Send the messages to OpenAI and list property-related items

### Interactive Example

```
Enter folder name (e.g., HomeGroup): HomeGroup
Enter date to extract (DD/MM/YYYY or DD/MM/YY): 28/10/25

Extracting messages from chat.txt...
Scanning media files in HomeGroup...

================================================================================
EXTRACTION RESULTS FOR 28/10/2025
================================================================================

📨 MESSAGES (5 found):
--------------------------------------------------------------------------------

[1] [11:32:42] Tanish:
    City is Hyderabad, but the system is Accepting Bellandur, Bengaluru as the Locality.

...

📎 MEDIA FILES (6 found):
--------------------------------------------------------------------------------

  PHOTO (6 file(s)):
    • [11:32:12] 00000004-PHOTO-2025-10-28-11-32-12.jpg (245.3 KB)

================================================================================
TOTAL: 5 message(s) and 6 media file(s)
================================================================================

################################################################################
PROPERTY MESSAGE IDENTIFICATION
################################################################################
Identified 3 property-related message(s).

[1] Message #1 (11:32:42) - Tanish
    Text  : City is Hyderabad, but the system is Accepting Bellandur, Bengaluru as the Locality.
    Reason: Specifies the intended property location discrepancy.
```

## 📖 Step-by-Step Execution Guide

### Method 1: Direct Execution (Recommended)

1. **Open Terminal/PowerShell**
   - Windows: Press `Win + X`, select "Windows PowerShell" or "Terminal"
   - Mac: Press `Cmd + Space`, type "Terminal"
   - Linux: Press `Ctrl + Alt + T`

2. **Navigate to Project Directory**
   ```bash
   cd "C:\Whatsapp automation"
   ```

3. **(Optional) Enable Property Analysis**
   ```bash
   # Windows PowerShell
   $Env:OPENAI_API_KEY = "sk-..."

   # macOS / Linux
   export OPENAI_API_KEY="sk-..."
   ```
   - Install the SDK once: `pip install openai`

4. **Run the Script**
   ```bash
   python extract_messages.py
   ```

5. **Respond to Prompts**
   - Folder name (e.g., `HomeGroup`)
   - Date in `DD/MM/YYYY` or `DD/MM/YY`

6. **View Results**
   - Messages + media summary in the terminal
   - Property-focused insights when OpenAI credentials are configured

### Method 2: Using as a Python Module

You can also import and use the functions programmatically:

```python
from extract_messages import extract_messages_for_date
from datetime import date

# Extract messages for a specific date
target_date = date(2025, 11, 5)  # November 5, 2025
messages = extract_messages_for_date("chat.txt", target_date)

# Process the messages
for msg in messages:
    print(f"{msg['datetime']} - {msg['sender']}: {msg['text']}")
```

## 📚 API Documentation

### Main Functions

#### `extract_messages_for_date(chat_file_path: str, target_date: date) -> List[Dict]`

**Purpose**: Extract messages from a WhatsApp chat file for a specific date.

**Parameters**:
- `chat_file_path` (str): Path to the WhatsApp chat export file (e.g., `"chat.txt"`)
- `target_date` (date): Python `date` object representing the target date

**Returns**:
- `List[Dict]`: List of message dictionaries, each containing:
  ```python
  {
      "datetime": datetime,  # Full datetime object
      "sender": str,         # Sender's name
      "text": str           # Message content
  }
  ```

**Raises**:
- `FileNotFoundError`: If the chat file doesn't exist

**Example**:
```python
from extract_messages import extract_messages_for_date
from datetime import date

messages = extract_messages_for_date("chat.txt", date(2025, 11, 5))
print(f"Found {len(messages)} messages")
```

#### `parse_whatsapp_date(date_str: str) -> Optional[date]`

**Purpose**: Parse a date string in DD/MM/YYYY or DD/MM/YY format.

**Parameters**:
- `date_str` (str): Date string in DD/MM/YYYY or DD/MM/YY format

**Returns**:
- `Optional[date]`: Python `date` object or `None` if parsing fails

**Example**:
```python
from extract_messages import parse_whatsapp_date

# Both formats work
date_obj1 = parse_whatsapp_date("28/10/2025")  # 4-digit year
date_obj2 = parse_whatsapp_date("28/10/25")    # 2-digit year
# Both return: date(2025, 10, 28)
```

#### `parse_message_line(line: str) -> Optional[Dict]`

**Purpose**: Parse a single line from WhatsApp chat export.

**Parameters**:
- `line` (str): A line from the chat file

**Returns**:
- `Optional[Dict]`: Message dictionary or `None` if line cannot be parsed

**Example**:
```python
from extract_messages import parse_message_line

line = "[28/10/25, 11:32:42 AM] Tanish: City is Hyderabad, but the system is Accepting Bellandur, Bengaluru as the Locality."
msg = parse_message_line(line)
# Returns: {"datetime": datetime(2025, 10, 28, 11, 32, 42), "sender": "Tanish", "text": "City is Hyderabad, but the system is Accepting Bellandur, Bengaluru as the Locality."}
```

#### `extract_media_files_for_date(folder_path: str, target_date: date) -> List[Dict]`

**Purpose**: Scan a WhatsApp export folder and list media files (photos, videos, docs) captured on the target date.

**Parameters**:
- `folder_path` (str): Path to the exported folder (e.g., `"HomeGroup"`)
- `target_date` (date): Date to filter files for

**Returns**:
- `List[Dict]`: Each dictionary contains filename, full path, media type, timestamp, and extension

#### `identify_property_related_messages(messages: List[Dict]) -> Optional[List[Dict]]`

**Purpose**: Use OpenAI to isolate property-related conversations.

**Parameters**:
- `messages` (List[Dict]): Output from `extract_messages_for_date`

**Returns**:
- `Optional[List[Dict]]`: `None` when analysis is skipped/failed, otherwise a list containing message index, sender, time, text, and reason

**Notes**:
- Requires `OPENAI_API_KEY` and the `openai` package
- Uses the `gpt-4o-mini` model and requests JSON-formatted results

#### `display_property_analysis(property_messages: Optional[List[Dict]]) -> None`

**Purpose**: Pretty-print OpenAI's property analysis results in the terminal.

## 📱 WhatsApp Export Format

The module expects WhatsApp messages in the standard export format:

### Supported Format

**Actual WhatsApp export format (with brackets and 2-digit year):**
```
[28/10/25, 11:32:42 AM] Tanish: City is Hyderabad, but the system is Accepting Bellandur, Bengaluru as the Locality.
[29/10/25, 5:04:53 PM] Syed@RanazonAI: Seasonal Greetings from *Alpine GMR Springfield*
[06/11/25, 6:25:15 PM] Syed@RanazonAI: same complaint from the csutomer - in mobile (android)
```

### Message Structure

Each message line follows this pattern:
```
[DD/MM/YY, H:MM:SS AM/PM] Sender Name: Message text
```

**Key characteristics:**
- Timestamps are enclosed in square brackets `[]`
- Date format: `DD/MM/YY` (2-digit year, e.g., `25` for 2025)
- Time format: `H:MM:SS AM/PM` (includes seconds, hour can be 1 or 2 digits)
- No separator between timestamp and sender (just a space)
- Sender and message separated by `: `

### Multi-line Messages

The module correctly handles messages that span multiple lines:
```
[29/10/25, 5:04:53 PM] Syed@RanazonAI: Seasonal Greetings from *Alpine GMR Springfield*

GMR Springfield - Live in Leisure 370 ways to create it. The Project is with 2 & 3 BHK Apartments at *Kompally-Bollarum*, Hyderabad.

*Possession:*
Ready to move in
```

### System Messages

The following system messages are automatically filtered out:
- Encryption notices
- Group creation messages
- Member join/leave notifications
- Group settings changes
- Security code messages
- Media omission notices (image omitted, document omitted, video omitted, etc.)

**Examples of filtered messages:**
```
[19/08/25, 2:26:58 PM] HomeHNI Tech Team: Messages and calls are end-to-end encrypted...
[28/10/25, 11:32:12 AM] Tanish: image omitted
[28/10/25, 6:22:15 PM] Syed@RanazonAI: just tested.docx document omitted
```

## 💡 Examples

### Example 1: Basic Usage

```python
from extract_messages import extract_messages_for_date
from datetime import date

# Extract messages for November 5, 2025
messages = extract_messages_for_date("chat.txt", date(2025, 11, 5))

# Print all messages
for msg in messages:
    print(f"[{msg['datetime'].strftime('%H:%M')}] {msg['sender']}: {msg['text']}")
```

### Example 2: Filter by Sender

```python
from extract_messages import extract_messages_for_date
from datetime import date

messages = extract_messages_for_date("chat.txt", date(2025, 11, 5))

# Get messages from a specific sender
alice_messages = [msg for msg in messages if msg['sender'] == 'Alice']

print(f"Alice sent {len(alice_messages)} messages")
```

### Example 3: Export to JSON

```python
import json
from extract_messages import extract_messages_for_date
from datetime import date

messages = extract_messages_for_date("chat.txt", date(2025, 11, 5))

# Convert datetime objects to strings for JSON
json_data = []
for msg in messages:
    json_data.append({
        "datetime": msg['datetime'].isoformat(),
        "sender": msg['sender'],
        "text": msg['text']
    })

# Save to file
with open("messages.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)
```

### Example 4: Count Messages by Hour

```python
from extract_messages import extract_messages_for_date
from datetime import date
from collections import Counter

messages = extract_messages_for_date("chat.txt", date(2025, 11, 5))

# Count messages by hour
hour_counts = Counter(msg['datetime'].hour for msg in messages)

print("Messages per hour:")
for hour in sorted(hour_counts.keys()):
    print(f"{hour:02d}:00 - {hour_counts[hour]} messages")
```

### Example 5: Identify Property Messages with OpenAI

```python
import os
from datetime import date
from extract_messages import (
    extract_messages_for_date,
    identify_property_related_messages,
)

os.environ["OPENAI_API_KEY"] = "sk-..."  # or set in your shell first

messages = extract_messages_for_date("HomeGroup/chat.txt", date(2025, 10, 28))

property_messages = identify_property_related_messages(messages)

if property_messages:
    for item in property_messages:
        print(f"#{item['index']} {item['text']}")
        print(f"Reason: {item['reason']}\n")
else:
    print("No property-related messages identified.")
```

## 🔍 Troubleshooting

### Problem: "Chat file not found"

**Solution**:
- Ensure `chat.txt` is in the same directory as `extract_messages.py`
- Check the file name is exactly `chat.txt` (case-sensitive on Linux/Mac)
- Verify you're running the script from the correct directory

### Problem: "Invalid date format"

**Solution**:
- Use the exact format: `DD/MM/YYYY` or `DD/MM/YY` (e.g., `28/10/2025` or `28/10/25`)
- Both 2-digit and 4-digit years are accepted
- Don't use dashes or other separators
- Ensure two digits for day and month (e.g., `28` not `8`)

### Problem: "No messages found"

**Possible causes**:
1. **Wrong date**: Verify the date you entered matches the date format in your chat file
2. **Date format mismatch**: Check if your WhatsApp export uses a different date format
3. **No messages on that date**: Verify there are actually messages for that date in the chat

**Debug steps**:
```python
# Check what dates are in your chat file
with open("chat.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()[:10]  # First 10 lines
    for line in lines:
        print(line)
```

### Problem: "OpenAI analysis skipped"

**Solution**:
- Ensure the `openai` package is installed (`pip install openai`)
- Set the `OPENAI_API_KEY` environment variable before running the script
- Confirm that your API key has sufficient quota and the selected model is available

### Problem: Encoding Errors

**Solution**:
The module automatically tries UTF-8 first, then falls back to latin-1. If you still get encoding errors:
- Re-export your WhatsApp chat
- Ensure the export is in plain text format

### Problem: Some Messages Not Parsed

**Possible causes**:
1. **Non-standard format**: Your WhatsApp export might use a different format
2. **Special characters**: Some special characters might interfere with parsing

**Debug**:
```python
from extract_messages import parse_message_line

# Test parsing a specific line
line = "05/11/2025, 10:25 am - Alice: Test message"
result = parse_message_line(line)
print(result)  # Should print a dictionary, not None
```

### Problem: Python Not Found

**Windows**:
```bash
# Try python3 instead
python3 extract_messages.py

# Or use full path
py extract_messages.py
```

**Mac/Linux**:
```bash
# Use python3 explicitly
python3 extract_messages.py
```

## 🔮 Future Enhancements

This module is part of a larger system. Future steps will include:

1. **OpenAI Integration**: Send extracted messages to OpenAI API for analysis
2. **Message Classification**: Identify important messages automatically
3. **HTML Generation**: Create webpages from processed messages
4. **Hostinger Upload**: Deploy generated pages via FTP or GitHub
5. **URL Generation**: Create unique URLs for customers

## 📝 Notes

- The module handles both 12-hour and 24-hour time formats automatically
- System messages are automatically filtered out
- Multi-line messages are preserved correctly
- The code is designed to be modular and testable
- All functions have type hints for better IDE support

## 🤝 Contributing

This is part of a larger automation project. When extending this module:
- Maintain the existing function signatures
- Add type hints to new functions
- Include docstrings for all public functions
- Test with various WhatsApp export formats

## 📄 License

This module is part of a private automation project.

---

**Last Updated**: 2025
**Python Version**: 3.10+
**Status**: Production Ready ✅

