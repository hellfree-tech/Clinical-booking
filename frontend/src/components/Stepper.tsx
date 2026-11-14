const STEPS = ['Choose a time', 'Your details', 'Confirmed'];

export function Stepper({ step }: { step: 1 | 2 | 3 }) {
  return (
    <ol className="stepper" aria-label="Booking progress">
      {STEPS.map((label, i) => {
        const n = i + 1;
        const state = n < step ? 'done' : n === step ? 'current' : 'todo';
        return (
          <li key={label} className={`step ${state}`} aria-current={state === 'current' ? 'step' : undefined}>
            <span className="step-num" aria-hidden="true">
              {state === 'done' ? '✓' : n}
            </span>
            <span className="step-label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
