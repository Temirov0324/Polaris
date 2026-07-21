# TravelAI

Sayohat byudjetini hisoblab beruvchi va jamg'arish rejasini boshqaruvchi veb-ilova + AI chat.
To'liq texnik topshiriq: [TEXNIK_TOPSHIRIQ.md](TEXNIK_TOPSHIRIQ.md).

Backend (Django) va frontend (HTML/CSS/JS) **bitta portda** ishlaydi — alohida
frontend server yo'q.

## Ishga tushirish

```bash
cp .env.example .env
docker-compose up
```

So'ng brauzerda oching: **http://localhost:8000**

Admin panel: http://localhost:8000/admin/
API hujjati (Swagger): http://localhost:8000/api/schema/swagger-ui/

Birinchi marta admin foydalanuvchi yaratish va 25 ta yo'nalishni yuklash uchun:

```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_destinations
```

AI chat Google Gemini (Google AI Studio) orqali ishlaydi — `.env` faylida
`GEMINI_API_KEY` ni to'ldiring (kalitni https://aistudio.google.com/apikey
dan bepul olish mumkin). Kalit bo'lmasa chat foydalanuvchiga muloyim xatolik
xabarini qaytaradi, ilova qulamaydi.

## Production'ga deploy qilish

VPS'ga joylashtirish bo'yicha to'liq qo'llanma: [DEPLOY.md](DEPLOY.md).

## Testlar

```bash
docker-compose exec web pytest --cov=apps --cov-report=term-missing
```

`budget_calculator` va `saving_plan` — 100% coverage; umumiy backend ≥70%.

## Lint

```bash
docker-compose exec web ruff check .
```
