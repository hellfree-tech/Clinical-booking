import { useState } from 'react';
import { api, type Booking } from '../api';
import { Alert, errorMessage } from '../components/Alert';
import { BookingCard } from '../components/BookingCard';
import { useSlotIndex } from '../hooks';

export function MyBookingsPage() {
  const slots = useSlotIndex();
  const [email, setEmail] = useState('');
  const [searched, setSearched] = useState<string | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = async (forEmail: string, after: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const page = await api.listBookings(forEmail, after);
      setBookings((prev) => (after ? [...prev, ...page.bookings] : page.bookings));
      setCursor(page.next_cursor);
      setSearched(forEmail);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const search = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBookings([]);
    setCursor(null);
    fetchPage(email.trim(), null);
  };

  return (
    <section className="narrow">
      <form className="card search" onSubmit={search}>
        <h2>My bookings</h2>
        <label htmlFor="lookup-email" className="muted">
          Enter the email you booked with.
        </label>
        <div className="inline">
          <input id="lookup-email" type="email" inputMode="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          <button className="btn primary" disabled={loading || !email.trim()}>
            Search
          </button>
        </div>
      </form>

      {error && <Alert>{error}</Alert>}
      <p className="sr-only" role="status" aria-live="polite">
        {loading ? 'Loading bookings' : searched ? `${bookings.length} ${bookings.length === 1 ? 'booking' : 'bookings'} shown${cursor ? ', more available' : ''}` : ''}
      </p>
      {searched && !loading && bookings.length === 0 && !error && <p className="empty">No bookings found for {searched}.</p>}

      <div className="list">
        {bookings.map((b) => (
          <BookingCard
            key={b.id}
            booking={b}
            slot={slots[b.slot_id]}
            onChange={(updated) => setBookings((list) => list.map((x) => (x.id === updated.id ? updated : x)))}
          />
        ))}
      </div>

      {cursor && searched && (
        <button className="btn ghost block" onClick={() => fetchPage(searched, cursor)} disabled={loading}>
          {loading ? 'Loading…' : 'Show more'}
        </button>
      )}
    </section>
  );
}
