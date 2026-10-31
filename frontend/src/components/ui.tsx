import type { ButtonHTMLAttributes, ReactNode } from 'react';

// Native semantic controls keep this shadcn-style component dependency-free.
export function Button({ variant = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' }) {
  return <button className={`button button-${variant} ${className}`} {...props} />;
}
export function Badge({ children, muted = false }: { children: ReactNode; muted?: boolean }) {
  return <span className={`badge ${muted ? 'badge-muted' : ''}`}>{children}</span>;
}
export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    home: <><path d="m3 10 9-7 9 7v10H3Z"/><path d="M9 20v-7h6v7"/></>,
    profile: <><circle cx="12" cy="8" r="4"/><path d="M4 21v-3c0-6 16-6 16 0v3"/></>,
    studio: <><path d="m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6Z"/></>,
    future: <><circle cx="12" cy="12" r="9"/><path d="m15 9-2 4-4 2 2-4Z"/></>,
    game: <><path d="M6 6h12l4 13-5 1-3-4h-4l-3 4-5-1Z"/><path d="M7 9v6m-3-3h6m6-2h.01m2 3h.01"/></>,
    timelines: <><circle cx="6" cy="4" r="2"/><circle cx="6" cy="20" r="2"/><circle cx="18" cy="6" r="2"/><path d="M6 6v12m0-4c8 0 12-1 12-6"/></>,
    compare: <><rect x="3" y="4" width="7" height="16" rx="2"/><rect x="14" y="4" width="7" height="16" rx="2"/></>,
    arrow: <path d="M4 12h15m-6-6 6 6-6 6"/>,
    leaf: <><path d="M4 21V4m0 12c10 0 16-4 16-13M4 21c10 0 16-4 16-13"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/></>,
    money: <><rect x="3" y="5" width="18" height="14" rx="3"/><circle cx="12" cy="12" r="3"/><path d="M6 12h.01m12 0h.01"/></>,
    globe: <><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/></>,
    back: <path d="m10 5-7 7 7 7m-7-7h18"/>,
    check: <path d="m5 12 4 4L19 6"/>,
    book: <><path d="M12 5c-4-3-8-1-9 0v15c3-2 6-2 9 0 3-2 6-2 9 0V5c-3-2-6-2-9 0Zm0 0v15"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.studio}</svg>;
}
export function PageHeading({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{children}</div>;
}
export function Landscape() {
  return <svg className="landscape" viewBox="0 0 600 400" fill="none" aria-hidden="true">
    <defs><linearGradient id="sky" x2="0" y2="1"><stop stopColor="#647963"/><stop offset="1" stopColor="#c4c6a2"/></linearGradient><linearGradient id="haze" x2="0" y2="1"><stop stopColor="#a2b296"/><stop offset="1" stopColor="#6f8974"/></linearGradient><linearGradient id="water" x2="1" y2="1"><stop stopColor="#7a9284"/><stop offset="1" stopColor="#314d43"/></linearGradient><clipPath id="arch"><path d="M80 400V230a220 220 0 0 1 440 0v240Z"/></clipPath></defs>
    <g clipPath="url(#arch)"><path fill="url(#sky)" d="M0 0h600v400H0z"/><circle cx="367" cy="105" r="37" fill="#e5debb" opacity=".85"/><path d="m0 229 115-107 87 78 99-69 143 86 156-66v249H0Z" fill="#7e927c"/><path d="m0 260 115-62 95 55 107-73 96 79 187-51v192H0Z" fill="url(#haze)"/><path d="M0 290c120-70 180-22 259-5s163-74 341-35v150H0Z" fill="#496b5a"/><path d="M300 264c-15 40 63 31 44 59-23 34-119 28-88 77h189c-110-43-52-44-62-70-9-23-62-22-55-63Z" fill="url(#water)"/><path d="M0 310c102-30 162 23 221 90H0Zm600-35c-80 11-125 52-138 125h138Z" fill="#294b3b"/>
    {[40,75,110,152,470,508,545,570].map((x, index) => <g key={x} transform={`translate(${x} ${265 + index % 3 * 20})`}><path d="m0-54-21 65h42Zm0-25-14 48h28Z" fill="#19392e"/><path d="M0 0v70" stroke="#19392e" strokeWidth="5"/></g>)}<path d="M358 110q7-8 14 0m8-9q7-8 14 0" stroke="#5d705b" strokeWidth="2"/>
    </g><path d="M80 400V230a220 220 0 0 1 440 0v240" stroke="#e5e2c5" opacity=".13"/><path d="M56 400V250a244 244 0 0 1 488 0v240" stroke="#e5e2c5" opacity=".08"/>
  </svg>;
}
