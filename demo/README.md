# Original CSV demo

Open `index.html` in a browser. It performs all parsing and calculations locally;
there are no libraries, external fonts, accounts, analytics or network calls.
All numbers are synthetic test input. This is an original working application,
not a reconstruction of a commercial application or coding-agent interface.

The controlled recording run is `python scripts/capture_demo.py` from the repo
root. Requires Python Playwright, Chromium and Playwright's FFmpeg video helper.
The default run records about 78 seconds at 1920 × 1080 and verifies:

- Six input rows total 12,000, mean 2,000.
- Changing June from 3,000 to 4,500 produces total 13,500.
- A deliberately inserted non-numeric row is rejected; the preceding valid
  result remains displayed. This negative test is not an unexpected AI failure.
- Reset restores total 12,000.
- Descending order places June first without changing totals.
- Minimum sales 2,000 leaves three rows totaling 7,500.

`capture_events.json` contains observed page text and monotonic elapsed times,
not invented editing timestamps. `capture.webm` is the actual viewport video;
`capture_verified.png` is the final verified app screen. The recorder fails
if assertions fail. Do not claim recording or verification succeeded unless
these outputs exist and have been inspected.

Execution limitation observed in the child runner on 2026-11-08: Chromium
could not open its process singleton socket (`Operation not permitted`). The
attempt to request a less restricted executor was rejected by the runtime's
granular approval policy. This is a runner limitation, not an application result.
The parent runner may attempt the same command within its existing authority.
