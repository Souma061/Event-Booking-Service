import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Ticket, Calendar, Clock, ChevronRight, ShoppingBag } from 'lucide-react';
import api from '../lib/api';
import type { BookingOut, BookingStatus } from '../types';
import './Bookings.css';

function statusBadgeClass(status: BookingStatus) {
  const map: Record<BookingStatus, string> = {
    CONFIRMED: 'badge-emerald',
    PENDING_PAYMENT: 'badge-gold',
    CANCELLED: 'badge-rose',
    FAILED: 'badge-rose',
  };
  return map[status] ?? 'badge-sky';
}

function BookingCard({ booking }: { booking: BookingOut }) {
  return (
    <article className="booking-card card" aria-label={`Booking #${booking.id}`}>
      <div className="booking-card-inner card-body">
        <div className="booking-card-top">
          <div className="booking-id-wrap">
            <span className="booking-id-label">Booking</span>
            <span className="booking-id">#{booking.id}</span>
          </div>
          <span className={`badge ${statusBadgeClass(booking.status)}`}>
            {booking.status.replace('_', ' ')}
          </span>
        </div>

        <div className="booking-info">
          <div className="booking-info-row">
            <Ticket size={14} />
            <span>Show #{booking.show_id}</span>
          </div>
          <div className="booking-info-row">
            <Calendar size={14} />
            <span>{new Date(booking.created_at).toLocaleDateString('en-IN', {
              day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
            })}</span>
          </div>
        </div>

        {/* Line Items */}
        {booking.items && booking.items.length > 0 && (
          <div className="booking-items">
            {booking.items.map(item => (
              <div key={item.id} className="booking-item-row">
                <span>{item.category} × {item.quantity}</span>
                <span>₹{parseFloat(item.line_total).toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        )}

        <div className="booking-card-footer">
          <div className="booking-total">
            <span className="booking-total-label">Total</span>
            <span className="booking-total-amt">
              {booking.currency} {parseFloat(booking.total_amount).toLocaleString('en-IN')}
            </span>
          </div>
          <Link
            to={`/events`}
            className="booking-browse-link"
            id={`view-booking-events-${booking.id}`}
          >
            Browse more <ChevronRight size={14} />
          </Link>
        </div>
      </div>
    </article>
  );
}

export default function Bookings() {
  const [bookings, setBookings] = useState<BookingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const { data } = await api.get<BookingOut[]>('/api/bookings/mine');
        setBookings(Array.isArray(data) ? data : []);
      } catch {
        setError('Failed to load bookings.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <main className="bookings-page page-enter" id="main-content">
      <div className="bookings-header">
        <div className="container bookings-header-inner">
          <div>
            <h1>My Bookings</h1>
            <p>{loading ? 'Loading…' : `${bookings.length} booking${bookings.length !== 1 ? 's' : ''} total`}</p>
          </div>
          <Link to="/events" className="btn btn-primary btn-sm" id="browse-events-btn">
            <Ticket size={14} /> Browse Events
          </Link>
        </div>
      </div>

      <div className="container bookings-body">
        {loading && (
          <div className="bookings-state">
            <div className="spinner" style={{ width: 32, height: 32 }} />
            <p>Loading your bookings…</p>
          </div>
        )}

        {!loading && error && (
          <div className="bookings-state">
            <p style={{ color: 'var(--clr-rose)' }}>{error}</p>
          </div>
        )}

        {!loading && !error && bookings.length === 0 && (
          <div className="bookings-state">
            <ShoppingBag size={48} style={{ color: 'var(--clr-text-3)' }} />
            <h3>No bookings yet</h3>
            <p>Explore events and book your first ticket!</p>
            <Link to="/events" className="btn btn-primary" id="empty-browse-events-btn">
              Browse Events
            </Link>
          </div>
        )}

        {!loading && !error && bookings.length > 0 && (
          <>
            {/* Status Summary */}
            <div className="bookings-summary">
              {(['CONFIRMED', 'PENDING_PAYMENT', 'CANCELLED'] as BookingStatus[]).map(status => {
                const count = bookings.filter(b => b.status === status).length;
                return count > 0 ? (
                  <div key={status} className={`summary-chip badge ${statusBadgeClass(status)}`}>
                    {count} {status.replace('_', ' ')}
                  </div>
                ) : null;
              })}
            </div>

            {/* Timeline */}
            <div className="bookings-timeline">
              <div className="timeline-header">
                <Clock size={14} />
                <span>Sorted by most recent</span>
              </div>
              <div className="bookings-grid">
                {bookings.map(b => <BookingCard key={b.id} booking={b} />)}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
