# lalehstore-media

Public media + tooling for the Instagram page **@lalehstoree** (lalehstore.com).
Files here are public on purpose: Metricool downloads them from
`https://raw.githubusercontent.com/mtmohammad/lalehstore-media/main/...` and keeps its own copy.

## Layout
- `tools/collage.py` — paper-collage stop-motion renderer (reel 1080x1920 or post video 1080x1350) from a JSON spec. See the docstring.
- `tools/story.py` — daily story (1080x1920 JPG) in the light brand style.
- `tools/fonts/` — Vazirmatn, Lalezar (Arabic subset, Persian-only text) and Quicksand (wordmark). All OFL.
- `posts/YYYY-MM-DD-slug/` — spec.json, product images, rendered `*.mp4` and `*-cover.jpg`.
- `stories/YYYY-MM-DD/` — spec.json, product image, `story.jpg`.
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
