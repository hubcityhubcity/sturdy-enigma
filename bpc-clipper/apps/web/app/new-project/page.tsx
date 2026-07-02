import Link from 'next/link';

export default function NewProjectPage() {
  return (
    <div className="container">
      <section className="hero">
        <div className="kicker">New project</div>
        <h1>Start with a file or a link.</h1>
        <p>
          This first version is a UI shell. The next pass will connect this form to the FastAPI project
          and source endpoints.
        </p>
      </section>

      <section className="card" style={{ marginTop: 24 }}>
        <h2>Project details</h2>
        <form className="form">
          <label>
            Project name
            <input className="input" placeholder="Example: Earn Your Leisure episode clips" />
          </label>

          <label>
            Source type
            <select className="select" defaultValue="link">
              <option value="link">Paste a link</option>
              <option value="upload">Upload a file</option>
            </select>
          </label>

          <label>
            Video link
            <input className="input" placeholder="https://example.com/video.mp4" />
          </label>

          <label>
            Upload file
            <input className="input" type="file" />
          </label>

          <label>
            <input type="checkbox" /> I confirm I have permission to process this source.
          </label>

          <div className="button-row">
            <Link className="button" href="/producer-mode">Create mock project</Link>
            <Link className="button secondary" href="/">Back</Link>
          </div>
        </form>
      </section>
    </div>
  );
}
