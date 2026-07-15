#!/usr/bin/env python3
"""
Telegram Bot for querying localhost API
- /getcamerares <SSCC> - Get camera result for specific SSCC
- /getanalyzed <limit> <offset> - Get paginated analyzed records
- Interactive buttons for predefined limits and offsets
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_GET_CAMERA_RES = f"{API_BASE_URL}/api/getcamerares"
API_GET_ANALYZED = f"{API_BASE_URL}/api/getanalyzed"

# Predefined values for quick selection
LIMIT_OPTIONS = [20, 50, 100, 500]
OFFSET_OPTIONS = [0, 100, 200, 500, 1000]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("Get Camera Result", callback_data="cmd_getcamerares"),
            InlineKeyboardButton("Get Analyzed Records", callback_data="cmd_getanalyzed"),
        ],
        [
            InlineKeyboardButton("Help", callback_data="cmd_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📦 Welcome to Pallet Query Bot!\n\n"
        "Use the buttons below or commands:\n"
        "• /getcamerares <SSCC> - Get camera result\n"
        "• /getanalyzed <limit> <offset> - Get analyzed records\n"
        "• /help - Show help",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
📖 **Bot Commands:**

**1. Get Camera Result**
• Command: `/getcamerares <SSCC>`
• Example: `/getcamerares 148102689000000010`
• Returns: Camera analysis result for the specified SSCC

**2. Get Analyzed Records**
• Command: `/getanalyzed <limit> <offset>`
• Example: `/getanalyzed 500 0`
• Returns: Paginated list of analyzed records (SSCC and Msg only)

**Predefined Options:**
• Limits: 20, 50, 100, 500
• Offsets: 0, 100, 200, 500, 1000

**Test SSCC Values:**
• `111` - Good result
• `666` - Bad result
• `777` - Unknown result
• `999` - Not found

**API Endpoints:**
• POST `/api/getcamerares` - Get camera result
• GET `/api/getanalyzed?limit=X&offset=Y` - Get analyzed records
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cmd_getcamerares":
        await query.edit_message_text(
            "🔍 **Get Camera Result**\n\n"
            "Enter SSCC code:\n"
            "Example: `148102689000000010`\n\n"
            "Test values: `111`, `666`, `777`, `999`",
            parse_mode="Markdown",
        )
        context.user_data["awaiting_sscc"] = True
        
    elif data == "cmd_getanalyzed":
        await show_limit_options(query)
        
    elif data == "cmd_help":
        await help_command(update, context)
        
    elif data.startswith("limit_"):
        limit = int(data.replace("limit_", ""))
        context.user_data["selected_limit"] = limit
        await show_offset_options(query, limit)
        
    elif data.startswith("offset_"):
        offset = int(data.replace("offset_", ""))
        limit = context.user_data.get("selected_limit", 500)
        await fetch_analyzed_records(query, limit, offset)
        
    elif data.startswith("quick_limit_offset_"):
        parts = data.replace("quick_limit_offset_", "").split("_")
        limit = int(parts[0])
        offset = int(parts[1])
        await fetch_analyzed_records(query, limit, offset)


async def show_limit_options(query) -> None:
    """Show limit selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton(f"{limit}", callback_data=f"limit_{limit}")
            for limit in LIMIT_OPTIONS
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 **Select Limit:**\n\n"
        "Choose how many records to fetch:",
        reply_markup=reply_markup,
    )


async def show_offset_options(query, limit: int) -> None:
    """Show offset selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton(f"{offset}", callback_data=f"offset_{offset}")
            for offset in OFFSET_OPTIONS
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"📊 **Selected Limit: {limit}**\n\n"
        "Choose offset:",
        reply_markup=reply_markup,
    )


async def get_camera_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /getcamerares command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an SSCC code.\n\n"
            "Usage: `/getcamerares <SSCC>`\n"
            "Example: `/getcamerares 148102689000000010`\n\n"
            "Test values: `111`, `666`, `777`, `999`",
        )
        return
    
    sscc = context.args[0].strip()
    await fetch_camera_result(update, sscc)


async def fetch_camera_result(update: Update, sscc: str) -> None:
    """Fetch camera result from API."""
    try:
        payload = {"SSCC": sscc}
        response = requests.post(
            API_GET_CAMERA_RES,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code == 200:
            data = response.json()
            await format_camera_result(update, data)
        else:
            await update.message.reply_text(
                f"❌ API Error: {response.status_code}\n"
                f"Response: {response.text}"
            )
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ Request timed out. Please check if the API is running.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text(
            "🔌 Cannot connect to the API.\n"
            "Make sure the localhost server is running on port 8000."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def format_camera_result(update: Update, data: Dict[str, Any]) -> None:
    """Format and send camera result."""
    if isinstance(data, dict):
        # Single record response
        response_text = "📦 **Camera Result**\n\n"
        for key, value in data.items():
            response_text += f"• **{key}**: `{value}`\n"
        await update.message.reply_text(response_text, parse_mode="Markdown")
    elif isinstance(data, list) and len(data) > 0:
        # Multiple records
        response_text = f"📦 **Camera Results ({len(data)} records)**\n\n"
        for i, record in enumerate(data[:10], 1):  # Show first 10
            response_text += f"**Record {i}:**\n"
            for key, value in record.items():
                response_text += f"  • **{key}**: `{value}`\n"
            response_text += "\n"
        if len(data) > 10:
            response_text += f"\n... and {len(data) - 10} more records"
        await update.message.reply_text(response_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No results found for the given SSCC.")


async def get_analyzed_records(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /getanalyzed command."""
    args = context.args
    
    # Parse arguments
    limit = 500
    offset = 0
    
    if args:
        try:
            if len(args) >= 1:
                limit = int(args[0])
                limit = min(max(limit, 1), 5000)  # Clamp between 1 and 5000
            if len(args) >= 2:
                offset = int(args[1])
                offset = max(offset, 0)
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid arguments.\n\n"
                "Usage: `/getanalyzed <limit> <offset>`\n"
                "Example: `/getanalyzed 500 0`\n\n"
                "Predefined options:\n"
                f"• Limits: {', '.join(map(str, LIMIT_OPTIONS))}\n"
                f"• Offsets: {', '.join(map(str, OFFSET_OPTIONS))}"
            )
            return
    
    await fetch_analyzed_records_from_api(update, limit, offset)


async def fetch_analyzed_records(query_or_update, limit: int, offset: int) -> None:
    """Fetch analyzed records from API."""
    try:
        url = f"{API_GET_ANALYZED}?limit={limit}&offset={offset}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(query_or_update, Update):
                await format_analyzed_records(query_or_update, data, limit, offset)
            else:
                # It's a callback query
                await format_analyzed_records_callback(query_or_update, data, limit, offset)
        else:
            error_msg = f"❌ API Error: {response.status_code}\nResponse: {response.text}"
            if isinstance(query_or_update, Update):
                await query_or_update.message.reply_text(error_msg)
            else:
                await query_or_update.edit_message_text(error_msg)
    except requests.exceptions.Timeout:
        error_msg = "⏰ Request timed out. Please check if the API is running."
        if isinstance(query_or_update, Update):
            await query_or_update.message.reply_text(error_msg)
        else:
            await query_or_update.edit_message_text(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "🔌 Cannot connect to the API. Make sure the localhost server is running on port 8000."
        if isinstance(query_or_update, Update):
            await query_or_update.message.reply_text(error_msg)
        else:
            await query_or_update.edit_message_text(error_msg)
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        if isinstance(query_or_update, Update):
            await query_or_update.message.reply_text(error_msg)
        else:
            await query_or_update.edit_message_text(error_msg)


async def fetch_analyzed_records_from_api(update: Update, limit: int, offset: int) -> None:
    """Wrapper for fetching analyzed records from Update context."""
    await fetch_analyzed_records(update, limit, offset)


async def format_analyzed_records(update: Update, data: List[Dict[str, Any]], limit: int, offset: int) -> None:
    """Format and send analyzed records."""
    if not data:
        await update.message.reply_text(
            f"📊 **Analyzed Records**\n\n"
            f"Limit: {limit}, Offset: {offset}\n\n"
            "No records found."
        )
        return
    
    response_text = f"📊 **Analyzed Records**\n\n"
    response_text += f"Limit: {limit}, Offset: {offset}\n"
    response_text += f"Total: {len(data)} records\n\n"
    
    for i, record in enumerate(data[:50], 1):  # Show first 50 to avoid message length limits
        sscc = record.get("SSCC", "N/A")
        msg = record.get("Msg", "N/A")
        response_text += f"{i}. **SSCC**: `{sscc}`\n"
        response_text += f"   **Msg**: `{msg}`\n\n"
    
    if len(data) > 50:
        response_text += f"\n... and {len(data) - 50} more records"
    
    await update.message.reply_text(response_text, parse_mode="Markdown")


async def format_analyzed_records_callback(query, data: List[Dict[str, Any]], limit: int, offset: int) -> None:
    """Format and send analyzed records from callback context."""
    if not data:
        await query.edit_message_text(
            f"📊 **Analyzed Records**\n\n"
            f"Limit: {limit}, Offset: {offset}\n\n"
            "No records found.",
            parse_mode="Markdown",
        )
        return
    
    response_text = f"📊 **Analyzed Records**\n\n"
    response_text += f"Limit: {limit}, Offset: {offset}\n"
    response_text += f"Total: {len(data)} records\n\n"
    
    for i, record in enumerate(data[:50], 1):
        sscc = record.get("SSCC", "N/A")
        msg = record.get("Msg", "N/A")
        response_text += f"{i}. **SSCC**: `{sscc}`\n"
        response_text += f"   **Msg**: `{msg}`\n\n"
    
    if len(data) > 50:
        response_text += f"\n... and {len(data) - 50} more records"
    
    # Add quick navigation buttons
    keyboard = []
    
    # Previous offset
    if offset >= 100:
        prev_offset = max(0, offset - 100)
        keyboard.append([
            InlineKeyboardButton("⬅️ Previous", callback_data=f"quick_limit_offset_{limit}_{prev_offset}"),
        ])
    
    # Next offset
    if len(data) >= limit:
        next_offset = offset + limit
        keyboard.append([
            InlineKeyboardButton("Next ➡️", callback_data=f"quick_limit_offset_{limit}_{next_offset}"),
        ])
    
    # Quick limit changes
    quick_limits = [
        (20, "20"),
        (50, "50"),
        (100, "100"),
        (500, "500"),
    ]
    keyboard.append([
        InlineKeyboardButton(f"Limit: {label}", callback_data=f"quick_limit_offset_{lim}_{offset}")
        for lim, label in quick_limits
    ])
    
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None
    
    await query.edit_message_text(
        response_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for SSCC."""
    if context.user_data.get("awaiting_sscc"):
        sscc = update.message.text.strip()
        context.user_data["awaiting_sscc"] = False
        await fetch_camera_result(update, sscc)


def main() -> None:
    """Run the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set it with: export TELEGRAM_BOT_TOKEN='your-bot-token'")
        return
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getcamerares", get_camera_result))
    application.add_handler(CommandHandler("getanalyzed", get_analyzed_records))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handler for text input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Start the Bot
    print("🤖 Bot is running...")
    print("Press Ctrl+C to stop")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
