# Taomdor Bot — Ishga tushirish yo'riqnomasi

## Railway.app orqali (tavsiya etiladi — bepul, 24/7)

### 1-qadam: GitHub akkaunt oching
1. github.com ga kiring
2. "Sign up" bosing → email bilan ro'yxatdan o'ting

### 2-qadam: Yangi repository yarating
1. GitHub'da "+" tugmasini bosing → "New repository"
2. Nom: `taomdor-bot`
3. "Create repository" bosing

### 3-qadam: Fayllarni yuklang
1. "uploading an existing file" havolasini bosing
2. Barcha 5 ta faylni sudrab tashlang:
   - bot.py
   - database.py
   - config.py
   - requirements.txt
   - Procfile
3. "Commit changes" bosing

### 4-qadam: Railway ga ulang
1. railway.app ga kiring
2. "Login with GitHub" bosing
3. "New Project" → "Deploy from GitHub repo"
4. `taomdor-bot` ni tanlang
5. Deploy tugmasini bosing

### 5-qadam: Bot ishlayapti!
Deploy tugagach bot avtomatik ishga tushadi.
Loglar ko'rish uchun: Railway → Deployments → View Logs

---

## Bot buyruqlari (admin uchun)

- `/start` — Admin paneliga kirish
- `/orders` — Yangi buyurtmalar
- `/all` — Oxirgi 10 buyurtma
- `/stats` — Statistika

## Holat tugmalari
Har bir buyurtmada tugmalar bor:
- 🆕 Yangi
- 👨‍🍳 Tayyorlanmoqda
- 🛵 Yetkazilmoqda
- ✅ Yetkazildi
- ❌ Bekor qilindi

Tugma bosilganda mijozga ham avtomatik xabar boradi.
