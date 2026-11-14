import { useEffect, useRef, useState } from 'react';
import type { Booking, Slot } from '../api';
import { BookingCard } from '../components/BookingCard';
import { Stepper } from '../components/Stepper';

export function Confirmation({ booking: initial, slot, onDone }: { booking: Booking; slot?: Slot; onDone: () => void }) {
  const [booking, setBooking] = useState(initial);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const cancelled = booking.status === 'cancelled';

  useEffect(() => {
    headingRef.current?.focus();
    window.scrollTo({ top: 0 });
  }, [cancelled]);

  return (
    <div className="confirmation">
      {!cancelled && <Stepper step={3} />}
      <div className={`hero ${cancelled ? 'cancelled' : ''}`}>
        <div className="hero-icon" aria-hidden="true">
          {cancelled ? '×' : '✓'}
        </div>
        <h2 ref={headingRef} tabIndex={-1}>
          {cancelled ? 'Your appointment has been cancelled' : "You're booked in"}
        </h2>
        <p>
          {cancelled
            ? 'The slot has been released.'
            : 'Keep your booking reference. You can use it to look up or cancel your appointment.'}
        </p>
      </div>
      <BookingCard booking={booking} slot={slot} onChange={setBooking} />
      <button className="btn primary" onClick={onDone}>
        Book another appointment
      </button>
    </div>
  );
}
