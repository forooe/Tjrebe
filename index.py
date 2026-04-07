import os
import time
import asyncio
import subprocess

# محاولة تنصيب aria2 يدوياً إذا لم يكن موجوداً
try:
    subprocess.run(["apt-get", "update", "-y"], check=False)
    subprocess.run(["apt-get", "install", "aria2", "-y"], check=False)
except:
    pass

import aria2p
from telethon import TelegramClient, events

# --- الإعدادات ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# تشغيل aria2 في الخلفية برمجياً
os.system("aria2c --enable-rpc --rpc-listen-all=false --rpc-max-request-size=10M --max-connection-per-server=16 --split=16 --daemon")
time.sleep(2) # انتظار المحرك ليقلع

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# دالة شريط التحميل (▰▱)
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
    await event.reply("أهلاً بك! البوت يعمل الآن بأقصى سرعة (مود Aria2) 🚀")

@bot.on(events.NewMessage)
async def handler(event):
    url = event.text
    if not url.startswith("http") or url.startswith("/"): return
    
    status_msg = await event.reply("📡 جاري السحب بواسطة Aria2...")
    start_time = time.time()
    
    try:
        download = aria2.add_uris([url], options={"split": "16", "max-connection-per-server": "16"})
        while not download.is_complete:
            download.update()
            try: await status_msg.edit(GET_PROGRESS_BAR(download.completed_length, download.total_length, start_time, "تحميل Aria2 ⬇️"))
            except: pass
            await asyncio.sleep(5)
        
        file_path = download.files[0].path
        file_name = f"{os.path.basename(file_path)}_By_pdfingebot"
        os.rename(file_path, file_name)
        
        # الرفع
        upload_start = time.time()
        last_edit = time.time()
        async def up_cb(current, total):
            nonlocal last_edit
            if time.time() - last_edit > 6:
                try: await status_msg.edit(GET_PROGRESS_BAR(current, total, upload_start, "رفع تليجرام ⬆️"))
                except: pass
                last_edit = time.time()
        
        await bot.send_file(event.chat_id, file_name, caption=f"✅ تم بنجاح!\n`{file_name}`", progress_callback=up_cb)
        await status_msg.delete()
    except Exception as e:
        await event.reply(f"❌ خطأ: `{str(e)}`")
    finally:
        if 'file_name' in locals() and os.path.exists(file_name): os.remove(file_name)

bot.run_until_disconnected()
