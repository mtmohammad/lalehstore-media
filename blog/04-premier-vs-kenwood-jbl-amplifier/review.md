# Review: 04 مقایسه آمپلی پریمیر 11000 با کنوود 8400 و جی بی ال A704؛ کدام قوی تر است؟
Date: 2026-11-12 (post-publication review; article published 2026-11-10 before the checklist existed) · Type: cluster · Focus keyword: مقایسه آمپلی پریمیر · Slug: premier-vs-kenwood-jbl-amplifier · Words: ~1830

## Pre-writing
- Cannibalization: closest = pillar «بهترین آمپلی فایر ماشین» (57254) → different intent (brand comparison vs category guide); linked both ways.
- Intent: comparison
- SERP top results reviewed (google hl=fa, 2026-11-10): digikala PRG-904, emalls PRG-904/8911/8984/804, aparat 8984, bahramshop 8984, gholab 8702 — all product listings, no comparison content.
- Information gain: 1) RMS vs Max explained with the 4600 W ÷ 14.4 V ≈ 320 A calculation 2) side-by-side table of 5 four-channel amps from store attributes incl. speaker-level input 3) in-stock alternatives (Kenwood 804, Pioneer 6704) with exact warranty text 4) bridge/system guidance

## Fact-check (all re-opened via Store API on 2026-11-12)
| # | Claim | Section | Source | Evidence / formula | Status |
|---|---|---|---|---|---|
| 1 | Premier 11000: 4 ch, max 4600 W, Bass Boost, HPF, LPF, China, warranty text | table, H2 پریمیر | Store API 13365 | «حداکثر توان خروجی : 4600W» «12 ماه ضمانت شرکت پریمیر -بوستر» | VERIFIED |
| 2 | Premier RMS not stated; out of stock | intro, table | Store API 13365 | no RMS attribute; is_in_stock false | VERIFIED |
| 3 | Kenwood 8400: max 720, 60×4 @4Ω, 90×4 @2Ω, 180×2 bridge, 5Hz–50kHz, HPF 50–200 −12, LPF 50–200 −24, speaker level, 18ماه ضمانت نت الکترونیک | H2 کنوود | Store API 11859 | attributes + description «قابلیت Speaker level» | VERIFIED |
| 4 | A704: class AB, 70×4, 90×4, 180×2, 10Hz–45kHz, S/N >75dB, filters 40–400 12dB/oct, speaker level, 12 ماه ضمانت صوت ایران کیش | H2 جی بی ال | Store API 56617 | attributes + description «آمپلی 4 کانال کلاس AB» | VERIFIED |
| 5 | Kenwood 804: max 1000, 80×4, 110×4, 170×2, no speaker level | table | Store API 57031 | «Speaker Level Inputs : ندارد» | VERIFIED |
| 6 | Pioneer 6704: max 1000, 60×4, 95×4, 190×2 | table | Store API 14094 | attributes | VERIFIED |
| 7 | Totals 240/280/320/240 W RMS @4Ω | image 2, text | rows 3–6 | channel RMS × 4 | DERIVED |
| 8 | 4600 ÷ 14.4 ≈ 320 A | H3 | general P = V·I, 14.4 V charging voltage (general) | 4600/14.4 = 319.4 | DERIVED |
| 9 | Kenwood 8400 «قدیمی تر سری HQR» | H2 کنوود | Store API 11859 description «از آمپلی های قدیمی… سری HQR» | | VERIFIED |

Products linked: 11859, 56617, 57031, 14094 — published ✓ in stock ✓ permalink ✓ warranty text ✓ · 13365 named, not linked (out of stock) ✓
Banned-content scan: 0 price/claim hits; «۱۴۰۵» only inside the pillar's title used as anchor in «مقالات مرتبط» (accepted)
Links checked: 7 body + 3 related, all 200; external: 0 (no official manufacturer page lists HQR8400 or PRG-11000)
Slop check: «در این مقاله» once → fixed in article.html (live fix pending); no other hits

## On-page
Title (63 chars rendered) → over 60; new rank_math_title proposed (pending) · Meta (131) ✓ · Internal links: 7 ✓ · External: 0 · Images: 3 + featured, alt ✓

## Score
| Category | Score | Max | Notes |
|---|---|---|---|
| A Accuracy & evidence | 28 | 30 | all numbers verified; no manufacturer link possible |
| B Reader value | 22 | 25 | "how we checked" line missing, one slop phrase (fixed locally) |
| C On-page SEO & links | 16 | 20 | title 63 chars, no external link |
| D AI-citation readiness | 13 | 15 | H2 openers mostly standalone |
| E Technical & publishing | 10 | 10 | 390px no overflow, images load, Rank Math meta saved, Article schema present, index |
| **Total** | **89** | **100** | |

P0 issues: none
Live checks: 390px overflow ✓ · images load ✓ · Rank Math meta ✓ · schema seen: Article, WebPage, BreadcrumbList, Organization, Person · noindex: no
DECISION: PUBLISH (already live) — 3 small live fixes pending (see meta.json pending_live_fixes), need the app browser.
