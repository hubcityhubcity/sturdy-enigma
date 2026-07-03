import Link from 'next/link';
import { PublishingPackageClient } from './PublishingPackageClient';

export default function PublishingPackagePage({ searchParams }: { searchParams: { exportId?: string } }) {
  return <div className="container">
    <section className="hero">
      <div className="kicker">Publishing package</div>
      <h1>Everything you need to post the clip.</h1>
      <p>Choose a headline, refine the caption to match your voice, copy the hashtags, then complete the final platform checks.</p>
      <div className="button-row"><Link className="button secondary" href="/producer-mode">Back to Producer Mode</Link></div>
    </section>
    <PublishingPackageClient exportId={searchParams?.exportId} />
  </div>;
}
