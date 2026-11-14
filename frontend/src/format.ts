const dayFmt = new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
const timeFmt = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
const dayShortFmt = new Intl.DateTimeFormat(undefined, { weekday: 'short' });
const dayNumFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' });
const dateTimeFmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });

export const formatDay = (iso: string) => dayFmt.format(new Date(iso));
export const formatWeekdayShort = (iso: string) => dayShortFmt.format(new Date(iso));
export const formatDayMonth = (iso: string) => dayNumFmt.format(new Date(iso));
export const formatTime = (iso: string) => timeFmt.format(new Date(iso));
export const formatDateTime = (iso: string) => dateTimeFmt.format(new Date(iso));
export const dayKey = (iso: string) => {
  const d = new Date(iso);
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
};

export function timeZoneLabel(): string {
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const short = new Intl.DateTimeFormat(undefined, { timeZoneName: 'short' })
    .formatToParts(new Date())
    .find((p) => p.type === 'timeZoneName')?.value;
  return short && short !== zone ? `${zone.replace(/_/g, ' ')} (${short})` : zone.replace(/_/g, ' ');
}

export const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

const tones = new Map<string, number>();

/** Gives each provider a distinct colour (0–5), in alphabetical order. */
export function registerProviders(names: Iterable<string>) {
  [...new Set(names)].sort().forEach((n, i) => tones.set(n, i % 6));
}

export function providerTone(name: string): number {
  return tones.get(name) ?? 0;
}

export const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join('');
