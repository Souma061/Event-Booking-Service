import { useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Calendar, MapPin, Clock, Users, ArrowLeft, Tag, Ticket } from 'lucide-react';
import api from '../lib/api';
import type { EventOut, VenueOut, ShowOut, ShowAvailabilityOut } from '../types';
import { useAuth } from '../context/useAuth';
import BookingModal from '../components/BookingModal';
import './EventDetail.css';

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function EventDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  const [event, setEvent] = useState<EventOut | null>(null);
  const [venue, setVenue] = useState<VenueOut | null>(null);
  const [shows, setShows] = useState<ShowOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [selectedShow, setSelectedShow] = useState<ShowOut | null>(null);
  const [availability, setAvailability] = useState<ShowAvailabilityOut | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [availLoading, setAvailLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [evRes, showsRes] = await Promise.all([
          api.get<EventOut>(`/api/events/${id}`),
          api.get<ShowOut[]>(`/api/events/${id}/shows`),
        ]);
        setEvent(evRes.data);
        setShows(showsRes.data);

        const { data: venueData } = await api.get<VenueOut>(`/api/events/venues/${evRes.data.venue_id}`);
        setVenue(venueData);
      } catch {
        setError('Event not found or could not be loaded.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleBookShow = async (show: ShowOut) => {
    setSelectedShow(show);
    setAvailLoading(true);
    try {
      const { data } = await api.get<ShowAvailabilityOut>(`/api/bookings/shows/${show.id}/availability`);
      setAvailability(data);
      setModalOpen(true);
    } catch {
      setAvailability(null);
      setModalOpen(true);
    } finally {
      setAvailLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="detail-state">
        <div className="spinner" style={{ width: 36, height: 36 }} />
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="detail-state">
        <p style={{ color: 'var(--clr-rose)' }}>{error || 'Event not found.'}</p>
        <Link to="/events" className="btn btn-secondary btn-sm">← Back to Events</Link>
      </div>
    );
  }

  const activeShows = shows.filter(s => s.status === 'ACTIVE');

  return (
    <main className="event-detail page-enter" id="main-content">
      <div className="container">
        {/* Back */}
        <Link to="/events" className="back-link" id="back-to-events">
          <ArrowLeft size={15} /> Back to Events
        </Link>

        <div className="detail-layout">
          {/* Main Info */}
          <div className="detail-main">
            <div className="detail-banner" style={{
              background: `linear-gradient(135deg, #4b2d8b, #1e1b4b)`
            }}>
              <div className="detail-banner-overlay" />
              {event.category && (
                <span className="detail-banner-cat">{event.category}</span>
              )}
            </div>

            <div className="detail-content">
              <h1>{event.title}</h1>
              {event.description && (
                <p className="detail-desc">{event.description}</p>
              )}

              <div className="detail-attrs">
                {venue && (
                  <>
                    <div className="detail-attr">
                      <MapPin size={15} />
                      <div>
                        <span className="attr-label">Venue</span>
                        <span className="attr-val">{venue.name}</span>
                      </div>
                    </div>
                    <div className="detail-attr">
                      <Tag size={15} />
                      <div>
                        <span className="attr-label">City</span>
                        <span className="attr-val">{venue.city}</span>
                      </div>
                    </div>
                    <div className="detail-attr">
                      <MapPin size={15} />
                      <div>
                        <span className="attr-label">Address</span>
                        <span className="attr-val">{venue.address}</span>
                      </div>
                    </div>
                  </>
                )}
                {event.category && (
                  <div className="detail-attr">
                    <Tag size={15} />
                    <div>
                      <span className="attr-label">Category</span>
                      <span className="attr-val">{event.category}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Shows Sidebar */}
          <aside className="detail-sidebar">
            <div className="shows-panel">
              <h3 className="shows-title">
                <Calendar size={16} /> Available Shows
              </h3>

              {shows.length === 0 && (
                <div className="shows-empty">
                  <Clock size={24} />
                  <p>No shows scheduled yet.</p>
                </div>
              )}

              {shows.map(show => (
                <div key={show.id} className={`show-card ${show.status}`}>
                  <div className="show-card-top">
                    <div>
                      <div className="show-date">
                        <Calendar size={13} />
                        {formatDateTime(show.start_at)}
                      </div>
                      <div className="show-end">
                        <Clock size={13} />
                        Ends: {formatDateTime(show.end_at)}
                      </div>
                    </div>
                    <span className={`badge ${show.status === 'ACTIVE' ? 'badge-emerald' : 'badge-rose'}`}>
                      {show.status}
                    </span>
                  </div>

                  {show.status === 'ACTIVE' ? (
                    isAuthenticated ? (
                      <button
                        className="btn btn-primary btn-sm btn-full"
                        onClick={() => handleBookShow(show)}
                        disabled={availLoading && selectedShow?.id === show.id}
                        id={`book-show-${show.id}`}
                      >
                        {availLoading && selectedShow?.id === show.id
                          ? <><span className="spinner" />Loading…</>
                          : <><Ticket size={14} /> Book Tickets</>
                        }
                      </button>
                    ) : (
                      <Link
                        to="/register"
                        state={{ from: location }}
                        className="btn btn-secondary btn-sm btn-full"
                        id={`register-to-book-${show.id}`}
                      >
                        Register to Book
                      </Link>
                    )
                  ) : (
                    <div className="show-unavailable">
                      <Users size={13} /> Unavailable
                    </div>
                  )}
                </div>
              ))}

              {activeShows.length === 0 && shows.length > 0 && (
                <p className="shows-no-active">No active shows available for booking.</p>
              )}
            </div>
          </aside>
        </div>
      </div>

      {/* Booking Modal */}
      {modalOpen && selectedShow && (
        <BookingModal
          show={selectedShow}
          availability={availability}
          eventTitle={event.title}
          onClose={() => setModalOpen(false)}
        />
      )}
    </main>
  );
}
