# Screens — Kürsü

Thirteen screens are designed. Their static exports are in `docs/design/reference/` (HTML with inline styles) and `docs/design/reference/png/` (screenshots). This file maps each one to a route, lists the exact Turkish copy, and says how the screen behaves.

- Text in `{braces}` is data. Everything else is fixed copy for `apps/app/src/i18n/tr.ts`.
- Copy marked **NEW** is a draft that is not in the design; keep it, but list it for product review.
- The reference screens show sample data. Their numbers are illustrations, not test fixtures.
- Number suffixes such as `1'i` and `%71'ini` are computed (see Formatting in `DESIGN_SYSTEM.md`).

## Route map

| Route | Screen | Reference | Priority |
|---|---|---|---|
| `/` | redirect: Onboarding when there is no profile, otherwise Today | — | P0 |
| `/onboarding` | Onboarding | `onboarding.html` | P0 |
| `/placement` | Placement test | `placement-test.html` | P0 |
| `/placement/result` | Placement result | `placement-result.html` | P0 |
| `/auth` | Sign up and sign in | not designed | P0 |
| `/paywall` | Season pass (modal) | `paywall.html` | P0 |
| `/(tabs)/today` | Today | `today.html`, `web-today.html` | P0 |
| `/(tabs)/lessons` | Lessons index | not designed | P0 |
| `/lessons/[lessonId]` | Micro-lesson | `micro-lesson.html` | P0 |
| `/practice/[sessionId]` | Question, then feedback | `placement-test.html` while answering, `question-review.html` after | P0 |
| `/notebook` | Mistake notebook | `mistake-notebook.html` | P0 |
| `/(tabs)/mock` | Mock index | not designed | P0 |
| `/mock/[attemptId]` | Mock exam | `mock-exam.html` | P0 |
| `/mock/[attemptId]/result` | Mock result | `nationwide-result.html` | P0, parts P2 |
| `/(tabs)/progress` | Progress | `progress.html` | P0, parts P2 |
| `/settings` | Settings | not designed | P0 |
| `/photo` | Photo solve | `photo-solve.html` | P1 |

Phone tabs: "Bugün", "Dersler", "Deneme", "Gelişim". Web side navigation (≥ 1024 px): "Bugün", "Dersler", "Yanlış defteri", "Deneme", "Gelişim". Accessibility label of both: "Ana menü".

## Onboarding — `onboarding.html`

Copy: "Kürsü" (app name from config) · "AGS · 8 Mayıs 2027" (exam chip, date from config) · "Planını üç soruda kuralım" · "Yanıtların günlük programını ve konu sırasını belirler." · "Branşın" · "Günde ne kadar çalışabilirsin?" · "30 dk" / "60 dk" / "90 dk" · "Sınava kaçıncı kez giriyorsun?" · "İlk kez" / "Yeniden" · "Seviye testine başla" · "30 soru · yaklaşık 25 dakika · kayıt gerekmez" · "Önce uygulamayı gez".

Score-type hint under the field: P2 "Puan türün P2: AGS %50, ÖABT %50." · P1 **NEW** "Puan türün P1: yalnız AGS." · P3 **NEW** "Puan türün P3: AGS %50, alan testi %50."

Sample fields for the seed (verify before launch): Sınıf Öğretmenliği (P2), Okul Öncesi Öğretmenliği (P2), Türkçe Öğretmenliği (P2), İngilizce Öğretmenliği (P3).

Behaviour: one screen (ONB-3). "60 dk" and "İlk kez" are preselected; the field must be chosen. "Seviye testine başla" saves the profile and opens `/placement`. "Önce uygulamayı gez" saves the profile and opens Today. Both create the guest user if needed (ONB-1).

## Placement test — `placement-test.html`

Copy: "Seviye tespiti" · "{current} / {total}" · subtest chip "{subtest}" · "Emin değilim" · "Boş bırak" · "Sonraki soru". Labels: "Testi kapat", "Test ilerlemesi", "Seçenekler".

Behaviour: one option can be selected and changed until "Sonraki soru" is pressed. "Sonraki soru" is disabled until an option is selected. "Boş bırak" submits a blank answer and advances. No feedback is shown during placement. Closing saves progress (PLC-4) and returns to the previous screen. After question 30 the app opens the result.

The same layout is the answering state of topic tests, reviews and lesson check questions. There the header title is "{subtest} testi" and, after "Sonraki soru", the feedback state below is shown.

## Placement result — `placement-result.html`

Copy: "Seviye sonucun hazır" · "Tahmini AGS netin" · "{low}–{high}" · "/ 80 soru" · "30 soruluk teste dayanan bir tahmindir, kesin sonuç değildir." · "Alt testlerin, zayıftan güçlüye" · "öncelikli" · "{correct} / {asked}" · "İlk haftanın planı" · "Günde {minutes} dk" · plan lines "{subtest}: {topic}" and "Pazar: ilk tam deneme" · "Hesap oluştur ve planı başlat" · "Şimdilik kayıt olmadan devam et".

Behaviour: subtests are sorted by `correct / asked`, weakest first; the two weakest carry the "öncelikli" chip. The primary button opens `/auth`, then the paywall (PAY-6), then Today. The secondary link opens Today as a guest.

## Paywall — `paywall.html`

Copy: "Sezon paketi" · "Sınava kadar tam erişim, tek ödeme" · "Paket, sonuçların açıklanacağı 11 Haziran 2027'ye kadar geçerlidir. Web, iOS ve Android'de aynı hesapla kullanılır." · table headers "Özellik", "Ücretsiz", "Sezon paketi" · "{price}" (for example "₺990") · "tek ödeme · KDV dahil" · "Sezon paketini al" · "Ücretsiz sürümle devam et" · "Kürsü atanma ya da puan garantisi vermez. Tahminler aralık olarak gösterilir." Label: "Kapat".

Table rows (feature · free · pass): "Günlük program" · "İlk 3 gün" · "Sınava kadar" — "Konu soruları" · "Günde 5" · "Sınırsız" — "Mikro ders" · "Günde 1" · "Sınırsız" — "Tam deneme" · "1" · "Tümü" — "Türkiye geneli deneme" · "Ayda 1" · "Tümü" (P2: hide until built) — "Fotoğraftan çözüm" · "Toplam 3" · "Günde 10" (P1: hide until built).

Behaviour: price, date and limit values come from `GET /v1/paywall`. A guest who presses "Sezon paketini al" is sent to `/auth` first. Opened from three places (PAY-6).

## Today — `today.html` and `web-today.html`

Copy: "{date}" (for example "1 Şubat Pazartesi") · "Sınava {n} gün" · "Bugün {n} görevin var" · "{total} görevden {done}'{suffix} tamam" · "Güzel başladın. Kalan süre {m} dk" · "%{percent}" · "Başla" · "{m} dk" · "{n} günlük seri" · "Haftalık hedef: 5 günün {k}'{suffix}". Labels: "Günün ilerlemesi", "Seri ve haftalık hedef".

Task rows: review "{n} tekrar sorusu" with meta "Yanlış defterinden" · lesson "{lesson title}" with meta "Mikro ders · {subtest}" · topic test "{topic}" with meta "Konu testi · {subtest} · {n} soru" · mock **NEW** "{mock title}" with meta "Deneme · 80 soru". A finished task appends " · tamamlandı" to its meta and shows the mint check tile.

Variants of the progress line: nothing done → "Kalan süre {m} dk"; some done → as designed; all done → **NEW** "Bugünkü program tamam".

P1 tile: "Fotoğraftan soru çöz" with "Bugün {n} hak". Until photo solve is built, leave it out and let the streak tile take the full width.

Behaviour: the first unfinished task is the highlighted card with "Başla"; its duration moves into the meta line. Tapping any task opens it. The whole list is computed by the server.

Web layout adds a side panel: "Tahmini AGS neti" · "{low}–{high}" · "Son 4 haftada +{n} net" · "Bu hafta öncelikli" with the three weakest subtests and "%{mastery}". The card "Türkiye geneli deneme 1" with its window and "Deneme kurallarını gör" is P2: leave it out.

## Micro-lesson — `micro-lesson.html`

Copy: "Mikro ders" · "{i} / {n}" · chip "{subtest} · {source short name}" · card kind label · "Kaynak: {source}" · "Madde metni" · "Önceki" · "Sonraki kart". Label: "Bugüne dön".

Card kind labels: "Sık karıştırılan kavram" (designed) · **NEW** "Tanım", "Örnek", "Sınavda nasıl sorulur".

Behaviour: a card is data: kind, title, one to three blocks (heading and text), optional tip, source. "Madde metni" opens the article text in a sheet when the source is a law. After the last card come the 2 check questions (LES-2), then the lesson is completed and the app returns to where it was opened.

## Question feedback — `question-review.html`

Copy: "{subtest} testi" · "{i} / {n}" · options as "A) {text}" · "Senin yanıtın" · "Doğru yanıt" · "Neden yanlış?" · "Bu yanılgı {k}. kez" · "Kaynak · {source}" · "İlgili mikro dersi aç" · "Bu soruda hata var" · "Yanlış defterine eklendi · ilk tekrar yarın" · "Sonraki soru". Labels: "Yanlış", "Doğru", "Testi kapat", "Neden yanlış".

Behaviour: shown after the answer is submitted. The rationale of the chosen option comes first (WHY-2). For quantitative questions the solution steps are listed under the rationale (TEST-4). When the answer was correct the heading is **NEW** "Neden doğru?" and no misconception chip is shown. The notebook line appears only when an entry was created or updated (NB-1). "Bu soruda hata var" opens a short report form (**NEW** "Hatayı kısaca anlat" · "Gönder" · "Teşekkürler, inceleyeceğiz.").

## Mistake notebook — `mistake-notebook.html`

Copy: "Yanlış defteri" · "{open} açık kayıt · {learned} kayıt öğrenildi" · "Bugünkü tekrar tamam" · "Yarın {n} soru seni bekliyor" · "Erken tekrar et" · "Konuya göre" · "Yanılgıya göre" · row meta "{subtest} · sıradaki tekrar {when}" with `{when}` as "yarın" or "{n} gün sonra" · "Tekrarlar 1, 3, 7, 14 ve 30 gün arayla gelir. Aynı soru yerine aynı konuyu ölçen yeni bir soru sorulur; üst üste üç doğru kaydı kapatır." Labels: "Bugüne dön", "Tekrar durumu", "Gruplama".

Variants: reviews due today → **NEW** "Bugün {n} tekrar sorun var" with button "Tekrara başla". Empty notebook → **NEW** "Defterin boş. Yanlış yaptığın ve emin olmadığın sorular burada toplanır."

Behaviour: rows are groups with their open-entry count. Starting a review creates a practice session of type `review`. On the free tier the notebook is view-only: starting a review opens the paywall.

## Mock exam — `mock-exam.html`

Copy: "{mock title}" · "Soru {i} / 80 · süre durdurulamaz" · "{mm:ss}" · "kalan süre" · "Sonra bak" · map heading "{subtest} · {from}–{to}" · legend "yanıtlandı", "sonra bak" · "Önceki" · "Sonraki" · "Denemeyi bitir". Labels: "Kalan süre", "Deneme ilerlemesi", "Seçenekler", "Soru haritası", "{n}, sonra bak".

The reference shows the P2 title "Türkiye geneli deneme 1". P0 mocks use their content title, for example "Deneme 1".

Behaviour: the header timer counts down to the server deadline and submits automatically at zero (MOCK-2). Options use `OptionCell` when all five are 4 characters or shorter, otherwise `OptionButton`. The map shows the questions of the current subtest; tapping a cell jumps to it. Answers are saved to the server as they are chosen. "Denemeyi bitir" asks first: **NEW** "Denemeyi bitirmek istiyor musun? {blank} soru boş." with "Bitir" and "Devam et". Practice mode shows **NEW** "alıştırma modu" in place of the timer.

## Mock result — `nationwide-result.html`

P0 copy: "{mock title}" · "{date}" · "Netin" · "{net}" · "/ 80" · "{correct} doğru" · "{wrong} yanlış" · "{blank} boş" · table headers "Alt test", "Netin" · "110 dakikanın {used}'{suffix} kullandın. Programın yarından itibaren {subtests} daha çok yer verecek." · "{wrong} yanlışı incele" · "Gelişimime git". Labels: "Bugüne dön", "Sonuç özeti".

P0 additions that are not in the design: a list **NEW** "Yanlışların konu dağılımı" with "{topic}" and "{n} yanlış" (MOCK-5); for free candidates a card **NEW** "Sezon paketiyle tüm denemeler açılır." with "Sezon paketini gör" (PAY-6).

P2 only, leave out until NAT is built: "Adayların %{p}'{suffix} geride bıraktın", the percentile ring with "yüzdelik dilim", "{rank}. / {total} aday", the "Ortalama" column, "ortalamanın altında", and "sonuçlar açıklandı" after the date.

## Progress — `progress.html`

Copy: "Gelişim" · "Sınava {n} gün" · "Tahmini AGS neti" · "{low}–{high}" · "Son 4 haftada {signed n} net" · "Alt test ustalığı" · "%{p}" · "Konu haritası" · "{n} konu" · "Sağlam {n}" · "Çalışılıyor {n}" · "Başlanmadı {n}" · "{n} gün" · "Günlük seri". Labels: "Tahmini net", "Alt test ustalığı", "Konu haritası", chart label "Dört haftalık net eğilimi: {values}".

P0 additions: **NEW** "Deneme geçmişi" list with "{mock title}", "{date}" and "{net} net" (PROG-4). With fewer than two weeks of data the trend chart is hidden.

P2 only: the tiles "{n} rozet" / "Son: {badge}" and "{rank}. sıra" / "Haftalık lig, 30 kişi". In P0 show the streak tile alone, full width, with the weekly goal line.

## Photo solve (P1) — `photo-solve.html`

Copy: "Fotoğraftan çözüm" · "Bugün {n} hak" · "Çekilen fotoğraf" · "Okunan soru" · "Yapay zekâ çözümü, hata içerebilir." · step titles and texts from the solution · "Yanıt" · "{answer}" · "İlgili mikro ders: {lesson}" · "Yeni fotoğraf çek" · "Bu çözümde hata var". Label: "Bugüne dön".

## Screens without a design

Build these from the design system, as plain as possible. All copy here is **NEW**.

| Screen | Content |
|---|---|
| Sign up / sign in | "Hesap oluştur" · "İlerlemen hesabına taşınır." · "E-posta ile devam et" · "Google ile devam et" · "Apple ile devam et" · "E-postana gelen 6 haneli kodu gir" · "Devam et" · "Kodu yeniden gönder" |
| Lessons index | "Dersler" · lessons grouped by subtest, then topic · row: lesson title, "{m} dk", done state · topic header with the mastery state |
| Mock index | "Deneme" · row per published mock: "{mock title}", "80 soru · 110 dk" · "Süreli başla" · "Alıştırma modu" · "Deneme geçmişi" |
| Settings | "Ayarlar" · "Günlük süre" · "Bildirim saati" · "Sorular yapay zekâyla üretilir ve otomatik denetlenir." · "Gizlilik" · "Kullanım koşulları" · "Çıkış yap" · "Hesabı sil" |
| Free limit reached | "Bugünkü ücretsiz sınırına ulaştın." · "Sezon paketini gör" · "Yarın devam et" |
| Loading, error, offline | "Yükleniyor…" · "Bir şeyler ters gitti." · "Tekrar dene" · "Bağlantı yok." |
