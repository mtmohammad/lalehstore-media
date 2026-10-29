# Blog articles for lalehstore.com (car audio pillar/cluster plan)

Plan + calendar (source of truth): Claude Docs doc **«پلن محتوای سیستم صوتی خودرو لاله استور»**
`https://claude.ai/artifact/BotMeumr88b9JZuPxJFjQy` (project id `57873fd4-affe-4e26-b9f9-7b192e298476`,
tab body node `ad2c9ce5-b34c`). Section «تقویم انتشار» = table of 32 articles: #, date, title, type
(پیلار / کلاستر / مستقل), pillar, main keyword, status dropdown (در صف / در حال نوشتن / منتشر شد / عقب افتاد).
Sections «ساختار پیلار و کلاستر» and «قواعد جلوگیری از جریمه تولید انبوه» are binding.

`blog-log.json` (this folder) = what was published: number, title, post id, URL, date, pillar, products linked,
images. Read it first; append after publishing. Pillar URLs are taken from here when writing clusters.

## One run = ONE article (never two)
1. Pick the lowest-numbered row whose status is «در صف» or «عقب افتاد» (skip a row only if its rule says so,
   e.g. #31/#32 need verified car-size data — then take the next row and say so in the report).
   If a cluster's pillar is not published yet, publish the pillar first (it is earlier in the calendar).
2. Research
   - Site data (no login needed): `https://lalehstore.com/wp-json/wc/store/v1/products?search=<q>&per_page=50`
     (name, permalink, price in Toman, is_in_stock, images, attributes). Category pages under
     `/car-speaker/ /component/ /car-subwoofer/ /amplifier/ /car-cd-player/` and brand sub-categories.
   - Existing site posts: `https://lalehstore.com/wp-json/wp/v2/posts?per_page=100&_fields=id,title,link`
     (avoid duplicate intent; link to related ones).
   - Specs: manufacturer pages (www2.jvckenwood.com, kenwood-electronics.co.uk, jbl.com, infinitysystems.com,
     pioneer press/spec pages) via WebFetch, plus the product attributes on the site. A number that is not
     confirmed is not written.
   - Competitors: Google top results for the main keyword (built-in browser, `hl=fa&gl=ir`), note what they
     cover and what they miss.
3. Write (Persian, Iranian buyer's words):
   - Pillar 2,500–3,500 words; cluster/مستقل 1,200–2,000 words.
   - Title from the calendar (may be tightened). Focus keyword in title, slug-friendly, first 100 words,
     one H2, meta description ≤ 160 chars. Year «۱۴۰۵» only in pillar titles.
   - First paragraph: the direct answer in 40–60 words.
   - H2/H3 sections, short paragraphs, one comparison table where comparing, «سؤالات متداول» 4–6 Q/A at the end.
   - Links: pillar ↔ cluster (anchor = pillar keyword), 1–2 sibling clusters, the matching category page
     (anchor = category keyword), 2–5 PUBLISHED in-stock products. Never link a draft or out-of-stock product.
   - Conventions: 3Way/2Way (first mention «سه راهه (3Way)»), «ساب ووفر» and «یقه ای» without ZWNJ,
     minimal ZWNJ (only «می‌» and «‌ها»), warranty text exactly as on the product page, prices in Toman with
     «قیمت امروز (<date>)» wording, no «نمایندگی رسمی» claims, Carozeria/Zenon are not amplifier speakers.
   - No invented tests, installs, customer quotes, reviews or statistics.
4. Images (all original, from the site's own high-quality product photos; never stock, never upscaled, never
   low-res): `tools/blog/sysgfx.py` (Playwright → WebP).
   - featured: `article_cover(title, kicker, [cut names], ac)` 1200×675
   - in text (2–4): `system_banner(...)` (how the products sit in the car — only technically compatible
     combinations), `compare_banner(...)`, `product_banner(...)`.
   - cutouts: download the product's main image (≥ 700 px) and cut it with `tools/blog/prodimg.py` (`cut()`),
     save as `<CUT_DIR>/<name>.png`. Brand colours are in sysgfx `BRAND`.
   - Open every rendered image with Read and fix overlaps, cut-off text, reversed mixed text.
   - Save the WebPs in `blog/<NN>-<slug>/` (NN = calendar number) and commit them.
5. Publish through the built-in browser (WordPress is logged in there; no passwords, no API keys):
   - open a new tab on `https://lalehstore.com/wp-admin/edit.php`; if it shows the login form, stop and report.
   - nonce: `await (await fetch('/wp-admin/admin-ajax.php?action=rest-nonce')).text()`
   - upload each image: base64 the WebP in the container, send it to the page in chunks
     (`window.__b = ''` then `window.__b += '<≤60 KB chunk>'` per call), then
     `fetch('/wp-json/wp/v2/media', {method:'POST', headers:{'X-WP-Nonce':n,'Content-Disposition':'attachment; filename="<name>.webp"','Content-Type':'image/webp'}, body: Uint8Array.from(atob(window.__b), c => c.charCodeAt(0))})`
     then POST `/wp-json/wp/v2/media/<id>` with `{alt_text, title}`.
   - post: POST `/wp-json/wp/v2/posts` `{title, slug, content, excerpt, status:'publish', categories:[1543], featured_media}`.
     Content = plain HTML (h2/h3/p/ul/table/img), images as
     `<figure class="wp-block-image size-full"><img src="…" alt="…" width=… height=… class="wp-image-<id>"/></figure>`.
   - Rank Math: POST `/wp-json/rankmath/v1/updateMeta` `{objectType:'post', objectID:<id>, meta:{rank_math_title, rank_math_description, rank_math_focus_keyword}}`.
   - If it is a cluster: append its link to the pillar post's «مقالات مرتبط» list (GET the pillar, add one `<li>`, POST it back).
   - Open the live URL and check it renders (images load, no broken links).
6. Log: append to `blog-log.json`, commit + push; set the calendar row's status to «منتشر شد» (or «عقب افتاد» with
   the reason as a doc comment on that row).
