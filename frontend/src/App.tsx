import { useState } from 'react';
import type { Booking, Slot } from './api';
import { BookPage } from './pages/BookPage';
import { Confirmation } from './pages/Confirmation';
import { FindBookingPage } from './pages/FindBookingPage';
import { MyBookingsPage } from './pages/MyBookingsPage';

type Tab = 'book' | 'mine' | 'find';

const TABS: [Tab, string][] = [
  ['book', 'Book'],
  ['mine', 'My bookings'],
  ['find', 'Find a booking'],
];

export default function App() {
  const [tab, setTab] = useState<Tab>('book');
  const [confirmed, setConfirmed] = useState<{ booking: Booking; slot?: Slot } | null>(null);

  const go = (t: Tab) => {
    setConfirmed(null);
    setTab(t);
  };

  return (
    <div className="app">
      <header className="masthead">
        <div className="masthead-inner">
        <div className="brand">
          <span className="logo" aria-hidden="true">
            +
          </span>
          <div>
            <h1>Clinic booking</h1>
            <p>Choose a time that suits you and we'll confirm it straight away.</p>
          </div>
        </div>
        <nav aria-label="Sections">
          <div className="tabs">
            {TABS.map(([key, label]) => {
              const current = tab === key && !confirmed;
              return (
                <button
                  key={key}
                  className={current ? 'tab active' : 'tab'}
                  aria-current={current ? 'page' : undefined}
                  onClick={() => go(key)}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </nav>
        </div>
      </header>

      <main id="main" className="shell">
        {confirmed ? (
          <Confirmation booking={confirmed.booking} slot={confirmed.slot} onDone={() => go('book')} />
        ) : tab === 'book' ? (
          <BookPage onBooked={(booking, slot) => setConfirmed({ booking, slot })} />
        ) : tab === 'mine' ? (
          <MyBookingsPage />
        ) : (
          <FindBookingPage />
        )}
      </main>
    </div>
  );
}
