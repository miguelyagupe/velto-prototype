# Dedicated capture worker — prepared, not deployed

Target: isolated hosted Linux container/VM, no personal desktop dependency. Dockerfile installs real Chromium, FFmpeg, fonts and code. Build/run on an authorized host with supported browser sandbox/runtime. This Docker image has not been built or deployed in the restricted current session; do not label it tested.

Browser recorder must use the Playwright-installed browser if no system chromium exists. Media persists on a mounted /app/episodes volume. Use fresh browser contexts, synthetic/approved data only; inject credentials only for specific approved tasks, never into captures/logs. Start with the synthetic demo and a 75-second quality test before any account workflow.

No provider or paid compute has been provisioned. Deployment requires a confirmed host and budget. Avoid running a paid GitHub Actions render implicitly. Keep scheduled jobs off until capture, voice, render, QA and artifacts survive a full remote run.

Acceptance: `python scripts/capture_demo.py`, actual 1920x1080 capture with readable interface, event log and no hidden sensitive data; then produce/QA and export standalone 9:16 edits. Terminal replay is a fallback engineering test, not acceptance for graphical capture.
