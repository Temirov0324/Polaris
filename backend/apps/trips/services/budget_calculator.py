"""Pure trip-budget calculation.

`calculate_budget` takes plain Decimal/int inputs and returns a
`BudgetResult` — no Django ORM calls, no I/O, fully deterministic. This is
what tests/test_budget_calculator.py exercises directly.

`estimate_trip_budget` is the thin, DB-touching wrapper the API views call:
it resolves the right PriceReference (falling back to the closest month
when the exact one is missing) and feeds plain numbers into the pure
function above.
"""
import math
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal

RESERVE_RATE = Decimal("0.15")
BUDGET_MIN_FACTOR = Decimal("0.90")
BUDGET_MAX_FACTOR = Decimal("1.15")
INSURANCE_PER_DAY_USD = Decimal("1.5")

TWO_PLACES = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class BudgetResult:
    flight: Decimal
    accommodation: Decimal
    food: Decimal
    transport: Decimal
    activities: Decimal
    visa: Decimal
    insurance: Decimal
    reserve: Decimal
    subtotal: Decimal
    total: Decimal
    budget_min: Decimal
    budget_max: Decimal
    confidence: str

    def as_dict(self):
        return asdict(self)


def calculate_budget(
    *,
    flight_return_usd: Decimal,
    hotel_night: Decimal,
    food_day: Decimal,
    transport_day_usd: Decimal,
    activity_day_usd: Decimal,
    visa_cost_usd: Decimal,
    duration_days: int,
    travelers_count: int = 1,
    confidence: str = "medium",
) -> BudgetResult:
    """Implements the algorithm from TEXNIK_TOPSHIRIQ.md section 4.

    Never returns a single number to show the user — always a range
    (budget_min, budget_max). All amounts are USD.
    """
    if duration_days < 1:
        raise ValueError("duration_days kamida 1 bo'lishi kerak")
    if travelers_count < 1:
        raise ValueError("travelers_count kamida 1 bo'lishi kerak")

    nights = duration_days - 1
    rooms = math.ceil(travelers_count / 2)  # 2 kishi bitta xonada

    flight = Decimal(flight_return_usd) * travelers_count
    accommodation = Decimal(hotel_night) * nights * rooms
    food = Decimal(food_day) * duration_days * travelers_count
    transport = Decimal(transport_day_usd) * duration_days * travelers_count
    activities = Decimal(activity_day_usd) * duration_days * travelers_count
    visa = Decimal(visa_cost_usd) * travelers_count
    insurance = INSURANCE_PER_DAY_USD * duration_days * travelers_count

    subtotal = flight + accommodation + food + transport + activities + visa + insurance
    reserve = subtotal * RESERVE_RATE
    total = subtotal + reserve

    return BudgetResult(
        flight=_q(flight),
        accommodation=_q(accommodation),
        food=_q(food),
        transport=_q(transport),
        activities=_q(activities),
        visa=_q(visa),
        insurance=_q(insurance),
        reserve=_q(reserve),
        subtotal=_q(subtotal),
        total=_q(total),
        budget_min=_q(total * BUDGET_MIN_FACTOR),
        budget_max=_q(total * BUDGET_MAX_FACTOR),
        confidence=confidence,
    )


def _month_distance(a: int, b: int) -> int:
    diff = abs(a - b)
    return min(diff, 12 - diff)


def get_price_reference(destination, month: int):
    """Returns (price_reference, is_exact_month_match)."""
    from apps.destinations.models import PriceReference

    exact = PriceReference.objects.filter(destination=destination, month=month).first()
    if exact is not None:
        return exact, True

    candidates = list(PriceReference.objects.filter(destination=destination))
    if not candidates:
        raise PriceReference.DoesNotExist(
            f"'{destination}' uchun narx ma'lumoti topilmadi"
        )

    nearest = min(candidates, key=lambda ref: _month_distance(ref.month, month))
    return nearest, False


def estimate_trip_budget(*, destination, start_date, duration_days, travelers_count, style) -> BudgetResult:
    price_ref, is_exact = get_price_reference(destination, start_date.month)
    confidence = price_ref.confidence if is_exact else "low"

    return calculate_budget(
        flight_return_usd=price_ref.flight_return_usd,
        hotel_night=price_ref.hotel_night(style),
        food_day=price_ref.food_day(style),
        transport_day_usd=price_ref.transport_day_usd,
        activity_day_usd=price_ref.activity_day_usd,
        visa_cost_usd=destination.country.visa_cost_usd,
        duration_days=duration_days,
        travelers_count=travelers_count,
        confidence=confidence,
    )
