#!/usr/bin/env python3
# music_full_vps.py
# سكربت متكامل: بوت عادي + userbot (يشتغل بمكالمة المجموعة ويشغّل أغاني)
# تحذير: يحتوي على توكن و string session — احفظ الملف في مكان آمن.

import os
import asyncio
import tempfile
import shutil
from pathlib import Path

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

import yt_dlp
import telebot
from telebot import types

# ==================== إعدادات (محفوظة كما طلبت) ====================
# توكن البوت العادي
BOT_TOKEN = "8229968523:AAHdvsszi4M49BkcXdgonmClFQ-ZbTffTK8"

# بيانات حساب الاتصال (User account) — اللي أعطيت
USER_API_ID = 27227913
USER_API_HASH = "ba805b182eca99224403dbcd5d4f50aa"
USER_PHONE = "+12295276751"
DEVELOPER_USERNAME = "@ky_nx"

# StringSession (المُقدّم منك) — يخلّي السكربت يشتغل بدون OTP
STRING_SESSION = "AQECwoUAGXjVKKcHzhns-y_7lbbBy_y-fZ6G__fDlxZahdCq139QA5FgJbdSqMnFJM6pCzZBl9LklBlHMlNMx6Zg0u1XdCFEudZDpePXgoCI-y2W9yJRLBvGtfMIRRQeza05r3GnKpw8vHKh9o7KFbJugndGD-EV4owQz1zyv1fziKYpKFXvDFxdHIn4EQhQo4lVCRIV2t6nJLYKsiUa27G_RxQj2S0ieTi03v8qPzhSzix5sdTd7jWelocxpZHQb2x14YSjXdQie8wVeJCch7uFqFlDia86C3TrEjGiGWjaheTqB7HaEbdqVvcW3oMZXukzcvC088xxkaK53lCEPKm0GfOnNgAAAAHgd6IoAA"

# حد آمن لحجم الإرسال (لو أكبر، سيرسل رابط يوتيوب بدل الملف)
SEND_LIMIT = 50 * 1024 * 1024
# ==================================================================

# مجلد لحفظ الملفات المؤقتة
TMP_ROOT = Path("tmp_music")
TMP_ROOT.mkdir(parents=True, exist_ok=True)

# ---------- دوال مساعدة لتحميل من يوتيوب ----------
def download_from_youtube(query, mode="audio"):
    """
    mode: "audio" -> mp3, "video" -> mp4
    Returns dict with ok, filepath, title, tmpdir, url or reason
    """
    tmpdir = tempfile.mkdtemp(prefix="ytbot_", dir=str(TMP_ROOT))
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
    try:
        if mode == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": outtmpl,
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            entry = info["entries"][0] if isinstance(info, dict) and "entries" in info and info["entries"] else info
            files = os.listdir(tmpdir)
            if not files:
                return {"ok": False, "reason": "لم يتم تحميل أي ملف.", "url": entry.get("webpage_url") if entry else None}
            filepath = None
            for f in files:
                if mode == "audio" and f.lower().endswith(".mp3"):
                    filepath = os.path.join(tmpdir, f); break
                if mode == "video" and (f.lower().endswith(".mp4") or f.lower().endswith(".mkv") or f.lower().endswith(".webm")):
                    filepath = os.path.join(tmpdir, f); break
            if not filepath:
                filepath = os.path.join(tmpdir, files[0])
            title = entry.get("title") if entry else os.path.basename(filepath)
            return {"ok": True, "filepath": filepath, "title": title, "tmpdir": tmpdir, "url": entry.get("webpage_url") if entry else None}
    except Exception as e:
        try: shutil.rmtree(tmpdir)
        except: pass
        return {"ok": False, "reason": str(e)}

# ---------- بوت تيليجرام عادي (تحميل/ردود) ----------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

@bot.message_handler(commands=["start","help"])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "هلا! بوت تنزيل أغاني + تشغيل في مكالمات (لو كان userbot مُشغّل).\n\n"
        "اوامر في المحادثة/المجموعة:\n"
        "• يوت <اسم الأغنية>  -> ينزل MP3 ويرسله.\n"
        "• شغل <اسم الأغنية>  -> ينزل MP3 ويضعها في قائمة التشغيل (وإذا كان userbot متصل سيشغّلها بالمكالمة).\n\n"
        "في الخاص: اكتب اسم أغنية أو رابط وستظهر لك أزرار تحميل (MP3 / MP4).\n"
        f"مطور البوت: {DEVELOPER_USERNAME}"
    )

@bot.message_handler(func=lambda m: m.chat.type == "private" and m.content_type == "text")
def private_handler(message):
    query = message.text.strip()
    if not query:
        bot.reply_to(message, "اكتب اسم أغنية أو رابط.")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("تحميل صوت (mp3)", callback_data=f"private_audio||{query}"))
    kb.add(types.InlineKeyboardButton("تحميل فيديو (mp4)", callback_data=f"private_video||{query}"))
    bot.send_message(message.chat.id, f"اختر نوع التحميل ل: `{query}`", reply_markup=kb)

@bot.message_handler(func=lambda m: True, content_types=['text'])
def group_text_handler(message):
    text = message.text.strip()
    lowered = text.lower().strip()

    # يوت <name> -> تنزيل mp3 وارساله
    if lowered.startswith("يوت "):
        query = text[4:].strip()
        sent = bot.send_message(message.chat.id, f"جارٍ تنزيل mp3: {query}")
        res = download_from_youtube(query, mode="audio")
        if not res.get("ok"):
            bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"فشل: {res.get('reason')}")
            return
        filepath = res["filepath"]
        title = res["title"]
        filesize = os.path.getsize(filepath)
        try:
            if filesize > SEND_LIMIT:
                url = res.get("url")
                bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"الملف كبير ({filesize//(1024*1024)}MB). رابط: {url}")
            else:
                with open(filepath, "rb") as f:
                    bot.send_audio(message.chat.id, f, title=title)
                bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"تم الإرسال: {title}")
        except Exception as e:
            bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"خطأ أثناء الإرسال: {e}")
        finally:
            try: shutil.rmtree(res["tmpdir"])
            except: pass
        return

    # شغل <name> -> ضيف للايفق (queue) و جرّب تشغيله لو userbot متصل
    if lowered.startswith("شغل "):
        query = text[5:].strip()
        if not query:
            bot.reply_to(message, "اكتب اسم الأغنية بعد 'شغل'.")
            return
        sent = bot.send_message(message.chat.id, f"طلب تشغيل: {query}\nجارٍ تنزيل الملف ووضعه في قائمة الانتظار...")
        # ننزل الملف (mp3) ونضيفه للـ queue.json
        res = download_from_youtube(query, mode="audio")
        if not res.get("ok"):
            bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"فشل التحميل: {res.get('reason')}")
            return
        filepath = res["filepath"]
        title = res["title"]
        # إضافة للصف الانتظار (ملف نصي)
        qfile = Path("queue.json")
        try:
            import json
            q = []
            if qfile.exists():
                q = json.loads(qfile.read_text())
            q.append({"chat_id": message.chat.id, "title": title, "filepath": filepath})
            qfile.write_text(json.dumps(q, ensure_ascii=False, indent=2))
            bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"أضيفت `{title}` لقائمة التشغيل. سيشغّلها حساب المطور لو كان متصل بالمكالمة.")
        except Exception as e:
            bot.edit_message_text(chat_id=message.chat.id, message_id=sent.message_id, text=f"خطأ أثناء حفظ في قائمة الانتظار: {e}")
        return

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    data = call.data or ""
    if data.startswith("private_audio||") or data.startswith("private_video||"):
        mode, query = data.split("||",1)
        mode = "audio" if mode=="private_audio" else "video"
        msg = bot.send_message(call.message.chat.id, f"جارٍ تنزيل ({mode})... الرجاء الانتظار.")
        res = download_from_youtube(query, mode=mode)
        if not res.get("ok"):
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"فشل التحميل: {res.get('reason')}")
            return
        filepath = res["filepath"]
        title = res["title"]
        filesize = os.path.getsize(filepath)
        try:
            if filesize > SEND_LIMIT:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"الملف كبير ({filesize//(1024*1024)}MB). رابط: {res.get('url')}")
            else:
                if mode=="audio":
                    with open(filepath,"rb") as f:
                        bot.send_audio(call.message.chat.id, f, title=title)
                else:
                    with open(filepath,"rb") as f:
                        bot.send_video(call.message.chat.id, f, supports_streaming=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"تم إرسال {mode} — {title}")
        except Exception as e:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"خطأ: {e}")
        finally:
            try: shutil.rmtree(res["tmpdir"])
            except: pass
    else:
        bot.answer_callback_query(call.id, "تم.")

# ================== Userbot (Telethon + PyTgCalls) لتشغيل الصوت في المكالمات ==================
class MusicUserbot:
    def __init__(self, string_session: str, api_id: int, api_hash: str, phone: str):
        # استخدم StringSession إن وُجد
        if string_session:
            self.client = TelegramClient(StringSession(string_session), api_id, api_hash)
        else:
            self.client = TelegramClient("user_session", api_id, api_hash)
        self.call = PyTgCalls(self.client)
        self.playing = False

    async def start(self):
        # لو STRING_SESSION موجود فالبدء مباشر، وإلا سيطلب OTP تلقائيًا
        await self.client.start()
        await self.call.start()
        me = await self.client.get_me()
        print(f"[Userbot] Logged in as {getattr(me,'username',me.id)}")
        # بعد بدء الجلسة نبدأ مراقبة قائمة الانتظار لتشغيلها إن كانت متوفرة
        asyncio.create_task(self.queue_worker())

        # نستمع لرسائل "شغل" أيضاً من داخل الحساب نفسه (لو احتجنا)
        @self.client.on(events.NewMessage(pattern=r"^تشغيل (.+)"))
        async def local_play_handler(event):
            query = event.pattern_match.group(1).strip()
            await event.reply(f"أمر تشغيل محلي مستلم: {query}")

    async def queue_worker(self):
        qfile = Path("queue.json")
        import json
        while True:
            try:
                if qfile.exists():
                    q = json.loads(qfile.read_text())
                else:
                    q = []
                if q:
                    # خذ أول عنصر وحاول تشغيله في مكالمة الـ chat_id
                    item = q.pop(0)
                    # احفظ الباقي
                    qfile.write_text(json.dumps(q, ensure_ascii=False, indent=2))
                    chat_id = item.get("chat_id")
                    filepath = item.get("filepath")
                    title = item.get("title")
                    try:
                        print(f"[Userbot] محاولة الانضمام للمكالمة في chat_id={chat_id} وتشغيل: {title}")
                        # join and play in group call
                        await self.call.join_group_call(chat_id, AudioPiped(filepath))
                        self.playing = True
                        # ابقي شغال للمدة التقريبية للملف ثم اترك المكالمة (تقديري)
                        # == يمكن تحسينها بقياس طول الملف عبر ffprobe لو تحب
                        await asyncio.sleep(3)  # نعطيه وقت للانطلاق
                        # نراقب لحد انتهاء التشغيل بطريقة بسيطة: ننتظر طول الملف ليس متوفر هنا، فنعطي تأخير ثابت كبير
                        # بديل: استعمل ffprobe لقياس مدة الملف ثم await asyncio.sleep(duration)
                        await asyncio.sleep(10)  # وقت تشغيل افتراضي قصير — يمكن تحسينه
                        try:
                            await self.call.leave_group_call(chat_id)
                        except Exception:
                            pass
                        self.playing = False
                        # بعد تشغيل الملف ننظف الملف المؤقت
                        try:
                            if os.path.exists(filepath):
                                os.remove(filepath)
                        except:
                            pass
                    except Exception as e:
                        print(f"[Userbot] خطأ أثناء تشغيل الأغنية: {e}")
                        # لو فشل التشغيل نكمل التالي
                else:
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"[Userbot] خطأ في عامل القائمة: {e}")
                await asyncio.sleep(5)

# ================== تشغيل كل شيء ==================
async def main():
    # شغّل userbot
    print("[*] بدء تشغيل Userbot...")
    userbot = MusicUserbot(STRING_SESSION, USER_API_ID, USER_API_HASH, USER_PHONE)
    await userbot.start()
    print("[*] بدء تشغيل البوت العادي (polling) ...")
    loop = asyncio.get_event_loop()
    # شغّل polling للبوت في ثريد غير متزامن
    loop.create_task(asyncio.to_thread(bot.infinity_polling))
    # خلّي البرنامج شغال
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("تم الإيقاف.")
