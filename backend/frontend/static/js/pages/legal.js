window.pages = window.pages || {};

const LEGAL_UPDATED = "2026-07-22";

window.pages.privacy = function renderPrivacy() {
  document.getElementById("app").innerHTML = `
    <div class="page legal-page">
      <h1>Maxfiylik siyosati</h1>
      <p class="legal-page__updated">Oxirgi yangilanish: ${LEGAL_UPDATED}</p>

      <h2>1. Qanday ma'lumot yig'amiz</h2>
      <p>Ro'yxatdan o'tganingizda: to'liq ismingiz, telefon raqamingiz va emailingiz. Profilda ixtiyoriy
      ravishda: uy shahringiz, valyuta tanlovingiz. Xizmatdan foydalanganda: sayohat rejalaringiz, byudjet
      hisob-kitoblari, jamg'arish yozuvlaringiz va AI chat bilan yozishmalaringiz.</p>

      <h2>2. Ma'lumotdan qanday foydalanamiz</h2>
      <p>Ma'lumotlaringiz faqat xizmatni ko'rsatish uchun ishlatiladi: hisobingizga kirish, byudjet
      hisoblash, jamg'arish rejasini kuzatish va (agar yoqilgan bo'lsa) email orqali eslatmalar yuborish.
      Ma'lumotlaringizni uchinchi shaxslarga sotmaymiz.</p>

      <h2>3. AI Chat va uchinchi tomon xizmatlari</h2>
      <p>AI chat funksiyasi Google Gemini (Google AI Studio) orqali ishlaydi. Chatga yozgan xabarlaringiz
      javob generatsiya qilish uchun Google'ga yuboriladi. Google'ning o'z maxfiylik siyosati alohida
      qo'llaniladi.</p>

      <h2>4. Ma'lumotlarni saqlash</h2>
      <p>Ma'lumotlaringiz hisobingiz faol bo'lgan davomida saqlanadi. Hisobingizni o'chirishni so'rasangiz,
      shaxsiy ma'lumotlaringiz o'chiriladi (qonun talab qilgan hollar bundan mustasno).</p>

      <h2>5. Xavfsizlik</h2>
      <p>Parolingiz shifrlangan holda saqlanadi. Kirish uchun xavfsiz (httpOnly) cookie'lardan
      foydalanamiz. Shunga qaramay, internet orqali uzatishning 100% xavfsiz usuli yo'qligini unutmang.</p>

      <h2>6. Sizning huquqlaringiz</h2>
      <p>Istalgan vaqtda profilingizdagi ma'lumotlarni ko'rish va tahrirlash, bildirishnomalarni
      o'chirish, yoki hisobingizni butunlay o'chirishni so'rash huquqiga egasiz.</p>

      <h2>7. Bog'lanish</h2>
      <p>Savollaringiz bo'lsa, ilova administratori bilan bog'laning.</p>
    </div>
  `;
};

window.pages.terms = function renderTerms() {
  document.getElementById("app").innerHTML = `
    <div class="page legal-page">
      <h1>Foydalanish shartlari</h1>
      <p class="legal-page__updated">Oxirgi yangilanish: ${LEGAL_UPDATED}</p>

      <h2>1. Xizmat haqida</h2>
      <p>PolarisAI — sayohat byudjetini hisoblash, jamg'arish rejasini tuzish va AI yordamchi orqali
      sayohat bilan bog'liq savollarga javob olish uchun mo'ljallangan xizmat.</p>

      <h2>2. Hisob yaratish</h2>
      <p>Ro'yxatdan o'tish uchun haqiqiy telefon raqami va emailingizni ko'rsatishingiz, hamda emailingizga
      yuborilgan tasdiqlash kodini kiritishingiz kerak. Hisobingiz xavfsizligi uchun javobgarlik
      sizning zimmangizda.</p>

      <h2>3. Byudjet hisob-kitoblari haqida</h2>
      <p>Ilovada ko'rsatilgan byudjet, narx va tavsiyalar — taxminiy ma'lumotlar asosida hisoblangan
      yo'l-yo'riq sifatida beriladi, real vaqt narxlari yoki kafolatlangan taklif emas. Yakuniy qaror va
      xarajatlar uchun mas'uliyat foydalanuvchida qoladi.</p>

      <h2>4. AI Chat</h2>
      <p>AI yordamchi javoblari avtomatik generatsiya qilinadi va har doim ham 100% aniq bo'lmasligi
      mumkin. Muhim qarorlar (viza, chipta xaridi va h.k.) uchun rasmiy manbalarni tekshiring.</p>

      <h2>5. Taqiqlangan foydalanish</h2>
      <p>Xizmatni qonunga zid maqsadlarda, boshqa foydalanuvchilarning hisobiga ruxsatsiz kirish uchun
      yoki xizmatning normal ishlashiga xalaqit beradigan tarzda ishlatish taqiqlanadi.</p>

      <h2>6. Xizmatni to'xtatish</h2>
      <p>Ushbu shartlarni buzgan hisoblarni ogohlantirishsiz to'xtatib qo'yishimiz mumkin. Siz ham
      istalgan vaqtda hisobingizdan foydalanishni to'xtatishingiz mumkin.</p>

      <h2>7. Javobgarlikni cheklash</h2>
      <p>Xizmat "bor holicha" taqdim etiladi. Byudjet hisob-kitoblari, AI tavsiyalari yoki xizmatdagi
      uzilishlar natijasida yuzaga kelgan har qanday zarar uchun javobgarlik cheklangan.</p>

      <h2>8. Shartlarning o'zgarishi</h2>
      <p>Ushbu shartlar vaqti-vaqti bilan yangilanishi mumkin. Muhim o'zgarishlar haqida ilova ichida
      xabar beramiz.</p>
    </div>
  `;
};
