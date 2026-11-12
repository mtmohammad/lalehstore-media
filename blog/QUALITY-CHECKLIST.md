# Quality checklist for lalehstore.com blog articles

Read this together with `blog/README.md`. One run = one article, and each one passes this checklist before it is
published. Save the filled-in template from section 9 as `blog/<NN>-<slug>/review.md` and commit it with the article.

- Source: adapted from **claude-blog** by AgriciDaniel (github.com/AgriciDaniel/claude-blog, commit
  `4f9c2cb8fd17f594e868d6c2ce0e8fb2c971f987`), MIT License, Copyright (c) 2025-2026 AgriciDaniel. Only the ideas were
  adapted. No code or scripts were copied.
- **Where this file and `blog/README.md` (or the calendar doc's binding sections) disagree, README wins.**
- Do not install or run claude-blog or its scripts. `analyze_blog.py` needs nltk cmudict and fails offline, and
  English readability scores (Flesch and similar) mean nothing for Persian. Every check here is done by hand or with
  a short script you write yourself (grep, a word count, fetch).
- Left out on purpose: Gemini or stock images, Pixabay/Unsplash, YouTube embeds, author pages and Person/ProfilePage
  schema, robots.txt and llms.txt edits, canonical/noindex/redirect fixes, DataForSEO, Search Console APIs, and
  readability formulas. Each of these breaks a README rule or needs settings access we don't have.

---

## 1. Pre-writing (record the results in review.md before you write)

### 1a. Intent and cannibalization
1. Load every existing post: `/wp-json/wp/v2/posts?per_page=100&_fields=id,title,link,slug`, plus the
   `focus_keyword` values in `blog-log.json`.
2. Compare the row's main keyword with each existing title, slug and focus keyword:
   - **Exact match** on the focus keyword, or the same question answered → **stop**. Do not write a duplicate.
     Pick a different angle that the calendar row allows, or mark the row «عقب افتاد» and say why. Never merge,
     redirect, noindex or canonicalize. Those need settings or other posts changed.
   - **Same stem or subset** (e.g. «آمپلی فایر ماشین» vs «بهترین آمپلی فایر ماشین») → allowed only if the
     intent differs. Write one sentence in review.md on how this article differs, and link the two posts to each other.
   - **Different intent** → OK. Note it and move on.
3. Intent label: informational / comparison / buying-guide. The blog does **not** target «خرید X» or «قیمت X»
   (transactional queries belong to the category and product pages). The blog links to those pages instead.
4. Keyword trap: a bare generic noun (e.g. «باند», «ساب») gives noisy research. Narrow it to the calendar row's
   angle (type, size, brand, use) before you search.

### 1b. Source tiers (only T1 and T2 may supply a fact)
| Tier | What | Use |
|---|---|---|
| T1 | lalehstore Store API or product pages you opened in this run (name, permalink, stock, attributes, warranty text) | Availability, model names, attributes, warranty wording |
| T1 | Official manufacturer spec page, manual or spec-sheet PDF on the manufacturer's domain (jbl.com, infinitysystems.com, jvckenwood.com, kenwood-electronics.co.uk, pioneer…) | Specs and technical figures |
| T2 | Other official pages from the same manufacturer (press release, support FAQ) | Context, release or replacement info |
| T3 | Google top results, competitor shops and blogs | **Gap analysis only.** Never the source of a fact or number |
| T4-5 | Forums, Digikala/Torob listings, Aparat/YouTube, AI answers, unsourced spec aggregators | Never used |

- When five sites repeat one spec, that is one source (an "echo"), not five confirmations. Go to the manufacturer.
- If the store attribute and the manufacturer page disagree, leave the number out and note the conflict in review.md.
- Write down the exact model code, including suffix or region variant, because specs differ between variants.

### 1c. Information gain (write it down before drafting)
Open the top 5 Google results (`hl=fa&gl=ir`). In review.md list what they cover and **at least 3 concrete gaps**
this article fills honestly. Gaps a shop can fill without faking anything:
- a side-by-side table of in-stock models from official specs, with the units and test conditions stated
- compatibility logic: RMS matching, impedance, bridge, channel count, with the inputs shown
- a decision guide («اگر … ، … مناسب تر است») tied to stated criteria
- a plain explanation of the confusing spec terms (RMS vs Max, sensitivity, frequency response)
- the exact warranty conditions from the product page, plus which models are actually in stock now
- original diagrams built from the site's own product photos
"Longer than competitors" is not an information gain.

---

## 2. Writing rules adopted from claude-blog
- **Answer first.** The first paragraph (40–60 words) gives the direct answer, names the product or entity, and
  says when the answer holds. No warm-up.
- **Every H2 opens with its own answer.** The first 1–2 sentences under an H2 answer that heading and still make
  sense if quoted alone. Use the full name («ساب جی بی ال <bdi dir="ltr">CS1214</bdi>»), not «این مدل».
- **Headings are promises.** Each section delivers what its H2 says, early. One H1 (the title), H2 → H3 with no
  skipped levels. Not every H2 is a question.
- **Scannable:** short paragraphs with one idea each, lists only for 3 or more parallel items, and one comparison
  table wherever you compare things (README table rules). A pillar may add a «فهرست مطالب» with `id` anchors on the H2s.
- **Citation capsules.** A sentence that states a spec names its source in the same sentence, e.g.
  «طبق صفحه مشخصات رسمی JBL، توان RMS این ساب … وات در … اهم است.» Put the number in only after it is verified (section 8).
- **Quotable sentences without statistics.** Most sentences that AI answers quote should be decision rules or
  definitions with no number at all, e.g. «توان RMS آمپلی فایر باید با توان RMS ساب در همان مقاومت هم خوانی داشته باشد.»
  A general technical principle (for example, two 4-ohm coils in parallel give 2 ohms) is allowed when it is correct
  and general. A derived number must show its verified inputs.
- **Use one name for one entity everywhere.** The same Persian name, the same Latin model code, the same unit wording.
- **Superlatives need a stated criterion.** «بیشترین توان RMS در بین مدل های این جدول» is OK.
  «بهترین ساب بازار» in the body is not (the calendar title is the only exception).
- **Honest E-E-A-T for a shop** (there is no hands-on experience, so none is claimed):
  - Put a "how we checked" line at the end of the body, e.g. «مشخصات این مقاله از صفحه رسمی سازنده و صفحه محصول
    در لاله استور گرفته شده است؛ قیمت و موجودی روز را در صفحه هر محصول ببینید.»
  - Keep the WordPress author as it is. Never invent a named author, credentials, "our technicians", or a review step
    that did not happen.
  - Banned experience claims: «ما تست کردیم»، «در تجربه ما»، «نصب های ما»، «مشتریان ما می گویند»،
    «پرفروش ترین»، «محبوب ترین»، «نمایندگی رسمی». Each one is an invented claim (P0).
  - Dates: WordPress shows the publish and modified dates. Do not type a date with ۱۴۰۵ into the body (README year
    rule). Change content dates or wording only when the facts really change. A fake freshness update is a Google
    warning sign.
- **Self-promotion:** mention the store by name for availability or warranty, at most 1–2 times, plus links.
  No sales copy.

---

## 3. AI-slop check for Persian (search the final text for each item, then rewrite or delete)

**Generic openers and closers:** «در دنیای امروز»، «در عصر حاضر»، «امروزه»، «همانطور که می دانید»،
«آیا تا به حال به این فکر کرده اید»، «اگر شما هم جزو کسانی هستید که»، «در این مقاله قصد داریم»،
«با ما همراه باشید»، «تا انتهای مقاله همراه ما باشید»، «امیدواریم این مقاله مفید بوده باشد»،
«نظرات خود را با ما در میان بگذارید»، a «سخن پایانی» heading that only repeats the article.

**Filler and announcements:** «لازم به ذکر است»، «شایان ذکر است»، «گفتنی است»، «قابل توجه است که»،
«نکته بسیار مهم این است که»، «از اهمیت بالایی برخوردار است»، «نقش بسیار مهمی ایفا می کند»،
«به طور کلی می توان گفت»، «در نهایت می توان نتیجه گرفت»، «در ادامه به بررسی … می پردازیم»،
«بیایید نگاهی بیندازیم»، «در یک کلام»، «راهنمای جامع» used in the body.

**Hype (also a fact risk):** «بی نظیر»، «شگفت انگیز»، «فوق العاده»، «انقلابی»، «جادویی»، «دنیایی از»،
«تجربه ای فراموش نشدنی»، «غرق در موسیقی»، «حرف اول را می زند»، «یکه تاز بازار»، «بی شک / بدون شک / قطعاً»
(when nothing is proven), «۱۰۰٪ اورجینال» (unless the product page says exactly that).

**English calques:** «این جایی است که … وارد می شود»، «در پایان روز»، «یک قدم جلوتر»، «بازی را تغییر می دهد»،
«به همین دلیل است که» repeated, «نه تنها … بلکه …» more than once per section.

**Structural patterns** (count them, fix any that repeat):
- several hedges in one sentence («معمولاً، ممکن است، تا حدودی، احتمالاً، به نوعی») → state it plainly or cut it
- triplets of adjectives («قدرتمند، شفاف و دقیق») used again and again
- paragraphs that start with «همچنین / علاوه بر این / از طرفی / در واقع» more than 2 in a row
- every H2 a question, or every H2 ending with a rhetorical question
- list items all the same length and shape (padding); vary detail to match the evidence
- false balance («از یک طرف … از طرف دیگر …») with no real trade-off
- sentences about the article («در این بخش می خواهیم …») instead of about the product
- the focus keyword forced into every heading or paragraph (keyword stuffing)
- the em dash «—» used as decoration → use a comma, «:» or a full stop

---

## 4. On-page SEO check (Rank Math + post body)
| Item | Pass rule |
|---|---|
| `rank_math_title` | ≤ 60 characters in the rendered `<title>` (check the live page). Focus keyword near the start. Matches the content. No price. ۱۴۰۵ only for a pillar |
| `rank_math_description` | ≤ 160 characters. Says what the reader gets. Contains the focus keyword naturally. No price, no year, no claim the body doesn't make |
| `rank_math_focus_keyword` | Same as the calendar main keyword. Not used as the focus keyword of any existing post |
| Slug | Short English, lowercase, hyphens, no year, no stop words, ≤ 5 words, unique on the site |
| Keyword placement | In the title, the first 100 words, and at least one H2 (README). No density target |
| Headings | One H1. H2/H3 with no skipped levels. H2s describe their sections |
| Internal links | Cluster: 5–10. Pillar: 8–14. Must include pillar ↔ cluster (anchor = pillar keyword), 1–2 sibling clusters, the category page (anchor = category keyword), and 2–5 **published, in-stock** products. At least one link in the first 3 paragraphs (for a cluster, the pillar link). At most 2 links per paragraph. No URL twice in the body (the «مقالات مرتبط» list is exempt). No «اینجا کلیک کنید / بیشتر بخوانید» anchors. No self-link |
| External links | 1–3 links to the official manufacturer pages actually used for specs (deep link to the model page, not the homepage). No competitor shops, no T3–T5 sites |
| Images | 2–4 in text + featured image, all original WebP from sysgfx. Persian descriptive `alt` with the model name. `width`/`height` set. Every number shown in an image also appears in the text or a table |
| Words | Strip the HTML and count on whitespace: pillar 2,500–3,500, cluster 1,200–2,000 |
| FAQ | «سؤالات متداول» with 4–6 real questions. Not copies of H2 text |

---

## 5. GEO / AI-citation checks
(Google says optimizing for AI features is ordinary SEO. There is no special markup, llms.txt or "chunking".)
- [ ] The first paragraph answers the main question by itself.
- [ ] The first 1–2 sentences of every H2 can be quoted alone. They name the entity and need no pronoun from the paragraph before.
- [ ] Each spec sentence carries its source in words («طبق سایت رسمی …») plus a link at first use.
- [ ] There is at least one comparison table where comparing. It uses `<thead>`/`<th>`, units in the header, and Latin codes in `<bdi>`.
- [ ] Steps are an `<ol>` and parallel options are a `<ul>`. Key terms are defined in one sentence when first used.
- [ ] FAQ answers start with the direct answer, run 1–3 sentences, and stand alone.
- [ ] No important fact exists only inside an image.
- [ ] Live page: the article text is in the HTML (WebFetch or `get_page_text` shows it) and there is no `noindex` in the robots meta.
  Do not edit robots.txt, Rank Math settings or llms.txt. If something blocks indexing, report it.

---

## 6. Schema (what we can actually do here)
- **Default: add no schema by hand.** Rank Math adds its JSON-LD `@graph` to every post automatically
  (normally Article/BlogPosting, WebPage, Organization/Person, BreadcrumbList). The type comes from Rank Math
  settings, and we may not change settings or schema post meta.
- **FAQPage:** do not add it. claude-blog says Google stopped showing FAQ rich results on 2026-05-07, so the markup
  gains nothing. Keep the visible FAQ for readers.
- **HowTo, Review, AggregateRating, Product markup in posts:** never. There are no real reviews, and a hand-made
  Product schema with price or availability would break the no-price rule.
- **A `<script type="application/ld+json">` inside post content** may be stripped. When the saving user lacks the
  `unfiltered_html` capability, WordPress runs content through kses, which removes `<script>`. On a single-site
  install, Administrators and Editors normally have that capability, but the `DISALLOW_UNFILTERED_HTML` constant or
  a security plugin can remove it. **Untested on lalehstore**, so don't rely on it. If a future README rule asks for
  in-content JSON-LD, first check `GET /wp-json/wp/v2/users/me?context=edit` → `capabilities.unfiltered_html`, then
  after saving confirm the script survived in `content.raw` and on the live page, and that it doesn't duplicate
  Rank Math's Article entity.
- **Live check after publishing:** view the source of the live URL. There must be one `application/ld+json` block
  whose Article/BlogPosting `headline` matches the title, with `datePublished` and `image` set to the featured
  image. Record what you saw. Do not try to fix schema yourself. Report it.

---

## 7. Fact-check pass (after the final draft and before publishing; repeat for any edit after publishing)
1. **List every claim:** every number (Persian ۰–۹ and Latin digits, including those in tables, alt text, FAQ and
   images), every spec, model code, warranty phrase, stock or availability statement, comparative or superlative
   («بیشترین»، «کم عمق ترین»، «تنها»، «جدیدترین»), and every replacement or discontinued claim.
2. **Re-open every source in this run.** Use WebFetch or the browser for manufacturer pages, and the Store API for
   products. Don't rely on memory or search snippets. If WebFetch returns a summary without the exact figure, open
   the page with `get_page_text`. If the figure still isn't visible, the claim is not verified.
3. **Match the context exactly:** the same model variant, the same unit (RMS vs Max/Peak), the same condition (the
   ohms, channels or bridge mode the power is rated at), and the same frequency or size units. Numbers must match the
   source exactly. Show any unit conversion. Don't round unless the source does.
4. **Mark each claim** in the review.md table as `VERIFIED` (with a quoted passage ≤ 25 words and the URL),
   `DERIVED` (with the formula and verified inputs) or `REMOVED`. Nothing stays `UNVERIFIED` in the published text.
5. **Products:** for every product link, run Store API `?search=<name>` or `/products/<id>`. It must be present
   (the Store API only returns published products), have `is_in_stock: true`, and its permalink must equal the href.
   Copy the warranty wording exactly from the product page.
6. **Banned-content scan** of the final HTML (any hit fails):
   `تومان|ریال|قیمت امروز|ارزان ?ترین|هم ?قیمت|نمایندگی رسمی|ما تست|تجربه ما|مشتریان ما`, any price-like digit
   followed by «هزار/میلیون», and ۱۴۰۵/1405 anywhere except a pillar title.
7. **Links:** fetch every href (internal from the site tab, external with WebFetch). It must return 200 and must not
   redirect to a homepage, search page or 404. Fix or remove any that fail.
8. **Images:** each one was rendered by sysgfx from the site's own photos, opened with Read, and checked: no
   overlap, no cut-off or reversed text, and the only numbers are verified ones.

---

## 8. Scoring rubric (100 points). Gate: publish only if the total is ≥ 85 AND there are zero P0 issues
| Category | Pts | What earns the points |
|---|---|---|
| **A. Accuracy & evidence** | 30 | Every number VERIFIED or DERIVED (12) · source named in the text at each spec (6) · names, codes and warranty match the product page (6) · superlatives tied to stated criteria, no hype (6) |
| **B. Reader value** | 25 | Matches the intent, first paragraph answers in 40–60 words (6) · ≥ 3 information gains vs SERP actually delivered (7) · decision help: table, if/then guidance, compatibility (6) · clean Persian, slop check passed, README conventions followed (6) |
| **C. On-page SEO & links** | 20 | Rank Math title, description, keyword and slug pass the section 4 table (6) · heading structure (3) · internal link set complete and correct (6) · manufacturer external links (2) · image alt and sizes (3) |
| **D. AI-citation readiness** | 15 | H2 openers can be quoted alone (5) · consistent entity naming with Latin codes (3) · extractable tables and lists, no facts only in images (4) · FAQ 4–6 with standalone answers (3) |
| **E. Technical & publishing** | 10 | Tables wrapped, text justified, no overflow at 390 px with rows aligned (4) · live page: images load, Rank Math meta saved, one Article schema, no noindex (4) · blog-log, calendar status and pillar «مقالات مرتبط» updated (2) |

Score strictly. Deduct for each defect. Don't round up. 85–100 = publish. Below 85 = fix and re-score, at most
3 rounds. If it still fails, mark the row «عقب افتاد» with the reason.

**P0 (any one blocks publishing, whatever the score):**
- a number not verified in this run's fact-check
- a link to a draft, private, out-of-stock or non-existent product
- an invented claim: a test, install, customer quote, review, statistic, sales rank, "official dealer", or
  first-hand experience
- any price figure or price phrase (section 7, step 6)
- a broken link (non-200, or a redirect to an unrelated page)
- also blocking, because README is binding: an AI-generated, stock or upscaled image; ۱۴۰۵ outside a pillar title;
  an exact cannibalization match with an existing post

---

## 9. review.md template (fill in every field, save as `blog/<NN>-<slug>/review.md`)
```markdown
# Review: <NN> <title>
Date: <YYYY-MM-DD> · Type: pillar|cluster|مستقل · Focus keyword: <kw> · Slug: <slug> · Words: <n>

## Pre-writing
- Cannibalization: <closest existing post(s) + verdict: different intent / differentiated how>
- Intent: <informational|comparison|buying-guide>
- SERP top 5 reviewed: <url1>, <url2>, ...
- Information gain (≥3): 1) ... 2) ... 3) ...

## Fact-check
| # | Claim (as written) | Section | Source URL | Evidence (≤25 words quoted) / formula | Status |
|---|---|---|---|---|---|
| 1 | | | | | VERIFIED/DERIVED/REMOVED |

Products linked: <id: name — published ✓ in stock ✓ permalink ✓ warranty text ✓>
Banned-content scan: <0 hits / list fixed>
Links checked: <n internal, n external, all 200>
Slop check: <phrases found and fixed>

## On-page
Title (<n> chars): ... · Meta (<n> chars): ... · Internal links: <n> · External: <n> · Images: <n>, alt ✓

## Score
| Category | Score | Max | Notes |
|---|---|---|---|
| A Accuracy & evidence | | 30 | |
| B Reader value | | 25 | |
| C On-page SEO & links | | 20 | |
| D AI-citation readiness | | 15 | |
| E Technical & publishing | | 10 | |
| **Total** | | **100** | |

P0 issues: <none | list>
Live checks: 390px overflow ✓ · images load ✓ · Rank Math meta ✓ · schema seen: <types> · noindex: no
DECISION: PUBLISH | BLOCKED (<reason>)
```
