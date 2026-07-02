# Data Model Map

## Purpose
This document defines the first data entities for the Black Podcast Clips AI Clipper MVP.

## Core entities

### User
Represents the operator or future SaaS user.

Fields:
- id
- email
- display name
- role
- created time

### Project
Represents one clipping session.

Fields:
- id
- user id
- project name
- status
- created time
- updated time

### Source
Represents the original media.

Fields:
- id
- project id
- source type
- original file name
- original link
- title
- duration
- width
- height
- media details
- thumbnail path
- storage path
- permission confirmed time

### Job
Represents long-running processing work.

Fields:
- id
- project id
- source id
- job type
- stage
- progress
- message
- status
- retry count
- error details
- started time
- completed time

### Transcript
Represents the full source transcript.

Fields:
- id
- project id
- source id
- language
- provider
- confidence
- created time

### Transcript Segment
Represents a sentence or phrase block.

Fields:
- id
- transcript id
- speaker id
- start time
- end time
- text
- confidence

### Transcript Word
Represents word-level timing.

Fields:
- id
- transcript id
- segment id
- speaker id
- start time
- end time
- word text
- confidence
- corrected text

### Speaker
Represents a detected or user-labeled speaker.

Fields:
- id
- project id
- label
- display name

### Candidate Clip
Represents one recommended clip moment.

Fields:
- id
- project id
- source id
- start time
- end time
- title
- excerpt
- score
- explanation
- category
- status

### Score Breakdown
Represents why a candidate was recommended.

Score factors:
- hook strength
- context clarity
- payoff strength
- emotion
- debate tension
- educational value
- quotability
- audio quality
- visual suitability
- caption readability
- risk penalty
- risk flags

### Edit Timeline
Represents the user-approved editable version of a candidate clip.

Fields:
- id
- candidate clip id
- project id
- start time
- end time
- hook text
- caption style
- crop mode
- preset id
- edit settings

### Preset
Represents a reusable Black Podcast Clips editing style.

Fields:
- id
- name
- description
- caption settings
- crop settings
- hook settings
- render settings
- system preset flag

### Export
Represents a rendered final output.

Fields:
- id
- project id
- edit timeline id
- status
- video path
- subtitle paths
- thumbnail path
- metadata path
- format
- created time
- completed time

### Analytics Metric
Represents performance data after publishing.

Fields:
- id
- export id
- platform
- views
- watch time
- completion rate
- likes
- comments
- shares
- saves
- follows
- collected time
- notes

## Important design rule
Analytics should connect to the final export, not only to the original candidate clip. The same moment can perform differently depending on hook, captions, pacing, and platform.