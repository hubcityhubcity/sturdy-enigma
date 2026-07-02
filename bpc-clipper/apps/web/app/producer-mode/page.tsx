const candidates = [
  {
    score: 88,
    category: 'Debate Heat',
    title: 'Strong opening debate moment',
    time: '02:00 - 02:44',
    excerpt: 'This clip starts with immediate tension, gives enough context, and lands with a clear payoff.',
    reason: 'Strong hook, clear contrast, clean payoff, low context risk.'
  },
  {
    score: 84,
    category: 'Strong Hook',
    title: 'Question-first cold open',
    time: '07:22 - 08:09',
    excerpt: 'The speaker opens with a direct question that makes the viewer want the answer.',
    reason: 'High first-two-second retention potential.'
  },
  {
    score: 81,
    category: 'Story Mode',
    title: 'Personal story with a lesson',
    time: '12:18 - 13:05',
    excerpt: 'A clear story arc with setup, emotion, and a practical takeaway.',
    reason: 'Good narrative structure and emotional clarity.'
  }
];

export default function ProducerModePage() {
  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">Producer Mode</div>
        <h1>Your strongest clips, ranked like a producer.</h1>
        <p>
          This dashboard will become the main review workspace. The first version shows mock candidates
          using the same structure the backend already returns.
        </p>
      </section>

      <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
        {candidates.map((candidate) => (
          <article className="card candidate" key={candidate.title}>
            <div>
              <div className="score">{candidate.score}</div>
              <div className="badge">{candidate.category}</div>
            </div>
            <div>
              <h2>{candidate.title}</h2>
              <p><strong>Source time:</strong> {candidate.time}</p>
              <p>{candidate.excerpt}</p>
              <p><strong>Why it ranked:</strong> {candidate.reason}</p>
            </div>
            <div className="button-row">
              <a className="button" href="#">Approve</a>
              <a className="button secondary" href="#">Edit</a>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
