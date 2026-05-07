import { useEffect, useMemo, useRef, useState } from 'react';
import { Bell, CheckCircle2, Clock, X } from 'lucide-react';
import { useAuth } from '../context/useAuth';
import './NotificationToaster.css';

type NotificationEvent = {
  event_id: string;
  event_type: string;
  timestamp: string;
  user_id: number;
  booking_id?: number | null;
  message: string;
  data?: Record<string, unknown>;
  channels: string[];
  priority: 'low' | 'normal' | 'high';
};

function buildWebSocketUrl(userId: number): string {
  const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
  const url = new URL(apiBase);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = `/ws/notifications/${userId}`;
  url.search = '';
  return url.toString();
}

function iconForEvent(eventType: string) {
  if (eventType.includes('payment')) return <CheckCircle2 size={18} />;
  if (eventType.includes('expired')) return <Clock size={18} />;
  return <Bell size={18} />;
}

export default function NotificationToaster() {
  const { user, isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<NotificationEvent[]>([]);
  const reconnectTimer = useRef<number | null>(null);
  const shouldReconnect = useRef(true);

  const wsUrl = useMemo(() => {
    return isAuthenticated && user ? buildWebSocketUrl(user.id) : null;
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (!wsUrl) {
      setNotifications([]);
      return undefined;
    }

    shouldReconnect.current = true;
    let socket: WebSocket | null = null;

    const connect = () => {
      socket = new WebSocket(wsUrl);

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as NotificationEvent;
          setNotifications((current) => [payload, ...current].slice(0, 4));
        } catch {
          const fallbackNotification: NotificationEvent = {
            event_id: crypto.randomUUID(),
            event_type: 'notification',
            timestamp: new Date().toISOString(),
            user_id: user?.id ?? 0,
            message: String(event.data),
            channels: ['websocket'],
            priority: 'normal',
          };
          setNotifications((current) => [
            fallbackNotification,
            ...current,
          ].slice(0, 4));
        }
      };

      socket.onclose = () => {
        if (shouldReconnect.current) {
          reconnectTimer.current = window.setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
      socket?.close();
    };
  }, [user?.id, wsUrl]);

  if (!notifications.length) return null;

  return (
    <div className="notification-stack" aria-live="polite" aria-label="Notifications">
      {notifications.map((notification) => (
        <div
          key={notification.event_id}
          className={`notification-toast priority-${notification.priority}`}
        >
          <div className="notification-icon" aria-hidden="true">
            {iconForEvent(notification.event_type)}
          </div>
          <div className="notification-content">
            <p className="notification-message">{notification.message}</p>
            {notification.booking_id && (
              <p className="notification-meta">Booking #{notification.booking_id}</p>
            )}
          </div>
          <button
            className="notification-dismiss"
            type="button"
            aria-label="Dismiss notification"
            onClick={() => {
              setNotifications((current) => current.filter((item) => item.event_id !== notification.event_id));
            }}
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
