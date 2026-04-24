import { Calendar, ChevronRight, Clock, ShoppingBag, Ticket, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import type { BookingOut, BookingStatus, TicketOut } from '../types';
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

interface TicketPreviewSelection {
  bookingId: number;
  showId: number;
  createdAt: string;
  totalAmount: string;
  currency: string;
  ticket: TicketOut;
}

function BookingCard({
  booking,
  onTicketClick,
}: {
  booking: BookingOut;
  onTicketClick: (selection: TicketPreviewSelection) => void;
}) {
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

        {/* Tickets & QR Codes */}
        {booking.tickets && booking.tickets.length > 0 && (
          <div className="booking-tickets">
            <div className="booking-tickets-title">Your Tickets</div>
            <div className="tickets-grid">
              {booking.tickets.map(ticket => (
                <button
                  key={ticket.id}
                  type="button"
                  className="ticket-item ticket-clickable"
                  onClick={() => onTicketClick({
                    bookingId: booking.id,
                    showId: booking.show_id,
                    createdAt: booking.created_at,
                    totalAmount: booking.total_amount,
                    currency: booking.currency,
                    ticket,
                  })}
                  id={`ticket-preview-${ticket.id}`}
                >
                  <div className="ticket-code">{ticket.ticket_code}</div>
                  {ticket.qr_image_base64 && (
                    <img
                      src={`data:image/png;base64,${ticket.qr_image_base64}`}
                      alt={`QR Code for ${ticket.ticket_code}`}
                      className="ticket-qr-thumb"
                    />
                  )}
                  <div className={`ticket-status ${ticket.status === 'ACTIVE' ? 'ok' : 'bad'}`}>
                    {ticket.status}
                  </div>
                </button>
              ))}
            </div>
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
  const [selectedTicket, setSelectedTicket] = useState<TicketPreviewSelection | null>(null);

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
                {bookings.map(b => (
                  <BookingCard
                    key={b.id}
                    booking={b}
                    onTicketClick={setSelectedTicket}
                  />
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {selectedTicket && (
        <div
          className="ticket-modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setSelectedTicket(null);
            }
          }}
          role="dialog"
          aria-modal="true"
          aria-label="Ticket preview"
        >
          <div className="ticket-modal card">
            <div className="ticket-modal-header">
              <div>
                <h3>Ticket Preview</h3>
                <p>{selectedTicket.ticket.ticket_code}</p>
              </div>
              <button
                className="ticket-modal-close"
                onClick={() => setSelectedTicket(null)}
                aria-label="Close ticket preview"
              >
                <X size={18} />
              </button>
            </div>

            <div className="ticket-modal-body">
              {selectedTicket.ticket.qr_image_base64 ? (
                <img
                  src={`data:image/png;base64,${selectedTicket.ticket.qr_image_base64}`}
                  alt={`Ticket QR for ${selectedTicket.ticket.ticket_code}`}
                  className="ticket-modal-qr"
                />
              ) : (
                <div className="ticket-modal-noqr">QR image not available</div>
              )}

              <div className="ticket-modal-meta">
                <div><span>Booking</span><strong>#{selectedTicket.bookingId}</strong></div>
                <div><span>Show</span><strong>#{selectedTicket.showId}</strong></div>
                <div><span>Status</span><strong>{selectedTicket.ticket.status}</strong></div>
                <div>
                  <span>Booked At</span>
                  <strong>
                    {new Date(selectedTicket.createdAt).toLocaleString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
                    })}
                  </strong>
                </div>
                <div><span>Total</span><strong>{selectedTicket.currency} {parseFloat(selectedTicket.totalAmount).toLocaleString('en-IN')}</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
