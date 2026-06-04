from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.types import  Message, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.types import LabeledPrice
from aiogram import F
import asyncio
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler



dp = Dispatcher()

BOT_TOKEN = "8812385852:AAHXVjR3udfw7G0oFIQED8g6iDadEhp09Ng"
payment_provider_token = "YOUR_PAYMENT_PROVIDER_TOKEN_HERE"
admin_id = 852371393
channel_id = -1003932672021  

bot = Bot(token=BOT_TOKEN, default_properties=DefaultBotProperties(parse_mode=ParseMode.HTML))




@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("You can use the /payment command to test payments.")




# ---------------------------- database setup
conn = sqlite3.connect('payments.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    invite_link TEXT,   
                    is_active INTEGER DEFAULT 1
                )''')




def add_payment(user_id: int, username: str, invite_link: str):
    expires_at = datetime.utcnow() + timedelta(days=30)
    cursor.execute(
        "INSERT OR REPLACE INTO payments (user_id, username, expires_at, invite_link, is_active) VALUES (?, ?, ?, ?, 1)",
        (user_id, username, expires_at, invite_link)
    )
    conn.commit()

def get_expired_payments():
    rows = conn.execute("SELECT user_id, invite_link FROM payments WHERE expires_at <= ? AND is_active = 1", (datetime.utcnow(),)).fetchall()
    return [r[0] for r in rows]

def get_active_payments() -> list[dict]:
    return cursor.execute("SELECT user_id, username, expires_at FROM payments WHERE expires_at > ? AND is_active = 1", (datetime.utcnow(),)).fetchall()

    









# ---------------------------- payment logic

@dp.message(Command("payment"))
async def payment_command(message: Message):
    await bot.send_invoice(
        chat_id=message.from_user.id,
        title="Sample Product",
        description="This is a sample product for testing payments.",
        payload="sample_payload",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Sample Product", amount=1000)], 
    )




@dp.pre_checkout_query()
async def pre_checkout_query_handler(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)




@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    await message.answer("Thank you for your payment! Your order has been received.")  
    await proccess_payment_successful(message)
    await feeedback(message) 




async def feeedback(message: Message):
    user = message.from_user.username
    bot.send_message(
        chat_id=admin_id,
        text = (
            f"<b> New subscription </b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i> New subscription from {user}"
        )
    )
    







# ----------------------------- payment succes ---------------------


async def proccess_payment_successful(message: Message):
    invite_link = await create_invite_link(bot)
    add_payment(message.from_user.id, message.from_user.username, invite_link)
    await message.answer(f"Payment succesful! Here is your unvite link:\n{invite_link}")

# ------------------------------ payment product function -------------------


async def create_invite_link(bot: Bot) -> str:
    invite_link = await bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, creates_join_request=False)
    return invite_link.invite_link

async def revoke_invite_link(bot: Bot, invite_link: str):
    await bot.revoke_chat_invite_link(chat_id=channel_id, invite_link=invite_link)

async def revoke_access(bot: Bot, user_id: int):
    try:
        await bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
    except Exception as e:
        print(f"Error revoking access for user {user_id}: {e}")



#------------------------------ scheduler for expiring payments -------------------
scheduler = AsyncIOScheduler()

async def check_expired_payments():
    for user_id in get_expired_payments():
        await revoke_access(bot, user_id)


scheduler.add_job(check_expired_payments, 'interval', hours=1)



async def main():
    print("Bot is running...")
    scheduler.start()
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())





    