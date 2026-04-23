/* ─── Auth ─── */
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  phone: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  role: 'ADMIN' | 'CUSTOMER';
  is_active: boolean;
  created_at: string;
}

/* ─── Events ─── */
export interface VenueOut {
  id: number;
  name: string;
  city: string;
  address: string;
}

export interface EventOut {
  id: number;
  title: string;
  description: string | null;
  category: string | null;
  venue_id: number;
  venue?: VenueOut;
  created_at: string;
  created_by: number;
}

export interface ShowOut {
  id: number;
  event_id: number;
  start_at: string;
  end_at: string;
  status: 'ACTIVE' | 'CANCELLED' | 'COMPLETED';
}

export interface InventoryRowOut {
  id: number;
  show_id: number;
  category: string;
  total_seats: number;
  available_seats: number;
  price: string;
}

export interface ShowAvailabilityOut {
  show_id: number;
  inventory: InventoryRowOut[];
}

/* ─── Bookings ─── */
export interface BookingItemIn {
  category: string;
  quantity: number;
}

export interface BookingCreateRequest {
  show_id: number;
  items: BookingItemIn[];
}

export interface BookingItemOut {
  id: number;
  category: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface TicketOut {
  id: number;
  ticket_code: string;
  qr_image_base64: string | null;
  status: string;
}

export type BookingStatus = 'PENDING_PAYMENT' | 'CONFIRMED' | 'CANCELLED' | 'FAILED';

export interface BookingOut {
  id: number;
  user_id: number;
  show_id: number;
  status: BookingStatus;
  total_amount: string;
  currency: string;
  created_at: string;
  items: BookingItemOut[];
  tickets: TicketOut[];
}

/* ─── Payments ─── */
export interface PaymentOrderCreateRequest {
  booking_id: number;
}

export interface PaymentOrderOut {
  booking_id: number;
  provider_order_id: string;
  amount_in_paise: number;
  currency: string;
  razorpay_key_id: string;
}

export interface PaymentVerificationRequest {
  booking_id: number;
  provider_order_id: string;
  provider_payment_id: string;
  provider_signature: string;
}

export interface PaymentVerificationOut {
  booking_id: number;
  status: string;
  ticket_codes: string[];
}
