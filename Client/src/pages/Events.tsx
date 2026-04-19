import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, MapPin, Calendar, Filter, SlidersHorizontal, Tag } from 'lucide-react';
import api from '../lib/api';
import type { EventOut, VenueOut } from '../types';
import './Events.css';

const CATEGORIES = ['All', 'Music', 'Comedy', 'Sports', 'Theater', 'Technology', 'Food'];

function getEventGradient(category: string | null) {
  const map: Record<string, string> = {
    music:      'linear-gradient(135deg, #6d28d9, #4f46e5)',
    comedy:     'linear-gradient(135deg, #059669, #0891b2)',
    sports:     'linear-gradient(135deg, #b45309, #d97706)',
    theater:    'linear-gradient(135deg, #be185d, #9d174d)',
    technology: 'linear-gradient(135deg, #1d4ed8, #2563eb)',
    food:       'linear-gradient(135deg, #d97706, #dc2626)',
  };
  return map[(category || '').toLowerCase()] || 'linear-gradient(135deg, #4b5563, #374151)';
}

function EventCard({ event, venue }: { event: EventOut; venue?: VenueOut }) {
  return (
    <article className="event-card card" aria-label={`Event: ${event.title}`}>
      <div className="event-card-banner" style={{ background: getEventGradient(event.category) }}>
        <div className="event-banner-overlay" />
        {event.category && (
          <span className="event-banner-category">{event.category}</span>
        )}
      </div>
      <div className="card-body event-card-body">
        <div>
          <h3 className="event-title">{event.title}</h3>
          {event.description && (
            <p className="event-desc">{event.description.slice(0, 90)}{event.description.length > 90 ? '…' : ''}</p>
          )}
        </div>
        <div className="event-meta">
          {venue && (
            <div className="event-meta-item">
              <MapPin size={13} />
              <span>{venue.name}, {venue.city}</span>
            </div>
          )}
          <div className="event-meta-item">
            <Calendar size={13} />
            <span>{new Date(event.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
          </div>
        </div>
        <Link
          to={`/events/${event.id}`}
          className="btn btn-secondary btn-sm btn-full"
          id={`event-view-${event.id}`}
        >
          View Details
        </Link>
      </div>
    </article>
  );
}

export default function Events() {
  const [events, setEvents] = useState<EventOut[]>([]);
  const [venues, setVenues] = useState<Record<number, VenueOut>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const { data } = await api.get<EventOut[]>('/api/events');
        setEvents(data);
        // Fetch venues for each unique venue_id
        const venueIds = Array.from(new Set(data.map(e => e.venue_id)));
        const venueMap: Record<number, VenueOut> = {};
        await Promise.all(
          venueIds.map(async (id) => {
            try {
              const { data: v } = await api.get<VenueOut>(`/api/events/venues/${id}`);
              venueMap[id] = v;
            } catch {
              // Not critical
            }
          })
        );
        setVenues(venueMap);
      } catch {
        setError('Failed to load events. Make sure the backend is running.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filtered = events.filter(e => {
    const matchCat = activeCategory === 'All' || e.category?.toLowerCase() === activeCategory.toLowerCase();
    const matchSearch = e.title.toLowerCase().includes(search.toLowerCase()) ||
      e.description?.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <main className="events-page page-enter" id="main-content">
      {/* Header */}
      <div className="events-header">
        <div className="container events-header-inner">
          <div>
            <h1>Browse Events</h1>
            <p>{loading ? 'Loading…' : `${filtered.length} event${filtered.length !== 1 ? 's' : ''} available`}</p>
          </div>
          {/* Search */}
          <div className="events-search-wrap">
            <Search size={16} className="events-search-icon" aria-hidden="true" />
            <input
              type="search"
              className="events-search"
              placeholder="Search events…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              id="events-search-input"
              aria-label="Search events"
            />
          </div>
        </div>
      </div>

      <div className="container events-body">
        {/* Filters sidebar */}
        <aside className="events-sidebar" aria-label="Event filters">
          <div className="filter-section">
            <div className="filter-title">
              <SlidersHorizontal size={14} />
              <span>Filters</span>
            </div>
            <div className="filter-group">
              <div className="filter-group-title">
                <Tag size={13} />Category
              </div>
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  className={`filter-btn ${activeCategory === cat ? 'active' : ''}`}
                  onClick={() => setActiveCategory(cat)}
                  id={`filter-${cat.toLowerCase()}`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Events grid */}
        <section className="events-grid-section" aria-label="Event listings">
          {loading && (
            <div className="events-state">
              <div className="spinner" style={{ width: 32, height: 32 }} />
              <p>Loading events…</p>
            </div>
          )}
          {!loading && error && (
            <div className="events-state">
              <Filter size={32} style={{ color: 'var(--clr-text-3)' }} />
              <p style={{ color: 'var(--clr-rose)' }}>{error}</p>
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="events-state">
              <Search size={32} style={{ color: 'var(--clr-text-3)' }} />
              <p>No events found. Try adjusting your filters.</p>
            </div>
          )}
          {!loading && !error && filtered.length > 0 && (
            <div className="events-grid">
              {filtered.map(event => (
                <EventCard key={event.id} event={event} venue={venues[event.venue_id]} />
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
