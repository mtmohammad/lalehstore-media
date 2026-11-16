// Run in a logged-in WordPress tab on lalehstore.com (browser JS). Applies Rank Math title/description
// from meta_plan.json. Rollback = same script with old_title_live/old_desc_live.
const plan = await (await fetch('https://raw.githubusercontent.com/mtmohammad/lalehstore-media/main/seo/2026-11-16/meta_plan.json')).json();
const n = await (await fetch('/wp-admin/admin-ajax.php?action=rest-nonce')).text();
const H = {'X-WP-Nonce': n, 'Content-Type': 'application/json'};
if (!plan.find(x => x.id)) throw new Error('no ids');
const tag = plan.find(x => !x.id && x.url.includes('برچسب-محصولات'));
if (tag) { const s = decodeURIComponent(tag.url).split('/').filter(Boolean).pop();
  const t = await (await fetch('/wp-json/wp/v2/product_tag?slug=' + encodeURIComponent(s), {headers: H})).json(); tag.id = t[0] && t[0].id; }
const out = [];
for (const x of plan) { if (!x.id) { out.push([x.url, 'no id']); continue; }
  const r = await fetch('/wp-json/rankmath/v1/updateMeta', {method: 'POST', headers: H,
    body: JSON.stringify({objectType: x.type, objectID: x.id, meta: {rank_math_title: x.title, rank_math_description: x.desc}})});
  out.push([x.id, r.status]); }
out
