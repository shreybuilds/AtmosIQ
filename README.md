# AtmosIQ 🌤️

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Telegram](https://img.shields.io/badge/bot-Telegram-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)
[![LLM Engine](https://img.shields.io/badge/LLM-Groq%20%2F%20Gemini-f9ab00?logo=google-gemini&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AtmosIQ is an intelligent, proactive weather notification platform that transforms complex, raw weather forecasts into personalized, conversational, and actionable daily alerts. By integrating real-time weather analytics, automated threat modeling (like rain detection), and LLM-powered synthesizers, AtmosIQ ensures you receive concise summaries that prepare you for the day ahead—without having to scroll through charts or parse numbers.

---

## 💡 Why AtmosIQ?

### The Problem
Traditional weather applications present a common set of challenges:
* **Information Overload:** They dump raw numbers, wind velocities, atmospheric pressures, and charts onto the user, requiring manual evaluation to answer basic questions (e.g., *"Do I need an umbrella today?"*).
* **Passive Consumption:** They rely on you proactively opening the app or website every morning. 
* **Generic Alerts:** Most default mobile weather alerts are either absent or spammy, offering little context about *why* the forecast matters to your daily routine.

### The AtmosIQ Solution
AtmosIQ shifts the paradigm from passive, raw data consumption to **proactive, contextual insights**:
* **Proactive & Push-First:** Instead of you looking for the forecast, AtmosIQ delivers it to your preferred communications channel (Telegram) at the exact time you schedule it.
* **LLM-Synthesized Context:** Using advanced Language Models (like LLaMA 3/Gemini), it translates complex metrics (temperature curves, precipitation probabilities, wind speeds) into 2-3 friendly, human-sounding sentences.
* **Intelligent Threat Detection:** The system automatically runs heuristics over the next 12 hours of meteorological data. If a significant event (like a >50% probability of rain) is predicted, it injects a highly visible alert banner *before* the summary, ensuring critical information is never missed.

---

## ✨ Features

### Current Capabilities
- [x] **LLM Weather Summarization:** Converts tabular forecast metrics into engaging, natural language updates.
- [x] **Automated Rain Forecasting:** Scans precipitation probability indexes for the next 12 hours and prepends high-priority `⚠️ Rain Alerts`.
- [x] **Instant On-Demand Reports:** Fetch the current weather context instantly via `/weather` command.
- [x] **Flexible Geocoding:** Automatically resolves generic city names (e.g., "New York", "London") into precise GPS coordinates using the Open-Meteo Geocoding API.
- [x] **Custom Dispatch Schedules:** Allow users to define their individual alert delivery times (e.g., `/settime 07:30`).
- [x] **Optimized Dispatch Engine:** Groups active users by location and time, executing single API queries for batch alerts to prevent rate limiting and optimize latency.
- [x] **Soft Subscription Management:** Allows users to opt-out with `/stop`, pausing alerts immediately while keeping preferences in database for easy reactivation.

### Planned & Upcoming Features
- [ ] **Multi-Channel Delivery:** Add support for Discord Webhooks, WhatsApp, and Email.
- [ ] **Multi-Lingual Summaries:** Enable alerts in Spanish, French, German, and Hindi.
- [ ] **Government Alert Feeds:** Integrate regional severe weather alerts (e.g., NOAA warnings).
- [ ] **Interactive Web Dashboard:** A visual front-end portal for subscription management and configuration.

---

## 🛠️ Tech Stack

| Component | Technology | Role / Usage |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core application logic and asynchronous processing |
| **Database** | PostgreSQL | Multi-user persistence, schemas, and performance views |
| **LLM Engine** | Groq SDK (Llama-3.1-8b) | Generates context-aware, friendly natural language summaries |
| **Weather Feed** | Open-Meteo API | Free, high-accuracy forecast and geocoding services |
| **Notification Channel** | Telegram Bot API | Delivers rich notifications and registers commands |
| **Scheduling** | Schedule (Python) | Executes continuous cron-like background jobs |

---

## 📐 Project Architecture

AtmosIQ separates concerns into lightweight modules for bot interactions, meteorological queries, database transactions, and background task dispatches:

```mermaid
graph TD
    User([Telegram User]) <-->|Commands & Messages| Bot[Telegram Bot bot.py]
    Scheduler[Scheduler scheduler.py] -->|1. Polling every min| DB[(PostgreSQL database.py)]
    DB -->|2. Returns active subscriptions| Scheduler
    Scheduler -->|3. Fetches grouped coordinates| WeatherAPI[Open-Meteo API weather.py]
    WeatherAPI -->|4. Raw meteorological data| Scheduler
    Scheduler -->|5. Context prompt| LLM[Groq Engine engine.py]
    LLM -->|6. Conversational summary| Bot
    Bot -->|7. Push alert message| User
    
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style DB fill:#bbf,stroke:#333,stroke-width:2px
    style LLM fill:#fdb,stroke:#333,stroke-width:2px
```

---

## ⚙️ Environment Variables

The application reads configurations from the environment. To set it up, create a `.env` file in the root directory (based on `.env.example`):

```bash
# Copy template
cp .env.example .env
```

Define the following parameters inside `.env`:

| Key | Description | Example |
| :--- | :--- | :--- |
| `BOT_TOKEN` | Token retrieved from Telegram's BotFather | `123456789:ABCdefGhIJKlmNoPQRsT...` |
| `GROQ_API_KEY` | Your Groq API Key to access LLM services | `gsk_AbCdEfGhIjKlMnOpQrStUvWxYz...` |
| `DB_URL` | Connection URL to your PostgreSQL instance | `postgresql://postgres:password@localhost:5432/atmosiq` |

> [!CAUTION]
> **Security Reminder:** Never commit the `.env` file or hardcode your API keys/database credentials. The root `.gitignore` is pre-configured to ignore `.env` files.

---

## 🚀 Installation & Setup

Follow these steps to run AtmosIQ locally or on your servers:

### 1. Prerequisites
- Python 3.10 or higher installed.
- PostgreSQL database instance running.
- Telegram Bot token (create one via [BotFather](https://t.me/BotFather)).
- Groq API credentials (get one at [Groq Console](https://console.groq.com/)).

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/AtmosIQ.git
cd AtmosIQ
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Database Setup
Create a PostgreSQL database (e.g., named `atmosiq`). The application is designed to automatically create the necessary `users` table and `active_users` database views on startup. No manual SQL migrations are required.

### 5. Launch the Application
Start the main loop, which boots up the Telegram long-polling listener and the background scheduler thread:
```bash
python main.py
```

---

## 🤖 Telegram Bot Usage

Open a chat with your Telegram Bot and use the following commands:

* `/start` - Displays the greeting interface and instructions.
* `/setlocation <city_name>` - Resolves city coordinates and registers your alert location.
  - *Example:* `/setlocation Tokyo`
* `/settime HH:MM` - Schedules daily alert delivery (24-hour UTC format).
  - *Example:* `/settime 08:00`
* `/weather` - Instantly returns the current LLM-summarized weather report for your saved location.
* `/stop` - Temporarily unsubscribes from the daily alert system.

---

## 🗂️ Folder Structure

```
AtmosIQ/
├── .env.example          # Sample environment configuration template
├── .gitignore            # Git exclusion rules
├── Procfile              # Heroku/Cloud deployment command setup
├── README.md             # Project documentation
├── requirements.txt      # Python package dependencies
├── main.py               # Application entrypoint (orchestrates bot & scheduler threads)
├── bot.py                # Telegram bot event handlers and command registrations
├── config.py             # Environment loader and global settings
├── database.py           # PostgreSQL client (handles CRUD operations and DB initialization)
├── engine.py             # Generative AI interface (interacts with LLM APIs)
├── scheduler.py          # Background polling loop that triggers alerts at scheduled times
└── weather.py            # Open-Meteo API integrator (geocoding & forecast fetching)
```

---

## 📸 Screenshots

*Place screenshots/GIFs of the bot interactions here once deployed:*

| Command Interface | Interactive Weather Summary | Rain Forecast Warnings |
| :---: | :---: | :---: |
| *(Add `/start` screenshot)* | *(Add `/weather` summary screenshot)* | *(Add `⚠️ Rain Alert` banner screenshot)* |

---

## 🗺️ Roadmap

- [x] **Phase 1: Foundation (Completed)**
  - Core weather fetching services.
  - Geocoding and basic coordinates database mapping.
  - Basic Telegram interactions.
- [x] **Phase 2: LLM Summaries & Scheduling (Completed)**
  - Integrated Groq/Gemini client for natural summaries.
  - Created grouped batch alerts.
  - Custom alert delivery times.
- [ ] **Phase 3: Threat Analytics & Extensions (Planned)**
  - Expand rain heuristics to include heatwaves, sub-zero freezes, and severe winds.
  - Add inline button configurations to avoid typing text commands.
- [ ] **Phase 4: Multi-Channel Expansion (Planned)**
  - Launch companion Discord and Slack alert systems sharing the same core backend engine.

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` file for more details.

---

## 👤 Author

**Shreyash Singh**
* GitHub: [@ShreyashSingh](https://github.com/ShreyashSingh) *(update link if needed)*
* Workspace: `shreyHack3000/AtmosIQ`
