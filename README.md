# lalehstore-media

Public media + tooling for the Instagram page **@lalehstoree** (lalehstore.com).
Files here are public on purpose: Metricool downloads them from
`https://raw.githubusercontent.com/mtmohammad/lalehstore-media/main/...` and keeps its own copy.

## Layout
- `tools/studio.py` — CURRENT style (since 2026-10-31): light story look + cinematic motion + 3D product models from the store photos (MiDaS depth, downloaded once to ~/.cache/lalehstore; dome fallback). Same spec as cinema.py. `python3 -I studio.py spec.json out.mp4 [--preview DIR]`.
- `tools/highlights.py` — Instagram highlight covers (see highlights/README.md).
- `tools/cinema.py` — previous style: cinematic paper-collage (smooth 30 fps motion, kinetic type, paper wipes) + `tools/music.py` royalty-free fallback music bed. Same spec as collage.py plus `music.mood`.
- `tools/collage.py` — older paper-collage stop-motion renderer (its parts are reused by cinema.py) (reel 1080x1920 or post video 1080x1350) from a JSON spec. See the docstring.
- `tools/story.py` — daily story (1080x1920 JPG) in the light brand style.
- `tools/fonts/` — Vazirmatn, Lalezar (Arabic subset, Persian-only text) and Quicksand (wordmark). All OFL.
- `posts/YYYY-MM-DD-slug/` — spec.json, product images, rendered `*.mp4` and `*-cover.jpg`.
- `stories/YYYY-MM-DD/` — spec.json, product image, `story.jpg`.
- `blog/` — weekly blog articles for lalehstore.com (car-audio pillar/cluster plan): workflow in `blog/README.md`, log in `blog/blog-log.json`.
- `tools/blog/` — `sysgfx.py` (article cover, product/system/comparison banners via Playwright) and `prodimg.py` (product cutouts).
- `content-log.json` — everything already published/scheduled. Read before choosing; append after scheduling.

## Run
```
pip install --break-system-packages pillow numpy scipy   # usually preinstalled
cd tools
python3 -I collage.py ../posts/<folder>/spec.json ../posts/<folder>/<name>.mp4 --preview /tmp/prev   # preview frames
python3 -I collage.py ../posts/<folder>/spec.json ../posts/<folder>/<name>.mp4                        # render
python3 -I story.py ../stories/<date>/spec.json ../stories/<date>/story.jpg
```
Requires ffmpeg.
