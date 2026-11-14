// Forwards /api/* to the API, adding X-API-Key server-side. Env: API_URL, API_KEY.
const FORWARDED_REQUEST_HEADERS = ['content-type', 'idempotency-key'];
const FORWARDED_RESPONSE_HEADERS = ['content-type', 'retry-after'];
const ALLOWED_PATH = /^(slots|bookings(\/[A-Za-z0-9_-]+)?)$/;

export default async function handler(req, res) {
  const { path = '', ...query } = req.query;
  const cleanPath = String(Array.isArray(path) ? path.join('/') : path).replace(/^\/+|\/+$/g, '');

  // /reset stays private.
  if (!ALLOWED_PATH.test(cleanPath)) {
    res.status(404).json({ error: 'not found' });
    return;
  }

  const url = new URL(`${process.env.API_URL.replace(/\/+$/, '')}/${cleanPath}`);
  for (const [k, v] of Object.entries(query)) {
    for (const item of [].concat(v)) url.searchParams.append(k, item);
  }

  const headers = { 'X-API-Key': process.env.API_KEY };
  for (const h of FORWARDED_REQUEST_HEADERS) if (req.headers[h]) headers[h] = req.headers[h];

  const hasBody = req.method !== 'GET' && req.method !== 'HEAD' && req.body !== undefined;
  try {
    const upstream = await fetch(url, {
      method: req.method,
      headers,
      body: hasBody ? (typeof req.body === 'string' ? req.body : JSON.stringify(req.body)) : undefined,
    });
    for (const h of FORWARDED_RESPONSE_HEADERS) {
      const v = upstream.headers.get(h);
      if (v) res.setHeader(h, v);
    }
    res.status(upstream.status).send(await upstream.text());
  } catch {
    res.status(502).json({ error: 'booking service is unreachable' });
  }
}
