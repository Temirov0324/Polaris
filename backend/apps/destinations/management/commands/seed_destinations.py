"""Seeds 25 popular outbound destinations (from Tashkent) with a full
12-month PriceReference each. Prices are rough estimates meant as a
starting point — admins should refine them via the CSV import in
/admin/destinations/pricereference/ over time.

image_url is seeded with a placeholder (picsum.photos, deterministic per
destination) — swap in real licensed photos via /admin/destinations/destination/
whenever you have them."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.destinations.models import Country, Destination, PriceReference

# fmt: off
DESTINATIONS = [
    {"country": "TR", "name_uz": "Turkiya", "name_en": "Turkey", "visa_type": "evisa", "visa_cost": 20,
     "visa_note": "Elektron viza onlayn 15 daqiqada olinadi.",
     "city_uz": "Istanbul", "city_en": "Istanbul", "popular": True,
     "desc": "Ikki qit'ani tutashtiruvchi tarixiy shahar, arzon parvozlar.",
     "flight": 220, "hotel": (18, 40, 85), "food": (10, 22, 45), "transport": 6, "activity": 10,
     "confidence": "high", "peak": [6, 7, 8, 12]},
    {"country": "GE", "name_uz": "Gruziya", "name_en": "Georgia", "visa_type": "free", "visa_cost": 0,
     "visa_note": "1 yilgacha vizasiz kirish mumkin.",
     "city_uz": "Tbilisi", "city_en": "Tbilisi", "popular": True,
     "desc": "Yaqin va arzon, tog' va sharob mintaqalari bilan mashhur.",
     "flight": 160, "hotel": (12, 28, 60), "food": (8, 18, 35), "transport": 4, "activity": 8,
     "confidence": "high", "peak": [5, 6, 7, 8, 9]},
    {"country": "AE", "name_uz": "BAA", "name_en": "United Arab Emirates", "visa_type": "evisa", "visa_cost": 90,
     "visa_note": "Elektron viza, odatda 3-5 kunda tayyor bo'ladi.",
     "city_uz": "Dubay", "city_en": "Dubai", "popular": True,
     "desc": "Zamonaviy me'morchilik, savdo markazlari va sun'iy orollar.",
     "flight": 280, "hotel": (30, 70, 150), "food": (15, 35, 70), "transport": 8, "activity": 20,
     "confidence": "high", "peak": [11, 12, 1, 2]},
    {"country": "EG", "name_uz": "Misr", "name_en": "Egypt", "visa_type": "evisa", "visa_cost": 25,
     "visa_note": "Elektron viza onlayn rasmiylashtiriladi.",
     "city_uz": "Qohira", "city_en": "Cairo", "popular": False,
     "desc": "Piramidalar va qadimiy sivilizatsiya izlari.",
     "flight": 340, "hotel": (15, 35, 75), "food": (10, 20, 40), "transport": 6, "activity": 15,
     "confidence": "medium", "peak": [10, 11, 12, 1, 2]},
    {"country": "MY", "name_uz": "Malayziya", "name_en": "Malaysia", "visa_type": "evisa", "visa_cost": 20,
     "visa_note": "Elektron viza (eNTRI/eVisa) talab qilinadi.",
     "city_uz": "Kuala-Lumpur", "city_en": "Kuala Lumpur", "popular": False,
     "desc": "Osiyoning zamonaviy shaharlaridan biri, arzon shopping.",
     "flight": 420, "hotel": (14, 32, 70), "food": (8, 18, 38), "transport": 5, "activity": 12,
     "confidence": "medium", "peak": [6, 7, 8]},
    {"country": "TH", "name_uz": "Tailand", "name_en": "Thailand", "visa_type": "on_arrival", "visa_cost": 35,
     "visa_note": "Chegarada 15-30 kunlik viza beriladi.",
     "city_uz": "Bangkok", "city_en": "Bangkok", "popular": True,
     "desc": "Ibodatxonalar, ko'cha taomlari va tirbandlik hayoti.",
     "flight": 400, "hotel": (12, 28, 65), "food": (8, 16, 35), "transport": 5, "activity": 12,
     "confidence": "high", "peak": [11, 12, 1, 2]},
    {"country": "KR", "name_uz": "Janubiy Koreya", "name_en": "South Korea", "visa_type": "embassy", "visa_cost": 40,
     "visa_note": "Elchixonaga hujjatlar bilan murojaat qilish kerak.",
     "city_uz": "Seul", "city_en": "Seoul", "popular": True,
     "desc": "K-pop, texnologiya va zamonaviy madaniyat markazi.",
     "flight": 480, "hotel": (25, 55, 110), "food": (12, 28, 55), "transport": 7, "activity": 15,
     "confidence": "medium", "peak": [4, 5, 9, 10]},
    {"country": "JP", "name_uz": "Yaponiya", "name_en": "Japan", "visa_type": "embassy", "visa_cost": 30,
     "visa_note": "Turistik viza elchixona orqali rasmiylashtiriladi.",
     "city_uz": "Tokio", "city_en": "Tokyo", "popular": True,
     "desc": "An'ana va texnologiya uyg'unlashgan megapolis.",
     "flight": 550, "hotel": (35, 75, 160), "food": (15, 32, 65), "transport": 9, "activity": 18,
     "confidence": "medium", "peak": [3, 4, 10, 11]},
    {"country": "CN", "name_uz": "Xitoy", "name_en": "China", "visa_type": "evisa", "visa_cost": 140,
     "visa_note": "Elektron/oddiy viza talab qilinadi.",
     "city_uz": "Pekin", "city_en": "Beijing", "popular": False,
     "desc": "Xitoy devori va boy tarixiy meros.",
     "flight": 380, "hotel": (20, 45, 95), "food": (10, 22, 45), "transport": 6, "activity": 14,
     "confidence": "low", "peak": [9, 10]},
    {"country": "RU", "name_uz": "Rossiya", "name_en": "Russia", "visa_type": "free", "visa_cost": 0,
     "visa_note": "Vizasiz kirish mumkin.",
     "city_uz": "Moskva", "city_en": "Moscow", "popular": True,
     "desc": "Qizil maydon va boy madaniy hayot.",
     "flight": 180, "hotel": (18, 40, 90), "food": (10, 22, 45), "transport": 6, "activity": 12,
     "confidence": "high", "peak": [6, 7, 12, 1]},
    {"country": "KZ", "name_uz": "Qozog'iston", "name_en": "Kazakhstan", "visa_type": "free", "visa_cost": 0,
     "visa_note": "Vizasiz kirish mumkin.",
     "city_uz": "Olmaota", "city_en": "Almaty", "popular": True,
     "desc": "Tog' manzaralari va qulay masofa.",
     "flight": 110, "hotel": (12, 28, 60), "food": (8, 16, 32), "transport": 4, "activity": 8,
     "confidence": "high", "peak": [6, 7, 8, 12, 1]},
    {"country": "AZ", "name_uz": "Ozarbayjon", "name_en": "Azerbaijan", "visa_type": "evisa", "visa_cost": 25,
     "visa_note": "ASAN Visa orqali onlayn olinadi.",
     "city_uz": "Boku", "city_en": "Baku", "popular": False,
     "desc": "Neft boyligi va zamonaviy me'morchilik uyg'unligi.",
     "flight": 200, "hotel": (16, 36, 75), "food": (9, 20, 40), "transport": 5, "activity": 10,
     "confidence": "medium", "peak": [5, 6, 9]},
    {"country": "IN", "name_uz": "Hindiston", "name_en": "India", "visa_type": "evisa", "visa_cost": 25,
     "visa_note": "Elektron turistik viza mavjud.",
     "city_uz": "Dehli", "city_en": "Delhi", "popular": False,
     "desc": "Rang-barang bozorlar va qadimiy ma'badlar.",
     "flight": 300, "hotel": (10, 24, 55), "food": (6, 14, 30), "transport": 4, "activity": 10,
     "confidence": "medium", "peak": [11, 12, 1, 2]},
    {"country": "VN", "name_uz": "Vetnam", "name_en": "Vietnam", "visa_type": "evisa", "visa_cost": 25,
     "visa_note": "Elektron viza 3 kun ichida tayyor bo'ladi.",
     "city_uz": "Xanoy", "city_en": "Hanoi", "popular": False,
     "desc": "Arzon narxlar va ajoyib tabiat.",
     "flight": 420, "hotel": (12, 26, 55), "food": (7, 15, 32), "transport": 5, "activity": 10,
     "confidence": "medium", "peak": [10, 11, 3, 4]},
    {"country": "ID", "name_uz": "Indoneziya", "name_en": "Indonesia", "visa_type": "free", "visa_cost": 0,
     "visa_note": "30 kungacha vizasiz kirish mumkin.",
     "city_uz": "Denpasar (Bali)", "city_en": "Denpasar (Bali)", "popular": True,
     "desc": "Plyajlar, sörf va tropik tabiat.",
     "flight": 500, "hotel": (16, 38, 85), "food": (8, 18, 38), "transport": 6, "activity": 14,
     "confidence": "medium", "peak": [6, 7, 8, 12]},
    {"country": "MV", "name_uz": "Maldiv orollari", "name_en": "Maldives", "visa_type": "free", "visa_cost": 0,
     "visa_note": "Kirishda 30 kunlik bepul viza beriladi.",
     "city_uz": "Male", "city_en": "Male", "popular": True,
     "desc": "Dunyodagi eng mashhur orol kurortlari.",
     "flight": 550, "hotel": (60, 150, 350), "food": (20, 45, 90), "transport": 10, "activity": 25,
     "confidence": "low", "peak": [12, 1, 2, 3]},
    {"country": "SA", "name_uz": "Saudiya Arabistoni", "name_en": "Saudi Arabia", "visa_type": "evisa",
     "visa_cost": 130, "visa_note": "Umra/turistik elektron viza mavjud.",
     "city_uz": "Jidda", "city_en": "Jeddah", "popular": False,
     "desc": "Umra ziyorati va Qizil dengiz sohili.",
     "flight": 320, "hotel": (25, 55, 120), "food": (12, 26, 50), "transport": 6, "activity": 10,
     "confidence": "medium", "peak": [3, 4, 9, 10]},
    {"country": "QA", "name_uz": "Qatar", "name_en": "Qatar", "visa_type": "evisa", "visa_cost": 0,
     "visa_note": "Bepul elektron viza beriladi.",
     "city_uz": "Doha", "city_en": "Doha", "popular": False,
     "desc": "Zamonaviy shahar va cho'l safari.",
     "flight": 300, "hotel": (28, 65, 140), "food": (14, 30, 60), "transport": 7, "activity": 16,
     "confidence": "medium", "peak": [11, 12, 1, 2]},
    {"country": "SG", "name_uz": "Singapur", "name_en": "Singapore", "visa_type": "embassy", "visa_cost": 30,
     "visa_note": "Turistik viza elchixona orqali olinadi.",
     "city_uz": "Singapur", "city_en": "Singapore", "popular": False,
     "desc": "Toza va yuqori texnologiyali shahar-davlat.",
     "flight": 450, "hotel": (30, 65, 140), "food": (12, 26, 55), "transport": 6, "activity": 15,
     "confidence": "medium", "peak": [6, 7, 12]},
    {"country": "IT", "name_uz": "Italiya", "name_en": "Italy", "visa_type": "embassy", "visa_cost": 80,
     "visa_note": "Shengen vizasi talab qilinadi.",
     "city_uz": "Rim", "city_en": "Rome", "popular": True,
     "desc": "Antik tarix va jahon oshxonasi poytaxti.",
     "flight": 400, "hotel": (25, 60, 130), "food": (14, 30, 60), "transport": 7, "activity": 15,
     "confidence": "medium", "peak": [6, 7, 8]},
    {"country": "FR", "name_uz": "Fransiya", "name_en": "France", "visa_type": "embassy", "visa_cost": 80,
     "visa_note": "Shengen vizasi talab qilinadi.",
     "city_uz": "Parij", "city_en": "Paris", "popular": True,
     "desc": "San'at, moda va Eyfel minorasi.",
     "flight": 420, "hotel": (28, 65, 140), "food": (15, 32, 65), "transport": 8, "activity": 16,
     "confidence": "medium", "peak": [6, 7, 8]},
    {"country": "ES", "name_uz": "Ispaniya", "name_en": "Spain", "visa_type": "embassy", "visa_cost": 80,
     "visa_note": "Shengen vizasi talab qilinadi.",
     "city_uz": "Barselona", "city_en": "Barcelona", "popular": False,
     "desc": "Gaudi me'morchiligi va O'rta dengiz sohili.",
     "flight": 410, "hotel": (24, 55, 120), "food": (13, 28, 55), "transport": 7, "activity": 14,
     "confidence": "medium", "peak": [6, 7, 8]},
    {"country": "DE", "name_uz": "Germaniya", "name_en": "Germany", "visa_type": "embassy", "visa_cost": 80,
     "visa_note": "Shengen vizasi talab qilinadi.",
     "city_uz": "Berlin", "city_en": "Berlin", "popular": False,
     "desc": "Tarix, muzeylar va jonli shahar hayoti.",
     "flight": 380, "hotel": (22, 50, 110), "food": (12, 26, 52), "transport": 7, "activity": 13,
     "confidence": "medium", "peak": [5, 6, 7]},
    {"country": "GB", "name_uz": "Buyuk Britaniya", "name_en": "United Kingdom", "visa_type": "embassy",
     "visa_cost": 120, "visa_note": "Alohida turistik viza talab qilinadi.",
     "city_uz": "London", "city_en": "London", "popular": True,
     "desc": "Qirollik saroylari va jahon darajasidagi muzeylar.",
     "flight": 450, "hotel": (30, 70, 150), "food": (15, 32, 65), "transport": 9, "activity": 18,
     "confidence": "medium", "peak": [6, 7, 8]},
    {"country": "GR", "name_uz": "Gretsiya", "name_en": "Greece", "visa_type": "embassy", "visa_cost": 80,
     "visa_note": "Shengen vizasi talab qilinadi.",
     "city_uz": "Afina", "city_en": "Athens", "popular": False,
     "desc": "Qadimgi Yunoniston tarixi va orollari.",
     "flight": 390, "hotel": (20, 48, 100), "food": (12, 26, 52), "transport": 6, "activity": 13,
     "confidence": "medium", "peak": [6, 7, 8, 9]},
]
# fmt: on


class Command(BaseCommand):
    help = "Seeds 25 popular destinations with 12 months of PriceReference each."

    def handle(self, *args, **options):
        with transaction.atomic():
            created_destinations = 0
            created_prices = 0

            for entry in DESTINATIONS:
                country, _ = Country.objects.update_or_create(
                    code=entry["country"],
                    defaults={
                        "name_uz": entry["name_uz"],
                        "name_en": entry["name_en"],
                        "visa_type": entry["visa_type"],
                        "visa_cost_usd": Decimal(entry["visa_cost"]),
                        "visa_note_uz": entry["visa_note"],
                        "is_active": True,
                    },
                )

                image_seed = f"{entry['country'].lower()}-{entry['city_en'].lower().replace(' ', '-')}"
                destination, was_created = Destination.objects.update_or_create(
                    country=country,
                    city_uz=entry["city_uz"],
                    defaults={
                        "city_en": entry["city_en"],
                        "description_uz": entry["desc"],
                        "is_popular": entry["popular"],
                        "image_url": f"https://picsum.photos/seed/{image_seed}/640/480",
                    },
                )
                created_destinations += int(was_created)

                hotel_e, hotel_s, hotel_c = entry["hotel"]
                food_e, food_s, food_c = entry["food"]

                for month in range(1, 13):
                    multiplier = Decimal("1.15") if month in entry["peak"] else Decimal("1.0")
                    _, price_created = PriceReference.objects.update_or_create(
                        destination=destination,
                        month=month,
                        defaults={
                            "flight_return_usd": Decimal(entry["flight"]) * multiplier,
                            "hotel_night_econom": Decimal(hotel_e) * multiplier,
                            "hotel_night_standard": Decimal(hotel_s) * multiplier,
                            "hotel_night_comfort": Decimal(hotel_c) * multiplier,
                            "food_day_econom": Decimal(food_e),
                            "food_day_standard": Decimal(food_s),
                            "food_day_comfort": Decimal(food_c),
                            "transport_day_usd": Decimal(entry["transport"]),
                            "activity_day_usd": Decimal(entry["activity"]),
                            "confidence": entry["confidence"],
                        },
                    )
                    created_prices += int(price_created)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(DESTINATIONS)} ta yo'nalish qayta ishlandi "
                    f"({created_destinations} ta yangi), "
                    f"{created_prices} ta yangi narx yozuvi qo'shildi."
                )
            )
