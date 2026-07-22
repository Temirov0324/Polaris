"""Single-call-plus-function-calling chat agent (section 7 of
TEXNIK_TOPSHIRIQ.md), backed by Gemini (Google AI Studio, model configurable
via GEMINI_MODEL) via the google-genai SDK. Deliberately NOT multi-agent /
LangGraph / MCP — one generate_content() call per turn, looping only to feed
function results back until the model produces a final text answer.
"""
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from google import genai
from google.genai import errors, types

from apps.chat.models import ChatMessage

from .tools import GEMINI_TOOL, execute_tool

logger = logging.getLogger(__name__)

DAILY_MESSAGE_LIMIT = 30
MAX_TOOL_ITERATIONS = 4
HISTORY_SIZE = 10
FALLBACK_REPLY = "Hozir javob bera olmadim, birozdan keyin urinib ko'ring"

SYSTEM_PROMPT = """Siz PolarisAI — o'zbekistonlik sayohatchilar uchun byudjet va \
jamg'arish yordamchisisiz. Faqat o'zbek tilida (lotin alifbosida) javob bering. \
Siz shunchaki maslahatchi emas, balki agentsiz — foydalanuvchi o'rniga haqiqiy \
amallarni (sayohat yaratish, jamg'arish qo'shish) bajara olasiz.

Siz FAQAT quyidagi turdagi so'rovlar bilan shug'ullanasiz:
1. Byudjet hisoblash (masalan: "Turkiyaga 7 kunga qancha kerak?")
2. Yo'nalish tavsiyasi (masalan: "$1200 bilan qayerga bora olaman?")
3. Viza ma'lumoti (masalan: "Yaponiyaga viza kerakmi?")
4. Jamg'arish maslahati (masalan: "Kuniga qancha yig'ishim kerak?")
5. Yangi sayohat rejasi yaratish (masalan: "Menga 15-avgustda Gruziyaga 5 kunlik \
sayohat yarat")
6. Jamg'arishga yozuv qo'shish (masalan: "Bugun $15 jamg'ardim")

Boshqa mavzudagi savollarga muloyimlik bilan rad javobi bering va o'z doirangizni \
eslating — masalan siyosat, dasturlash yoki umumiy suhbat mavzularida yordam bera \
olmasligingizni ayting.

Amal bajarish qoidalari (5 va 6-bandlar):
- create_trip yoki add_saving_entry'ni FAQAT foydalanuvchi barcha zarur ma'lumotni \
(yo'nalish, sana, davomiylik / summasi) aniq aytgandan keyin chaqiring. Yetishmayotgan \
ma'lumot bo'lsa — tool chaqirmasdan, avval so'rang.
- Sana, summa yoki davomiylikni hech qachon o'zingiz o'ylab topmang — faqat \
foydalanuvchi aniq aytgan qiymatlarni ishlating.
- Amal bajarilgandan so'ng, tool natijasidagi haqiqiy qiymatlar (ID, byudjet, sana) \
bilan aniq tasdiqlang — "Sayohat yaratildi!" kabi umumiy gap emas.
- Agar tool xatolik qaytarsa (masalan yo'nalish topilmadi) — buni foydalanuvchiga \
tushuntiring, boshqa harakat o'ylab topmang.

Qat'iy qoidalar:
- Javobingiz qisqa bo'lsin: 3-5 jumla, agar foydalanuvchi batafsil so'ramasa.
- Raqam (narx, byudjet, muddat) kerak bo'lsa — ALBATTA tegishli tool'ni chaqiring, \
xotiradan yoki taxmin qilib hech qachon raqam aytmang.
- Byudjetni har doim diapazon sifatida bering (masalan "$850 – $1050"), hech qachon \
bitta aniq raqam sifatida emas.
- Agar tool ma'lumot topa olmasa — "bu ma'lumot menda yo'q" deb ayting, taxmin qilmang.
- Narx bashorati QILMANG ("chipta arzonlashadi", "narx tez orada oshadi" kabi gaplar taqiqlanadi).
"""

# ChatMessage stores "user"/"assistant" (matches the API section 3.8 spec);
# Gemini's Content.role uses "user"/"model" — translate only at this boundary.
_ROLE_TO_GEMINI = {
    ChatMessage.Role.USER: "user",
    ChatMessage.Role.ASSISTANT: "model",
}


def consume_rate_limit(user) -> bool:
    """Returns True and records the message if the user is still under the
    daily limit; returns False (without recording) once they hit it."""
    key = f"chat_rate:{user.id}:{timezone.localdate().isoformat()}"
    count = cache.get_or_set(key, 0, timeout=60 * 60 * 26)
    if count >= DAILY_MESSAGE_LIMIT:
        return False
    cache.incr(key)
    return True


def _get_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _build_contents(history) -> list:
    return [
        types.Content(role=_ROLE_TO_GEMINI[message.role], parts=[types.Part.from_text(text=message.content)])
        for message in history
    ]


def _extract_text(response) -> str:
    text = (response.text or "").strip()
    return text or "Kechirasiz, javob shakllantira olmadim."


def _generate_with_retry(client, **kwargs):
    """Gemini occasionally returns a transient 503 ("high demand") even
    though the SDK's own retry already gave up — one extra retry clears
    most of these without surfacing the generic fallback to the user."""
    try:
        return client.models.generate_content(**kwargs)
    except errors.ServerError:
        time.sleep(1.5)
        return client.models.generate_content(**kwargs)


def _run_agent_loop(contents: list, user) -> str:
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[GEMINI_TOOL],
        max_output_tokens=1024,
    )
    working_contents = list(contents)

    for _ in range(MAX_TOOL_ITERATIONS):
        response = _generate_with_retry(
            client,
            model=settings.GEMINI_MODEL,
            contents=working_contents,
            config=config,
        )

        if not response.function_calls:
            return _extract_text(response)

        working_contents.append(response.candidates[0].content)

        response_parts = []
        for part in response.candidates[0].content.parts:
            if part.function_call:
                result = execute_tool(part.function_call.name, dict(part.function_call.args or {}), user)
                response_parts.append(
                    types.Part.from_function_response(name=part.function_call.name, response=result)
                )
        working_contents.append(types.Content(role="user", parts=response_parts))

    return "Kechirasiz, hozir javob shakllantira olmadim, birozdan keyin qayta urinib ko'ring."


def send_message(user, content: str, trip=None) -> str:
    """Persists the user's message, asks Gemini (with tools) for a reply,
    persists that too, and returns the reply text. Rate limiting is the
    caller's responsibility (see consume_rate_limit)."""
    ChatMessage.objects.create(user=user, trip=trip, role=ChatMessage.Role.USER, content=content)

    history = list(
        ChatMessage.objects.filter(user=user).order_by("-created_at", "-id")[:HISTORY_SIZE]
    )
    history.reverse()
    contents = _build_contents(history)

    try:
        reply_text = _run_agent_loop(contents, user)
    except Exception:
        logger.exception("Gemini chat request failed for user %s", user.id)
        reply_text = FALLBACK_REPLY

    ChatMessage.objects.create(user=user, trip=trip, role=ChatMessage.Role.ASSISTANT, content=reply_text)
    return reply_text
