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
API_HEALTH_CHECK = f"{API_BASE_URL}/api/health"

# Predefined values for quick selection
LIMIT_OPTIONS = [20, 50, 100, 500]
OFFSET_OPTIONS = [0, 100, 200, 500, 1000]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("📦 Get Camera Result", callback_data="cmd_getcamerares"),
            InlineKeyboardButton("📊 Get Analyzed Records", callback_data="cmd_getanalyzed"),
        ],
        [
            InlineKeyboardButton("🧰 Health Check", callback_data="cmd_health"),
            InlineKeyboardButton("❓ Help", callback_data="cmd_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📦 Welcome to Pallet Query Bot!\n\n"
        "Use the buttons below or commands:\n"
        "• /getcamerares <SSCC> - Get camera result\n"
        "• /getanalyzed <limit> <offset> - Get analyzed records\n"
        "• /health - Check API health\n"
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

**Interactive Buttons for getanalyzed:**
• Click "📊 Get Analyzed Records" button
• Select from predefined limits: 20, 50, 100, 500
• Select from predefined offsets: 0, 100, 200, 500, 1000
• Use Previous/Next buttons to navigate through pages
• Quick limit change buttons available

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
        
    elif data == "cmd_getanalyzed" or data == "cmd_start":
        await show_analyzed_menu(query)
        
    elif data == "cmd_help":
        await help_command(update, context)

    elif data == "cmd_health":
        await check_health(query, context)
        
    elif data == "back_to_analyzed_menu":
        await show_analyzed_menu(query)
        
    elif data == "back_to_limit_select":
        await show_limit_options(query)
        
    elif data == "cmd_custom_analyzed":
        await show_limit_options(query)
        
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
        
    elif data.startswith("nav_"):
        # Navigation: nav_<direction>_<limit>_<offset>
        parts = data.replace("nav_", "").split("_")
        direction = parts[0]
        limit = int(parts[1])
        offset = int(parts[2])
        
        if direction == "prev":
            new_offset = max(0, offset - limit)
        elif direction == "next":
            new_offset = offset + limit
        else:
            new_offset = offset
        
        await fetch_analyzed_records(query, limit, new_offset)
        
    elif data.startswith("change_limit_"):
        # change_limit_<new_limit>_<current_offset>
        parts = data.replace("change_limit_", "").split("_")
        new_limit = int(parts[0])
        current_offset = int(parts[1])
        # Adjust offset to stay on same page when changing limit
        new_offset = (current_offset // new_limit) * new_limit
        await fetch_analyzed_records(query, new_limit, new_offset)
    
    elif data == "no_op":
        # Do nothing, just acknowledge the click
        pass


async def show_analyzed_menu(query) -> None:
    """Show main menu for analyzed records with quick action buttons."""
    keyboard = [
        [
            InlineKeyboardButton("🔢 Quick: Last 20", callback_data="quick_limit_offset_20_0"),
            InlineKeyboardButton("🔢 Quick: Last 50", callback_data="quick_limit_offset_50_0"),
        ],
        [
            InlineKeyboardButton("🔢 Quick: Last 100", callback_data="quick_limit_offset_100_0"),
            InlineKeyboardButton("🔢 Quick: Last 500", callback_data="quick_limit_offset_500_0"),
        ],
        [
            InlineKeyboardButton("⚙️ Custom Limit & Offset", callback_data="cmd_custom_analyzed"),
        ],
        [
            InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="cmd_start"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 **Get Analyzed Records**\n\n"
        "Choose an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def show_limit_options(query) -> None:
    """Show limit selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton(f"{limit}", callback_data=f"limit_{limit}")
            for limit in LIMIT_OPTIONS
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_analyzed_menu"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 **Select Limit:**\n\n"
        "Choose how many records to fetch per page:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def show_offset_options(query, limit: int) -> None:
    """Show offset selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton(f"{offset}", callback_data=f"offset_{offset}")
            for offset in OFFSET_OPTIONS
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_limit_select"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"📊 **Selected Limit: {limit}**\n\n"
        "Choose starting offset:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
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


async def format_analyzed_records(update: Update, data: Dict[str, Any], limit: int, offset: int) -> None:
    """Format and send analyzed records. Handles response with Count and Records fields."""
    # Extract records from the response
    records = []
    total_count = 0
    
    if isinstance(data, dict):
        records = data.get("Records", [])
        total_count = data.get("Count", len(records))
    elif isinstance(data, list):
        records = data
        total_count = len(records)
    
    if not records:
        await update.message.reply_text(
            f"📊 **Analyzed Records**\n\n"
            f"Limit: {limit}, Offset: {offset}\n"
            f"Total available: {total_count}\n\n"
            "No records found in this page.",
        )
        return
    
    response_text = f"📊 **Analyzed Records**\n\n"
    response_text += f"Limit: {limit}, Offset: {offset}\n"
    response_text += f"Total available: {total_count}\n"
    response_text += f"Returned: {len(records)} records\n\n"
    
    # Show records (limit to 50 to avoid message length limits)
    max_to_show = 50
    for i, record in enumerate(records[:max_to_show], 1):
        sscc = record.get("SSCC", "N/A")
        msg = record.get("Msg", "N/A")
        response_text += f"{i}. **SSCC**: `{sscc}`\n"
        response_text += f"   **Msg**: `{msg}`\n\n"
    
    if len(records) > max_to_show:
        response_text += f"\n... and {len(records) - max_to_show} more records in this page"
    
    # Add total info
    if total_count > (offset + len(records)):
        remaining = total_count - (offset + len(records))
        response_text += f"\n\n📈 {remaining} more records available"
    
    await update.message.reply_text(response_text, parse_mode="Markdown")


async def format_analyzed_records_callback(query, data: Dict[str, Any], limit: int, offset: int) -> None:
    """Format and send analyzed records from callback context with interactive navigation."""
    # Extract records from the response
    records = []
    total_count = 0
    
    if isinstance(data, dict):
        records = data.get("Records", [])
        total_count = data.get("Count", len(records))
    elif isinstance(data, list):
        records = data
        total_count = len(records)
    
    if not records:
        keyboard = [
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="cmd_getanalyzed"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📊 **Analyzed Records**\n\n"
            f"Limit: {limit}, Offset: {offset}\n"
            f"Total available: {total_count}\n\n"
            "No records found in this page.",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        return
    
    response_text = f"📊 **Analyzed Records**\n\n"
    response_text += f"Limit: {limit}, Offset: {offset}\n"
    response_text += f"Total available: {total_count}\n"
    response_text += f"Showing: {len(records)} records\n\n"
    
    # Show records (limit to 50 to avoid message length limits)
    max_to_show = 50
    for i, record in enumerate(records[:max_to_show], 1):
        sscc = record.get("SSCC", "N/A")
        msg = record.get("Msg", "N/A")
        response_text += f"{i}. **SSCC**: `{sscc}`\n"
        response_text += f"   **Msg**: `{msg}`\n\n"
    
    if len(records) > max_to_show:
        response_text += f"\n... and {len(records) - max_to_show} more records in this page\n"
    
    # Build keyboard with navigation and quick actions
    keyboard = []
    
    # Navigation row: Previous and Next
    nav_buttons = []
    
    # Previous button
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"nav_prev_{limit}_{offset}"))
    
    # Page info button (non-clickable, just for display)
    current_page = (offset // limit) + 1
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    nav_buttons.append(InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="no_op"))
    
    # Next button
    if (offset + limit) < total_count:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav_next_{limit}_{offset}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Quick limit change row
    limit_buttons = []
    for lim in LIMIT_OPTIONS:
        limit_buttons.append(InlineKeyboardButton(
            f"Limit: {lim}", 
            callback_data=f"change_limit_{lim}_{offset}"
        ))
    if limit_buttons:
        keyboard.append(limit_buttons)
    
    # Quick offset jump row
    offset_buttons = []
    for off in OFFSET_OPTIONS:
        offset_buttons.append(InlineKeyboardButton(
            f"Offset: {off}",
            callback_data=f"quick_limit_offset_{limit}_{off}"
        ))
    if offset_buttons:
        keyboard.append(offset_buttons)
    
    # Back to menu
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Analyzed Menu", callback_data="cmd_getanalyzed"),
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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



async def check_health(update_or_query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle health button callback."""
    await fetch_health_status(update_or_query, context)


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command."""
    await fetch_health_status(update, context)


async def fetch_health_status(update_or_query, context: ContextTypes.DEFAULT_TYPE = None) -> None:
    """Fetch health status from API and display all data."""
    try:
        response = requests.get(API_HEALTH_CHECK, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            health_text = "\U0001f9f0 *API Health Check*\n\n"
            health_text += f"\u2699 *Status*: `{data.get('status', 'N/A')}` - {data.get('status', 'N/A')}\n"
            health_text += f"\u2022 *Version*: `{data.get('version', 'N/A')}`\n"
            health_text += f"\u2022 *Semantic Version*: `{data.get('semantic_version', 'N/A')}`\n"
            health_text += f"\u2022 *API Name*: `{data.get('api_name', 'N/A')}`\n"
            health_text += f"\u2022 *Build Date*: `{data.get('build_date', 'N/A')}`\n"
            health_text += f"\u2022 *Commit Count*: `{data.get('commit_count', 'N/A')}`\n\n"
            
            git_data = data.get('git', {})
            if git_data:
                health_text += "\U0001f4c1 *Git Info:*\n"
                health_text += f"  \u2022 Commit Hash: `{git_data.get('short_hash', git_data.get('commit_hash', 'N/A'))}`\n"
                health_text += f"  \u2022 Commit Date: `{git_data.get('commit_date', 'N/A')}`\n"
                health_text += f"  \u2022 Commit Message: `{git_data.get('commit_message', 'N/A')}`\n"
                health_text += f"  \u2022 Is Dirty: `{git_data.get('is_dirty', False)}`\n\n"
            
            scanned_dirs = data.get('scanned_dirs', {})
            if scanned_dirs:
                health_text += "\U0001f4c1 *Scanned Directories:*\n"
                health_text += f"  \u2022 Today: `{scanned_dirs.get('today', 'N/A')}`\n"
                health_text += f"  \u2022 This Week: `{scanned_dirs.get('this_week', 'N/A')}`\n"
                health_text += f"  \u2022 Total: `{scanned_dirs.get('total', 'N/A')}`\n"
                health_text += f"  \u2022 Min Size: `{scanned_dirs.get('min_size_mb', 'N/A')} MB`\n"
                health_text += f"  \u2022 Threshold: `{scanned_dirs.get('threshold_mb', 'N/A')} MB`\n\n"
            
            disk_data = data.get('free_disk_space', {})
            if disk_data:
                health_text += "\U0001f4be *Disk Space:*\n"
                for drive, info in disk_data.items():
                    if info.get('available', False):
                        free = info.get('free_gb', 'N/A')
                        total = info.get('total_gb', 'N/A')
                        used = info.get('used_percent', 'N/A')
                        health_text += f"  \u2022 Drive {drive}: `{free} GB free` / `{total} GB total` ({used}% used)\n"
                    else:
                        error = info.get('error', 'N/A')
                        health_text += f"  \u2022 Drive {drive}: \u274c `{error}`\n"
            
            if isinstance(update_or_query, Update):
                await update_or_query.message.reply_text(health_text, parse_mode="Markdown")
            else:
                await update_or_query.edit_message_text(health_text, parse_mode="Markdown")
        else:
            error_msg = f"\u274c API Health Check Failed: {response.status_code}\nResponse: {response.text}"
            if isinstance(update_or_query, Update):
                await update_or_query.message.reply_text(error_msg)
            else:
                await update_or_query.edit_message_text(error_msg)
    except requests.exceptions.Timeout:
        error_msg = "\u23f0 Health check request timed out. Please check if the API is running."
        if isinstance(update_or_query, Update):
            await update_or_query.message.reply_text(error_msg)
        else:
            await update_or_query.edit_message_text(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "\ud83d\udd0c Cannot connect to the API. Make sure the localhost server is running on port 8000."
        if isinstance(update_or_query, Update):
            await update_or_query.message.reply_text(error_msg)
        else:
            await update_or_query.edit_message_text(error_msg)
    except Exception as e:
        error_msg = f"\u274c Health check error: {str(e)}"
        if isinstance(update_or_query, Update):
            await update_or_query.message.reply_text(error_msg)
        else:
            await update_or_query.edit_message_text(error_msg)


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
    application.add_handler(CommandHandler("health", health_check))
    
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
