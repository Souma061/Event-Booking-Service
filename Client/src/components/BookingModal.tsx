import { useState, useMemo } from 'react';
import { X, Ticket, Plus, Minus, ShoppingCart, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../lib/api';
import type { ShowOut, ShowAvailabilityOut, InventoryRowOut, BookingOut, PaymentOrderOut } from '../types';
import './BookingModal.css';

function loadScript(src: string): Promise<boolean> {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

interface Props {
  show: ShowOut;
  availability: ShowAvailabilityOut | null;
  eventTitle: string;
  onClose: () => void;
}

interface CartItem {
  category: string;
  quantity: number;
  price: number;
  available: number;
}

interface ApiErrorResponse {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

interface CashfreeCheckoutResult {
  error?: {
    message?: string;
  };
  paymentDetails?: unknown;
}

interface CashfreeInstance {
  checkout: (options: {
    paymentSessionId: string;
    redirectTarget: '_modal';
  }) => Promise<CashfreeCheckoutResult>;
}

interface CashfreeWindow extends Window {
  Cashfree?: (options: { mode: 'sandbox' | 'production' }) => CashfreeInstance;
}

function buildIdempotencyKey(): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function getApiErrorDetail(err: unknown): string | undefined {
  return (err as ApiErrorResponse)?.response?.data?.detail;
}

function initCart(inv: InventoryRowOut[]): CartItem[] {
  return inv.map(row => ({
    category: row.category,
    quantity: 0,
    price: parseFloat(row.price),
    available: row.available_seats,
  }));
}

export default function BookingModal({ show, availability, eventTitle, onClose }: Props) {
  const [cart, setCart] = useState<CartItem[]>(
    () => availability ? initCart(availability.inventory) : []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const update = (cat: string, delta: number) => {
    setCart(prev => prev.map(item =>
      item.category === cat
        ? { ...item, quantity: Math.max(0, Math.min(item.available, item.quantity + delta)) }
        : item
    ));
    setError('');
  };

  const total = useMemo(() => cart.reduce((sum, i) => sum + i.quantity * i.price, 0), [cart]);
  const itemsToBook = useMemo(() => cart.filter(i => i.quantity > 0), [cart]);

  const handleBook = async () => {
    if (itemsToBook.length === 0) {
      setError('Please select at least one ticket.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data: booking } = await api.post<BookingOut>('/api/bookings', {
        show_id: show.id,
        items: itemsToBook.map(i => ({ category: i.category, quantity: i.quantity })),
      }, {
        headers: { 'Idempotency-Key': buildIdempotencyKey() },
      });

      const { data: paymentOrder } = await api.post<PaymentOrderOut>('/api/payments/orders', {
        booking_id: booking.id
      });

      const scriptLoaded = await loadScript('https://sdk.cashfree.com/js/v3/cashfree.js');
      if (!scriptLoaded) {
        setError('Payment gateway failed to load. Please check your connection.');
        setLoading(false);
        return;
      }

      const cashfreeFactory = (window as CashfreeWindow).Cashfree;
      if (!cashfreeFactory) {
        setError('Payment gateway is unavailable. Please try again.');
        setLoading(false);
        return;
      }

      const cashfree = cashfreeFactory({ mode: 'production' });

      const checkoutOptions = {
          paymentSessionId: paymentOrder.payment_session_id,
          redirectTarget: '_modal',
      } as const;

      cashfree.checkout(checkoutOptions).then(async (result) => {
          if (result.error) {
              setError(result.error.message || 'Payment failed or cancelled.');
              setLoading(false);
          }
          if (result.paymentDetails) {
              try {
                  await api.post('/api/payments/verify', {
                      booking_id: paymentOrder.booking_id,
                      provider_order_id: paymentOrder.provider_order_id,
                  });
                  setSuccess(true);
                  setTimeout(onClose, 2000);
              } catch (verifyErr: unknown) {
                  const msg = getApiErrorDetail(verifyErr);
                  setError(msg || 'Payment verification failed.');
                  setLoading(false);
              }
          }
      });

    } catch (err: unknown) {
      const msg = getApiErrorDetail(err);
      setError(msg || 'Booking failed. Please try again.');
      setLoading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  const displayCart = availability ? cart : [];

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick} role="dialog" aria-modal="true" aria-label="Book tickets">
      <div className="modal-panel">
        {/* Header */}
        <div className="modal-header">
          <div>
            <h3 className="modal-title">
              <Ticket size={16} /> Book Tickets
            </h3>
            <p className="modal-subtitle">{eventTitle}</p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close booking modal" id="booking-modal-close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {success ? (
            <div className="modal-success">
              <CheckCircle size={48} />
              <h3>Booking Confirmed! 🎉</h3>
              <p>Your tickets have been booked. Check "My Bookings" for details.</p>
            </div>
          ) : !availability ? (
            <div className="modal-no-avail">
              <AlertCircle size={32} />
              <p>Availability data unavailable. Please try again.</p>
            </div>
          ) : (
            <>
              {/* Seat Categories */}
              <div className="seat-categories">
                {displayCart.map(item => (
                  <div key={item.category} className="seat-row">
                    <div className="seat-info">
                      <span className="seat-category">{item.category}</span>
                      <span className="seat-price">₹{item.price.toLocaleString('en-IN')}</span>
                    </div>
                    <div className="seat-avail">
                      {item.available} left
                    </div>
                    <div className="seat-qty-control">
                      <button
                        className="qty-btn"
                        onClick={() => update(item.category, -1)}
                        disabled={item.quantity === 0}
                        aria-label={`Decrease ${item.category} quantity`}
                        id={`decrease-${item.category}`}
                      >
                        <Minus size={14} />
                      </button>
                      <span className="qty-num">{item.quantity}</span>
                      <button
                        className="qty-btn"
                        onClick={() => update(item.category, 1)}
                        disabled={item.quantity >= item.available}
                        aria-label={`Increase ${item.category} quantity`}
                        id={`increase-${item.category}`}
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {error && (
                <div className="alert alert-error">
                  <AlertCircle size={15} />
                  <span>{error}</span>
                </div>
              )}

              {/* Order Summary */}
              {itemsToBook.length > 0 && (
                <div className="order-summary">
                  <div className="summary-title">Order Summary</div>
                  {itemsToBook.map(i => (
                    <div key={i.category} className="summary-row">
                      <span>{i.category} × {i.quantity}</span>
                      <span>₹{(i.price * i.quantity).toLocaleString('en-IN')}</span>
                    </div>
                  ))}
                  <div className="divider" style={{ margin: '8px 0' }} />
                  <div className="summary-total">
                    <span>Total</span>
                    <span>₹{total.toLocaleString('en-IN')}</span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!success && availability && (
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={onClose} id="booking-cancel-btn">Cancel</button>
            <button
              className="btn btn-primary"
              onClick={handleBook}
              disabled={loading || itemsToBook.length === 0}
              id="booking-confirm-btn"
            >
              {loading
                ? <><span className="spinner" />Processing…</>
                : <><ShoppingCart size={15} /> Confirm Booking — ₹{total.toLocaleString('en-IN')}</>
              }
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
