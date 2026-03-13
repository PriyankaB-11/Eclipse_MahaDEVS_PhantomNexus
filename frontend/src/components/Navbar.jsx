import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/devices', label: 'Devices' },
  { to: '/network', label: 'Network Map' },
];

export default function Navbar() {
  return (
    <header className="topbar sticky top-0 z-20">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.35em] text-[var(--accent-primary)]">Phantom Nexus</p>
          <h1 className="font-display text-2xl font-semibold">IoT Recruitment Risk Command</h1>
          <p className="mt-1 text-xs soft-label">Behavioral trust intelligence for connected devices</p>
        </div>
        <nav className="nav-shell flex flex-wrap items-center gap-2 rounded-full p-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `nav-link rounded-full px-4 py-2 text-sm font-medium transition ${
                  isActive ? 'nav-link-active' : ''
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
