⚡ Svitlo Monitor v0.1

A lightweight Python + Docker service that monitors blackout schedules from
[be-svitlo.oe.if.ua](https://be-svitlo.oe.if.ua) and sends Telegram alerts when
the data changes.

---

## 🚀 Features

- Monitors multiple queue URLs (e.g., 4.2, 5.2)
- Detects JSON changes automatically
- Sends alerts via Telegram
- Lightweight: Python 3.11-slim base
- Docker Compose ready
- Configurable via `.env`

---

## 🧰 Requirements

- Docker & Docker Compose installed  
- A Telegram Bot token and Chat ID  
  (Create one with [@BotFather](https://t.me/BotFather))

---

## ⚙️ Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your_username>/svitlo-monitor.git
   cd svitlo-monitor