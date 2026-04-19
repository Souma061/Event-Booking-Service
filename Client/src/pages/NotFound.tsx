import { Link } from 'react-router-dom';
import { Home, Search } from 'lucide-react';

export default function NotFound() {
  return (
    <main id="main-content" style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: 'var(--space-xl)',
      gap: 'var(--space-lg)',
      minHeight: '70vh',
    }}>
      <div style={{
        fontSize: '6rem',
        fontFamily: 'var(--font-display)',
        fontWeight: 800,
        background: 'linear-gradient(135deg, var(--clr-accent), var(--clr-accent-2))',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        lineHeight: 1,
      }}>
        404
      </div>
      <h1 style={{ fontSize: '1.75rem', marginBottom: 0 }}>Page not found</h1>
      <p style={{ maxWidth: 380, fontSize: '1rem' }}>
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link to="/" className="btn btn-primary" id="notfound-home-btn">
          <Home size={15} /> Go Home
        </Link>
        <Link to="/events" className="btn btn-secondary" id="notfound-events-btn">
          <Search size={15} /> Browse Events
        </Link>
      </div>
    </main>
  );
}
