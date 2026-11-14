export interface Slot {
  id: string;
  provider: string;
  start: string;
  end: string;
  available: boolean;
}

export interface Booking {
  id: string;
  slot_id: string;
  name: string;
  email: string;
  status: 'confirmed' | 'cancelled';
  created_at: string;
}

export interface BookingPage {
  bookings: Booking[];
  next_cursor: string | null;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly retryAfter?: number,
  ) {
    super(message);
  }
}

// Same-origin; the proxy adds the API key.
const BASE = '/api';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init.headers },
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const message = (data as { error?: string } | null)?.error ?? `Request failed (${res.status})`;
    const retryAfter = res.headers.get('Retry-After');
    throw new ApiError(res.status, message, retryAfter ? Number(retryAfter) : undefined);
  }
  return data as T;
}

export const api = {
  listSlots: (provider?: string) =>
    request<{ slots: Slot[] }>(`/slots${provider ? `?provider=${encodeURIComponent(provider)}` : ''}`).then((r) => r.slots),

  getBooking: (id: string) => request<Booking>(`/bookings/${encodeURIComponent(id)}`),

  cancelBooking: (id: string) => request<Booking>(`/bookings/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  listBookings: (email: string, cursor?: string | null, limit = 5) => {
    const q = new URLSearchParams({ email, limit: String(limit) });
    if (cursor) q.set('cursor', cursor);
    return request<BookingPage>(`/bookings?${q}`);
  },

  /** Retries reuse the Idempotency-Key, so they can't double-book. */
  async createBooking(body: { slot_id: string; name: string; email: string }, idempotencyKey: string): Promise<Booking> {
    const attempts = 3;
    for (let i = 1; ; i++) {
      try {
        return await request<Booking>('/bookings', {
          method: 'POST',
          headers: { 'Idempotency-Key': idempotencyKey },
          body: JSON.stringify(body),
        });
      } catch (err) {
        const retriable = !(err instanceof ApiError) || err.status >= 500;
        if (!retriable || i >= attempts) throw err;
        await new Promise((r) => setTimeout(r, 400 * i));
      }
    }
  },
};

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
