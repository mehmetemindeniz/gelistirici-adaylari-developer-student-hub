# Proje: Geliştirici Adayları (Premium Minimalist Platform)

## 1. Tasarım Felsefesi
- **Stil:** Minimalist, modern, "Clean Tech" görünümü.
- **Renk Paleti:** Koyu tema (Arka plan: #0f172a, Kartlar: #1e293b).
- **Kullanıcı Deneyimi:** Akıcı geçişler, büyük tıklama alanları, mobil öncelikli yapı.
- **UI Framework:** Tailwind CSS (CDN).

## 2. Basitleştirilmiş Dizin Yapısı
/ (Kök Dizin)
├── app.py              # Tüm Backend ve Rotalar (Tek dosya, temiz yorum satırlı)
├── models.py           # Veritabanı Şeması (SQLite)
├── static/
│   ├── css/            # Özel dokunuşlar için minimal CSS
│   ├── js/             # Sohbet ve UI etkileşimleri için Vanilla JS
│   └── uploads/        # Profil fotoları, paylaşılan resimler ve dökümanlar
└── templates/          # HTML Şablonları (Anlaşılır isimlendirme)

## 3. Temel Özellikler & Akış
- **Onaylı Üyelik:** Kayıt -> Admin Onayı (Pending State) -> Erişim.
- **Sohbet (Chat):** Sayfa yenilenmeden mesajlaşma (Vanilla JS + Fetch API). WhatsApp tarzı sağ/sol balonlar.
- **Döküman Arşivi:** Kategorize edilmiş indirme listesi.
- **Akış (Feed):** Resimli ve linkli haber paylaşımları.
- **Profil:** Fotoğraf yükleme ve kullanıcı bilgilerini düzenleme.

## 4. Teknik Detaylar
- Şifreler hashlenerek saklanacak (Security).
- Admin Paneli: `/admin` rotasında, kullanıcı onaylama/silme odaklı.
- Tüm formlar "Client-side Validation" (JS) içermeli.