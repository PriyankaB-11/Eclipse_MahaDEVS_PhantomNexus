import { Link } from 'react-router-dom';

const features = [
  {
    title: 'Adaptive Trust Scoring',
    description:
      'Track each device with a continuous trust score that reacts to drift, anomaly bursts, and peer behavior shifts in near real time.',
  },
  {
    title: 'Botnet Recruitment Detection',
    description:
      'Surface early-stage compromise signals before full command-and-control lock-in by correlating behavior vectors and outbound patterns.',
  },
  {
    title: 'Graph-Powered Threat Context',
    description:
      'Visualize blast radius and suspicious relationships through a dynamic network map built for SOC triage workflows.',
  },
  {
    title: 'Device-Level Investigation',
    description:
      'Open deep technical investigations with anomaly decomposition, peer correlations, trust gating state, and actionable mitigation clues.',
  },
  {
    title: 'SOC-Ready Explainability',
    description:
      'Convert model output into clear, structured narratives so analysts can move from alert to decision with less friction.',
  },
  {
    title: 'Exportable Security Reports',
    description:
      'Generate downloadable PDF reports per device to document evidence, risk rationale, and recommended response steps.',
  },
];

export default function Landing() {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl border border-[var(--hero-border)] bg-[var(--hero-bg)] px-6 py-10 shadow-[var(--hero-shadow)] sm:px-10 sm:py-14">
        <div className="pointer-events-none absolute -top-28 right-[-120px] h-80 w-80 rounded-full bg-[var(--accent-primary)]/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 left-[-100px] h-72 w-72 rounded-full bg-orange-400/10 blur-3xl" />

        <p className="font-mono text-xs uppercase tracking-[0.34em] text-[var(--accent-primary)]">Phantom Nexus</p>
        <h1 className="mt-4 max-w-4xl font-display text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl">
          Stop IoT botnet recruitment before it becomes network-wide compromise.
        </h1>
        <p className="mt-5 max-w-3xl text-base soft-label sm:text-lg">
          A unified detection and investigation platform for security teams: identify suspicious devices early,
          understand why risk is rising, and respond with confidence.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link className="btn-accent rounded-xl px-5 py-3 text-sm font-semibold" to="/dashboard">
            Enter Command Dashboard
          </Link>
          <Link className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10" to="/devices">
            Explore Devices
          </Link>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.34em] text-[var(--accent-primary)]">What We Offer</p>
            <h2 className="mt-2 font-display text-3xl font-semibold">Features built for modern SOC operations</h2>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {features.map((feature) => (
            <article key={feature.title} className="surface-card rounded-3xl p-6 transition duration-300 hover:-translate-y-1 hover:border-[var(--accent-primary)]/40">
              <h3 className="font-display text-xl font-semibold text-white">{feature.title}</h3>
              <p className="mt-3 text-sm soft-label">{feature.description}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
