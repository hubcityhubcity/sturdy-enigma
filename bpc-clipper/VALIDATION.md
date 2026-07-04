# Titan Clipper real-media validation gate

Do not deploy Titan Clipper to a staging or public server until this checklist passes with an owner-approved test video.

## Product truth rules

- A real upload must never silently receive canned demo transcript text.
- Transcript responses must identify the provider that produced them.
- A successful render must produce a real `.mp4`, not a placeholder text file.
- Titan Brain must score transcript text from the uploaded source.
- The creator must see actionable failure messages when a real transcription provider or FFmpeg is unavailable.

## Test source

Use a 60–180 second video you own or have explicit permission to process. It should contain:

- clear spoken English
- at least one complete opinion, story, or disagreement
- audible speech throughout most of the clip
- a standard MP4, MOV, or WebM container

Do not use private client material or copyrighted content you do not have permission to process.

## Required end-to-end pass

1. Start the API with a real transcription provider configured.
2. Upload the test source and confirm that validation reports real duration and codecs.
3. Generate a transcript and confirm its text visibly matches the source audio.
4. Generate candidates and verify Titan Brain explanations correspond to actual moments in the transcript.
5. Approve one candidate and render it.
6. Confirm the export video path ends in `.mp4` and the file opens as a playable vertical video.
7. Confirm SRT, VTT, metadata, and publishing package are present and refer to the same candidate.
8. Repeat with one intentional failure: no configured real transcription provider. The app must state the configuration problem and must not fabricate candidates.

## Exit criteria

The product-validation phase is complete only when the complete path succeeds with real media and the intentional failure produces a clear, honest error. Passing unit tests, Docker builds, or a generated demo file does not satisfy this gate.
