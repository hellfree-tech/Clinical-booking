import { ApiError } from '../api';

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 429) {
      return `Too many booking attempts. Please wait ${err.retryAfter ?? 60} seconds and try again.`;
    }
    if (err.status === 409) return 'Sorry, someone has just booked this slot. Please choose another time.';
    if (err.status === 404) return 'We could not find that. Please check and try again.';
    return capitalize(err.message);
  }
  return 'We could not reach the booking service. Check your connection and try again.';
}

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function Alert({ kind = 'error', children }: { kind?: 'error' | 'info'; children: React.ReactNode }) {
  return (
    <div className={`alert ${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  );
}
