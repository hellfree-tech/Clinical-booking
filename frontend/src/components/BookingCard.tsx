import { useEffect, useId, useRef, useState } from 'react';
import { api, type Booking, type Slot } from '../api';
import { formatDateTime, formatDay, formatTime, initials, providerTone } from '../format';
import { Alert, errorMessage } from './Alert';

export function StatusBadge({ status }: { status: Booking['status'] }) {
  return <span className={`badge ${status}`}>{status === 'confirmed' ? 'Confirmed' : 'Cancelled'}</span>;
}

export function BookingCard({
  booking,
  slot,
  onChange,
}: {
  booking: Booking;
  slot?: Slot;
  onChange?: (b: Booking) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const titleId = useId();
  const keepRef = useRef<HTMLButtonElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (confirming) keepRef.current?.focus();
  }, [confirming]);

  const close = () => {
    setConfirming(false);
    requestAnimationFrame(() => cancelRef.current?.focus());
  };

  const cancel = async () => {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.cancelBooking(booking.id);
      setConfirming(false);
      onChange?.(updated);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const when = slot ? `${formatDay(slot.start)}, ${formatTime(slot.start)}` : `slot ${booking.slot_id}`;

  return (
    <article className="card booking" aria-labelledby={titleId}>
      <div className="booking-head">
        <span className={`avatar tone-${slot ? providerTone(slot.provider) : 0}`} aria-hidden="true">
          {initials(booking.name)}
        </span>
        <div className="booking-title">
          {slot ? (
            <>
              <h3 id={titleId}>{formatDay(slot.start)}</h3>
              <p className="muted">
                {formatTime(slot.start)}–{formatTime(slot.end)} with {slot.provider}
              </p>
            </>
          ) : (
            <h3 id={titleId}>Slot {booking.slot_id}</h3>
          )}
        </div>
        <StatusBadge status={booking.status} />
      </div>
      <dl className="details">
        <dt>Reference</dt>
        <dd>
          <code>{booking.id}</code>
        </dd>
        <dt>Name</dt>
        <dd>{booking.name}</dd>
        <dt>Email</dt>
        <dd>{booking.email}</dd>
        <dt>Booked</dt>
        <dd>{formatDateTime(booking.created_at)}</dd>
      </dl>

      {error && <Alert>{error}</Alert>}

      {booking.status === 'confirmed' && onChange && !confirming && (
        <button ref={cancelRef} className="btn ghost danger" onClick={() => setConfirming(true)}>
          Cancel appointment
        </button>
      )}

      {confirming && (
        <div
          className="confirm-cancel"
          role="group"
          aria-label="Confirm cancellation"
          onKeyDown={(e) => e.key === 'Escape' && !busy && close()}
        >
          <p>Cancel your appointment on {when}? The time will be released for someone else.</p>
          <div className="actions">
            <button className="btn danger-solid" onClick={cancel} disabled={busy}>
              {busy ? 'Cancelling…' : 'Yes, cancel it'}
            </button>
            <button ref={keepRef} className="btn ghost" onClick={close} disabled={busy}>
              Keep appointment
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
