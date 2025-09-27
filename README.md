# Telegram Music Bot (بوت تشغيل وتحميل أغاني)

هذه الحزمة تحتوي على سكربت `music_full_vps.py` — بوت تيليجرام عادي + userbot لتشغيل ملفات صوتية في مكالمات المجموعات وتحميلها من يوتيوب.

**ملاحظة أمان:** الملف يحتوي على `BOT_TOKEN` و`STRING_SESSION` و`API_HASH` إلخ — هذه مفاتيح حساسة. احفظ الملف في مكان آمن ولا تشاركه علنًا.

## ملفات المشروع
- `music_full_vps.py` — السكربت الرئيسي (بالعربية).
- `requirements.txt` — تبعيات Python.
- `Procfile` — لتشغيل على Heroku كـ worker.
- `runtime.txt` — نسخة بايثون الموصى بها.
- `.gitignore` — (مضمَّن في الأرشيف) تجاهل الملفات المؤقتة.
- `README.md` — هذا الملف.

## نشر على Heroku (خطوات سريعة)
1. أنشئ تطبيق جديد على Heroku.
2. أضف buildpack للـ APT (لتركيب ffmpeg) إن أردت تشغيل تحويلات صوتية:
   - `https://github.com/heroku/heroku-buildpack-apt`
   ثم أضف buildpack للـ Python (موجود افتراضيًا).
3. في تبويب "Settings" أضف Config Vars إذا رغبت بعدم تضمين المفاتيح في الملف:
   - `BOT_TOKEN`, `STRING_SESSION`, `USER_API_ID`, `USER_API_HASH`, `USER_PHONE`
   أو اترك القيم مضمنة داخل الملف (غير مستحسن).
4. ارفع الكود (git push heroku main) أو استخدم GitHub integration.
5. شغّل الـ worker من تبويب "Resources".

## ملاحظات فنية
- تحتاج Heroku لتوفر `ffmpeg` في البيئة لتقوم yt-dlp بعملية استخراج/تحويل الصوت. استخدم buildpack apt لإضافة `ffmpeg`.
- `pytgcalls` قد يحتاج نسخ معينة من مكتبات الصوت. إذا واجهت مشاكل بـ PyTgCalls على Heroku فقد تحتاج إلى VPS (مثل VPS خاص يدعم ALSA).
- السكربت يخزن الملفات المؤقتة في مجلد `tmp_music/` ويستخدم `queue.json` لقائمة التشغيل.

## ملفات الحساسية
أضف `tmp_music/` و`queue.json` إلى `.gitignore` قبل رفعك لGitHub إن أردت.

---
استخدم هذا الأرشيف كما ترغب. تم إعداد كل شيء حسب طلبك.
