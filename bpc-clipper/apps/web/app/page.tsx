import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">Titan Clipper AI</div>
        <h1>The AI production system for high-retention short-form content.</h1>
        <p>
          Upload a podcast or paste a source link. Titan finds the strongest moments,
          explains why they rank, and prepares clips for TikTok, YouTube Shorts, and Reels.
          Built first for Black Podcast Clips.
        </p>
        <div className="button-row">
          <Link className="button" href="/new-project">Start a project</Link>
          <Link className="button secondary" href="/producer-mode">Open Producer Mode</Link>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Upload or link</h2>
          <p>Start with a local file or a direct source link. The workflow is designed to stay simple and fast.</p>
        </div>
        <div className="card">
          <h2>Titan Brain</h2>
          <p>See ranked clip candidates with transparent Hook, Curiosity, Emotion, Debate, Story, and Retention signals.</p>
        </div>
        <div className="card">
          <h2>Producer Mode</h2>
          <p>Approve high-potential moments, generate export packages, and render vertical content from one workspace.</p>
        </div>
      </section>
    </div>
  );
}
