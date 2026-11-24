# 🤖 Telegram Opportunity Scout

> Automated daily digest that monitors any Telegram career channel, semantically evaluates postings using an LLM against your personal skills profile, and dispatches top matches directly to your Telegram handle.

---

## ⚡ Quickstart

```bash
# 1. Clone & install dependencies
git clone https://github.com/YourUsername/telegram-opportunity-scout.git
cd telegram-opportunity-scout
pip install -r requirements.txt

# 2. Test offline dry-run (no credentials required)
python3 -m src.cli --sample --dry-run
```

---

## 🏛️ Architecture: Ingestion, Evaluation & Dispatch

The project topology strictly separates into three modular layers:

```
src/
├── ingestion/        # Layer 1: Fetches channel messages (Telethon MTProto / Mock)
├── evaluation/       # Layer 2: LLM semantic scoring & prompt synthesis (Google Gemini)
├── dispatch/         # Layer 3: Telegram HTML card formatting & delivery (Telethon)
├── config.py         # Loads .env credentials & profile.json
├── models.py         # Data models & schemas
└── cli.py            # Pipeline orchestrator
```

1. **`ingestion/` (Collect):** Connects to Telegram using personal client credentials to read new posts from public channels or private invite links.
2. **`evaluation/` (Analyze):** Feeds posts and your profile (`profile.json`) to Gemini to semantically score relevance (0–100), extract deadlines/links, and synthesize fit rationale.
3. **`dispatch/` (Deliver):** Compiles matched opportunities into concise HTML cards and delivers them directly to your Telegram username or Saved Messages.

---

## ⚙️ Configuration

### 1. Credentials (`.env`)
```bash
cp .env.example .env
```
```env
# Telegram MTProto (https://my.telegram.org)
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+1234567890

# Target channel and recipient handle
TELEGRAM_CHANNEL_IDENTIFIER=https://t.me/your_target_channel
TELEGRAM_TARGET_HANDLE=@your_username

# Google Gemini API Key (https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_key
```

### 2. Candidate Profile (`profile.json`)
```bash
cp profile.example.json profile.json
```
```json
{
  "candidate": {
    "title": "Software Systems & Robotics Candidate",
    "summary": "Background in autonomous vehicles, ROS 2, computer vision, and systems programming.",
    "preferred_role_types": ["Internship", "Full-Time", "Hackathon"]
  },
  "domains": [
    {
      "id": "robotics",
      "name": "Robotics & Autonomous Systems",
      "description": "AV perception, sensor fusion, visual SLAM, and simulation.",
      "keywords": ["ROS 2", "C++", "LiDAR", "Gazebo"]
    }
  ],
  "negative_filters": ["sales representative", "telemarketing", "tuition teacher"],
  "scoring": { "min_threshold": 40, "max_results": 5 }
}
```

---

## 🛠️ CLI Usage

```bash
# Standard daily run (fetches channel, evaluates via Gemini, dispatches to Telegram)
python3 -m src.cli

# Preview formatted digest in terminal without dispatching
python3 -m src.cli --dry-run

# Custom lookback window & score threshold
python3 -m src.cli --lookback-hours 48 --min-score 75
```

---

## ⏰ Daily Automation

Add to your `crontab -e` to run daily at 08:30:
```bash
30 8 * * * cd /path/to/telegram-opportunity-scout && python3 -m src.cli >> output/scout.log 2>&1
```
*(Or generate a macOS LaunchAgent via `python3 scripts/setup_cron.py`)*

---

## 🚧 Work in Progress (WIP)

- **Notion Integration:** Automatically sync matched opportunities, application deadlines, and direct links into a personal Notion tracker database.
- **LLM-Powered Profile Interpretation:** Allow raw resume PDFs or unstructured LinkedIn / portfolio markdown to be automatically parsed and synthesized into structured scoring profiles.

---

## 🧪 Tests

```bash
python3 -m unittest discover tests
```
Runs 15 offline unit tests testing ingestion, evaluation, and dispatch layers with mocked API responses.
