"""Admin-only content agent — lets the founder paste raw destination/price
data in natural language and have it validated and written straight into
the Country/Destination/PriceReference catalog. Mirrors apps.chat.services'
single-call-plus-function-calling shape, but scoped to catalog data only
(see .tools) and gated to superusers (see apps.admin_agent.views). Uses its
own API key (GEMINI_ADMIN_API_KEY) so usage is billed/rate-limited
separately from the user-facing chat agent.
"""
import logging
import time

from django.conf import settings
from google import genai
from google.genai import errors, types

from .tools import GEMINI_TOOL, execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6
HISTORY_SIZE = 20
FALLBACK_REPLY = "Hozir javob bera olmadim, birozdan keyin urinib ko'ring"

SYSTEM_PROMPT = """Siz PolarisAI administratori uchun kontent kiritish yordamchisisiz. \
Direktor sizga sayohat yo'nalishlari, davlatlar yoki narxlar haqida xom ma'lumot \
(matn, jadval, ro'yxat) beradi — sizning vazifangiz uni diqqat bilan tekshirib, to'g'ri \
formatga solib, mavjud tool'lar orqali bazaga qo'shish.

Qat'iy chegara: sizda FAQAT davlat/yo'nalish/narx (Country/Destination/PriceReference) \
ma'lumotlari bilan ishlaydigan tool'lar bor. Foydalanuvchilarning shaxsiy ma'lumotlari, \
sayohat rejalari yoki jamg'armalariga sizning HECH QANDAY kirishingiz yo'q — bunday so'rov \
kelsa (masalan "foydalanuvchi X ni o'chir" yoki "Y ning jamg'armasini ko'rsat"), buni \
bajara olmasligingizni ayting va nima uchunligini tushuntiring.

Ishlash tartibi:
1. Har doim avval list_countries / list_destinations / get_price_status bilan mavjud \
ma'lumotni tekshiring — dublikat yaratmang, mavjud bo'lsa yangilang.
2. Raqamlarni diqqat bilan tekshiring: comfort narxi standard'dan, standard esa \
econom'dan qimmat bo'lishi kerak — agar direktor bergan raqamlar bunga zid bo'lsa, tool \
chaqirishdan oldin so'rab tasdiqlang.
3. Agar biror maydon (masalan davlat kodi yoki oy) berilmagan yoki noaniq bo'lsa — \
taxmin qilmang, aniqlashtirib so'rang.
4. Har bir amaldan so'ng, aniq nima qo'shilgani/yangilangani haqida qisqa va aniq xabar \
bering (shahar, oy, qiymatlar) — umumiy "qo'shildi" emas.
5. Tool xatolik qaytarsa, xatoni direktorga tushuntiring va to'g'ri ma'lumot so'rang.

Javoblaringiz o'zbek tilida, qisqa va ishbilarmon uslubda bo'lsin.
"""

_ROLE_TO_GEMINI = {"user": "user", "assistant": "model"}


def _get_client():
    return genai.Client(api_key=settings.GEMINI_ADMIN_API_KEY)


def _build_contents(history: list) -> list:
    return [
        types.Content(role=_ROLE_TO_GEMINI[m["role"]], parts=[types.Part.from_text(text=m["content"])])
        for m in history
    ]


def _extract_text(response) -> str:
    text = (response.text or "").strip()
    return text or "Kechirasiz, javob shakllantira olmadim."


def _generate_with_retry(client, **kwargs):
    try:
        return client.models.generate_content(**kwargs)
    except errors.ServerError:
        time.sleep(1.5)
        return client.models.generate_content(**kwargs)


def _run_agent_loop(contents: list, actor) -> tuple:
    from apps.admin_agent.models import AdminAgentLog

    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[GEMINI_TOOL],
        max_output_tokens=1536,
    )
    working_contents = list(contents)
    actions = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = _generate_with_retry(
            client, model=settings.GEMINI_MODEL, contents=working_contents, config=config
        )

        if not response.function_calls:
            return _extract_text(response), actions

        working_contents.append(response.candidates[0].content)

        response_parts = []
        for part in response.candidates[0].content.parts:
            if part.function_call:
                tool_name = part.function_call.name
                tool_args = dict(part.function_call.args or {})
                result = execute_tool(tool_name, tool_args)
                success = bool(result.get("ok", True))
                AdminAgentLog.objects.create(
                    performed_by=actor,
                    tool_name=tool_name,
                    arguments=tool_args,
                    result=result,
                    success=success,
                )
                actions.append({"tool": tool_name, "arguments": tool_args, "result": result})
                response_parts.append(types.Part.from_function_response(name=tool_name, response=result))
        working_contents.append(types.Content(role="user", parts=response_parts))

    return "Juda ko'p amal bajarildi, iltimos so'rovni qismlarga bo'lib yuboring.", actions


def handle_message(actor, message: str, history: list) -> dict:
    """actor: the superuser triggering this request — used only for audit
    logging (AdminAgentLog.performed_by), never exposed to the model."""
    if not settings.GEMINI_ADMIN_API_KEY:
        return {
            "reply": "Admin AI yordamchisi hali sozlanmagan — GEMINI_ADMIN_API_KEY o'rnatilmagan.",
            "history": history,
            "actions": [],
        }

    contents = _build_contents(history + [{"role": "user", "content": message}])
    try:
        reply_text, actions = _run_agent_loop(contents, actor)
    except Exception:
        logger.exception("Admin agent request failed for user %s", actor.id)
        reply_text, actions = FALLBACK_REPLY, []

    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply_text},
    ]
    return {"reply": reply_text, "history": new_history[-HISTORY_SIZE:], "actions": actions}
