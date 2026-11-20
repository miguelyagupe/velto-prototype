> Curated portfolio source snapshot (20 November 2026), without the private development history. [Evidence and current limits](PORTFOLIO.md).

> Current editorial specification: [docs/CURRENT_SPEC.md](docs/CURRENT_SPEC.md). Series: I Tried Making AI Do...; 5–7 minutes, 2–3 Shorts. Preserve current engine.

# AI Workflow Lab — production engine MVP

A local, evidence-first FFmpeg renderer. This package does not claim to autonomously research, narrate, capture or publish a complete episode. Those upstream capabilities and episode status are recorded separately in `docs/` and `episodes/`.

## Requirements

Python 3.11+, FFmpeg and ffprobe on PATH; FFmpeg needs libx264, AAC, libass and drawtext. No Python dependencies, API credentials or paid services are required by the rendering engine. Optional narration/capture tools have their own dependencies.

```sh
python -m unittest discover -s tests -v
python -m awl validate episodes/EP001/timeline.json
python -m awl render episodes/EP001/timeline.json --output episodes/EP001/export.mp4
python -m awl qa episodes/EP001/export.mp4 --timeline episodes/EP001/timeline.json
```

Paths are examples; use the supplied episode timeline filename. Run from repository root, or `pip install -e .` then use `awl`.

## Timeline contract

All paths resolve relative to the timeline JSON, so complete episode folders can be moved together. `in`, `out` and `destination` use seconds. Destinations must be contiguous, matching the accumulated scene durations. Narration duration must match within 0.3 seconds. Source video intervals and crops must stay within media bounds. Missing assets, missing proof, missing licenses, invalid subtitle timing and mismatched narration fail explicitly.

```json
{
  "version": 1,
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "narration": "voice.wav",
  "captions": "captions.srt",
  "proofs": "proofs.json",
  "burn_captions": true,
  "scenes": [{
    "source": "capture.mp4",
    "in": 0,
    "out": 10,
    "destination": 0,
    "license": "Original capture; rights reviewed separately",
    "proof_id": "p1",
    "crop": {"x": 0, "y": 0, "width": 1920, "height": 1080},
    "overlay": "Optional concise title"
  }]
}
```

Proofs are a JSON object with a `proofs` list, each entry containing unique `id`, a real local `path`, and a `claim`. The engine verifies references and hashes; it cannot establish whether a claim is true or a license is valid. Human/editorial review remains mandatory. Source URL, capture date and licensing details belong in the episode asset manifest.

For vertical output set width 1080, height 1920 and author a separate timeline, crop choices and narration/subtitles. The renderer never silently derives or approves Shorts from a landscape crop. Crops act as static highlight zooms; split at an actual event to change focus. Scenes use cuts, not decorative transitions. Titles are optional support for actual footage.

## Outputs and QA

Each render creates MP4, SRT and `.render.json` with exact commands, elapsed render time, input hashes and output hash. FFmpeg temporary files are removed after rendering. Re-running to the same output deliberately replaces the previous output; keep versioned filenames to retain comparisons.

The `.qa.json` checks H.264/yuv420p, AAC/48 kHz, 30 fps, expected geometry/duration, full decode, black intervals, silence intervals, integrated loudness and true peak. A technical pass is **not** editorial approval. `publishable` and `editorial_approved` stay false. Full playback, narration quality/synchronization, secrets, claim evidence, rights and vertical legibility require a recorded review. Silence is flagged for review; black intervals fail the technical gate. Intentional black sections must be reviewed rather than silently ignored.

The source JSON, narration, SRT and assets are the editable project; no CapCut compatibility is claimed. There is no upload code, no paid API invocation and no automatic publication. The engine does not fabricate missing content or pad a short video into a long episode.
