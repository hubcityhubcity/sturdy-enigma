import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">Black Podcast Clips AI</div>
        <h1>The AI producer for high-retention podcast clips.</h1>
        <p>
          Upload a podcast or paste a source link. BPC Clipper finds the strongest moments,
          scores them with the Hub City Score, and prepares clips for TikTok, YouTube Shorts,
          and Reels.
        </p>
        <div className="button-row">
          <Link className="button" href="/new-project">Start a project</Link>
          <Link className="button secondary" href="/producer-mode">View Producer Mode</Link>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Upload or link</h2>
          <p>Start with a local file or a direct source link. The workflow is built to feel simple and fast.</p>
        </div>
        <div className="card">
          <h2>Producer Mode</h2>
          <p>See ranked clip candidates by hook strength, context, payoff, debate heat, and story value.</p>
        </div>
        <div className="card">
          <h2>Export pack</h2>
          <p>Prepare vertical video, subtitles, titles, captions, hashtags, and source metadata.</p>
        </div>
      </section>
    </div>
  );
}
