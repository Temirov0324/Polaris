# PolarisAI — Texnik Topshiriq (V1 MVP, Web versiya)

> Bu hujjat Claude Code uchun mo'ljallangan. Har bir bo'lim mustaqil vazifa sifatida
> berilishi mumkin. Bosqichma-bosqich boring — hammasini bir buyruqda bermang.

---

## 0. Loyiha haqida qisqacha

**Nima quriladi:** O'zbekistonlik foydalanuvchilar uchun sayohat byudjetini hisoblab
beruvchi va jamg'arish rejasini boshqaruvchi **veb-ilova** (fullstack website) + AI chat.

**V1 doirasi:** 3 ta funksiya — byudjet hisoblash, jamg'arish rejasi, AI chat.
Narx monitoringi, bashorat, marketplace, bron qilish **V1'ga kirmaydi**.

**Platforma:** Faqat **veb** (brauzer orqali ishlaydi, responsive — desktop va mobil
brauzerda ham yaxshi ko'rinishi kerak). Native mobil ilova **yo'q**.

**Til:** Interfeys — o'zbek tili (lotin). Kod, kommentariya, commit — ingliz tili.

**Muhim arxitektura talabi:** Backend va frontend **bitta portda** ishlaydi. Alohida
frontend server (masalan `npm run dev` -> 5173-port) bo'lmaydi. Django ilovaning o'zi
statik HTML/CSS/JS fayllarni ham serve qiladi, shu bilan birga `/api/v1/...` ostida
API'ni ham beradi. Foydalanuvchi bitta manzilga kiradi: `http://localhost:8000/`.

---

## 1. Texnologiya stack

### Backend
- Python 3.12
- Django 5.x + Django REST Framework
- PostgreSQL 16
- Redis (faqat cache va Celery broker uchun)
- Celery (kunlik push/email eslatmalar uchun — V1'da email, push keyinroq)
- `django-environ` — konfiguratsiya
- `djangorestframework-simplejwt` — autentifikatsiya (JWT httpOnly cookie orqali saqlanadi)
- `drf-spectacular` — OpenAPI hujjat
- `whitenoise` — statik fayllarni Django orqali productionda serve qilish
- Anthropic Python SDK — AI chat

### Frontend
- **Toza HTML5 + CSS3 + Vanilla JavaScript (ES6+)**. Hech qanday build tool, bundler,
  npm, React/Vue/Angular **ishlatilmaydi**. Sabab: bitta portda, alohida build bosqichisiz,
  Django statik fayl sifatida to'g'ridan-to'g'ri serve qilishi kerak.
- Sahifalar orasida navigatsiya: oddiy ko'p sahifali (multi-page) HTML **yoki** bitta
  `index.html` + JS orqali soha almashtirish (SPA-lite, hash routing `#/dashboard` kabi).
  Tavsiya: SPA-lite, chunki auth holatini boshqarish osonroq.
- `fetch()` API orqali backend bilan aloqa (`/api/v1/...`), JSON.
- Grafik uchun: yengil, CDN'siz kutubxona shart emas — oddiy `<canvas>` bilan qo'lda
  chizilgan bar chart yetarli (progress halqa, haftalik ustunli grafik).
- CSS: oddiy custom CSS, o'zgaruvchilar (`:root { --color-primary: ... }`) orqali
  theming. CSS framework (Tailwind/Bootstrap) shart emas, lekin xohlasa engil
  utility-class yondashuvi qo'lda yozilishi mumkin.
- LocalStorage: faqat UI sozlamalari uchun (masalan tanlangan valyuta). Token —
  httpOnly cookie'da, JS orqali o'qib bo'lmaydigan tarzda (XSS himoyasi uchun).

### Infra
- Docker + docker-compose (dev va prod) — **bitta** `web` xizmati (Django + statik
  frontend), `db` (Postgres), `redis`, `celery`
- Nginx (faqat prod uchun reverse proxy, dev'da shart emas — `manage.py runserver`
  yoki `gunicorn` bitta portda yetarli)
- GitHub Actions (lint + test)

---

## 2. Repository tuzilmasi

```
travelai/
├── backend/
│   ├── config/                # Django settings (base/dev/prod), urls.py (API + frontend routing)
│   ├── apps/
│   │   ├── users/              # User, auth, profile
│   │   ├── destinations/       # Yo'nalishlar va narx bazasi
│   │   ├── trips/               # Sayohat rejalari, byudjet
│   │   ├── savings/             # Jamg'arish yozuvlari
│   │   ├── chat/                 # AI chat
│   │   └── notifications/       # Email/push eslatmalar
│   ├── core/                   # Umumiy: base models, exceptions, pagination
│   ├── frontend/                # <-- statik frontend shu yerda joylashadi
│   │   ├── templates/
│   │   │   └── index.html      # Yagona kirish nuqtasi (SPA-lite shell)
│   │   └── static/
│   │       ├── css/
│   │       │   ├── base.css
│   │       │   ├── components.css
│   │       │   └── pages/
│   │       ├── js/
│   │       │   ├── api.js          # fetch wrapper, token refresh
│   │       │   ├── router.js       # hash-based router
│   │       │   ├── state.js        # oddiy global state
│   │       │   ├── pages/
│   │       │   │   ├── auth.js
│   │       │   │   ├── dashboard.js
│   │       │   │   ├── trip-create.js
│   │       │   │   ├── savings.js
│   │       │   │   ├── chat.js
│   │       │   │   └── profile.js
│   │       │   └── components/
│   │       │       ├── progress-ring.js
│   │       │       └── bar-chart.js
│   │       └── img/
│   ├── requirements/
│   ├── Dockerfile
│   └── manage.py
├── docker-compose.yml
└── README.md
```

Django `TEMPLATES` sozlamasida `backend/frontend/templates` qo'shiladi,
`STATICFILES_DIRS` ga `backend/frontend/static` qo'shiladi. Bitta catch-all view
(`TemplateView`) barcha frontend route'larni (`/`, `/dashboard`, `/trips/new` va h.k.)
`index.html` ga yo'naltiradi, `/api/`, `/admin/`, `/static/` bundan mustasno.

---

## 3. Ma'lumotlar modeli

### 3.1 `users.User`
Django AbstractUser'dan meros. `username` o'rniga **telefon raqam** bilan kirish.

| Maydon | Tur | Izoh |
|---|---|---|
| `phone` | CharField(13), unique | `+998901234567` formatida |
| `full_name` | CharField(150) | |
| `home_city` | CharField(50) | default: `Tashkent` |
| `currency` | CharField(3) | `USD` yoki `UZS`, default `USD` |
| `monthly_income` | DecimalField, null | Ixtiyoriy |
| `has_passport` | BooleanField | default False |
| `travel_style` | CharField choices | `econom` / `standard` / `comfort` |
| `created_at` | DateTimeField | |

> Eslatma: mobil versiyadagi `fcm_token` maydoni V1 veb versiyasida kerak emas
> (push o'rniga email eslatma ishlatiladi — 8-bo'limga qarang).

### 3.2 `destinations.Country`
| Maydon | Tur |
|---|---|
| `name_uz` | CharField(100) |
| `name_en` | CharField(100) |
| `code` | CharField(2), unique — ISO |
| `visa_type` | CharField choices: `free` / `on_arrival` / `evisa` / `embassy` |
| `visa_cost_usd` | DecimalField |
| `visa_note_uz` | TextField, blank |
| `is_active` | BooleanField |

### 3.3 `destinations.Destination`
Shahar darajasidagi yo'nalish.

| Maydon | Tur |
|---|---|
| `country` | FK → Country |
| `city_uz`, `city_en` | CharField(100) |
| `image_url` | URLField, blank |
| `description_uz` | TextField |
| `is_popular` | BooleanField |

### 3.4 `destinations.PriceReference` ⭐ **Loyihaning yuragi**
Toshkentdan chiqadigan o'rtacha narxlar. **Qo'lda kiritiladi**, API'dan emas.

| Maydon | Tur | Izoh |
|---|---|---|
| `destination` | FK → Destination | |
| `month` | IntegerField (1–12) | Mavsumiylik uchun |
| `flight_return_usd` | DecimalField | Borish-kelish, econom |
| `hotel_night_econom` | DecimalField | |
| `hotel_night_standard` | DecimalField | |
| `hotel_night_comfort` | DecimalField | |
| `food_day_econom` | DecimalField | |
| `food_day_standard` | DecimalField | |
| `food_day_comfort` | DecimalField | |
| `transport_day_usd` | DecimalField | Shahar ichi |
| `activity_day_usd` | DecimalField | |
| `confidence` | CharField: `high`/`medium`/`low` | Ma'lumot ishonchliligi |
| `updated_at` | DateTimeField | |

**Unique together:** `(destination, month)`

Admin panelda import/export uchun `django-import-export` ulanadi — narxlarni CSV orqali
yangilash mumkin bo'lsin.

### 3.5 `trips.Trip`
| Maydon | Tur |
|---|---|
| `user` | FK → User |
| `destination` | FK → Destination |
| `start_date` | DateField |
| `duration_days` | IntegerField |
| `travelers_count` | IntegerField, default 1 |
| `style` | CharField: econom/standard/comfort |
| `budget_min` | DecimalField — hisoblangan |
| `budget_max` | DecimalField — hisoblangan |
| `target_amount` | DecimalField — foydalanuvchi tasdiqlagan maqsad |
| `status` | CharField: `planning` / `saving` / `completed` / `cancelled` |
| `created_at` | DateTimeField |

### 3.6 `trips.BudgetBreakdown`
Trip bilan 1:1. Hisoblash natijasi saqlanadi (qayta hisoblamaslik uchun).

Maydonlar: `flight`, `accommodation`, `food`, `transport`, `activities`,
`visa`, `insurance`, `reserve` — barchasi DecimalField (USD).

### 3.7 `savings.SavingEntry`
| Maydon | Tur |
|---|---|
| `trip` | FK → Trip |
| `amount` | DecimalField |
| `date` | DateField |
| `note` | CharField(200), blank |
| `created_at` | DateTimeField |

**Unique together:** `(trip, date)` — kuniga bitta yozuv, yangilanadi.

### 3.8 `chat.ChatMessage`
| Maydon | Tur |
|---|---|
| `user` | FK → User |
| `trip` | FK → Trip, null | Kontekst uchun |
| `role` | CharField: `user` / `assistant` |
| `content` | TextField |
| `created_at` | DateTimeField |

---

## 4. Byudjet hisoblash logikasi

**Joylashuv:** `apps/trips/services/budget_calculator.py`

Bu **sof funksiya** bo'lishi kerak — Django modelga bog'liq bo'lmagan, oson test qilinadigan.

### Algoritm

```
Kirish: destination_id, start_date, duration_days, travelers_count, style

1. month = start_date.month
2. price_ref = PriceReference.objects.get(destination=destination, month=month)
   Agar topilmasa → eng yaqin oydagi ma'lumotni ol, "low confidence" belgila

3. flight        = price_ref.flight_return_usd * travelers_count
4. nights        = duration_days - 1
   accommodation = hotel_night_{style} * nights * ceil(travelers_count / 2)
   # 2 kishi bitta xonada
5. food          = food_day_{style} * duration_days * travelers_count
6. transport     = transport_day_usd * duration_days * travelers_count
7. activities    = activity_day_usd * duration_days * travelers_count
8. visa          = country.visa_cost_usd * travelers_count
9. insurance     = 1.5 * duration_days * travelers_count   # kuniga ~$1.5
10. subtotal     = 3..9 yig'indisi
    reserve      = subtotal * 0.15
11. total        = subtotal + reserve

12. Diapazon:
    budget_min = total * 0.90
    budget_max = total * 1.15
```

### MUHIM qoidalar
- **Hech qachon bitta aniq raqam ko'rsatilmaydi.** Har doim diapazon: `$850 – $1050`.
- Barcha hisob USD'da. UZS'ga konvertatsiya faqat ko'rsatishda.
- `confidence` maydoni foydalanuvchiga ham ko'rsatiladi ("Bu taxminiy hisob").
- Test yozing: `tests/test_budget_calculator.py` — kamida 10 ta case.

---

## 5. Jamg'arish rejasi logikasi

**Joylashuv:** `apps/savings/services/saving_plan.py`

```
days_left    = (trip.start_date - today).days
per_day      = ceil(target_amount / days_left)
per_week     = per_day * 7
per_month    = per_day * 30

saved        = SUM(SavingEntry.amount)
remaining    = target_amount - saved
progress_pct = (saved / target_amount) * 100

# Real tezlik asosida prognoz
days_active  = (today - trip.created_at.date()).days or 1
actual_rate  = saved / days_active
projected_finish_days = remaining / actual_rate  (agar actual_rate > 0)

on_track = projected_finish_days <= days_left
```

**Streak hisobi:** ketma-ket kunlar soni, bugundan orqaga qarab `SavingEntry` mavjudligi
bo'yicha. Bitta kun tashlab ketilsa streak nolga tushadi.

---

## 6. API endpointlar

Barcha endpointlar prefiksi: `/api/v1/`. Frontend shu bilan bir xil originda
(`http://localhost:8000`) ishlagani uchun CORS sozlash **shart emas** — faqat
`SameSite=Lax` cookie yetarli.

### Auth
| Method | Path | Izoh |
|---|---|---|
| POST | `/auth/register/` | phone, full_name, password |
| POST | `/auth/login/` | phone, password → access + refresh (httpOnly cookie) |
| POST | `/auth/refresh/` | |
| POST | `/auth/logout/` | Cookie tozalanadi |
| GET/PATCH | `/auth/me/` | Profil |

> **Eslatma:** V1'da SMS tasdiqlash **yo'q** — oddiy parol. SMS integratsiyasi V2'da.

### Destinations
| Method | Path | Izoh |
|---|---|---|
| GET | `/destinations/` | Ro'yxat. Query: `?popular=true`, `?search=` |
| GET | `/destinations/{id}/` | Batafsil + viza ma'lumoti |
| POST | `/destinations/suggest/` | Byudjet bo'yicha tavsiya. Body: `budget_usd`, `duration_days`, `month` → mos yo'nalishlar ro'yxati |

### Trips
| Method | Path | Izoh |
|---|---|---|
| POST | `/trips/estimate/` | **Saqlamasdan** hisoblash (preview) |
| GET/POST | `/trips/` | Ro'yxat / yaratish |
| GET/PATCH/DELETE | `/trips/{id}/` | |
| GET | `/trips/{id}/plan/` | Jamg'arish rejasi + progress |

### Savings
| Method | Path | Izoh |
|---|---|---|
| GET/POST | `/trips/{id}/savings/` | Yozuvlar / qo'shish |
| DELETE | `/savings/{id}/` | |
| GET | `/trips/{id}/savings/stats/` | Streak, haftalik grafik ma'lumoti |

### Chat
| Method | Path | Izoh |
|---|---|---|
| GET | `/chat/messages/` | Tarix (paginated) |
| POST | `/chat/send/` | Xabar yuborish → AI javobi |

**Umumiy talablar:**
- Barcha javoblar `{ "data": ..., "meta": ... }` formatida
- Xatolik: `{ "error": { "code": "...", "message_uz": "...", "details": {} } }`
- Pagination: `limit`/`offset`, default limit 20
- `drf-spectacular` orqali `/api/schema/swagger-ui/` ishlashi shart

---

## 7. AI Chat implementatsiyasi

**Joylashuv:** `apps/chat/services/agent.py`

### Doira (scope)
AI faqat 4 turdagi savolga javob beradi:
1. Byudjet hisoblash — "Turkiyaga 7 kunga qancha kerak?"
2. Yo'nalish tavsiyasi — "$1200 bilan qayerga bora olaman?"
3. Viza ma'lumoti — "Yaponiyaga viza kerakmi?"
4. Jamg'arish maslahati — "Kuniga qancha yig'ishim kerak?"

Boshqa mavzuda: muloyim rad javobi va doirani eslatish.

### Arxitektura
**Bitta LLM chaqiruvi + function calling.** Multi-agent, LangGraph, MCP — **ishlatilmaydi**.

### Tool'lar (function calling)

```python
TOOLS = [
    {
        "name": "calculate_budget",
        "description": "Berilgan yo'nalish uchun sayohat byudjetini hisoblaydi",
        "input_schema": {
            "destination_city": str,   # majburiy
            "duration_days": int,
            "travelers_count": int,
            "month": int,
            "style": str               # econom/standard/comfort
        }
    },
    {
        "name": "suggest_destinations",
        "description": "Byudjetga mos yo'nalishlarni topadi",
        "input_schema": {
            "budget_usd": float,
            "duration_days": int,
            "month": int,
            "preference": str          # dengiz/shahar/tabiat/arzon — ixtiyoriy
        }
    },
    {
        "name": "get_visa_info",
        "description": "O'zbekiston fuqarosi uchun viza talabini qaytaradi",
        "input_schema": {"country_name": str}
    },
    {
        "name": "get_user_trips",
        "description": "Foydalanuvchining joriy sayohat rejalari va progressi",
        "input_schema": {}
    },
]
```

**Har bir tool bazadan real ma'lumot qaytaradi. AI raqam o'ylab topmaydi.**

### System prompt talablari
- O'zbek tilida (lotin) javob beradi
- Qisqa: 3–5 jumla, agar foydalanuvchi batafsil so'ramasa
- Raqam kerak bo'lsa — **majburan tool chaqiradi**, xotiradan aytmaydi
- Byudjetni har doim diapazon sifatida beradi
- Bilmasa — "bu ma'lumot menda yo'q" deydi, taxmin qilmaydi
- Narx bashorati **qilmaydi** ("chipta arzonlashadi" degan gap taqiqlanadi)

### Texnik
- Har so'rovda oxirgi 10 ta xabar kontekstga qo'shiladi
- `max_tokens=1024`
- Rate limit: foydalanuvchiga kuniga 30 ta xabar (Redis counter)
- Xatolik bo'lsa: "Hozir javob bera olmadim, birozdan keyin urinib ko'ring"
- Barcha so'rov/javob `ChatMessage`ga saqlanadi
- Frontendda chat sahifasi `fetch()` bilan oddiy so'rov-javob (streaming shart emas, V1)

---

## 8. Bildirishnomalar

Mobil versiyadan farqli o'laroq, veb'da push token yo'q — **email orqali** eslatma
yuboriladi (Celery + Django `send_mail`, dev'da konsolga chiqadi).

**Celery beat vazifalari:**

| Vazifa | Vaqt | Mazmun |
|---|---|---|
| `daily_saving_reminder` | Har kuni 20:00 (Toshkent) | "Bugun $6 jamg'arishni unutmang. Yaponiyagacha 145 kun." |
| `weekly_progress` | Yakshanba 10:00 | "Bu hafta $42 yig'dingiz. Maqsadning 41%i bajarildi." |
| `streak_warning` | Har kuni 21:30 | Faqat streak > 3 va bugun yozuv yo'q bo'lsa |

Foydalanuvchi profil sahifasida har birini o'chira olishi kerak
(`users.User` ga `notify_daily`, `notify_weekly`, `notify_streak` boolean maydonlari).

---

## 9. Veb-ilova — sahifalar

Barcha sahifalar bitta `index.html` shell ichida hash-router orqali almashadi
(`#/login`, `#/dashboard`, `#/trips/new`, `#/savings`, `#/chat`, `#/profile`).
Responsive: 360px (mobil brauzer) dan 1440px (desktop) gacha to'g'ri ko'rinishi shart.

### Onboarding / Landing (`#/` — auth qilinmagan foydalanuvchi uchun)
Uch bosqichli tanishtiruv bloklari bitta sahifada (scroll yoki slayder):
1. "Sayohat orzu emas, reja"
2. "Qancha kerakligini biz hisoblaymiz"
3. "Kuniga bir oz — va siz yo'ldasiz"
→ "Boshlash" / "Kirish" tugmalari

### Auth
- `#/login` — telefon + parol
- `#/register` — telefon, ism, parol

### Dashboard (`#/dashboard`)
Agar aktiv sayohat bo'lsa:
- Katta progress halqa (%) — `<canvas>` bilan chizilgan
- Yo'nalish nomi + rasm + qolgan kunlar
- "Bugun jamg'ardim" tugmasi (asosiy CTA, katta)
- Streak indikatori (🔥 12 kun)
- Yig'ilgan / Maqsad / Qolgan — uchta katta raqam

Agar sayohat yo'q bo'lsa: bo'sh holat + "Sayohat rejasi yaratish" tugmasi

### Sayohat yaratish (`#/trips/new`, bosqichma-bosqich, 5 qadam)
Bitta sahifa ichida JS bilan boshqariladigan wizard (progress bar yuqorida):
1. Yo'nalish tanlash (qidiruv input + mashhurlar grid, kartochkalar)
2. Sana va davomiylik (`<input type="date">` + kunlar soni)
3. Necha kishi (+/- stepper)
4. Uslub (econom / standard / comfort — kartochkalar, radio-style)
5. **Natija ekrani:** byudjet diapazoni + bo'linish jadvali (flight/hotel/food/...) +
   kuniga qancha kerakligi → "Maqsad qilib belgilash" tugmasi

### Jamg'arish (`#/savings`)
- Oddiy kalendar ko'rinishi (JS bilan chizilgan grid, qaysi kunlar belgilangan — yashil)
- Haftalik ustunli grafik (`<canvas>`)
- Yozuvlar ro'yxati (jadval/list)
- Tez qo'shish: preset tugmalar ($5 / $10 / $20 / boshqa — modal input)

### Chat (`#/chat`)
- Oddiy xabar ro'yxati (user o'ngda, assistant chapda — chat bubble uslubi)
- Boshlang'ich taklif tugmalari:
  "$1000 bilan qayerga bora olaman?" / "Turkiyaga qancha kerak?" / "Vizasiz davlatlar"
- Typing indicator (uch nuqta animatsiyasi, CSS bilan)

### Profil (`#/profile`)
- Shaxsiy ma'lumot (ism, telefon, uy shahri)
- Valyuta tanlash (USD / UZS)
- Bildirishnoma sozlamalari (checkbox'lar)
- Sayohatlar tarixi (ro'yxat, statusi bilan)

---

## 10. Dizayn ko'rsatmalari

- **Uslub:** toza, ko'p bo'sh joy, bitta asosiy rang
- **Asosiy rang:** to'q ko'k-yashil (`#0F766E` atrofida) yoki chuqur binafsha — ishonch hissi
- **Shrift:** Inter yoki Manrope (Google Fonts orqali emas — self-hosted `.woff2`
  fayllar `static/fonts/` ichida, chunki bitta portda, tashqi CDN'ga bog'liqlikni
  kamaytirish uchun). O'zbek lotin harflarini to'liq qo'llab-quvvatlaydi.
- **Radius:** 16px kartochkalar, 12px tugmalar
- **Layout:** desktopda markazlashgan `max-width: 480px` "mobil-uslub" konteyner
  (chunki bu asosan shaxsiy moliyaviy ilova, keng ekranda cho'zilib ketmasligi kerak) —
  yoki, agar desktop uchun ko'proq joy kerak bo'lsa, dashboard kengroq grid-layout
  bo'lishi mumkin. Claude Code ishga tushirishda ikkinchi variantni tanlasin (desktopda
  qulayroq), lekin mobil brauzerda ham to'liq ishlaydigan qilib.
- **Dark mode:** V1'da **kerak emas**
- **Animatsiya:** minimal. Faqat progress halqa va sahifa o'tishlari (CSS transition)
- Raqamlar katta va o'qilishi oson bo'lsin — bu moliyaviy ilova

---

## 11. Ishlab chiqish bosqichlari

Claude Code'ga **shu tartibda** vazifa bering:

**1-bosqich — poydevor**
- Docker-compose (postgres, redis, web/backend — bitta xizmat)
- Django loyiha skeleti, settings bo'linishi (base/dev/prod)
- Frontend statik fayllarni serve qilish sozlamasi (templates + staticfiles + catch-all view)
- User modeli + JWT auth (httpOnly cookie)
- Admin panel sozlash

**2-bosqich — ma'lumot qatlami**
- Country, Destination, PriceReference modellari
- Admin + import-export
- 25 ta yo'nalish uchun seed fixture (`seed_destinations.py` management command)

**3-bosqich — byudjet**
- `budget_calculator.py` + testlar (avval test yozing)
- `/trips/estimate/` va Trip CRUD endpointlari

**4-bosqich — jamg'arish**
- SavingEntry, saving_plan servisi, endpointlar, streak logikasi

**5-bosqich — AI chat**
- Tool'lar, agent servisi, rate limiting, endpointlar

**6-bosqich — Frontend skeleti**
- `index.html` shell, router.js, api.js (fetch wrapper + token refresh), base.css
  (theme o'zgaruvchilari), auth sahifalari

**7-bosqich — Frontend asosiy sahifalar**
- Dashboard, sayohat yaratish wizard'i, natija ekrani

**8-bosqich — Frontend jamg'arish + chat**
- Kalendar, bar chart komponenti, chat UI

**9-bosqich — sayqal**
- Celery vazifalari (email eslatmalar), bo'sh holatlar, xatolik holatlari, loading
  skeletonlar, responsive tuzatishlar

---

## 12. Sifat talablari

- **Testlar:** backend business logic uchun majburiy (pytest). Coverage ≥ 70%
  `budget_calculator` va `saving_plan` uchun — 100%
- **Linting:** `ruff` (backend), `eslint` (frontend JS, config bilan, build tool'siz
  ham ishlaydigan sozlamada). CI'da tekshiriladi
- **Migratsiyalar:** har bir model o'zgarishi alohida migratsiya
- **Sirlar:** `.env` orqali, hech qachon repoga tushmaydi. `.env.example` bo'lsin
- **Kommitlar:** Conventional Commits (`feat:`, `fix:`, `refactor:`)
- **README:** loyihani **bitta** buyruq bilan ishga tushirish yo'riqnomasi
  (`docker-compose up`), so'ng `http://localhost:8000` ochish yetarli bo'lsin

---

## 13. V1'ga KIRMAYDIGAN narsalar

Claude Code bularni **qo'shmasin**, hatto foydali ko'rinsa ham:

- ❌ Real vaqt flight/hotel API integratsiyasi
- ❌ Narx bashorati (Price Prediction)
- ❌ Narx monitoringi
- ❌ Tur agentlik paneli / marketplace
- ❌ Bron qilish va to'lov
- ❌ Multi-agent AI arxitekturasi
- ❌ Ijtimoiy funksiyalar, do'stlar, guruh sayohatlari
- ❌ Dark mode
- ❌ Native mobil ilova (Flutter/React Native/Swift/Kotlin)
- ❌ Frontend build tool/bundler (Webpack, Vite, npm paketlari, React/Vue)
- ❌ Alohida portda ishlaydigan frontend server — hammasi bitta Django portida

Agar bu funksiyalardan biri kerak deb hisoblasangiz — avval TODO qoldiring,
implementatsiya qilmang.
