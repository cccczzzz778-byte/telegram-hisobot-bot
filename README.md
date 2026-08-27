# Telegram hisobot boti

Bot guruhdagi rasmli hisobotlarni jim kuzatadi. Rasm izohidan muassasa nomini
topadi, bir muassasaning shu kundagi birinchi hisobotini saqlaydi va admin
buyrug‘i bilan rangli Excel hisobot beradi.

## Ishga tushirish

1. Python 3.11 yoki yangiroq versiyani o‘rnating.
2. `python -m venv .venv` buyrug‘i bilan virtual muhit yarating.
3. Windows: `.venv\\Scripts\\activate`; Linux: `source .venv/bin/activate`.
4. `pip install -r requirements.txt`.
5. `.env.example` nusxasini `.env` deb nomlang va `BOT_TOKEN` hamda `DATABASE_URL` qiymatlarini kiriting.
6. Kodlar bilan bir papkadagi `muassasalar.xlsx` faylini kerak bo‘lsa yangilang.
7. `python bot.py` buyrug‘i bilan ishga tushiring.

Bot Neon PostgreSQL bazasiga ulangan; hisobotlar server qayta ishga tushganda
ham saqlanadi. `Dockerfile` Railway deploy uchun tayyorlangan.
Railway’da `New Project` → `Deploy from GitHub Repo` orqali repozitoriyni tanlang.
Railway Dockerfile’ni avtomatik topadi va botni `python bot.py` bilan long polling
rejimida ishga tushiradi. Public domain yaratish talab qilinmaydi.

Loyiha tekis tuzilgan: barcha kodlar va `muassasalar.xlsx` bitta papkada.
`data` yoki boshqa ichma-ich papka talab qilinmaydi.

Botni guruhga admin qiling. Privacy Mode yoqilgan bo‘lsa, BotFather orqali
`/setprivacy` → `Disable` qiling; aks holda bot oddiy rasmli xabarlarni ko‘rmaydi.

## Buyruqlar

- `/start` — admin menyusi va buyruqlarni ko‘rsatish.
- `/hisobot` — bugungi Excel hisobot.
- `/hisobot 26.08.2026` — ko‘rsatilgan sana hisoboti.
- `/royhat` — amaldagi muassasalar ro‘yxatini olish.
- `/stats` — bugungi qisqa statistika.
- `/stats 26.08.2026` — ko‘rsatilgan sana statistikasi.
- `/admin_qosh 123456789` — Telegram ID bo‘yicha yangi bot adminini qo‘shish.
- `/yordam` — mavjud buyruqlarni ko‘rsatish.

Buyruqlar faqat botning shaxsiy chatida ishlaydi. Ulardan `.env` dagi
`ADMIN_IDS`, maqsadli guruh administratorlari va keyin qo‘shilgan bot adminlari
foydalana oladi. Har bir bot admini yangi bot adminini qo‘sha oladi. Ruxsatsiz
buyruqqa bot javob bermaydi.

## Muhim sozlamalar

- `DEADLINE_TIME=14:00` — shu vaqtdan keyin kelgan hisobot “Kechikdi”.
- `REPORT_TITLE=083 forma` — Excelning oxirgi ustuni nomi.
- `MATCH_THRESHOLD=0.64` — muassasa nomini aniqlash sezgirligi.
- Aliaslar ustunida muassasaning qisqa nomlarini `;` bilan ajrating.

Muassasa nomi topilsa, izohda xodim F.I.Sh. bo‘lmasa ham hisobot qabul qilinadi.
Guruhdagi xabarlarga bot hech qanday javob yubormaydi.
