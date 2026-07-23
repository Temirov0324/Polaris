"""Isolated Gemini call using Google Search grounding.

Kept separate from the main tool-calling loop in .agent because the Gemini
API does not support mixing search grounding with custom function-
declaration tools in a single request. The outer agent calls into this via
the research_destinations_online tool (see .tools), gets back grounded
findings and their source URLs, and decides what — if anything — to write
using its own validated upsert_* tools. This module never touches the
database itself.
"""
from django.conf import settings
from google import genai
from google.genai import errors, types

MAX_CITIES = 10

RESEARCH_SYSTEM_PROMPT = """Siz sayohat tadqiqotchisisiz. Google qidiruvi orqali FAQAT \
haqiqiy, joriy ma'lumot toping — hech qachon xotiradan yoki taxmin qilib raqam aytmang. \
Har bir narx qaysi manbadan olinganini yodda tuting. Agar ishonchli ma'lumot topa \
olmasangiz, shunday deb ayting — o'ylab topmang yoki bo'sh joyni taxminiy raqam bilan \
to'ldirmang.
"""


def _get_client():
    return genai.Client(api_key=settings.GEMINI_ADMIN_API_KEY)


def run_web_research(country_name: str, city_count: int = 5) -> dict:
    try:
        city_count = max(1, min(int(city_count), MAX_CITIES))
    except (TypeError, ValueError):
        city_count = 5

    prompt = (
        f"{country_name} davlatidagi sayohatchilar uchun eng yaxshi {city_count} ta shaharni top. "
        "Har bir shahar uchun quyidagilarni USD da toping (joriy, haqiqiy narxlarni qidiring):\n"
        "- O'zbekistondan borish-kelish chipta narxi (taxminiy)\n"
        "- Mehmonxona bir kechasi: byudjet / o'rtacha / qulay toifalarda\n"
        "- Ovqat bir kunlik: byudjet / o'rtacha / qulay toifalarda\n"
        "- Mahalliy transport bir kunlik\n"
        "- Faoliyat/ko'rgazma bir kunlik\n"
        "- Viza turi va narxi (O'zbekiston fuqarosi uchun)\n\n"
        "Har bir raqam qaysi manbadan olinganini qisqacha ko'rsating."
    )

    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=RESEARCH_SYSTEM_PROMPT,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        max_output_tokens=4096,
    )
    try:
        response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)
    except errors.ServerError as exc:
        return {"ok": False, "error": f"Qidiruv xizmati xatosi: {exc}"}
    except Exception as exc:  # surfaced to the calling tool, never a crash
        return {"ok": False, "error": str(exc)}

    text = (response.text or "").strip()
    if not text:
        return {"ok": False, "error": "Qidiruv natija bermadi"}

    sources = []
    try:
        chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
        for chunk in chunks:
            if chunk.web and chunk.web.uri:
                sources.append({"title": chunk.web.title or chunk.web.uri, "uri": chunk.web.uri})
    except (AttributeError, IndexError, TypeError):
        pass

    return {"ok": True, "findings": text, "sources": sources}
