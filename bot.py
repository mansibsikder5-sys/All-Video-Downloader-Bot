import os
import threading
import asyncio
import httpx
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---- Fake Server for Render Free Tier ----
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Downloader Bot with 2026 Ultra API Engine is Running! ⚡"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---- Telegram Bot Logic ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    full_name = user.full_name

    await update.message.reply_text(
        "👋 আসসালামু আলাইকুম!\n"
        "আমি আপনার **অল-ইন-ওয়ান ভিডিও ডাউনলোডার বট**। 🤖✨\n\n"
        "আমাকে যেকোনো ভিডিওর লিঙ্ক পাঠান, আমি সেটি সরাসরি ডাউনলোড করে দেবো! 😎\n\n"
        "🎯 **আমি যা যা ডাউনলোড করতে পারি:**\n"
        "🔹 TikTok Videos 🎬\n"
        "🔹 YouTube Shorts & Videos 📺\n"
        "🔹 Facebook Videos 📱\n"
        "🔹 Instagram Reels 📸\n\n"
        "🚀 ஜাস্ট লিঙ্কটি কপি করে এখানে পেস্ট করে দিন!"
    )

    BACKUP_CHAT_ID = os.environ.get("TELEGRAM_BACKUP_CHAT_ID")
    if BACKUP_CHAT_ID:
        try:
            log_message = (
                "🎉 **নতুন ইউজার জয়েন করেছে!** 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **নাম:** {full_name}\n"
                f"🆔 **আইডি:** `{user_id}`\n"
                f"🔗 **ইউজারনেম:** {username}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 _বটটি সফলভাবে কাজ করছে..._"
            )
            await context.bot.send_message(chat_id=BACKUP_CHAT_ID, text=log_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Backup Channel Error: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("⚠️ ওহ! দয়া করে একটি সঠিক ভিডিও লিঙ্ক (URL) পাঠান। 🧩")
        return

    status_message = await update.message.reply_text("🔍 লিঙ্কটি চেক করা হচ্ছে... একটু অপেক্ষা করুন! ⏳")

    try:
        await status_message.edit_text("⚡ আমাদের সার্ভারে ভিডিও প্রসেস শুরু হয়েছে... 📥")
        
        # 🔥 ২০২৬ সালের আপডেটেড কোবাল্ট এপিআই প্রোটোকল
        api_url = "https://current.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {
            "url": url,
            "vQuality": "720", 
            "isAudioOnly": False
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            
            # ১ম সার্ভার বিজি থাকলে ব্যাকআপ গ্লোবাল এন্ডপয়েন্টে ট্রাই করবে
            if response.status_code != 200:
                fallback_api = "https://api.cobalt.tools/api/json"
                response = await client.post(fallback_api, headers=headers, json=payload)

            result = response.json()

        video_url = result.get("url")
        
        if video_url:
            await status_message.edit_text("🚀 ডাউনলোড সফল! এবার ভিডিওটি আপনার চ্যাটে পাঠানো হচ্ছে... 📤")
            
            # সরাসরি ভিডিওর ইউআরএল টেলিগ্রামে পুশ করা
            await update.message.reply_video(
                video=video_url, 
                caption="🎉 আপনার কাঙ্ক্ষিত ভিডিওটি রেডি! উপভোগ করুন। 🔥\n\n👑 Developer By MANSIB"
            )
            await status_message.delete()
        else:
            raise Exception("No video stream found from API")

    except Exception as e:
        print(f"Error: {str(e)}")
        await status_message.edit_text(
            "❌ দুঃখিত! ভিডিওটি প্রসেস করা সম্ভব হয়নি।\n\n"
            "💡 **কারণ ও সমাধান:**\n"
            "১. লিঙ্কটি ভুল, প্রাইভেট প্রোফাইল বা স্টোরি লিঙ্ক হতে পারে। 🧩\n"
            "২. এপিআই সার্ভার অতিরিক্ত জ্যাম। দয়া করে ১ মিনিট পর আবার চেষ্টা করুন, হয়ে যাবে! ⚡"
        )

def main():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    print("Bot is starting with 2026 Ultra API Engine...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
