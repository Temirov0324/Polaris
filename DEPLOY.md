# PolarisAI — VPS'ga deploy qilish qo'llanmasi

Bu qo'llanma **Ubuntu 22.04/24.04** VPS uchun yozilgan (DigitalOcean, Hetzner va
shunga o'xshash provayderlarda standart tanlov). Boshqa distributivda buyruqlar
biroz farq qilishi mumkin.

Hozircha **domen yo'q** — sayt `http://VPS_IP_MANZILINGIZ` orqali ochiladi.
Domen olganingizda, hujjat oxiridagi "Keyinroq: domen va HTTPS qo'shish"
bo'limiga qarang.

---

## 1. VPS'ga ulanish

```bash
ssh root@VPS_IP_MANZILINGIZ
```

## 2. Docker o'rnatish

```bash
curl -fsSL https://get.docker.com | sh
```

O'rnatilganini tekshiring:

```bash
docker --version
docker compose version
```

## 3. Xavfsizlik devori (firewall)

Faqat SSH (22), HTTP (80) portlarini oching — boshqa hamma narsa (Postgres,
Redis) tashqaridan yopiq bo'lishi kerak:

```bash
apt install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw enable
```

`ufw enable` so'raganda "y" deb tasdiqlang. **Diqqat**: SSH portini (22)
ochishni unutmang, aks holda serverdan uzilib qolasiz.

## 4. Kodni serverga olib borish

Eng oson yo'l — GitHub'ga push qilib, serverda `git clone` qilish. Agar
loyihangiz hali GitHub'da bo'lmasa, avval shu bilan shug'ullaning (menga
ayting, yordam beraman), yoki `scp` orqali to'g'ridan-to'g'ri fayllarni
ko'chirishingiz mumkin:

```bash
# O'z kompyuteringizda (loyiha papkasida), git bilan:
git clone <repo-url> travelai
scp -r . root@VPS_IP_MANZILINGIZ:/opt/travelai

# Yoki serverda, agar GitHub'da bo'lsa:
mkdir -p /opt/travelai && cd /opt/travelai
git clone <repo-url> .
```

Qolgan barcha buyruqlar `/opt/travelai` papkasida bajariladi:

```bash
cd /opt/travelai
```

## 5. `.env` faylini sozlash

```bash
cp .env.prod.example .env
nano .env
```

Quyidagilarni to'ldiring:

| O'zgaruvchi | Qiymat |
|---|---|
| `DJANGO_SECRET_KEY` | Tasodifiy uzun matn (pastdagi buyruq bilan yarating) |
| `ALLOWED_HOSTS` | VPS'ingizning IP manzili |
| `POSTGRES_PASSWORD` **va** `DATABASE_URL`ichidagi parol | Bir xil kuchli parol |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey dan olingan kalit |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Real SMTP ma'lumotlari — **shart**, aks holda ro'yxatdan o'tish/parol tiklash kodlari hech kimga yetib bormaydi (`.env.prod.example`dagi Gmail namunasiga qarang) |
| `SENTRY_DSN` (ixtiyoriy) | https://sentry.io dan bepul olinadigan DSN — xatoliklarni kuzatish uchun |

`DJANGO_SECRET_KEY` yaratish uchun (serverda Python bor):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Natijani nusxalab, `.env` faylidagi `DJANGO_SECRET_KEY=` qatoriga qo'ying.

`Ctrl+O`, `Enter`, `Ctrl+X` — saqlab chiqish (nano'da).

## 6. Ishga tushirish

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Birinchi marta image qurilishi biroz vaqt oladi (2-5 daqiqa). Tugagach:

```bash
docker compose -f docker-compose.prod.yml ps
```

Barcha xizmatlar (`db`, `redis`, `web`, `celery`, `celery-beat`, `nginx`)
"running"/"healthy" holatda bo'lishi kerak.

## 7. Admin va boshlang'ich ma'lumotlar

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec web python manage.py seed_destinations
```

## 8. Tekshirish

Brauzerda oching: `http://VPS_IP_MANZILINGIZ`

Admin panel: `http://VPS_IP_MANZILINGIZ/admin/`

---

## Foydali buyruqlar

```bash
# Loglarni ko'rish
docker compose -f docker-compose.prod.yml logs -f web

# Xizmatlarni qayta ishga tushirish
docker compose -f docker-compose.prod.yml restart

# To'xtatish
docker compose -f docker-compose.prod.yml down

# Yangi kod chiqqanda (GitHub'dan yangilash + qayta qurish)
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Keyinroq: domen va HTTPS qo'shish

Domen sotib olganingizda:

1. **DNS**: domen provayderingizda `A` yozuvi yarating — domenni VPS IP
   manzilingizga yo'naltiring (masalan `example.uz` → `203.0.113.10`).
   O'zgarish tarqalishi uchun 10-60 daqiqa kuting.

2. **`.env` faylini yangilang**:
   ```
   ALLOWED_HOSTS=203.0.113.10,example.uz,www.example.uz
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   AUTH_COOKIE_SECURE=True
   ```

3. **Certbot bilan bepul SSL sertifikat oling**:
   ```bash
   apt install -y certbot python3-certbot-nginx
   docker compose -f docker-compose.prod.yml stop nginx
   certbot certonly --standalone -d example.uz -d www.example.uz
   ```
   Bu `/etc/letsencrypt/live/example.uz/` papkasiga sertifikat yozadi.

4. **`nginx/nginx.conf`ga 443-port bloki qo'shish** kerak bo'ladi (bu qadamda
   menga qayta murojaat qiling — men `nginx.conf`ni va `docker-compose.prod.yml`
   dagi sertifikat volume'larini sizning aniq domeningiz uchun yangilab beraman).

5. Firewall'da 443-portni oching: `ufw allow 443/tcp`

6. Xizmatlarni qayta ishga tushiring:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

---

## Telegram bot sozlash (ixtiyoriy)

Bog'langan foydalanuvchilar barcha eslatmalarni (kunlik, streak, narx
pasayishi) email o'rniga Telegram orqali oladi — ochilish ehtimoli ancha
yuqori. Bot ichida `/byudjet <shahar> <kunlar>` buyrug'i ham ishlaydi.

**Talab**: webhook faqat HTTPS domen orqali ishlaydi — avval yuqoridagi
"Domen va HTTPS qo'shish" bosqichini bajaring.

1. Telegramda **@BotFather**ga yozing, `/newbot` buyrug'ini yuboring,
   ko'rsatmalarga amal qiling. Oxirida sizga **token** (masalan
   `123456:ABC-DEF...`) va bot **username**i (masalan `PolarisAIBot`)
   beriladi.

2. `.env` faylini yangilang:
   ```
   TELEGRAM_BOT_TOKEN=<BotFather bergan token>
   TELEGRAM_BOT_USERNAME=<bot username, @ belgisisiz>
   TELEGRAM_WEBHOOK_SECRET=<tasodifiy matn>
   ```
   `TELEGRAM_WEBHOOK_SECRET` yaratish uchun:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```

3. Konteynerlarni qayta ishga tushiring:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --force-recreate web celery celery-beat
   ```

4. Webhook'ni **bir marta** ro'yxatdan o'tkazing (o'z kompyuteringizdan
   yoki VPS'dan bajarish mumkin):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<domeningiz>/api/v1/telegram/webhook/<WEBHOOK_SECRET>/"
   ```
   Javobda `"ok":true` chiqishi kerak.

5. Tekshirish: Telegram'da botingizni toping, `/help` yuboring — buyruqlar
   ro'yxati kelishi kerak. Saytda Profil → "Telegram bilan bog'lash"
   tugmasini bosib, hisobingizni bog'lang.

## Admin AI yordamchi sozlash (ixtiyoriy)

`/admin/agent/` — faqat superuser (siz) kira oladigan sahifa: davlat,
yo'nalish va narx ma'lumotlarini erkin matn shaklida yozib/joylashtirib
berasiz, agent ularni tekshirib to'g'ridan-to'g'ri bazaga qo'shadi.
Foydalanuvchilarning shaxsiy ma'lumotlari (User, Trip, SavingEntry,
ChatMessage) bilan bu agentning hech qanday aloqasi yo'q — u faqat
Country/Destination/PriceReference jadvallarini o'zgartira oladi.

Foydalanuvchilarga xizmat qiladigan chat (`GEMINI_API_KEY`) bilan
aralashmasligi uchun **alohida** Gemini kaliti ishlatiladi.

1. https://aistudio.google.com/apikey saytidan yangi API kalit oling
   (yoki mavjud `GEMINI_API_KEY` bilan bir xil loyihadan ikkinchi kalit
   yarating).

2. `.env` faylini yangilang:
   ```
   GEMINI_ADMIN_API_KEY=<yangi kalit>
   ```

3. Konteynerni qayta ishga tushiring:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --force-recreate web
   ```

4. Tekshirish: `/admin/` panelga superuser sifatida kiring, yuqori
   menyudagi "AI yordamchi" tugmasini bosing va sinov uchun bitta davlat
   yoki yo'nalish yozib ko'ring.
