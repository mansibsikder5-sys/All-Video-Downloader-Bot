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
    return "⚡ Premium Downloader Bot is Running Smoothly! ⚡"

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
        "🚀 জাস্ট লিঙ্কটি কপি করে এখানে পেস্ট করে দিন!"
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
        
        # 🚀 অল্টারনেটিভ শক্তিশালী প্রিমিয়াম নো-ব্লক এপিআই ইঞ্জিন (যা ডিরেক্ট ভিডিও স্ট্রিম ইউআরএল দেয়)
        api_url = "https://co.wuk.sh/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "vQuality": "720",
            "isAudioOnly": False,
            "disableMetadata": True
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            result = response.json()

        video_url = result.get("url")
        
        if video_url:
            await status_message.edit_text("🚀 ডাউনলোড সফল! এবার ভিডিওটি আপনার চ্যাটে পাঠানো হচ্ছে... 📤")
            
            # সরাসরি ভিডিও টেলিগ্রামে পাঠিয়ে দেওয়া
            await update.message.reply_video(
                video=video_url, 
                caption="🎉 আপনার কাঙ্ক্ষিত ভিডিওটি রেডি! উপভোগ করুন। 🔥\n\n👑 Developer By MANSIB"
            )
            await status_message.delete()
        else:
            # যদি এপিআই প্রথম মেথডে ফেল করে, তবে সেকেন্ডারি মেথড ট্রাই করবে
            raise Exception("Primary API returned empty url")

    except Exception as e:
        print(f"Error: {str(e)}")
        # ২য় মেথড (ব্যাকআপ এপিআই)
        try:
            backup_url = f"https://api.cobalt.tools/api/json"
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(backup_url, headers={"Accept": "application/json", "Content-Type": "application/json"}, json={"url": url})
                res_data = res.json()
                b_url = res_data.get("url")
                if b_url:
                    await update.message.reply_video(video=b_url, caption="🎉 আপনার কাঙ্ক্ষিত ভিডিওটি রেডি! উপভোগ করুন। 🔥\n\n👑 Developer By MANSIB")
                    await status_message.delete()
                    return
        except:
            pass

        await status_message.edit_text(
            "❌ দুঃখিত! ভিডিওটি প্রসেস করা সম্ভব হয়নি।\n\n"
            "💡 **সম্ভাব্য কারণ:**\n"
            "১. লিঙ্কটি প্রাইভেট বা স্টোরি লিঙ্ক হতে পারে (যা FastDL-ও পারে না)। 🧩\n"
            "২. রেন্ডার নেটওয়ার্ক অতিরিক্ত জ্যামের কারণে রেসপন্স করতে দেরি করেছে। দয়া করে আবার চেষ্টা করুন! 🛑"
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

    print("Bot is starting with Hybrid API Engine...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
