import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, Zap, Shield, Star, Ticket, Music, Mic, Trophy } from 'lucide-react';
import './Home.css';

const CATEGORIES = [
  { icon: Music, label: 'Concerts', color: 'var(--clr-accent)', count: '240+' },
  { icon: Mic, label: 'Comedy Shows', color: 'var(--clr-emerald)', count: '80+' },
  { icon: Trophy, label: 'Sports', color: 'var(--clr-gold)', count: '150+' },
  { icon: Star, label: 'Theater', color: 'var(--clr-rose)', count: '60+' },
];

const FEATURES = [
  {
    icon: Zap,
    title: 'Fast Checkout',
    desc: 'Reserve seats in a few steps with live inventory and Cashfree-powered payments.',
  },
  {
    icon: Shield,
    title: 'Secure Payments',
    desc: 'Industry-grade encryption and PCI-compliant payment processing keeps your data safe.',
  },
  {
    icon: Ticket,
    title: 'QR Tickets',
    desc: 'Receive QR-code tickets instantly via email. No printing needed — just show and go.',
  },
  {
    icon: Calendar,
    title: 'Easy Management',
    desc: 'View, manage, and cancel bookings from your personal dashboard anytime.',
  },
];

export default function Home() {
  return (
    <main className="home page-enter" id="main-content">
      {/* ─── Hero ─── */}
      <section className="hero" aria-label="Hero">
        <div className="hero-grid" aria-hidden="true" />
        <div className="container hero-content">
          <div className="hero-badge">
            <Zap size={12} />
            <span>Verified shows. Secure checkout.</span>
          </div>
          <h1 className="hero-headline">
            Book tickets for<br />
            <span className="gradient-text">live experiences</span><br />
            with confidence
          </h1>
          <p className="hero-sub">
            Discover concerts, comedy, sports, and theatre with real-time seat availability,
            verified payments, and QR tickets ready for entry.
          </p>
          <div className="hero-actions">
            <Link to="/events" className="btn btn-primary btn-lg" id="hero-explore-btn">
              Explore Events <ArrowRight size={16} />
            </Link>
            <Link to="/register" className="btn btn-secondary btn-lg" id="hero-signup-btn">
              Create Free Account
            </Link>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-num">Live</span>
              <span className="stat-label">Seat Inventory</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-num">QR</span>
              <span className="stat-label">Ticket Entry</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-num">UPI</span>
              <span className="stat-label">Cards & Netbanking</span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Categories ─── */}
      <section className="section-categories" aria-label="Event categories">
        <div className="container">
          <div className="section-header">
            <h2>Browse by Category</h2>
            <p>Find the type of event that excites you most</p>
          </div>
          <div className="categories-grid">
            {CATEGORIES.map(({ icon: Icon, label, color, count }) => (
              <Link
                key={label}
                to={`/events?category=${label.toLowerCase().replace(' ', '-')}`}
                className="category-card"
                style={{ '--cat-color': color } as React.CSSProperties}
                id={`category-${label.toLowerCase().replace(' ', '-')}`}
              >
                <div className="category-icon-wrap">
                  <Icon size={24} />
                </div>
                <div className="category-info">
                  <h3>{label}</h3>
                  <span className="category-count">{count} events</span>
                </div>
                <ArrowRight size={16} className="category-arrow" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section className="section-features" aria-label="Platform features">
        <div className="container">
          <div className="section-header">
            <h2>Why EventVault?</h2>
            <p>A booking flow built around clarity, payment safety, and fast entry</p>
          </div>
          <div className="features-grid">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="feature-card card">
                <div className="card-body">
                  <div className="feature-icon">
                    <Icon size={20} />
                  </div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA Banner ─── */}
      <section className="section-cta" aria-label="Call to action">
        <div className="container">
          <div className="cta-card">
            <div className="cta-content">
              <h2>Ready to Experience Live Events?</h2>
              <p>Create an account, choose a show, and keep every ticket in one place.</p>
              <div className="cta-actions">
                <Link to="/register" className="btn btn-primary btn-lg" id="cta-register-btn">
                  Get Started for Free <ArrowRight size={16} />
                </Link>
                <Link to="/events" className="btn btn-ghost btn-lg">
                  Browse Events
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
