import os
import time
import asyncio
import aria2p
from telethon import TelegramClient, events

# --- الإعدادات من Variables Railway ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# بدء تشغيل البوت
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ربط الكود بمحرك Aria2 الذي يعمل في الخلفية
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# دالة شريط التحميل (طبق الأصل لمودك ▰▱)
def GET_PROGRESS_BAR(current, total, start_time, action):
    now = time.time()
    diff = now - start_time
    if diff <= 0: return "جاري البدء..."
    
    percentage = (current * 100 / total) if total > 0 else 0
    speed = current / diff 
    
    filled_blocks = int(percentage / 10)
    bar = "▰" * filled_blocks + "▱" * (10 - filled_blocks)
    
    return (
        f"🚀 **{action}**\n\n"
        f"【{bar}】 {round(percentage, 2)}%\n"
        f"📦 الحجم: {round(current / 1024 / 1024, 2)} / {round(total / 1024 / 1024, 2)} MB\n"
        f"⚡ السرعة: {round(speed / 1024 / 1024, 2)} MB/s"
    )

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    name = user.first_name
    username = f"@{user.username}" if user.username else "لا يوجد يوزر نيم"
    uid = user.id
    
    if OWNER_ID != 0:
        try:
            log_text = (f"👤 **مستخدم جديد دخل للبوت:**\n\n📝 الاسم: {name}\n🔗 اليوزر: {username}\n🆔 الأيدي: `{uid}`")
            await bot.send_message(OWNER_ID, log_text)
        except: pass
        
    welcome_msg = (f"أهلاً بك يا {name} في بوت الرفع الصاروخي 🚀\n\n"
                   f"تم تفعيل محرك Aria2 لسرعة خيالية (16 اتصال متوازي)!\n"
                   f"أرسل الرابط المباشر الآن لتتم معالجته فوراً! ✨")
    await event.reply(welcome_msg)

@bot.on(events.NewMessage)
async def handler(event):
    url = event.text
    if not url.startswith("http") or url.startswith("/"): return

    user = await event.get_sender()
    if OWNER_ID != 0:
        try:
            admin_log = f"🔗 **طلب جديد من {user.first_name}:**\n📍 الرابط: {url}"
            await bot.send_message(OWNER_ID, admin_log)
        except: pass

    status_msg = await event.reply("📡 جاري استخدام محرك Aria2 للسحب بأقصى سرعة...")
    start_time = time.time()

    try:
        # التحميل باستخدام Aria2 (توزيع الحمل على 16 اتصال)
        download = aria2.add_uris([url], options={"split": "16", "max-connection-per-server": "16"})
        
        while not download.is_complete:
            download.update()
            # تحديث شريط التحميل كل 4 ثواني لتقليل الضغط
            text = GET_PROGRESS_BAR(download.completed_length, download.total_length, start_time, "تحميل Aria2 ⬇️")
            try: await status_msg.edit(text)
            except: pass
            await asyncio.sleep(4)

        # تجهيز الملف بعد التحميل
        file_path = download.files[0].path
        file_name = f"{os.path.basename(file_path)}_By_pdfingebot"
        os.rename(file_path, file_name)

        # المرحلة 2: الرفع لتليجرام
        upload_start = time.time()
        last_edit = time.time()

        async def up_cb(current, total):
            nonlocal last_edit
            if time.time() - last_edit > 5:
                try: await status_msg.edit(GET_PROGRESS_BAR(current, total, upload_start, "رفع تليجرام ⬆️"))
                except: pass
                last_edit = time.time()

        await bot.send_file(
            event.chat_id,
            file_name,
            caption=f"✅ **تم الإكمال بنجاح!**\n📦 الاسم: `{file_name}`",
            progress_callback=up_cb,
            force_file=True,
            supports_streaming=True
        )
        await status_msg.delete()

    except Exception as e:
        await event.reply(f"❌ **حدث خطأ:**\n`{str(e)}`")
    finally:
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)

print("🚀 الوحش انطلق الآن بمحرك Aria2 على Railway!")
bot.run_until_disconnected()
