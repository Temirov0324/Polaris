"""Function-calling tools for the chat agent. Every tool hits the real
database — the model is never allowed to invent a number from memory."""
from datetime import date
from decimal import Decimal

from django.db.models import Q
from google.genai import types

# Plain JSON-schema tool definitions — kept separate from the google-genai
# `types.Tool` wrapper below so they stay easy to read/test without an SDK
# dependency.
TOOL_SCHEMAS = [
    {
        "name": "calculate_budget",
        "description": "Berilgan yo'nalish uchun sayohat byudjetini hisoblaydi",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_city": {"type": "string", "description": "Shahar nomi, masalan 'Istanbul'"},
                "duration_days": {"type": "integer", "description": "Sayohat davomiyligi (kun)"},
                "travelers_count": {"type": "integer", "description": "Sayohatchilar soni", "default": 1},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Sayohat oyi (1-12)"},
                "style": {
                    "type": "string",
                    "enum": ["econom", "standard", "comfort"],
                    "description": "Sayohat uslubi",
                    "default": "standard",
                },
            },
            "required": ["destination_city", "duration_days", "month"],
        },
    },
    {
        "name": "suggest_destinations",
        "description": "Byudjetga mos yo'nalishlarni topadi",
        "parameters": {
            "type": "object",
            "properties": {
                "budget_usd": {"type": "number"},
                "duration_days": {"type": "integer"},
                "month": {"type": "integer", "minimum": 1, "maximum": 12},
                "preference": {
                    "type": "string",
                    "description": "Ixtiyoriy: dengiz / shahar / tabiat / arzon",
                },
            },
            "required": ["budget_usd", "duration_days", "month"],
        },
    },
    {
        "name": "get_visa_info",
        "description": "O'zbekiston fuqarosi uchun viza talabini qaytaradi",
        "parameters": {
            "type": "object",
            "properties": {"country_name": {"type": "string"}},
            "required": ["country_name"],
        },
    },
    {
        "name": "get_user_trips",
        "description": "Foydalanuvchining joriy sayohat rejalari va progressi",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "create_trip",
        "description": (
            "Foydalanuvchi uchun yangi sayohat rejasini yaratadi va bazaga saqlaydi — "
            "byudjetni avtomatik hisoblab, jamg'arish maqsadini belgilaydi. Faqat "
            "foydalanuvchi ketish sanasi va davomiyligini aniq aytgandan keyin chaqiring."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination_city": {"type": "string", "description": "Shahar nomi, masalan 'Istanbul'"},
                "start_date": {"type": "string", "description": "Ketish sanasi, YYYY-MM-DD formatida"},
                "duration_days": {"type": "integer", "description": "Sayohat davomiyligi (kun)"},
                "travelers_count": {"type": "integer", "description": "Sayohatchilar soni", "default": 1},
                "style": {
                    "type": "string",
                    "enum": ["econom", "standard", "comfort"],
                    "description": "Sayohat uslubi",
                    "default": "standard",
                },
                "target_amount": {
                    "type": "number",
                    "description": (
                        "Ixtiyoriy: jamg'arish maqsad summasi (USD). Berilmasa, "
                        "hisoblangan byudjet diapazonining o'rtachasi ishlatiladi."
                    ),
                },
            },
            "required": ["destination_city", "start_date", "duration_days"],
        },
    },
    {
        "name": "add_saving_entry",
        "description": (
            "Foydalanuvchining faol sayohat rejasiga jamg'arish yozuvini qo'shadi. "
            "Kuniga bitta yozuv — bir xil sanaga qayta chaqirilsa, summa yangilanadi."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Jamg'arilgan summa (USD)"},
                "trip_id": {
                    "type": "integer",
                    "description": "Ixtiyoriy: aniq sayohat ID. Berilmasa, eng so'nggi faol sayohat ishlatiladi.",
                },
                "date": {
                    "type": "string",
                    "description": "Ixtiyoriy: sana YYYY-MM-DD formatida. Berilmasa, bugungi sana ishlatiladi.",
                },
                "note": {"type": "string", "description": "Ixtiyoriy izoh"},
            },
            "required": ["amount"],
        },
    },
]

GEMINI_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=schema["name"],
            description=schema["description"],
            parameters_json_schema=schema["parameters"],
        )
        for schema in TOOL_SCHEMAS
    ]
)


def _month_start_date(month: int) -> date:
    """Anchors the given month to the nearest upcoming occurrence."""
    today = date.today()
    year = today.year if month >= today.month else today.year + 1
    return date(year, month, 1)


def _tool_calculate_budget(user, destination_city, duration_days, month, travelers_count=1, style="standard"):
    from apps.destinations.models import Destination, PriceReference
    from apps.trips.services.budget_calculator import estimate_trip_budget

    destination = (
        Destination.objects.select_related("country")
        .filter(Q(city_uz__icontains=destination_city) | Q(city_en__icontains=destination_city))
        .first()
    )
    if destination is None:
        return {"found": False, "message_uz": f"'{destination_city}' uchun ma'lumot bazamizda yo'q"}

    try:
        result = estimate_trip_budget(
            destination=destination,
            start_date=_month_start_date(month),
            duration_days=duration_days,
            travelers_count=travelers_count,
            style=style,
        )
    except PriceReference.DoesNotExist:
        return {"found": False, "message_uz": f"'{destination.city_uz}' uchun narx ma'lumoti hali kiritilmagan"}

    return {
        "found": True,
        "destination": destination.city_uz,
        "country": destination.country.name_uz,
        "budget_min_usd": float(result.budget_min),
        "budget_max_usd": float(result.budget_max),
        "confidence": result.confidence,
    }


def _tool_suggest_destinations(user, budget_usd, duration_days, month, preference=None):
    from apps.destinations.models import Destination, PriceReference
    from apps.trips.services.budget_calculator import estimate_trip_budget

    queryset = Destination.objects.select_related("country")
    if preference:
        filtered = queryset.filter(Q(description_uz__icontains=preference) | Q(city_uz__icontains=preference))
        if filtered.exists():
            queryset = filtered

    start_date = _month_start_date(month)
    budget_decimal = Decimal(str(budget_usd))

    matches = []
    for destination in queryset:
        try:
            result = estimate_trip_budget(
                destination=destination,
                start_date=start_date,
                duration_days=duration_days,
                travelers_count=1,
                style="standard",
            )
        except PriceReference.DoesNotExist:
            continue
        if result.budget_max <= budget_decimal:
            matches.append((result.budget_max, destination, result))

    matches.sort(key=lambda item: item[0])
    top = matches[:5]

    return {
        "count": len(top),
        "destinations": [
            {
                "city": destination.city_uz,
                "country": destination.country.name_uz,
                "budget_min_usd": float(result.budget_min),
                "budget_max_usd": float(result.budget_max),
            }
            for _, destination, result in top
        ],
    }


def _tool_get_visa_info(user, country_name):
    from apps.destinations.models import Country

    country = Country.objects.filter(
        Q(name_uz__icontains=country_name) | Q(name_en__icontains=country_name)
    ).first()
    if country is None:
        return {"found": False, "message_uz": f"'{country_name}' uchun ma'lumot bazamizda yo'q"}

    return {
        "found": True,
        "country": country.name_uz,
        "visa_type": country.visa_type,
        "visa_cost_usd": float(country.visa_cost_usd),
        "note_uz": country.visa_note_uz,
    }


def _tool_get_user_trips(user):
    from apps.savings.services.saving_plan import get_saving_plan
    from apps.trips.models import Trip

    trips = (
        Trip.objects.filter(user=user)
        .exclude(status=Trip.Status.CANCELLED)
        .select_related("destination__country")
    )

    data = []
    for trip in trips:
        entry = {
            "destination": trip.destination.city_uz,
            "start_date": trip.start_date.isoformat(),
            "status": trip.status,
            "budget_min_usd": float(trip.budget_min),
            "budget_max_usd": float(trip.budget_max),
        }
        if trip.target_amount:
            plan = get_saving_plan(trip)
            entry.update(
                target_amount_usd=float(trip.target_amount),
                saved_usd=float(plan.saved),
                progress_pct=float(plan.progress_pct),
                on_track=plan.on_track,
            )
        data.append(entry)

    return {"trips": data}


def _resolve_active_trip(user, trip_id=None):
    from apps.trips.models import Trip

    qs = Trip.objects.filter(user=user).select_related("destination")
    if trip_id is not None:
        return qs.filter(id=trip_id).first()
    return (
        qs.filter(status__in=[Trip.Status.PLANNING, Trip.Status.SAVING])
        .order_by("-created_at")
        .first()
    )


def _tool_create_trip(
    user,
    destination_city,
    start_date,
    duration_days,
    travelers_count=1,
    style="standard",
    target_amount=None,
):
    from django.db import transaction

    from apps.destinations.models import Destination, PriceReference
    from apps.trips.models import BudgetBreakdown, Trip
    from apps.trips.services.budget_calculator import estimate_trip_budget

    destination = (
        Destination.objects.select_related("country")
        .filter(Q(city_uz__icontains=destination_city) | Q(city_en__icontains=destination_city))
        .first()
    )
    if destination is None:
        return {"created": False, "message_uz": f"'{destination_city}' uchun ma'lumot bazamizda yo'q"}

    try:
        parsed_date = date.fromisoformat(start_date)
    except (TypeError, ValueError):
        return {"created": False, "message_uz": "Sana formati noto'g'ri — YYYY-MM-DD ko'rinishida bo'lishi kerak"}

    if parsed_date <= date.today():
        return {"created": False, "message_uz": "Ketish sanasi kelajakda bo'lishi kerak"}

    try:
        result = estimate_trip_budget(
            destination=destination,
            start_date=parsed_date,
            duration_days=duration_days,
            travelers_count=travelers_count,
            style=style,
        )
    except PriceReference.DoesNotExist:
        return {"created": False, "message_uz": f"'{destination.city_uz}' uchun narx ma'lumoti hali kiritilmagan"}

    if target_amount:
        final_target = Decimal(str(target_amount))
    else:
        final_target = result.budget_min + (result.budget_max - result.budget_min) / 2

    with transaction.atomic():
        trip = Trip.objects.create(
            user=user,
            destination=destination,
            start_date=parsed_date,
            duration_days=duration_days,
            travelers_count=travelers_count,
            style=style,
            target_amount=final_target,
            budget_min=result.budget_min,
            budget_max=result.budget_max,
        )
        BudgetBreakdown.objects.create(
            trip=trip,
            flight=result.flight,
            accommodation=result.accommodation,
            food=result.food,
            transport=result.transport,
            activities=result.activities,
            visa=result.visa,
            insurance=result.insurance,
            reserve=result.reserve,
        )

    return {
        "created": True,
        "trip_id": trip.id,
        "destination": destination.city_uz,
        "start_date": parsed_date.isoformat(),
        "duration_days": duration_days,
        "travelers_count": travelers_count,
        "style": style,
        "budget_min_usd": float(result.budget_min),
        "budget_max_usd": float(result.budget_max),
        "target_amount_usd": float(final_target),
    }


def _tool_add_saving_entry(user, amount, trip_id=None, date=None, note=""):
    import datetime as _datetime

    from apps.savings.models import SavingEntry

    trip = _resolve_active_trip(user, trip_id)
    if trip is None:
        return {"saved": False, "message_uz": "Faol sayohat rejasi topilmadi — avval sayohat yarating"}

    if date:
        try:
            parsed_date = _datetime.date.fromisoformat(date)
        except ValueError:
            return {"saved": False, "message_uz": "Sana formati noto'g'ri — YYYY-MM-DD ko'rinishida bo'lishi kerak"}
    else:
        parsed_date = _datetime.date.today()

    entry, _created = SavingEntry.objects.update_or_create(
        trip=trip,
        date=parsed_date,
        defaults={"amount": Decimal(str(amount)), "note": note or ""},
    )

    return {
        "saved": True,
        "trip_id": trip.id,
        "destination": trip.destination.city_uz,
        "date": parsed_date.isoformat(),
        "amount_usd": float(entry.amount),
    }


TOOL_HANDLERS = {
    "calculate_budget": _tool_calculate_budget,
    "suggest_destinations": _tool_suggest_destinations,
    "get_visa_info": _tool_get_visa_info,
    "get_user_trips": _tool_get_user_trips,
    "create_trip": _tool_create_trip,
    "add_saving_entry": _tool_add_saving_entry,
}


def execute_tool(name: str, tool_input: dict, user) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Noma'lum tool: {name}"}
    try:
        return handler(user=user, **tool_input)
    except Exception as exc:  # tool errors become a message the model can react to, not a crash
        return {"error": str(exc)}
