import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import { api, ApiError, newIdempotencyKey, type Booking, type Slot } from '../api';
import { Alert, errorMessage } from '../components/Alert';
import { Stepper } from '../components/Stepper';
import { dayKey, formatDay, formatDayMonth, formatTime, formatWeekdayShort, prefersReducedMotion, providerTone, registerProviders, timeZoneLabel } from '../format';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const slotLabel = (s: Slot) =>
  `${formatDay(s.start)}, ${formatTime(s.start)} to ${formatTime(s.end)} with ${s.provider}${s.available ? '' : ', already booked'}`;

export function BookPage({ onBooked }: { onBooked: (b: Booking, slot: Slot) => void }) {
  const [slots, setSlots] = useState<Slot[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>('');
  const [selected, setSelected] = useState<Slot | null>(null);
  const [dayChoice, setDayChoice] = useState<string | null>(null);
  const formCardRef = useRef<HTMLElement>(null);
  const tz = useMemo(timeZoneLabel, []);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const list = await api.listSlots();
      registerProviders(list.map((s) => s.provider));
      setSlots(list);
    } catch (err) {
      setLoadError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const providers = useMemo(() => [...new Set((slots ?? []).map((s) => s.provider))].sort(), [slots]);

  const days = useMemo(() => {
    const now = Date.now();
    const upcoming = (slots ?? []).filter((s) => new Date(s.start).getTime() > now && (!provider || s.provider === provider));
    const groups = new Map<string, Slot[]>();
    for (const s of upcoming) {
      const k = dayKey(s.start);
      groups.set(k, [...(groups.get(k) ?? []), s]);
    }
    return [...groups.values()];
  }, [slots, provider]);

  const activeDay =
    days.find((d) => dayKey(d[0].start) === dayChoice) ?? days.find((d) => d.some((s) => s.available)) ?? days[0];

  // On mobile the form is below the slots; scroll to it once rendered.
  useEffect(() => {
    const card = formCardRef.current;
    if (!selected || !card) return;
    if (card.getBoundingClientRect().top > window.innerHeight * 0.6) {
      card.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
    }
  }, [selected]);

  const upcomingCount = days.reduce((n, d) => n + d.filter((s) => s.available).length, 0);

  return (
    <>
    <Stepper step={selected ? 2 : 1} />
    <div className="book-layout">
      <section className="card" aria-labelledby="choose-heading">
        <div className="section-head">
          <h2 id="choose-heading">1. Choose a time</h2>
          <button className="btn ghost small" onClick={load}>
            Refresh
          </button>
        </div>
        <p className="tz-note">Times are shown in {tz}.</p>

        {providers.length > 1 && (
          <div className="chips" role="group" aria-label="Filter by provider">
            {['', ...providers].map((p) => (
              <button key={p || 'all'} className={provider === p ? 'chip active' : 'chip'} aria-pressed={provider === p} onClick={() => setProvider(p)}>
                {p && <span className={`dot tone-${providerTone(p)}`} aria-hidden="true" />}
                {p || 'All providers'}
              </button>
            ))}
          </div>
        )}

        <p className="sr-only" role="status" aria-live="polite">
          {slots ? `${upcomingCount} available ${upcomingCount === 1 ? 'time' : 'times'}` : 'Loading available times'}
        </p>

        {loadError && <Alert>{loadError}</Alert>}
        {!slots && !loadError && (
          <p className="muted" aria-hidden="true">
            Loading available times…
          </p>
        )}
        {slots && days.length === 0 && <p className="empty">No upcoming appointments right now. Please check back later.</p>}

        {days.length > 0 && (
          <div className="day-strip" role="group" aria-label="Choose a day">
            {days.map((d) => {
              const free = d.filter((s) => s.available).length;
              const active = d === activeDay;
              return (
                <button
                  key={dayKey(d[0].start)}
                  className={`day-chip${active ? ' active' : ''}`}
                  aria-pressed={active}
                  aria-label={`${formatDay(d[0].start)}, ${free} ${free === 1 ? 'time' : 'times'} available`}
                  disabled={free === 0}
                  onClick={() => setDayChoice(dayKey(d[0].start))}
                >
                  <span className="day-chip-weekday">{formatWeekdayShort(d[0].start)}</span>
                  <span className="day-chip-date">{formatDayMonth(d[0].start)}</span>
                  <span className="day-chip-count">{free} free</span>
                </button>
              );
            })}
          </div>
        )}

        {activeDay && (
          <div className="day">
            <h3 id="active-day-heading">{formatDay(activeDay[0].start)}</h3>
            <div className="slot-grid" role="group" aria-labelledby="active-day-heading">
              {activeDay.map((s) => (
                <button
                  key={s.id}
                  className={`slot${selected?.id === s.id ? ' selected' : ''}`}
                  disabled={!s.available}
                  onClick={() => setSelected(s)}
                  aria-pressed={selected?.id === s.id}
                  aria-label={slotLabel(s)}
                >
                  <span className="slot-time">{formatTime(s.start)}</span>
                  <span className="slot-provider">
                    <span className={`dot tone-${providerTone(s.provider)}`} aria-hidden="true" />
                    {s.available ? s.provider : 'Booked'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      <section ref={formCardRef} className="card form-card" aria-labelledby="details-heading">
        <h2 id="details-heading">2. Your details</h2>
        {selected ? (
          <BookingForm
            key={selected.id}
            slot={selected}
            onBooked={(b) => onBooked(b, selected)}
            onSlotTaken={() => {
              setSelected(null);
              load();
            }}
          />
        ) : (
          <p className="muted">Pick a time to continue.</p>
        )}
      </section>
    </div>
    </>
  );
}

function BookingForm({ slot, onBooked, onSlotTaken }: { slot: Slot; onBooked: (b: Booking) => void; onSlotTaken: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const ids = { name: useId(), nameErr: useId(), email: useId(), emailErr: useId() };
  // Same key while details are unchanged, so resubmits can't double-book.
  const idem = useRef<{ body: string; key: string } | null>(null);

  useEffect(() => {
    nameRef.current?.focus({ preventScroll: true });
  }, []);

  const nameError = touched && !name.trim() ? 'Enter your name.' : null;
  const emailError = touched && !EMAIL_RE.test(email.trim()) ? 'Enter a valid email address, like name@example.com.' : null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!name.trim()) return nameRef.current?.focus();
    if (!EMAIL_RE.test(email.trim())) return emailRef.current?.focus();

    const body = { slot_id: slot.id, name: name.trim(), email: email.trim() };
    const bodyKey = JSON.stringify(body);
    if (idem.current?.body !== bodyKey) idem.current = { body: bodyKey, key: newIdempotencyKey() };

    setSubmitting(true);
    setError(null);
    try {
      onBooked(await api.createBooking(body, idem.current.key));
    } catch (err) {
      setError(errorMessage(err));
      if (err instanceof ApiError && err.status === 409) setTimeout(onSlotTaken, 2500);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit} noValidate aria-describedby="selected-slot">
      <div className="selected-slot" id="selected-slot">
        <strong>{formatDay(slot.start)}</strong>
        <span>
          {formatTime(slot.start)}–{formatTime(slot.end)} · {slot.provider}
        </span>
      </div>

      <div className="field">
        <label htmlFor={ids.name}>Full name</label>
        <input
          id={ids.name}
          ref={nameRef}
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
          required
          aria-invalid={!!nameError}
          aria-describedby={nameError ? ids.nameErr : undefined}
          maxLength={200}
        />
        {nameError && (
          <small id={ids.nameErr} className="field-error">
            {nameError}
          </small>
        )}
      </div>

      <div className="field">
        <label htmlFor={ids.email}>Email</label>
        <input
          id={ids.email}
          ref={emailRef}
          type="email"
          inputMode="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
          aria-invalid={!!emailError}
          aria-describedby={emailError ? ids.emailErr : undefined}
          maxLength={254}
        />
        {emailError && (
          <small id={ids.emailErr} className="field-error">
            {emailError}
          </small>
        )}
      </div>

      {error && <Alert>{error}</Alert>}

      <button className="btn primary block" type="submit" disabled={submitting} aria-busy={submitting}>
        {submitting ? 'Booking…' : 'Book appointment'}
      </button>
    </form>
  );
}
