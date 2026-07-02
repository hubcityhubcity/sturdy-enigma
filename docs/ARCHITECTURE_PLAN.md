# Architecture Plan

Black Podcast Clips AI Clipper will be a local-first web application that can later become a SaaS product.

## Stack

- Frontend: Next.js with TypeScript
- Backend: Python FastAPI
- Worker: Python background worker
- Queue: Redis
- Database: PostgreSQL
- Media tools: FFmpeg and FFprobe
- Storage: local filesystem first, cloud storage adapter later

## Main modules

1. Source intake
2. Job tracking
3. Media probing
4. Audio extraction
5. Transcription adapter
6. Speaker adapter
7. Clip candidate generator
8. Hub City Score engine
9. Producer Mode review dashboard
10. Caption engine
11. Render engine
12. Publishing pack generator
13. Analytics feedback layer

## Source intake

The first screen should allow either upload or link input.

Upload input supports common video and audio files.

Link input starts with direct downloadable media links for the MVP. Additional source providers should be added later through clean adapter classes.

## Job states

- queued
- validating_source
- importing_source
- probing_media
- extracting_audio
- transcribing
- segmenting
- scoring_candidates
- ready_for_review
- rendering
- complete
- failed

## Hub City Score

Every recommended clip should receive a transparent score with these factors:

- Hook strength
- Context clarity
- Payoff strength
- Emotion
- Debate tension
- Educational value
- Quotability
- Audio quality
- Visual suitability
- Caption readability
- Risk penalty

## MVP order

1. Project scaffold
2. API health check
3. Web dashboard shell
4. Upload or link project creation
5. Job status tracker
6. Mock transcript input
7. Candidate clip ranking
8. Producer Mode candidate list
9. Basic export placeholder

## Guardrails

- Do not commit secrets.
- Keep every clip tied to exact source timecodes.
- Keep editing user-approved.
- Make AI recommendations explainable.
- Build adapters so providers can be swapped later.