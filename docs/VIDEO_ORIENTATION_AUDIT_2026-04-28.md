# Video Orientation Audit (2026-04-28)

> **Resolved in the current pipeline:** uploads with display rotation are now
> autorotated into physically upright pixels before OpenCV/MediaPipe processing,
> and their rotation metadata is removed. Browser fallback transcoding uses the
> same ffmpeg autorotation behavior and a versioned cache. When external ffmpeg
> tools are unavailable, the OpenCV decode path explicitly enables metadata
> autorotation and sizes the overlay from the corrected frame. Regression coverage
> is in `tests/test_video_orientation.py`, including the 180° mobile case.

## Scope
This document records the original audit findings for the persistent rotated-overlay issue.

## What the current pipeline does

1. **Upload bytes are saved directly with no normalization**.
   - `safe_tmp_video()` writes the uploaded file as-is to temp storage.
2. **The analyzer stages that same source and runs the OpenCV/MediaPipe pipeline**.
3. **Overlay frames are rendered using `cv2.VideoCapture` and `cv2.VideoWriter` dimensions**.
4. **UI playback re-encodes overlay to MP4 and attempts to clear rotation metadata**.

## Audit findings

### 1) Ingest does not normalize camera orientation metadata
The upload path stores the original file as-is, with no ffmpeg orientation normalization at ingest time. This means phone camera files can carry rotation metadata into downstream steps unchanged.

### 2) OpenCV-based extraction/render path uses decoded raster orientation, not intended display orientation
Overlay generation (`extract_all.process_video`) reads dimensions and frames from OpenCV capture and writes output with those dimensions. There is no rotation-metadata-aware correction step before drawing/writing.

This is the key mismatch with mobile recordings:
- iOS/Android clips often rely on metadata (display matrix / rotate tag) for upright playback.
- OpenCV paths commonly process the raw raster orientation.
- Result: overlay video can be encoded sideways relative to what the user saw in camera roll.

### 3) UI normalization tries metadata reset, but not geometric correction
The UI transcode command includes `-metadata:s:v:0 rotate=0` and `-vf format=yuv420p,setsar=1`.

Important implications:
- This clears a common rotate tag, but does **not** apply a physical transpose/rotate to pixels.
- If pixels are already sideways from the OpenCV path, they stay sideways.
- Depending on source/container and ffmpeg behavior, display matrix side data can still produce inconsistent player behavior.

### 4) Multiple encode hops increase orientation ambiguity
The pipeline can perform several stages:
- extraction overlay encode
- offline overlay rerender
- annotation overlay pass
- UI playback transcode

None of these stages establishes one canonical orientation contract (e.g., “all overlays must be physically upright, no rotation metadata”). So different players can render differently.

## Why this presents as “app rotates videos 90°”
From user perspective:
- Original phone video appears upright in gallery/browser player (metadata honored).
- Pipeline output appears sideways in app because processing path is based on raw raster orientation.

So the observed rotation is real at product level, even if technically it is a metadata-vs-raster orientation mismatch.

## Evidence locations in code
- Upload write-through with no orientation normalization.
- OpenCV capture/writer overlay rendering path.
- UI transcode sets `rotate=0` but does not rotate pixels.
- Overlay transcode helpers in pipeline stages do not enforce a canonical orientation policy.

## Resolution implemented
1. The canonical rule is now: **all pipeline outputs must be physically upright with no rotation metadata**.
2. The pipeline probes rotation near ingest and delegates signed display-matrix handling to ffmpeg autorotation before stripping metadata.
3. Downstream OpenCV explicitly enables metadata autorotation as a runtime fallback and derives output dimensions from the corrected decoded frame.
4. Regression tests cover signed display matrices, 180° mobile input, OpenCV fallback, zero-copy desktop input, and browser fallback transcoding.
5. Orientation diagnostics record rotation and dimensions before and after normalization.

