"""Function-calling tools for the admin content agent — deliberately scoped
to catalog/reference data only (Country, Destination, PriceReference).
There is no tool here that can read or write User, Trip, SavingEntry,
ChatMessage, or any other model holding end-user personal data: the model
has no way to touch it even if a prompt tried to talk it into that."""
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from google.genai import types

from apps.destinations.models import Country, Destination, PriceReference

# Generous global sanity bounds (USD) — not destination-specific, just
# enough to catch obviously wrong numbers (unit confusion, a monthly rent
# figure typed into a nightly hotel field, a search-grounded hallucination,
# etc.) before they reach the database.
PRICE_BOUNDS = {
    "flight_return_usd": (20, 5000),
    "hotel_night_econom": (3, 2000),
    "hotel_night_standard": (3, 2000),
    "hotel_night_comfort": (3, 2000),
    "food_day_econom": (2, 500),
    "food_day_standard": (2, 500),
    "food_day_comfort": (2, 500),
    "transport_day_usd": (1, 200),
    "activity_day_usd": (1, 500),
}

TOOL_SCHEMAS = [
    {
        "name": "list_countries",
        "description": (
            "Bazadagi barcha davlatlar ro'yxatini qaytaradi (kod va nom bilan) — "
            "dublikat yaratmaslik uchun avval shuni chaqiring."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "upsert_country",
        "description": (
            "Davlat qo'shadi yoki (shu kod bilan davlat mavjud bo'lsa) yangilaydi. "
            "code — 2 harfli davlat kodi (masalan 'TR', 'AE')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "2 harfli davlat kodi, masalan 'TR'"},
                "name_uz": {"type": "string"},
                "name_en": {"type": "string"},
                "visa_type": {
                    "type": "string",
                    "enum": ["free", "on_arrival", "evisa", "embassy"],
                    "description": "free=vizasiz, on_arrival=chegarada beriladi, evisa=elektron, embassy=elchixona",
                },
                "visa_cost_usd": {"type": "number", "description": "Viza narxi USD da, vizasiz bo'lsa 0"},
                "visa_note_uz": {"type": "string", "description": "Ixtiyoriy izoh"},
                "is_active": {"type": "boolean", "default": True},
            },
            "required": ["code", "name_uz", "name_en", "visa_type", "visa_cost_usd"],
        },
    },
    {
        "name": "list_destinations",
        "description": (
            "Bazadagi yo'nalishlar ro'yxati (ixtiyoriy: davlat kodi bo'yicha filtr) — "
            "dublikat yaratmaslik uchun avval shuni chaqiring."
        ),
        "parameters": {
            "type": "object",
            "properties": {"country_code": {"type": "string", "description": "Ixtiyoriy: 2 harfli davlat kodi"}},
        },
    },
    {
        "name": "upsert_destination",
        "description": (
            "Yo'nalish (shahar) qo'shadi yoki mavjud bo'lsa yangilaydi. Davlat avval "
            "upsert_country bilan qo'shilgan bo'lishi kerak."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "country_code": {"type": "string"},
                "city_uz": {"type": "string"},
                "city_en": {"type": "string"},
                "image_url": {"type": "string", "description": "Ixtiyoriy"},
                "description_uz": {"type": "string", "description": "Ixtiyoriy"},
                "is_popular": {"type": "boolean", "default": False},
            },
            "required": ["country_code", "city_uz", "city_en"],
        },
    },
    {
        "name": "get_price_status",
        "description": "Berilgan shahar uchun qaysi oylarda narx ma'lumoti to'ldirilganini ko'rsatadi.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "upsert_price_reference",
        "description": (
            "Berilgan shahar va oy uchun narx ma'lumotini qo'shadi yoki yangilaydi. "
            "Barcha narxlar USD da va musbat (0 dan katta) bo'lishi shart."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "month": {"type": "integer", "minimum": 1, "maximum": 12},
                "flight_return_usd": {"type": "number"},
                "hotel_night_econom": {"type": "number"},
                "hotel_night_standard": {"type": "number"},
                "hotel_night_comfort": {"type": "number"},
                "food_day_econom": {"type": "number"},
                "food_day_standard": {"type": "number"},
                "food_day_comfort": {"type": "number"},
                "transport_day_usd": {"type": "number"},
                "activity_day_usd": {"type": "number"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"], "default": "medium"},
            },
            "required": [
                "city",
                "month",
                "flight_return_usd",
                "hotel_night_econom",
                "hotel_night_standard",
                "hotel_night_comfort",
                "food_day_econom",
                "food_day_standard",
                "food_day_comfort",
                "transport_day_usd",
                "activity_day_usd",
            ],
        },
    },
    {
        "name": "research_destinations_online",
        "description": (
            "Berilgan davlat uchun internetdan (Google qidiruv orqali) eng yaxshi shaharlar va "
            "ularning taxminiy narxlari haqida ma'lumot topadi. Bu FAQAT qidiruv — bazaga hech "
            "narsa yozmaydi. Natijani diqqat bilan o'qib, keyin o'zingiz upsert_* tool'lari bilan "
            "bazaga qo'shing, va HAR DOIM confidence='low' bilan (chunki bu internetdan topilgan "
            "taxminiy ma'lumot, direktor bergan ma'lumot emas)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "country_name": {"type": "string", "description": "Davlat nomi, masalan 'Tailand'"},
                "city_count": {
                    "type": "integer",
                    "description": "Nechta shahar haqida ma'lumot topish kerak (maksimum 10)",
                    "default": 5,
                },
            },
            "required": ["country_name"],
        },
    },
]

GEMINI_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=schema["name"], description=schema["description"], parameters_json_schema=schema["parameters"]
        )
        for schema in TOOL_SCHEMAS
    ]
)


def _tool_list_countries():
    return {
        "countries": [
            {"code": c.code, "name_uz": c.name_uz, "name_en": c.name_en, "visa_type": c.visa_type}
            for c in Country.objects.order_by("name_uz")
        ]
    }


def _tool_upsert_country(code, name_uz, name_en, visa_type, visa_cost_usd, visa_note_uz="", is_active=True):
    code = (code or "").strip().upper()
    if len(code) != 2 or not code.isalpha():
        return {"ok": False, "error": f"Noto'g'ri davlat kodi: '{code}' — 2 harfdan iborat bo'lishi kerak"}
    if visa_type not in Country.VisaType.values:
        return {"ok": False, "error": f"Noto'g'ri visa_type: '{visa_type}'"}
    if not (name_uz or "").strip() or not (name_en or "").strip():
        return {"ok": False, "error": "name_uz va name_en bo'sh bo'lishi mumkin emas"}
    try:
        visa_cost = Decimal(str(visa_cost_usd))
    except InvalidOperation:
        return {"ok": False, "error": f"visa_cost_usd noto'g'ri son: {visa_cost_usd}"}
    if visa_cost < 0:
        return {"ok": False, "error": "visa_cost_usd manfiy bo'lishi mumkin emas"}

    country, created = Country.objects.update_or_create(
        code=code,
        defaults={
            "name_uz": name_uz.strip(),
            "name_en": name_en.strip(),
            "visa_type": visa_type,
            "visa_cost_usd": visa_cost,
            "visa_note_uz": (visa_note_uz or "").strip(),
            "is_active": bool(is_active),
        },
    )
    return {"ok": True, "created": created, "code": country.code, "name_uz": country.name_uz}


def _tool_list_destinations(country_code=None):
    qs = Destination.objects.select_related("country")
    if country_code:
        qs = qs.filter(country__code=country_code.strip().upper())
    return {
        "destinations": [
            {"id": d.id, "city_uz": d.city_uz, "city_en": d.city_en, "country_code": d.country.code}
            for d in qs.order_by("city_uz")
        ]
    }


def _tool_upsert_destination(country_code, city_uz, city_en, image_url="", description_uz="", is_popular=False):
    code = (country_code or "").strip().upper()
    country = Country.objects.filter(code=code).first()
    if country is None:
        return {"ok": False, "error": f"'{code}' kodli davlat topilmadi — avval upsert_country bilan qo'shing"}
    if not (city_uz or "").strip() or not (city_en or "").strip():
        return {"ok": False, "error": "city_uz va city_en bo'sh bo'lishi mumkin emas"}

    defaults = {
        "city_en": city_en.strip(),
        "image_url": (image_url or "").strip(),
        "description_uz": (description_uz or "").strip(),
        "is_popular": bool(is_popular),
    }
    existing = Destination.objects.filter(country=country, city_uz__iexact=city_uz.strip()).first()
    if existing:
        for field, value in defaults.items():
            setattr(existing, field, value)
        existing.save()
        return {"ok": True, "created": False, "id": existing.id, "city_uz": existing.city_uz}

    destination = Destination.objects.create(country=country, city_uz=city_uz.strip(), **defaults)
    return {"ok": True, "created": True, "id": destination.id, "city_uz": destination.city_uz}


def _resolve_destination(city):
    city = (city or "").strip()
    return (
        Destination.objects.select_related("country")
        .filter(Q(city_uz__iexact=city) | Q(city_en__iexact=city))
        .first()
    )


def _tool_get_price_status(city):
    destination = _resolve_destination(city)
    if destination is None:
        return {"ok": False, "error": f"'{city}' nomli yo'nalish topilmadi"}
    months = set(destination.price_references.values_list("month", flat=True))
    return {
        "ok": True,
        "city": destination.city_uz,
        "months_filled": sorted(months),
        "months_missing": sorted(set(range(1, 13)) - months),
    }


def _tool_upsert_price_reference(
    city,
    month,
    flight_return_usd,
    hotel_night_econom,
    hotel_night_standard,
    hotel_night_comfort,
    food_day_econom,
    food_day_standard,
    food_day_comfort,
    transport_day_usd,
    activity_day_usd,
    confidence="medium",
):
    destination = _resolve_destination(city)
    if destination is None:
        return {"ok": False, "error": f"'{city}' nomli yo'nalish topilmadi — avval upsert_destination bilan qo'shing"}

    try:
        month = int(month)
    except (TypeError, ValueError):
        return {"ok": False, "error": f"month butun son bo'lishi kerak: {month}"}
    if not 1 <= month <= 12:
        return {"ok": False, "error": "month 1 dan 12 gacha bo'lishi kerak"}

    if confidence not in PriceReference.Confidence.values:
        return {"ok": False, "error": f"Noto'g'ri confidence: '{confidence}'"}

    raw_values = {
        "flight_return_usd": flight_return_usd,
        "hotel_night_econom": hotel_night_econom,
        "hotel_night_standard": hotel_night_standard,
        "hotel_night_comfort": hotel_night_comfort,
        "food_day_econom": food_day_econom,
        "food_day_standard": food_day_standard,
        "food_day_comfort": food_day_comfort,
        "transport_day_usd": transport_day_usd,
        "activity_day_usd": activity_day_usd,
    }
    values = {}
    for field, raw in raw_values.items():
        try:
            amount = Decimal(str(raw))
        except InvalidOperation:
            return {"ok": False, "error": f"{field} noto'g'ri son: {raw}"}
        if amount <= 0:
            return {"ok": False, "error": f"{field} musbat bo'lishi kerak (berilgan: {raw})"}
        low, high = PRICE_BOUNDS[field]
        if not (low <= amount <= high):
            return {
                "ok": False,
                "error": f"{field} ishonarli oraliqdan tashqarida: {raw} (kutilgan: ${low}–${high})",
            }
        values[field] = amount

    price_ref, created = PriceReference.objects.update_or_create(
        destination=destination,
        month=month,
        defaults={**values, "confidence": confidence},
    )
    return {"ok": True, "created": created, "city": destination.city_uz, "month": month, "confidence": confidence}


def _tool_research_destinations_online(country_name, city_count=5):
    # Local import: research.py imports google.genai at module scope, and
    # this keeps that dependency out of the hot path for founder-provided-
    # data requests that never touch it.
    from .research import run_web_research

    return run_web_research(country_name, city_count)


TOOL_HANDLERS = {
    "list_countries": lambda **kw: _tool_list_countries(**kw),
    "upsert_country": lambda **kw: _tool_upsert_country(**kw),
    "list_destinations": lambda **kw: _tool_list_destinations(**kw),
    "upsert_destination": lambda **kw: _tool_upsert_destination(**kw),
    "get_price_status": lambda **kw: _tool_get_price_status(**kw),
    "upsert_price_reference": lambda **kw: _tool_upsert_price_reference(**kw),
    "research_destinations_online": lambda **kw: _tool_research_destinations_online(**kw),
}


def execute_tool(name: str, tool_input: dict) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"ok": False, "error": f"Noma'lum tool: {name}"}
    try:
        return handler(**tool_input)
    except TypeError as exc:
        return {"ok": False, "error": f"Noto'g'ri parametrlar: {exc}"}
    except Exception as exc:  # tool errors become a message the model can react to, not a crash
        return {"ok": False, "error": str(exc)}
