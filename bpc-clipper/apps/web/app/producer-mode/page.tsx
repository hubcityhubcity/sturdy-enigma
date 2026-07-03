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
        <h1>Your strongest clips, ranked like a producer.</h1>
        <p>
          Review candidates from a project when the API is running, or fall back to demo candidates
          so the workspace remains usable during local development.
        </p>
        <div className="button-row">
          <Link className="button secondary" href="/new-project">New project</Link>
          <Link className="button secondary" href="/">Dashboard</Link>
        </div>
      </section>

      <ProducerModeClient projectId={projectId} />
      <ChatEvidenceImporter projectId={projectId} />
      <SourceCandidateBrowser projectId={projectId} />
    </div>
  );
}
