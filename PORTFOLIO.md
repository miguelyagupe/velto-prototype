# velto. — portfolio evidence

> This is a curated source snapshot prepared on 20 November 2026. Earlier private commit and Actions history is not included.

**Status: work in progress.** velto. is an evidence-first workflow for producing videos from real experiments. It is a technical production prototype, not a finished autonomous video service or published channel.

## Problem and approach

The workflow is intended to reduce repetitive capture, editing, rendering and technical checking while preserving source evidence and human editorial judgment. The current repository implements a local FFmpeg rendering engine with timeline validation, proof references, narration and captions, and technical QA. Optional capture and narration scripts are separate from the renderer. See [README](README.md), [architecture](WORKFLOW_ARCHITECTURE.md) and [current editorial specification](docs/CURRENT_SPEC.md).

The owner conceived and directed the project and developed it with AI assistance. The repository and workflow history show implementation and iteration; they do not measure hours saved for a real creative team.

## Evidence in this snapshot

- The [75-second technical test report](episodes/EP001/AI_Workflow_Lab_Technical_Test_75s.qa.json) records a technical pass for a terminal-replay prototype. It also records `editorial_approved: false` and `publishable: false`.
- The [capture script](scripts/capture_demo.py), [renderer](awl/engine.py), [tests](tests/test_engine.py), and [technical QA report](episodes/EP001/AI_Workflow_Lab_Technical_Test_75s.qa.json) show the implemented workflow and its narrower validation. A remote capture test was observed during the audit, but its original run record and short-lived artifacts are not part of this snapshot.

## What remains

The target in [the current specification](docs/CURRENT_SPEC.md) is a genuine 5–7 minute episode plus two or three separately edited vertical videos, with a reviewed audiovisual master, thumbnail, rights record and approval before any public upload. The current technical prototype does not satisfy that target. The [episode status](episodes/EP001/PRODUCTION_STATUS.md) and [QA report](episodes/EP001/AI_Workflow_Lab_Technical_Test_75s.qa.json) record the narrower evidence.

A portfolio demonstration requires a durable, reviewed video file or recording that another person can open. Before sharing, inspect the whole playback for narration, claims, licenses and sensitive data. Do not label a technical pass as editorial approval.

## Suggested portfolio presentation

Show a short reviewed clip of the synthetic CSV experiment and explain the chain: source experiment → recorded evidence → timeline/proofs → render → technical QA → human review. Pair it with a small code excerpt from `awl/engine.py` or `scripts/capture_demo.py`, after checking the excerpt and its dependencies. State the current limits plainly.

This repository has no license file. Public access to the code does not grant permission to reuse it or any media assets. Review recordings and source assets before sharing them in an application.
