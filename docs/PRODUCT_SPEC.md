# Product spec — Kürsü

Source: the product requirements document (PRD) as of 18 November 2026. This file restates it as numbered rules. Rule ids such as `PLC-3` are stable; name tests after them.

- **must** marks required behaviour.
- **DEFAULT** marks a value the PRD does not fix. Implement it as written, keep it in one place on the server, and make it easy to change.

## 1. Product

Kürsü prepares teacher candidates for the MEB-AGS exam. It tells each candidate what to study every day. All questions, lessons and explanations are generated and quality-checked offline, then imported; the app only serves them. The first release covers the six subtests of the AGS session and runs on web, iOS and Android. "Kürsü" is a working name: keep the display name in one configuration value.

## 2. Glossary

| UI term (Turkish) | Meaning | Identifier in code |
|---|---|---|
| AGS | the exam (Akademi Giriş Sınavı) | `exam`, code `ags-2027` |
| Alt test | one of the six sections of the exam | `subtest` |
| Konu | topic inside a subtest (31 in total) | `topic` |
| Kazanım | the learning objective a question measures | `objective` |
| Yanılgı | the misconception behind a wrong option | `misconception` |
| Mikro ders | lesson of 3–5 minutes on one concept | `lesson`, `lesson_card` |
| Konu testi | practice test of 10–15 questions on one topic | `practice_session` of type `topic_test` |
| Seviye tespiti | placement test | `placement` |
| Günlük program | personal daily plan | `daily_plan`, `plan_task` |
| Yanlış defteri | notebook of missed and unsure questions | `mistake_entry` |
| Aralıklı tekrar | spaced repetition | `review` |
| Kardeş soru | a different question that measures the same objective | sibling question |
| Deneme | full mock exam | `mock_exam`, `mock_attempt` |
| Türkiye geneli deneme | nationwide mock exam in a fixed window (P2) | `nationwide_mock` |
| Net | score: correct minus a quarter of wrong | `net` |
| Ustalık | mastery of a topic or subtest | `mastery` |
| Sezon paketi | one-time purchase with full access | `season_pass` entitlement |
| Seri | streak of completed days | `streak` |
| Rozet, lig | badge, weekly league (P2) | `badge`, `league` |
| Branş | teaching field chosen at onboarding | `field` |
| Puan türü | score type P1, P2 or P3 | `score_type` |
| Emin değilim | "not sure" mark on an answer | `not_sure` |
| Sonra bak | "look later" mark inside a mock exam | `flagged` |
| Hata bildirimi | report that a question or solution is wrong | `content_report` |
| Karantina | content hidden until it is re-checked | status `quarantined` |

## 3. Exam facts

- 80 questions, 110 minutes, five options (A–E) per question.
- `net = correct − wrong / 4`. Blank answers count as neither.
- Exam day: Saturday 8 May 2027. Results day: 11 June 2027. Both come from remote config.

| Subtest (display name) | Code | Questions | Order in exam | P1 weight |
|---|---|---|---|---|
| Sözel Yetenek | `verbal` | 15 | 1–15 | 20 |
| Sayısal Yetenek | `quantitative` | 15 | 16–30 | 20 |
| Tarih | `history` | 6 | 31–36 | 15 |
| Türkiye Coğrafyası (short: Coğrafya) | `geography` | 6 | 37–42 | 10 |
| Eğitim Bilimleri | `education` | 30 | 43–72 | 25 |
| Mevzuat | `legislation` | 8 | 73–80 | 10 |

## 4. Candidates and score types

- The field chosen at onboarding sets the score type: fields without a field exam (ÖABT) are **P1**, fields with ÖABT are **P2**, foreign-language fields are **P3**.
- In P1 the AGS weights are those in the table above. In P2 and P3 the AGS session counts for half of the score, so each weight is halved. Kürsü covers only the AGS session.
- The field list is data (`fields` table). Seed it with the four sample fields in `docs/SCREENS.md`; the full official list is added later.

## 5. Features and priorities

Build P0 first. P1 and P2 are built only when a milestone names them.

| Feature | Priority | Free tier |
|---|---|---|
| Onboarding and goal setting | P0 | yes |
| Placement test and result report | P0 | yes |
| Personal daily plan | P0 | first 3 days |
| Micro-lessons | P0 | 1 per day |
| Topic tests with step-by-step solutions | P0 | 5 questions per day |
| "Neden yanlış?" explanation | P0 | on every question solved |
| Mistake notebook and spaced repetition | P0 | view only |
| Timed mock exam | P0 | 1 mock |
| Progress tracking | P0 | summary |
| Season pass purchase | P0 | purchase screen available |
| Error reporting | P0 | yes |
| Daily streak and weekly goal | P0 | yes |
| Photo solve | P1 | 3 in total |
| Nationwide mock exam | P2 | 1 per month |
| Badges and weekly league | P2 | yes |

## 6. Rules

### 6.1 Onboarding (ONB)

- **ONB-1** A candidate must be able to finish onboarding, take the placement test and see the result without creating an account. The app creates a guest user silently.
- **ONB-2** Onboarding asks three things: field, daily study time (30, 60 or 90 minutes), first attempt or repeat attempt. Then it offers "start the placement test" and "look around first".
- **ONB-3** The four steps must be completable in 60 seconds: one screen, no extra confirmation steps.
- **ONB-4** The exam date is never asked. The countdown ("Sınava N gün") is computed from server time and is identical on every screen.
- **ONB-5** Sign-up is offered on the placement result screen, by email, Google or Apple.
- **ONB-6** When a guest signs up, all progress moves to the account. Nothing is lost or duplicated.

### 6.2 Placement test (PLC)

- **PLC-1** 30 questions, about 25 minutes, not timed. Distribution: education 11, verbal 6, quantitative 6, legislation 3, history 2, geography 2.
- **PLC-2** There are three difficulty levels. Each subtest starts at the middle level; a correct answer raises the level for the next question of that subtest, a wrong answer lowers it.
- **PLC-3** The candidate can mark "Emin değilim" on any answer and can leave a question blank ("Boş bırak").
- **PLC-4** If the test is interrupted, it resumes at the same question.
- **PLC-5** The result shows the estimated AGS net as a **range** (for example 28–34), never as a single number, with the note that it is an estimate.
- **PLC-6** The result lists the six subtests from weakest to strongest and shows the plan for the first week.
- **PLC-7** The candidate can retake a 10-question short version every 14 days.

### 6.3 Daily plan (PLAN)

- **PLAN-1** The plan is recomputed every day and is a list of tasks for that day.
- **PLAN-2** Inputs: days to the exam, daily study time, score-type weights, topic mastery, reviews that are due.
- **PLAN-3** Reviews that are due are the first task of the day.
- **PLAN-4** A typical day: due reviews, one or two micro-lessons, one topic test of 10–15 questions. One day a week is mock day.
- **PLAN-5** The total estimated duration of the day's tasks must not exceed the chosen daily time. Every task shows its estimated duration.
- **PLAN-6** Topics with high weight and low mastery come first.
- **PLAN-7** In the last 30 days before the exam no new topics are opened; the plan shifts to mocks and reviews.
- **PLAN-8** When the candidate changes the daily time, today's plan is recomputed immediately.
- **PLAN-9** Tasks from a missed day are not piled onto the next day. They are redistributed over the remaining days.
- **PLAN-10** When every task of the day is done, the day counts as complete and is added to the streak.

### 6.4 Micro-lessons (LES)

- **LES-1** A lesson teaches one concept in 3–5 minutes with 4–6 cards. Card kinds: definition, example, commonly confused concept, how it is asked in the exam.
- **LES-2** A lesson ends with 2 check questions. A wrong answer shows the related card again.
- **LES-3** Every lesson shows its source: a law article or a section of the topic notes.
- **LES-4** Finishing a lesson updates the mastery of its topic.

### 6.5 Topic tests (TEST)

- **TEST-1** A topic test has 10–15 questions. Difficulty is chosen from the candidate's mastery of that topic.
- **TEST-2** Every question has five options and the same format as the exam.
- **TEST-3** The candidate can mark "Emin değilim" while answering.
- **TEST-4** After answering, the solution opens step by step. In quantitative questions each operation is its own step.

### 6.6 "Neden yanlış?" explanation (WHY)

- **WHY-1** Every option has its own rationale: why the correct one is correct, and which misconception each distractor rests on.
- **WHY-2** The rationale of the option the candidate chose is shown first.
- **WHY-3** Every explanation shows its source. Legislation: law name, article number and article text. Other subtests: the related micro-lesson.
- **WHY-4** When the same misconception occurs three times, the app suggests a short review lesson for it. The screen shows the count ("Bu yanılgı 2. kez").
- **WHY-5** Every explanation has a "Bu soruda hata var" action (see CNT).
- **WHY-6** The correct option, rationales and solution steps must never reach the client before the candidate has answered that question.

### 6.7 Mistake notebook and spaced repetition (NB)

- **NB-1** Every wrong answer and every answer marked "Emin değilim" creates or updates a notebook entry.
- **NB-2** The notebook can be grouped by topic and by misconception.
- **NB-3** A review asks a sibling question, never the same question again.
- **NB-4** Review intervals are 1, 3, 7, 14 and 30 days. A correct answer moves the entry to the next interval; a wrong answer moves it back to the first.
- **NB-5** Three correct answers in a row close the entry as "öğrenildi" (learned).
- **NB-6** When fewer than 14 days remain to the exam, intervals shorten and every open entry is asked at least once before exam day.

### 6.8 Timed mock exam (MOCK)

- **MOCK-1** A mock has 80 questions in the exam's order and distribution, and lasts 110 minutes.
- **MOCK-2** The timer cannot be paused and keeps running when the app is closed. The server owns the deadline.
- **MOCK-3** A candidate who wants no timer chooses practice mode ("alıştırma modu").
- **MOCK-4** Inside a mock the candidate can move freely between questions, change answers, and mark questions "Sonra bak". A question map shows answered, flagged and current questions.
- **MOCK-5** The result shows net, per-subtest breakdown, time used, and the topic distribution of wrong answers.
- **MOCK-6** 10 mocks exist at launch; 2 are added every two weeks. Mocks are content; the app lists whatever is published.
- **MOCK-7** No rationales are shown during a mock. Review opens after submission.

### 6.9 Progress (PROG)

- **PROG-1** Estimated AGS net as a range, and its change over the last four weeks.
- **PROG-2** Mastery per subtest as a percentage.
- **PROG-3** Topic map: every topic is "başlanmadı", "çalışılıyor" or "sağlam".
- **PROG-4** Mock history.

### 6.10 Streak and weekly goal (STRK)

- **STRK-1** Completing the day's plan adds one day to the streak.
- **STRK-2** One day per week can be frozen, so a single missed day does not break the streak.
- **STRK-3** Weekly goal: complete the plan on 5 of 7 days.
- **STRK-4** Gamification rewards and never punishes: no negative messages, no loss animations.
- **STRK-5** At most one notification per day, at the time the candidate chooses.

### 6.11 Season pass and paywall (PAY)

- **PAY-1** Free candidates use the placement test and the limits in section 5. The season pass removes the limits.
- **PAY-2** The pass is a one-time purchase, valid until results day (11 June 2027).
- **PAY-3** A pass bought on any platform is valid on all three. Entitlements live on the server.
- **PAY-4** Web sells by card, with instalments. iOS and Android sell through in-store one-time purchase.
- **PAY-5** On web the launch price is tested in three groups: ₺790, ₺990 and ₺1.290. A candidate always sees the same price. Prices come from the server.
- **PAY-6** The paywall appears in three places: after the placement result and plan have been shown; when a free limit is reached; on the mock result screen.
- **PAY-7** The app never promises an appointment or a score. Estimates are always ranges. The paywall carries the disclaimer text in `docs/SCREENS.md`.

### 6.12 Content status and error reports (CNT)

- **CNT-1** The app serves only content with status `published`, or `prerelease` to the candidates selected for it. `quarantined` and `retired` content is never served.
- **CNT-2** New questions are first shown to 5% of candidates (`prerelease`), then to everyone.
- **CNT-3** Any candidate can report a question or a photo solution. Reports from three different candidates quarantine the question automatically.
- **CNT-4** When a question a candidate has answered turns out to be faulty, that candidate is notified and their nets are recomputed without it.
- **CNT-5** The app states clearly that questions are AI-generated and automatically checked.
- **CNT-6** Every question and lesson stores its source references, so that content tied to a changed law article can be found.

### 6.13 Photo solve (PHOTO) — P1

- **PHOTO-1** The candidate photographs a question; the app reads it and solves it step by step, and links the related micro-lesson.
- **PHOTO-2** Every solution carries the label "Yapay zekâ çözümü, hata içerebilir."
- **PHOTO-3** If confidence is low the app gives no solution: it says it could not solve the question and suggests the related topic.
- **PHOTO-4** Questions outside the AGS scope are rejected.
- **PHOTO-5** Limits: 10 photos per day with the season pass, 3 in total on the free tier.
- **PHOTO-6** A photographed question is never added to the question bank and never shown to another candidate. The image is deleted after 30 days.

### 6.14 Nationwide mock exam (NAT) — P2

- **NAT-1** First session Sunday 7 February 2027, then every two weeks until the exam.
- **NAT-2** The window opens Saturday 10:00 and closes Sunday 23:59 (Europe/Istanbul). The candidate starts the 110 minutes at any moment inside the window.
- **NAT-3** Results are published when the window closes: rank, percentile, comparison with subtest averages.
- **NAT-4** With fewer than 100 participants no rank is shown, only the percentile.
- **NAT-5** The questions are used nowhere else in the app until the window closes.

### 6.15 Badges and weekly league (GAM) — P2

- **GAM-1** Badges: first mock, 100 questions, 7-day streak, one subtest reaching "sağlam".
- **GAM-2** Weekly league in groups of 30; points come from completed tasks. The candidate can turn the league off in settings.

## 7. Defaults where the PRD is silent

All are **DEFAULT**: implement on the server, in one module, with named constants and tests.

- **D-1 Net estimate.** For each subtest, `p = (correct + 1) / (answered + 2)`. Expected net is the sum over subtests of `questions × (p − (1 − p) / 4)`. The range is the estimate ± `max(3, 10%)`, rounded to whole numbers and clamped to 0–80. After the placement test, use the last 28 days of answers the same way.
- **D-2 Mastery.** Per topic, a value between 0 and 1. After each answer, `m ← m + 0.2 × (x − m)`, where `x` is 1 for correct, 0.5 for correct but marked not sure, 0 for wrong. Finishing a lesson raises `m` to at least 0.3. States: `not_started` (no answers and no lesson), `solid` (`m ≥ 0.75` and at least 8 answers), otherwise `in_progress`. Subtest mastery is the mean of its topics.
- **D-3 Plan builder.** Order: due reviews (1.25 minutes per question, at most 40% of the daily time); then up to two lessons (5 minutes each) for the topics with the highest `subtest weight × (1 − mastery)`; then one topic test (1.5 minutes per question, 10–15 questions) on the top topic. Stop adding tasks when the next one would exceed the daily time.
- **D-4 Mock day.** Sunday. On mock day the plan is a single mock and is exempt from PLAN-5.
- **D-5 Near-exam reviews (NB-6).** With fewer than 14 days left the intervals become 1, 2, 3 and 5 days, and every open entry is due no later than the day before the exam.
- **D-6 Streak freeze (STRK-2).** Weeks run Monday to Sunday. The first missed day of a week uses the freeze automatically; a second missed day resets the streak to 0.
- **D-7 Free-tier counters.** Daily limits reset at 00:00 Europe/Istanbul. "First 3 days" of the daily plan counts calendar days from the first plan.
- **D-8 Difficulty for topic tests (TEST-1).** Mastery below 0.4 → level 1, below 0.75 → level 2, otherwise level 3; mix in one level up or down for a third of the questions.

## 8. Out of scope for the first release

- ÖABT field tests.
- Free chat with an AI coach.
- Video and live lessons.
- Exams other than AGS.
- A panel for teachers or institutions.
- Showing past ÖSYM questions.
- The offline content pipeline (generation and quality gates). The app only imports its output.

## 9. Privacy and compliance

- Personal data falls under Türkiye's KVKK. Store the minimum: account identity, study data, purchases.
- Nothing personal is sent to an AI provider. Photo-solve requests carry the image and no user identifiers.
- Photos are deleted after 30 days. Retention periods are configuration.
- A signed-in candidate can delete the account and its data from settings.
- Consent texts, privacy notice and refund terms are provided by counsel later. Leave clearly marked slots for them; do not write legal text.

## 10. Open product questions

Do not decide these. Keep each one configurable.

- Final product name.
- Launch price (PAY-5) and free-tier limits (section 5).
- The official field list and each field's score type.
- Whether mock day should respect the daily time (D-4).
- How email sign-up works (see `docs/ARCHITECTURE.md`).

## 11. What success is measured by

Record the events needed for these measures (see the analytics section of `docs/ARCHITECTURE.md`): paying candidates; placement tests finished ÷ started; season passes ÷ placement tests finished; candidates active 7 days after sign-up; daily plans completed ÷ started; difference between first and last mock net; content reports and time to quarantine.
