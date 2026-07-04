import Link from 'next/link';
import { PublishingPackageClient } from './PublishingPackageClient';

export default async function PublishingPackagePage({ searchParams }: { searchParams: Promise<{ exportId?: string }> }) {
  const { exportId } = await searchParams;

  return <div className="container">
    <section className="hero">
      <div className="kicker">Publishing package</div>
      <h1>Everything you need to post the clip.</h1>
      <p>Choose a headline, refine the caption to match your voice, copy the hashtags, then complete the final platform checks.</p>
      <div className="button-row"><Link className="button secondary" href="/producer-mode">Back to Producer Mode</Link></div>
    </section>
    <PublishingPackageClient exportId={exportId} />
  </div>;
}
