# Black Podcast Clips AI Clipper PRD

## Vision
Black Podcast Clips AI Clipper turns long-form podcast and interview content into polished, high-retention short-form clips for TikTok, YouTube Shorts, Instagram Reels, and future platforms.

This is not only a clipping utility. It is the production operating system for Black Podcast Clips and the foundation for a future SaaS product.

## Core user
Primary user: Hub City / Black Podcast Clips operator.

Secondary future users:
- Podcast editors
- Short-form content creators
- Media pages
- Podcast networks
- Agencies
- Independent commentators

## Core promise
Upload a video or paste a link. The system imports the source, finds the strongest moments, explains why each moment matters, lets the user edit everything, then exports platform-ready clips with captions, hooks, thumbnails, metadata, and analytics tracking.

## MVP workflow
1. User starts a new project.
2. User chooses upload or URL ingest.
3. User confirms they have rights/permission to process the source.
4. System imports media and extracts metadata.
5. System extracts audio and generates transcript.
6. System segments transcript into candidate moments.
7. System ranks clips using the Hub City Score.
8. User reviews top candidates in Producer Mode.
9. User edits in/out points, hook, caption style, crop, and preset.
10. System renders 9:16 MP4, SRT/VTT, thumbnail frame, and publishing metadata.
11. User stores/export the final publishing pack.

## Key principles
- Quality over quantity.
- No fake quotes or fake context.
- Every AI recommendation must explain itself.
- The user must control the final edit.
- The system should learn from Black Podcast Clips performance over time.
- Seamless upload/link workflow is mandatory.
- Respect copyright, platform rules, privacy, and source permissions.

## Must-have MVP features

### Project creation
- New project name
- Source type: upload or URL
- Rights-attestation checkbox
- Source metadata preview
- Job status timeline

### Upload ingest
- Accept MP4, MOV, WebM, MKV, M4V
- Accept audio-only MP3, WAV, M4A when practical
- Validate media with FFmpeg probe
- Store original source separately from derived assets

### URL ingest
- Paste URL
- Validate URL
- Fetch available metadata
- Import/download only when lawful and technically allowed
- Begin with direct downloadable URLs for MVP
- Add provider adapters later
- Show clear failure reasons for unsupported/private/restricted links

### Transcription
- Word-level timestamps
- Sentence/phrase grouping
- Speaker diarization adapter interface
- Confidence scores
- Manual correction path

### Producer Mode
Candidate categories:
- Top clips overall
- Strongest hooks
- Debate heat
- Story mode
- Educational moments
- Emotional moments
- Quote-worthy moments
- Clips likely to generate comments

### Hub City Score
Transparent scoring dimensions:
- Hook strength
- Context clarity
- Payoff
- Emotion/intensity
- Debate/tension
- Educational value
- Quotability
- Audio clarity
- Visual suitability
- Caption readability
- Risk/context-loss flags

### Editing
- In/out trim
- Conservative jump-cut suggestions
- Silence removal preview
- Caption editor
- Hook text options
- Crop/reframe controls
- BPC presets

### Export
- 1080x1920 H.264 MP4
- SRT
- VTT
- JSON metadata
- CSV export log
- Thumbnail frame
- Title/caption/hashtag suggestions

## BPC presets

### BPC Clean Editorial
Premium, clean, readable captions with minimal movement.

### BPC Debate Heat
Faster pacing, speaker labels, emphasis captions, stronger hooks.

### BPC Story Mode
Smoother pacing, narrative setup, emotional readability.

### BPC Commentary / Reaction
Host/reaction panel-ready layout for future Hub City commentary clips.

## Future features
- Direct publishing integrations
- Team accounts
- SaaS subscriptions
- Analytics import from TikTok/YouTube/Instagram
- Audience DNA Engine
- Auto thumbnail designer
- Caption template marketplace
- Multi-language support
- Brand kits for other creators

## MVP acceptance criteria
A user can upload a test video or paste a direct media URL, process it, view ranked clip candidates, select one, edit its hook/caption/timing, apply a BPC preset, and export a vertical video publishing pack.