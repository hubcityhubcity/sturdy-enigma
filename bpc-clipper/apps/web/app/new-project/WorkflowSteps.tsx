'use client';

type WorkflowStep = {
  label: string;
  detail: string;
  state: 'complete' | 'active' | 'upcoming';
};

export function WorkflowSteps({ steps }: { steps: WorkflowStep[] }) {
  return <ol style={{ display: 'grid', gap: 10, padding: 0, margin: '20px 0 0', listStyle: 'none' }}>
    {steps.map((step, index) => <li key={step.label} className="card" style={{ margin: 0, opacity: step.state === 'upcoming' ? 0.62 : 1 }}>
      <strong>{step.state === 'complete' ? '✓' : `${index + 1}.`} {step.label}</strong>
      <p style={{ margin: '5px 0 0', opacity: 0.82 }}>{step.detail}</p>
    </li>)}
  </ol>;
}
