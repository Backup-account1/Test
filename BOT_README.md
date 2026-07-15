# Telegram Bot for Pallet Query API

A Telegram bot that queries the localhost API for camera results and analyzed records.

## Features

- **Get Camera Result**: Query camera analysis for a specific SSCC code
- **Get Analyzed Records**: Fetch paginated list of analyzed records with filters
- **Interactive Buttons**: Quick selection of predefined limits and offsets
- **Test Data Support**: Built-in test SSCC values (111, 666, 777, 999)

## API Endpoints Used

1. **POST** `/api/getcamerares` - Get camera result for specific SSCC
2. **GET** `/api/getanalyzed?limit=X&offset=Y` - Get paginated analyzed records

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_bot.txt
```

### 2. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to create a new bot
4. Copy the **API token** provided by BotFather

### 3. Set Environment Variable

```bash
# Linux/macOS
export TELEGRAM_BOT_TOKEN='your-bot-token-here'

# Windows (Command Prompt)
set TELEGRAM_BOT_TOKEN=your-bot-token-here

# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN='your-bot-token-here'
```

Or create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your-bot-token-here
```

### 4. Start the API Server

Make sure your FastAPI server is running:

```bash
cd /workspace/Backup-account1__Test
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

### 5. Run the Bot

```bash
python telegram_bot.py
```

## Usage

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message with buttons | `/start` |
| `/help` | Show help information | `/help` |
| `/getcamerares <SSCC>` | Get camera result for SSCC | `/getcamerares 148102689000000010` |
| `/getanalyzed <limit> <offset>` | Get analyzed records | `/getanalyzed 500 0` |

### Interactive Buttons

1. **Get Camera Result** - Click to enter SSCC code
2. **Get Analyzed Records** - Click to select limit and offset
3. **Quick Navigation** - Previous/Next buttons for pagination
4. **Quick Limits** - Change limit with one click

### Predefined Values

**Limits:** 20, 50, 100, 500 (max: 5000)

**Offsets:** 0, 100, 200, 500, 1000

### Test SSCC Values

| SSCC | Expected Result |
|------|-----------------|
| `111` | Good result (Ok) |
| `666` | Bad result (Bad 66.6 percent) |
| `777` | Unknown result (Unknown . Not scanned) |
| `999` | Not found |

## Examples

### Get Camera Result

```
User: /getcamerares 111

Bot:
📦 **Camera Result**

• **IDPoint**: ID1
• **SSCC**: 111
• **Status**: PalletResult
• **Probability**: Ok
• **Degree**: Ok
• **Result**: Ok
```

### Get Analyzed Records

```
User: /getanalyzed 500 0

Bot:
📊 **Analyzed Records**

Limit: 500, Offset: 0
Total: 23 records

1. **SSCC**: `148102689000000010`
   **Msg**: done

2. **SSCC**: `111`
   **Msg**: test message

...
```

### Using Buttons

1. Click "Get Analyzed Records" button
2. Select limit (e.g., 500)
3. Select offset (e.g., 0)
4. View results with navigation buttons

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN` - Required. Your Telegram bot token from @BotFather
- `API_BASE_URL` - Optional. Default: `http://localhost:8000`

### Customizing Predefined Values

Edit the `telegram_bot.py` file to change:

```python
LIMIT_OPTIONS = [20, 50, 100, 500]
OFFSET_OPTIONS = [0, 100, 200, 500, 1000]
```

## Troubleshooting

### Connection Errors

If you see "Cannot connect to the API" error:

1. Make sure the FastAPI server is running: `uvicorn main:app --reload --port 8000 --host 0.0.0.0`
2. Check if the server is accessible: `curl -s http://localhost:8000/api/health`
3. Verify the port is correct (default: 8000)

### Bot Not Responding

1. Check if the bot is running: Look for "Bot is running..." message
2. Verify the token is correct
3. Make sure you're messaging the correct bot

### Message Too Long

Telegram has message length limits. The bot automatically truncates results to show the first 50 records and indicates if there are more.

## Running in Production

### Using systemd (Linux)

Create a service file `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Pallet Query Bot
After=network.target

[Service]
User=your-username
WorkingDirectory=/workspace/Backup-account1__Test
Environment=TELEGRAM_BOT_TOKEN=your-bot-token
ExecStart=/usr/bin/python3 /workspace/Backup-account1__Test/telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

### Using Docker

Create a Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_bot.txt .
RUN pip install -r requirements_bot.txt

COPY telegram_bot.py .

CMD ["python", "telegram_bot.py"]
```

Run with:
```bash
docker build -t telegram-bot .
docker run -e TELEGRAM_BOT_TOKEN=your-bot-token -p 8000:8000 telegram-bot
```

## License

MIT License
