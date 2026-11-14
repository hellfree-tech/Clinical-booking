import { useState } from 'react';
import { api, type Booking } from '../api';
import { Alert, errorMessage } from '../components/Alert';
import { BookingCard } from '../components/BookingCard';
import { useSlotIndex } from '../hooks';

export function FindBookingPage() {
  const slots = useSlotIndex();
  const [id, setId] = useState('');
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const find = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    setBooking(null);
    try {
      setBooking(await api.getBooking(id.trim()));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="narrow">
      <form className="card search" onSubmit={find}>
        <h2>Find a booking</h2>
        <label htmlFor="lookup-ref" className="muted">
          Enter the booking reference from your confirmation.
        </label>
        <div className="inline">
          <input id="lookup-ref" placeholder="b_…" autoComplete="off" spellCheck={false} value={id} onChange={(e) => setId(e.target.value)} />
          <button className="btn primary" disabled={loading || !id.trim()}>
            {loading ? 'Searching…' : 'Find'}
          </button>
        </div>
      </form>
      {error && <Alert>{error}</Alert>}
      {booking && <BookingCard booking={booking} slot={slots[booking.slot_id]} onChange={setBooking} />}
    </section>
  );
}
