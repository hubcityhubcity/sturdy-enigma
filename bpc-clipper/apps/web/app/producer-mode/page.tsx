import Link from 'next/link';
import { ChatEvidenceImporter } from './ChatEvidenceImporter';
import { ProducerModeClient } from './ProducerModeClient';
import { SourceCandidateBrowser } from './SourceCandidateBrowser';

export default function ProducerModePage({ searchParams }: { searchParams: { projectId?: string } }) {
  const projectId = searchParams?.projectId;

  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">Producer Mode</div>
        <h1>Turn one long source into clips you can actually publish.</h1>
        <p>
          Pick a source, let Titan identify the strongest moments, review the reasoning, then approve the
          winner for a vertical export with captions and metadata. You stay in control of the final choice.
        </p>
        <div className="button-row">
          <Link className="button secondary" href="/new-project">Start another project</Link>
          <Link className="button secondary" href="/">Dashboard</Link>
        </div>
      </section>

      {!projectId && <section className="card" style={{ marginTop: 24 }}>
        <h2>Start with a project</h2>
        <p>Create a project first so Titan has a source to analyze. Demo candidates remain available below for a quick look at the review experience.</p>
        <Link className="button" href="/new-project">Create a project</Link>
      </section>}

      {projectId && <section className="card" style={{ marginTop: 24 }}>
        <h2>Your production path</h2>
        <div className="grid">
          <div><strong>1. Analyze</strong><p>Choose the source and find meaningful moments.</p></div>
          <div><strong>2. Review</strong><p>Check Titan Brain’s score, evidence, and risk flags.</p></div>
          <div><strong>3. Export</strong><p>Approve the best candidate and render the publishing package.</p></div>
        </div>
      </section>}

      <ProducerModeClient projectId={projectId} />
      {projectId && <ChatEvidenceImporter projectId={projectId} />}
      {projectId && <SourceCandidateBrowser projectId={projectId} />}
    </div>
  );
}
