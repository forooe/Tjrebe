import os
import time
import asyncio
import subprocess
import aria2p
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo

# --- إعدادات Railway ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# تشغيل aria2 في الخلفية
os.system("aria2c --enable-rpc --rpc-listen-all=false --rpc-max-request-size=10M --max-connection-per-server=16 --split=16 --daemon")
time.sleep(2)
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

def GET_PROGRESS_BAR(current, total, start_time, action):
    now = time.time()
    diff = now - start_time
    if diff <= 0: return "جاري البدء..."
    percentage = (current * 100 / total) if total > 0 else 0
    speed = current / diff 
    bar = "▰" * int(percentage / 10) + "▱" * (10 - int(percentage / 10))
    return (f"🚀 **{action}**\n\n【{bar}】 {round(percentage, 2)}%\n"
            f"📦 الحجم: {round(current/1024/1024, 2)} / {round(total/1024/1024, 2)} MB\n"
            f"⚡ السرعة: {round(speed/1024/1024, 2)} MB/s")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    if OWNER_ID != 0:
        await bot.send_message(OWNER_ID, f"👤 دخول جديد: {user.first_name}")
    await event.reply(f"أهلاً بك يا {user.first_name} في بوت الرفع الصاروخي 🚀\nكل ما عليك هو إرسال الرابط المباشر الآن!")

@bot.on(events.NewMessage)
async def handler(event):
    url = event.text
    if not url.startswith("http") or url.startswith("/"): return
    
    status_msg = await event.reply("📡 جاري السحب بواسطة Aria2...")
    start_time = time.time()
    
    try:
        # تحميل Aria2 (سريع جداً)
        download = aria2.add_uris([url], options={"split": "16", "max-connection-per-server": "16"})
        while not download.is_complete:
            download.update()
            try: await status_msg.edit(GET_PROGRESS_BAR(download.completed_length, download.total_length, start_time, "تحميل Aria2 ⬇️"))
            except: pass
            await asyncio.sleep(5)
        
        file_path = download.files[0].path
        file_name = f"{os.path.basename(file_path)}_By_pdfingebot"
        os.rename(file_path, file_name)
        
        # --- مود الرفع الصاروخي المعدل ---
        upload_start = time.time()
        last_edit = time.time()

        async def up_cb(current, total):
            nonlocal last_edit
            if time.time() - last_edit > 7:
                try: await status_msg.edit(GET_PROGRESS_BAR(current, total, upload_start, "رفع تليجرام الصاروخي ⬆️"))
                except: pass
                last_edit = time.time()

        # استخدام ميزة الرفع المتوازي (Fast Upload)
        # ملاحظة: Telethon مع cryptg ستستغل الـ 8 vCPU في Railway بالكامل هنا
        await bot.send_file(
            event.chat_id,
            file_name,
            caption=f"✅ **تم الإكمال بنجاح!**\n📦 الاسم: `{file_name}`",
            progress_callback=up_cb,
            force_file=True,
            supports_streaming=True,
            # السر في السطرين التاليين:
            part_size_kb=512, # قطعة كبيرة لتقليل عدد الطلبات
            allow_cache=False # عدم استهلاك الرام في الكاش لزيادة السرعة
        )
        await status_msg.delete()

    except Exception as e:
        await event.reply(f"❌ خطأ: `{str(e)}`")
    finally:
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)

bot.run_until_disconnected()
