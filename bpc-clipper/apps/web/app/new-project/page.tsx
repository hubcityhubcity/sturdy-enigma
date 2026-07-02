import Link from 'next/link';
import { NewProjectForm } from './NewProjectForm';

export default function NewProjectPage() {
  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">New project</div>
        <h1>Start with a file or a link.</h1>
        <p>
          Create a project, confirm permission, paste a direct media link, and queue the first mock
          candidate generation flow through the FastAPI backend.
        </p>
        <div className="button-row">
          <Link className="button secondary" href="/">Back to dashboard</Link>
        </div>
      </section>

      <NewProjectForm />
    </div>
  );
}
