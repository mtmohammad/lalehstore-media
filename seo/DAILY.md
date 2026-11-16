# Daily on-site SEO job for lalehstore.com (brands: JBL, Infinity, Kenwood, Carozeria)

Owner decision (Mohammad, 1405-08-25): apply changes directly on the live site, every day, and report.
Plan doc: https://claude.ai/artifact/KDhraNvUJExkb63JmJgAn6 (section «برنامه برندها»).
Queue: `seo/queue.json` (categories, in-stock brand products, out-of-stock products). Log: `seo/log/<YYYY-MM-DD>.md`.
Rollback for descriptions = remove the ls-seo block (the rest is never touched). Backups before every change: `seo/backup/<YYYY-MM-DD>/<type>-<id>.json` (old description, short description,
Rank Math title/description/robots). The repo is public: never commit nonces, cookies or credentials.

## Facts Mohammad gave (binding)
- Lalehstore is the dealer (نمایندگی) of **JBL, Infinity, Kenwood and Carozeria**. «نمایندگی <brand>» may be used
  in titles and text for these four brands only. Never write «نمایندگی» for Pioneer, Premier/Booster, Sony or
  any other brand; remove it from their titles when a page is touched. Do not add «رسمی» unless he says so.
- The store sells head units (رادیو پخش), speakers, components, subwoofers, amplifiers. It does NOT sell
  head-unit panels or spare parts: never target «پنل/قطعات ضبط» queries.
- Most out-of-stock products will not come back.
- No price figures typed anywhere (prices change); «قیمت روز» wording is fine. No invented specs, tests, reviews,
  customer quotes or statistics. Specs only from the product's own attributes or the manufacturer page.
  If they disagree, leave the number out.

## Before starting
1. `TZ=Asia/Tehran date`; `git pull`.
2. Built-in browser: new tab on `https://lalehstore.com/wp-admin/edit.php`. Login page → stop, notify Mohammad
   (log in to WordPress in the Claude app browser), do nothing else.
3. Nonce: `await (await fetch('/wp-admin/admin-ajax.php?action=rest-nonce')).text()`.
4. Search Console MCP (`Google_Search_Console`, property `https://lalehstore.com/`) for the queries of each page
   you touch (last 90 days, `get_search_by_page_query`). Unavailable → continue without, say so in the log.

## Daily quota (in this order; stop early rather than rush)
A. **1 category** from `queue.categories` (status todo).
B. **4 in-stock brand products** from `queue.products`.
C. **25 out-of-stock products** from `queue.out_of_stock`.
D. Pending one-off items in `seo/2026-11-16/` (12 titles) on the first run that finds WordPress logged in.

### A. Category template (product_cat)
- Rank Math title ≤ 60: `خرید {نوع} {برند} اصل | نمایندگی {برند} در لاله استور` (shorten if needed; keep
  «{نوع} {برند}» at the start, e.g. «ساب ووفر جی بی ال»). Description ≤ 160 with the brand, type, گارانتی and
  «قیمت روز». Focus keyword = «{نوع} {برند}».
- Description (GET then PUT `/wp-json/wc/v3/products/categories/<id>` `{description}`): keep the existing text,
  add or replace one block between `<!-- ls-seo:start -->` and `<!-- ls-seo:end -->` containing:
  1. a 60–90 word opening paragraph (who it suits, with/without amp, sizes available, warranty name as on the
     product pages);
  2. a table of the IN-STOCK models only: model (Persian name + `<bdi dir="ltr">` code, linked), size, RMS (W),
     impedance (Ω), sensitivity (dB) from attributes; blog table styles from `blog/README.md`;
  3. «راهنمای انتخاب»: 2–3 links: the matching blog pillar (sub → /best-car-subwoofer/, amp → /best-car-amplifier/,
     component → /best-car-component/), the brand hub (see below), sibling brand categories (same brand, other type);
  4. FAQ (3–4): «{برند} ساخت کجاست» only if the answer is on an official page you opened or in the existing text,
     «گارانتی {برند} در لاله استور» (exact warranty text from product pages), «کدام مدل بدون آمپ…» (from the
     sensitivity/impedance rule in the component pillar). No invented facts.
- Brand hubs (link target «نمایندگی {برند}»): JBL → `/برچسب-محصولات/نمایندگی-جی-بی-ال-در-ایران/`,
  Kenwood → `/برچسب-محصولات/kenwood-agent/`, Infinity → `/برچسب-محصولات/نمایندگی-اینفینیتی-در-تهران/`,
  Carozeria → `/car-speaker/car-speaker-carozeria/` until a Carozeria hub exists. When a hub is touched, give it a
  links block to all four brand × type categories.

### B. In-stock product template
- Title ≤ 60: `{نام فارسی} {کد مدل} | مشخصات و قیمت روز` (+ « - نمایندگی {برند}» only if it fits).
  Description ≤ 160 with the main spec (RMS/size/ohm) and warranty. Focus keyword = the query with the most
  impressions for that page in Search Console, else «{نوع} {برند} {مدل}».
- Description (PUT `/wp-json/wc/v3/products/<id>` `{description}`): add the ls-seo block at the TOP: a spec table
  from the product attributes (only attributes that exist), one «مناسب برای» sentence derived from the specs, and
  links: its category (anchor = category keyword), the blog pillar, 1–2 in-stock siblings. Keep the rest as is.
- Every image `alt` = product name (POST `/wp-json/wp/v2/media/<id>` `{alt_text}`), only if empty.

### C. Out-of-stock policy (decided 1405-08-25: most will not return)
For each item first get its Search Console impressions for the last **12 months** (page filter equals URL):
1. **≥ 30 impressions in 12 months → keep indexed.** Title `مشخصات {نام} {کد} (مدل قدیمی) | لاله استور`, no
   «خرید/قیمت» in the title; add an ls-seo block at the top: «این مدل در حال حاضر موجود نیست.» + 1–3 in-stock
   replacements of the same type (brand first, then similar size/RMS) as linked cards. Keep the spec content.
2. **1–29 impressions → keep indexed**, add only the replacement block (no title change).
3. **0 impressions in 12 months → noindex, follow** via Rank Math (`rank_math_robots: ["noindex","follow"]`).
   Page stays live (no delete, no redirect, no draft), drops out of the sitemap automatically. Reversible.
Never delete or redirect a product. Never change stock status, price or the product name.

## After the quota
- Check every touched URL live: 200, new `<title>`, no `noindex` unless intended, table renders at 390 px.
- Update `queue.json` statuses, write `seo/log/<date>.md` (what changed, old → new title, ids), commit + push.
- Every Saturday also: compare last 7 days vs previous 7 days for the touched pages (GSC) in the log.
- Notify Mohammad only with a short Persian summary (counts + anything that needs him); silence is not allowed
  when WordPress was logged out.

## Drafts (checked 2026-11-16)
Old out-of-stock drafts already 301 to successor products: never publish them. New drafts are Mohammad's; publish only if he asks per product.
