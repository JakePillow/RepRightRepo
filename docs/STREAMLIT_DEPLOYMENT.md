# Streamlit Deployment Plan

## What can ship immediately

This repo can be deployed to **Streamlit Community Cloud** with:

- app entrypoint: `ui/streamlit_app.py`
- Python dependencies from `requirements.txt`
- Linux system dependency from `packages.txt`
- project config from `.streamlit/config.toml`
- secrets pasted into Community Cloud Advanced Settings

This is enough to make the app reachable from a browser on desktop, tablet, and modern phones.

Official references used:

- Streamlit Community Cloud deploy docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Dependency and `packages.txt` docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- File organization docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- Secrets docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Upload limit docs: https://docs.streamlit.io/knowledge-base/deploy/increase-file-uploader-limit-streamlit-cloud
- Supported browsers docs: https://docs.streamlit.io/knowledge-base/using-streamlit/supported-browsers
- `st.file_uploader` behavior docs: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- Uploaded files live in RAM docs: https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted
- Static/generated file persistence note: https://docs.streamlit.io/develop/concepts/configuration/serving-static-files

## Immediate deploy checklist

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create an app from that repo.
3. Select `ui/streamlit_app.py` as the entrypoint.
4. In Advanced Settings, choose **Python 3.10**.
   - This matters because the pinned `mediapipe==0.10.21` stack in this repo is currently aligned with the local Python 3.10 environment.
5. Paste secrets equivalent to:

```toml
OPENAI_API_KEY = "..."
REPRIGHT_COACH_MODE = "auto"
REPRIGHT_COACH_MODEL = "gpt-4.1-mini"
REPRIGHT_COACH_TIMEOUT_S = "30"
```

6. Deploy and verify:
   - upload works
   - analysis runs
   - overlay renders
   - coach response returns

## Best viva / thesis demo settings

For a live thesis demo, the safest setup is:

```toml
REPRIGHT_DEMO_MODE = "true"
REPRIGHT_DEMO_FORCE_STUB = "true"
REPRIGHT_COACH_MODE = "auto"
```

What this does:

- keeps the real video analysis pipeline active
- makes coach responses deterministic and network-independent
- shows a visible demo-mode reminder in the UI

This is the best tradeoff for a viva because the analysis still demonstrates your core system, while the coaching layer becomes much less likely to fail due to API/network issues.

## What the current deploy will do on iPhone / iOS

For iPhone users, the app will work as a **web app in Safari**. Streamlit officially supports the latest Safari versions, and Safari is the browser engine that matters on iOS.

Expected iPhone flow:

1. User records a lift in the iPhone Camera app.
2. User opens the Streamlit app URL in Safari.
3. User taps the upload control.
4. User selects a clip from **Photos** or **Files**.
5. The browser uploads the video to the Streamlit backend.
6. The backend processes the clip and returns the analysis UI.

Important iOS reality:

- The reliable path is **record first, upload second**.
- Do not assume a custom in-browser live video recorder.
- Large 4K or long-duration iPhone videos will be the main failure mode because uploads are bandwidth-heavy and `st.file_uploader` stores the uploaded file in backend RAM before processing.
- Short clips are the right product assumption for mobile.

## Confirmed repo constraints that still need restructuring

The app is deployable now, but the current architecture is not yet ideal for a public, durable, multi-user product.

### 1. Local file persistence is not durable

Current repo behavior:

- `ui/chat_store.py` writes threads to `data/chats`
- `repright/analyser.py` stages uploads into `data/uploads`
- `scripts/pipeline.py` writes generated artifacts into `data/processed/runs`

Why this matters on Community Cloud:

- generated files are not guaranteed to persist across app restarts or sessions
- local disk is not the right source of truth for public multi-user history

Required restructure:

- move chat/thread persistence out of local JSON files into a real store:
  - simplest: Supabase Postgres
  - acceptable: SQLite is not recommended for public multi-user cloud use here
- move uploaded clips and generated overlays/analysis JSON into object storage:
  - S3
  - Cloudflare R2
  - Supabase Storage

### 2. Analysis currently runs synchronously inside the Streamlit process

Current repo behavior:

- `ui/services.py` runs analysis directly in the request path
- `scripts/pipeline.py` performs the heavy video work in-process

Why this matters:

- one user’s video job can block resources for others
- mobile users are more likely to hit timeouts or appear “stuck”
- Community Cloud is fine for light apps, but heavy synchronous video inference is the biggest scaling risk

Best restructure:

- keep Streamlit as the UI
- move video analysis into a separate worker or API service
- have Streamlit submit a job and poll status

Recommended target split:

- **Streamlit app**: upload UI, session state, results rendering, chat UX
- **analysis worker/API**: MediaPipe/OpenCV/overlay pipeline
- **object storage**: uploads and artifacts
- **database**: threads, job status, artifact references, metadata

### 3. Chat history currently depends on local files plus local artifacts

Current repo behavior:

- old chat sessions expect local analysis JSON and overlay paths to still exist

Why this matters:

- once the app restarts or files disappear, restored sessions degrade

Required restructure:

- persist only durable references in thread records
- analysis JSON should live in object storage or DB-backed storage
- overlay URLs should be durable signed URLs or storage paths

### 4. Mobile support needs product constraints, not just hosting

For iOS specifically, public success depends on:

- short uploads
- clear guidance on clip length
- visible upload-size expectations
- no reliance on desktop-only affordances

Recommended product constraints:

- target clips under 30 to 45 seconds
- recommend 1080p rather than 4K
- surface a user-facing note that phone users should upload from Photos/Files after recording

## Best deployment path

### Phase 1: Fastest viable public demo

Use Streamlit Community Cloud directly with the current codebase plus the deploy files added here.

Good for:

- thesis demos
- advisor review
- limited-user sharing
- validating UI and basic phone access

Not good for:

- durable session history
- high concurrency
- lots of public traffic
- large mobile uploads

### Phase 2: Best production-style architecture

Use a hybrid deployment:

- **Streamlit Community Cloud** for the frontend
- **external inference worker/API** for analysis
- **managed DB** for chats, threads, metadata
- **object storage** for videos and overlays

This is the best path if the goal is “anyone on nearly any device can run it” with fewer reliability problems.

## Concrete code changes still recommended after this commit

These are the next restructures I would recommend implementing in the repo:

1. Introduce a storage abstraction for:
   - thread records
   - analysis JSON
   - overlay/video artifacts

2. Replace direct `Path("data/...")` persistence with backends:
   - `LocalStorageBackend` for local dev
   - `CloudStorageBackend` for deployed use

3. Move analysis invocation behind a service boundary:
   - local mode calls the pipeline directly
   - cloud mode posts a job to a worker service

4. Persist only durable artifact references in thread state.

5. Add mobile-facing upload guidance in the UI:
   - recommended clip length
   - preferred resolution
   - iPhone upload instructions

## Bottom line

Yes, this app can be deployed on Streamlit and opened from iPhones.

But two statements are both true:

- **Community Cloud is enough for a shareable browser-based demo now.**
- **A durable public version needs storage and analysis to be split out of the Streamlit app process.**

That is the key architectural change to treat as non-optional if the goal is broad public use rather than a demo deployment.
