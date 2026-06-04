# 🤖 Telegram Subscription Bot

> A production-ready Telegram bot that handles paid subscriptions, auto-manages private channel access, and revokes it when subscriptions expire — all fully automated.

---

## 💡 What This Project Does

Users pay inside Telegram (via Telegram Stars or a payment provider), instantly receive a one-time invite link to a private channel, and get automatically removed when their 30-day subscription expires. No manual work for the admin.

**The full flow in 3 steps:**
1. User sends `/payment` → bot sends an invoice
2. User pays → bot creates a unique invite link and saves the subscription to the database
3. Every hour, a background scheduler checks for expired subscriptions and revokes access automatically

---

## ⚙️ Tech Stack

| Layer | Tool |
|---|---|
| Bot framework | [aiogram 3.x](https://docs.aiogram.dev/) |
| Payments | Telegram Stars (`XTR`) / Stripe via Telegram Payments |
| Database | SQLite via `sqlite3` |
| Task scheduling | [APScheduler](https://apscheduler.readthedocs.io/) (`AsyncIOScheduler`) |
| Channel management | Telegram Bot API — `create_chat_invite_link`, `ban_chat_member` |

---

## 🗂️ Project Structure

```
telegram-subscription-bot/
├── main.py          # Entry point — polling + scheduler startup
├── payments.db      # SQLite database (auto-created on first run)
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/telegram-subscription-bot.git
cd telegram-subscription-bot
```

### 2. Install dependencies

```bash
pip install aiogram apscheduler
```

### 3. Configure the bot

Open `main.py` and fill in your credentials:

```python
BOT_TOKEN = "your_bot_token_here"          # from @BotFather
payment_provider_token = "your_token_here" # from @BotFather → Payments
channel_id = -1001234567890                # your private channel ID (integer)
```

### 4. Add the bot to your channel

Go to your private channel → **Settings** → **Administrators** → add your bot.
Required permissions: **Invite Users**, **Ban Members**.

### 5. Run

```bash
python main.py
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    expires_at  TIMESTAMP NOT NULL,
    invite_link TEXT,
    is_active   INTEGER DEFAULT 1
);
```

---

## 📋 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/payment` | Sends a payment invoice |
| `/pay` | Dev shortcut — simulates successful payment (for testing) |

---

## 🔑 How to Get Your Channel ID

1. Add your bot as admin to the channel
2. Forward any message from the channel to [@userinfobot](https://t.me/userinfobot)
3. It will return the channel ID — a negative number like `-1001234567890`
4. Use that number (not a string) in `channel_id`

---

## 💳 Payment Modes

**Telegram Stars (no provider needed):**
```python
provider_token = ""
currency = "XTR"
```

**Test mode with Stripe (no real charges):**
Get a test token via `@BotFather → /mybots → Payments → Stripe TEST`
```python
provider_token = "284685063:TEST:..."
currency = "USD"
prices = [LabeledPrice(label="Subscription", amount=500)]  # $5.00
```

---

## 🔄 How Auto-Revoke Works

`APScheduler` runs `check_expired_payments()` every hour in the same async event loop as the bot:

```python
async def check_expired_payments():
    for user_id in get_expired_payments():
        await revoke_access(bot, user_id)

scheduler.add_job(check_expired_payments, 'interval', hours=1)
```

`revoke_access` calls `ban_chat_member` followed by `unban_chat_member` — this kicks the user from the channel while keeping them unblocked so they can resubscribe later.

---

## 🛡️ One-Time Invite Links

Each subscriber gets a unique link with `member_limit=1` — it can only be used once and becomes invalid after that:

```python
await bot.create_chat_invite_link(
    chat_id=channel_id,
    member_limit=1,
    creates_join_request=False
)
```

This prevents link sharing between users.

---

## 📌 Notes

- All times are stored and compared in **UTC**
- The scheduler checks every **hour** — you can lower this to `minutes=30` for tighter expiry
- SQLite is fine for solo projects; swap for PostgreSQL if you expect many concurrent users
- Bot token and provider token should be moved to environment variables (`.env`) before deploying to production

---

## 👤 Author

Built as a portfolio project demonstrating real-world Telegram bot development: async Python, payment processing, database management, and automated task scheduling.

Open to freelance work and collaborations — feel free to reach out.
