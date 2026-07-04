'use client';

import { useEffect, useState } from 'react';
import { getPublishingPackage, PublishingPackage } from '../../lib/api';

function CopyButton({ value, label = 'Copy' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return <button className="button secondary" type="button" onClick={copy}>{copied ? 'Copied' : label}</button>;
}

export function PublishingPackageClient({ exportId }: { exportId?: string }) {
  const [packageData, setPackageData] = useState<PublishingPackage | null>(null);
  const [status, setStatus] = useState(exportId ? 'Loading publishing package...' : 'Open this page from a completed export.');

  useEffect(() => {
    if (!exportId) return;
    let cancelled = false;
    getPublishingPackage(exportId).then((result) => {
      if (cancelled) return;
      setPackageData(result);
      setStatus('Ready to publish. Personalize these suggestions before posting.');
    }).catch((error: unknown) => {
      if (!cancelled) setStatus(error instanceof Error ? error.message : 'Unable to load the publishing package.');
    });
    return () => { cancelled = true; };
  }, [exportId]);

  if (!packageData) return <section className="card" style={{ marginTop: 24 }}><p>{status}</p></section>;
  const hashtagLine = packageData.hashtags.join(' ');

  return <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
    <article className="card">
      <h2>Recommended post</h2>
      <p><strong>Title:</strong> {packageData.recommended_title}</p>
      <p style={{ whiteSpace: 'pre-wrap' }}>{packageData.recommended_caption}</p>
      <div className="button-row"><CopyButton value={packageData.recommended_title} label="Copy title" /><CopyButton value={packageData.recommended_caption} label="Copy caption" /></div>
    </article>

    <article className="card">
      <h2>Title options</h2>
      {packageData.title_options.map((title) => <div key={title} className="card" style={{ margin: '10px 0 0' }}><strong>{title}</strong><div className="button-row" style={{ marginTop: 8 }}><CopyButton value={title} /></div></div>)}
    </article>

    <article className="card">
      <h2>Caption options</h2>
      {packageData.caption_options.map((caption) => <div key={caption} className="card" style={{ margin: '10px 0 0' }}><p style={{ whiteSpace: 'pre-wrap', marginTop: 0 }}>{caption}</p><div className="button-row"><CopyButton value={caption} label="Copy caption" /></div></div>)}
    </article>

    <article className="card">
      <h2>Hashtags</h2>
      <p>{hashtagLine}</p>
      <CopyButton value={hashtagLine} label="Copy hashtags" />
    </article>

    <article className="card">
      <h2>Final posting checklist</h2>
      <ol style={{ paddingLeft: 20, marginBottom: 0 }}>{packageData.publishing_checklist.map((item) => <li key={item} style={{ marginTop: 8 }}>{item}</li>)}</ol>
    </article>
  </section>;
}
