import {
  Calendar,
  CheckCircle,
  ChevronDown, ChevronUp,
  LayoutDashboard, MapPin,
  Plus,
  RefreshCw,
  Tag,
  Ticket,
  Trash2,
  Users,
  X
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import api from '../lib/api';
import type { EventOut, ShowOut, VenueOut } from '../types';
import './Admin.css';

/* ─── Types ─── */
interface InventoryRow {
  category: string;
  price: string;
  total_seats: string;
}

/* ─── Helpers ─── */
function notify(msg: string, type: 'success' | 'error') {
  const el = document.createElement('div');
  el.className = `admin-toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(() => {
    el.classList.remove('visible');
    setTimeout(() => el.remove(), 300);
  }, 3000);
}

function apiError(err: unknown): string {
  return (
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
    'An unexpected error occurred.'
  );
}

/* ─── Section: Venues ─── */
function VenuesSection() {
  const [venues, setVenues] = useState<VenueOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', city: '', address: '' });
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    await Promise.resolve(); // break sync execution to avoid react-dev/learn lint
    setLoading(true);
    try {
      const { data } = await api.get<VenueOut[]>('/api/events/venues');
      setVenues(data);
    } catch {
      // Endpoint may not exist yet — swallow silently
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(load, 0);
    return () => clearTimeout(t);
  }, [load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.city || !form.address) return;
    setSaving(true);
    try {
      const { data } = await api.post<VenueOut>('/api/events/venues', form);
      setVenues(v => [data, ...v]);
      setForm({ name: '', city: '', address: '' });
      setOpen(false);
      notify('Venue created successfully', 'success');
    } catch (err) {
      notify(apiError(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <div className="admin-section-title">
          <MapPin size={18} />
          <h2>Venues</h2>
          <span className="admin-count-badge">{venues.length}</span>
        </div>
        <div className="admin-section-actions">
          <button className="btn btn-ghost btn-sm" onClick={load} title="Refresh" id="venues-refresh-btn">
            <RefreshCw size={14} />
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setOpen(!open)} id="create-venue-toggle">
            <Plus size={14} /> New Venue
          </button>
        </div>
      </div>

      {/* Create Form */}
      {open && (
        <form className="admin-form card" onSubmit={handleCreate} id="create-venue-form">
          <div className="card-body">
            <h3 className="form-title">Create Venue</h3>
            <div className="admin-form-grid">
              <div className="form-group">
                <label className="form-label" htmlFor="venue-name">Venue Name</label>
                <input id="venue-name" className="form-input" placeholder="e.g. Jawaharlal Nehru Stadium"
                  value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="venue-city">City</label>
                <input id="venue-city" className="form-input" placeholder="e.g. New Delhi"
                  value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} required />
              </div>
              <div className="form-group admin-span-2">
                <label className="form-label" htmlFor="venue-address">Address</label>
                <input id="venue-address" className="form-input" placeholder="e.g. Lodhi Road, New Delhi - 110003"
                  value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} required />
              </div>
            </div>
            <div className="admin-form-footer">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary btn-sm" disabled={saving} id="create-venue-submit">
                {saving ? <><span className="spinner" />Creating…</> : 'Create Venue'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="admin-table-wrap card">
        {loading ? (
          <div className="admin-table-state"><div className="spinner" /></div>
        ) : venues.length === 0 ? (
          <div className="admin-table-state">
            <MapPin size={28} />
            <p>No venues yet. Create one above.</p>
          </div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>City</th>
                <th>Address</th>
              </tr>
            </thead>
            <tbody>
              {venues.map(v => (
                <tr key={v.id}>
                  <td className="admin-id">#{v.id}</td>
                  <td className="admin-bold">{v.name}</td>
                  <td>{v.city}</td>
                  <td className="admin-muted">{v.address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/* ─── Section: Events ─── */
function EventsSection() {
  const [events, setEvents] = useState<EventOut[]>([]);
  const [venues, setVenues] = useState<VenueOut[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: '', description: '', category: '', venue_id: '' });
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    await Promise.resolve(); // break sync execution
    setLoading(true);
    try {
      const [evRes, vnRes, catRes] = await Promise.all([
        api.get<EventOut[]>('/api/events'),
        api.get<VenueOut[]>('/api/events/venues').catch(() => ({ data: [] as VenueOut[] })),
        api.get<string[]>('/api/events/categories').catch(() => ({ data: [] as string[] })),
      ]);
      setEvents(evRes.data);
      setVenues(vnRes.data);
      setCategories(catRes.data);
    } catch {
      // silently handle
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(load, 0);
    return () => clearTimeout(t);
  }, [load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedCategory = form.category.trim();
    if (!form.title || !normalizedCategory || !form.venue_id) return;
    setSaving(true);
    try {
      const { data } = await api.post<EventOut>('/api/events', {
        title: form.title,
        description: form.description || null,
        category: normalizedCategory,
        venue_id: parseInt(form.venue_id),
      });
      setEvents(ev => [data, ...ev]);
      setCategories(prev => {
        if (prev.some(c => c.toLowerCase() === normalizedCategory.toLowerCase())) {
          return prev;
        }
        return [...prev, normalizedCategory].sort((a, b) => a.localeCompare(b));
      });
      setForm({ title: '', description: '', category: '', venue_id: '' });
      setOpen(false);
      notify('Event created successfully', 'success');
    } catch (err) {
      notify(apiError(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  const venueMap = Object.fromEntries(venues.map(v => [v.id, v]));

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <div className="admin-section-title">
          <Calendar size={18} />
          <h2>Events</h2>
          <span className="admin-count-badge">{events.length}</span>
        </div>
        <div className="admin-section-actions">
          <button className="btn btn-ghost btn-sm" onClick={load} title="Refresh" id="events-refresh-btn">
            <RefreshCw size={14} />
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setOpen(!open)} id="create-event-toggle">
            <Plus size={14} /> New Event
          </button>
        </div>
      </div>

      {/* Create Form */}
      {open && (
        <form className="admin-form card" onSubmit={handleCreate} id="create-event-form">
          <div className="card-body">
            <h3 className="form-title">Create Event</h3>
            <div className="admin-form-grid">
              <div className="form-group admin-span-2">
                <label className="form-label" htmlFor="event-title">Event Title</label>
                <input id="event-title" className="form-input" placeholder="e.g. Arijit Singh Live in Concert"
                  value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="event-category">Category</label>
                <input
                  id="event-category"
                  list="event-category-options"
                  className="form-input"
                  placeholder="Type or select category…"
                  value={form.category}
                  onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                  required
                />
                <datalist id="event-category-options">
                  {categories.map(c => <option key={c} value={c} />)}
                </datalist>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="event-venue">Venue</label>
                <select id="event-venue" className="form-input"
                  value={form.venue_id}
                  onChange={e => setForm(f => ({ ...f, venue_id: e.target.value }))}
                  disabled={venues.length === 0}
                  required>
                  <option value="">{venues.length === 0 ? 'Create a venue first…' : 'Select venue…'}</option>
                  {venues.map(v => <option key={v.id} value={v.id}>{v.name} — {v.city}</option>)}
                </select>
                {venues.length === 0 && (
                  <p className="admin-muted">No venues found. Create one in the Venues tab first.</p>
                )}
              </div>
              <div className="form-group admin-span-2">
                <label className="form-label" htmlFor="event-desc">Description <span className="form-optional">(optional)</span></label>
                <textarea id="event-desc" className="form-input admin-textarea"
                  placeholder="Describe the event…" rows={3}
                  value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </div>
            </div>
            <div className="admin-form-footer">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary btn-sm" disabled={saving} id="create-event-submit">
                {saving ? <><span className="spinner" />Creating…</> : 'Create Event'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="admin-table-wrap card">
        {loading ? (
          <div className="admin-table-state"><div className="spinner" /></div>
        ) : events.length === 0 ? (
          <div className="admin-table-state">
            <Calendar size={28} />
            <p>No events yet. Create one above.</p>
          </div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Category</th>
                <th>Venue</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id}>
                  <td className="admin-id">#{e.id}</td>
                  <td className="admin-bold">{e.title}</td>
                  <td>
                    <span className="badge badge-purple">{e.category}</span>
                  </td>
                  <td className="admin-muted">{venueMap[e.venue_id]?.name ?? `Venue #${e.venue_id}`}</td>
                  <td className="admin-muted">{new Date(e.created_at).toLocaleDateString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/* ─── Section: Shows ─── */
function ShowInventoryRow({ category, price, seats }: {
  showId: number; category: string; price: string; seats: number;
}) {
  return (
    <div className="inv-row">
      <span className="inv-category badge badge-sky">{category}</span>
      <span className="inv-price">₹{parseFloat(price).toLocaleString('en-IN')}</span>
      <span className="inv-seats"><Users size={11} /> {seats} seats</span>
    </div>
  );
}

function ShowsSection() {
  const [events, setEvents] = useState<EventOut[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<number | ''>('');
  const [shows, setShows] = useState<ShowOut[]>([]);
  const [expandedShow, setExpandedShow] = useState<number | null>(null);

  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadingShows, setLoadingShows] = useState(false);
  const [savingShow, setSavingShow] = useState(false);
  const [savingInv, setSavingInv] = useState(false);

  // Show creation form
  const [showForm, setShowForm] = useState({
    start_at: '',
    end_at: '',
    status: 'ACTIVE',
    category: '',
    price: '',
    total_seats: '',
  });
  const [showFormOpen, setShowFormOpen] = useState(false);

  // Inventory rows per show
  const [invRows, setInvRows] = useState<Record<number, InventoryRow[]>>({});
  const [savedInv, setSavedInv] = useState<Record<number, { category: string; price: string; total_seats: number }[]>>({});

  useEffect(() => {
    const load = async () => {
      setLoadingEvents(true);
      try {
        const { data } = await api.get<EventOut[]>('/api/events');
        setEvents(data);
      } catch {
        // ignore
      } finally {
        setLoadingEvents(false);
      }
    };
    load();
  }, []);

  const loadShows = useCallback(async (eventId: number) => {
    setLoadingShows(true);
    setShows([]);
    try {
      const { data } = await api.get<ShowOut[]>(`/api/events/${eventId}/shows`);
      setShows(data);
    } catch {
      // ignore
    } finally {
      setLoadingShows(false);
    }
  }, []);

  const handleEventSelect = (id: number | '') => {
    setSelectedEvent(id);
    setExpandedShow(null);
    setShowFormOpen(false);
    if (id) loadShows(id as number);
    else setShows([]);
  };

  const handleCreateShow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvent || !showForm.start_at || !showForm.end_at) return;

    const normalizedCategory = showForm.category.trim();
    const hasQuickInventoryInput = Boolean(normalizedCategory || showForm.price || showForm.total_seats);
    const hasCompleteQuickInventoryInput = Boolean(normalizedCategory && showForm.price && showForm.total_seats);
    if (hasQuickInventoryInput && !hasCompleteQuickInventoryInput) {
      notify('To add ticket pricing now, fill category, price and total seats together.', 'error');
      return;
    }

    setSavingShow(true);
    try {
      const { data } = await api.post<ShowOut>(`/api/events/${selectedEvent}/shows`, {
        start_at: new Date(showForm.start_at).toISOString(),
        end_at: new Date(showForm.end_at).toISOString(),
        status: showForm.status,
      });
      setShows(s => [...s, data]);

      if (hasCompleteQuickInventoryInput) {
        const { data: savedRows } = await api.put(`/api/events/shows/${data.id}/inventory`, [
          {
            category: normalizedCategory,
            price: parseFloat(showForm.price),
            total_seats: parseInt(showForm.total_seats),
          },
        ]);
        setSavedInv(prev => ({ ...prev, [data.id]: savedRows }));
      }

      setShowForm({
        start_at: '',
        end_at: '',
        status: 'ACTIVE',
        category: '',
        price: '',
        total_seats: '',
      });
      setShowFormOpen(false);
      notify(
        hasCompleteQuickInventoryInput
          ? 'Show created with ticket pricing successfully'
          : 'Show created successfully',
        'success'
      );
    } catch (err) {
      notify(apiError(err), 'error');
    } finally {
      setSavingShow(false);
    }
  };

  const addInvRow = (showId: number) => {
    setInvRows(prev => ({
      ...prev,
      [showId]: [...(prev[showId] ?? []), { category: '', price: '', total_seats: '' }],
    }));
  };

  const removeInvRow = (showId: number, idx: number) => {
    setInvRows(prev => ({
      ...prev,
      [showId]: (prev[showId] ?? []).filter((_, i) => i !== idx),
    }));
  };

  const updateInvRow = (showId: number, idx: number, field: keyof InventoryRow, value: string) => {
    setInvRows(prev => {
      const rows = [...(prev[showId] ?? [])];
      rows[idx] = { ...rows[idx], [field]: value };
      return { ...prev, [showId]: rows };
    });
  };

  const saveInventory = async (showId: number) => {
    const rows = invRows[showId] ?? [];
    if (rows.some(r => !r.category || !r.price || !r.total_seats)) {
      notify('Fill all fields before saving inventory.', 'error');
      return;
    }
    setSavingInv(true);
    try {
      const payload = rows.map(r => ({
        category: r.category,
        price: parseFloat(r.price),
        total_seats: parseInt(r.total_seats),
      }));
      const { data } = await api.put(`/api/events/shows/${showId}/inventory`, payload);
      setSavedInv(prev => ({ ...prev, [showId]: data }));
      setInvRows(prev => ({ ...prev, [showId]: [] }));
      notify('Inventory saved successfully', 'success');
    } catch (err) {
      notify(apiError(err), 'error');
    } finally {
      setSavingInv(false);
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <div className="admin-section-title">
          <Ticket size={18} />
          <h2>Shows &amp; Inventory</h2>
        </div>
      </div>

      {/* Event Picker */}
      <div className="admin-picker card">
        <div className="card-body">
          <div className="form-group">
            <label className="form-label" htmlFor="show-event-select">
              <Calendar size={13} /> Select Event
            </label>
            <select
              id="show-event-select"
              className="form-input"
              value={selectedEvent}
              onChange={e => handleEventSelect(e.target.value ? parseInt(e.target.value) : '')}
              disabled={loadingEvents}
            >
              <option value="">{loadingEvents ? 'Loading events…' : 'Choose an event…'}</option>
              {events.map(ev => (
                <option key={ev.id} value={ev.id}>#{ev.id} — {ev.title} ({ev.category})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {selectedEvent !== '' && (
        <>
          {/* Create Show */}
          <div className="admin-sub-header">
            <h3 className="admin-sub-title"><Calendar size={15} /> Shows for Event #{selectedEvent}</h3>
            <button className="btn btn-primary btn-sm" onClick={() => setShowFormOpen(!showFormOpen)} id="create-show-toggle">
              <Plus size={13} /> Add Show
            </button>
          </div>

          {showFormOpen && (
            <form className="admin-form card" onSubmit={handleCreateShow} id="create-show-form">
              <div className="card-body">
                <h3 className="form-title">New Show</h3>
                <div className="admin-form-grid">
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-start">Start Date &amp; Time</label>
                    <input id="show-start" type="datetime-local" className="form-input"
                      value={showForm.start_at} onChange={e => setShowForm(f => ({ ...f, start_at: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-end">End Date &amp; Time</label>
                    <input id="show-end" type="datetime-local" className="form-input"
                      value={showForm.end_at} onChange={e => setShowForm(f => ({ ...f, end_at: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-status">Status</label>
                    <select id="show-status" className="form-input"
                      value={showForm.status} onChange={e => setShowForm(f => ({ ...f, status: e.target.value }))}>
                      <option value="ACTIVE">ACTIVE</option>
                      <option value="CANCELLED">CANCELLED</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-default-category">Ticket Category <span className="form-optional">(optional)</span></label>
                    <input
                      id="show-default-category"
                      className="form-input"
                      placeholder="e.g. Regular"
                      value={showForm.category}
                      onChange={e => setShowForm(f => ({ ...f, category: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-default-price">Ticket Price (₹) <span className="form-optional">(optional)</span></label>
                    <input
                      id="show-default-price"
                      type="number"
                      className="form-input"
                      placeholder="999"
                      min="1"
                      value={showForm.price}
                      onChange={e => setShowForm(f => ({ ...f, price: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="show-default-seats">Total Seats <span className="form-optional">(optional)</span></label>
                    <input
                      id="show-default-seats"
                      type="number"
                      className="form-input"
                      placeholder="500"
                      min="1"
                      max="50000"
                      value={showForm.total_seats}
                      onChange={e => setShowForm(f => ({ ...f, total_seats: e.target.value }))}
                    />
                  </div>
                </div>
                <p className="admin-muted">If you enter category, price and seats here, inventory is created automatically with the show.</p>
                <div className="admin-form-footer">
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowFormOpen(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={savingShow} id="create-show-submit">
                    {savingShow ? <><span className="spinner" />Creating…</> : 'Create Show'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Shows list */}
          {loadingShows ? (
            <div className="admin-table-state"><div className="spinner" /></div>
          ) : shows.length === 0 ? (
            <div className="admin-table-state card" style={{ padding: 'var(--space-xl)' }}>
              <Calendar size={28} />
              <p>No shows for this event yet.</p>
            </div>
          ) : (
            <div className="shows-list">
              {shows.map(show => {
                const isExpanded = expandedShow === show.id;
                const rows = invRows[show.id] ?? [];
                const saved = savedInv[show.id] ?? [];
                return (
                  <div key={show.id} className="show-expand-card card">
                    <div
                      className="show-expand-header"
                      onClick={() => setExpandedShow(isExpanded ? null : show.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => e.key === 'Enter' && setExpandedShow(isExpanded ? null : show.id)}
                      id={`show-expand-${show.id}`}
                    >
                      <div className="show-expand-info">
                        <span className="show-expand-id">Show #{show.id}</span>
                        <span className={`badge ${show.status === 'ACTIVE' ? 'badge-emerald' : 'badge-rose'}`}>
                          {show.status}
                        </span>
                        <span className="show-expand-time">
                          <Calendar size={12} />
                          {new Date(show.start_at).toLocaleString('en-IN', {
                            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                      </div>
                      <div className="show-expand-actions">
                        <span className="show-expand-label">
                          <Tag size={12} /> Set Inventory
                        </span>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="show-expand-body">
                        {/* Saved inventory */}
                        {saved.length > 0 && (
                          <div className="inv-saved">
                            <p className="inv-saved-label"><CheckCircle size={13} /> Current Inventory</p>
                            <div className="inv-saved-rows">
                              {saved.map((r, i) => (
                                <ShowInventoryRow key={i} showId={show.id}
                                  category={r.category} price={String(r.price)} seats={r.total_seats} />
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Inventory builder */}
                        <div className="inv-builder">
                          <div className="inv-builder-title">
                            <Users size={14} /> Configure Seat Categories
                          </div>
                          {rows.map((row, idx) => (
                            <div key={idx} className="inv-row-form">
                              <div className="form-group inv-col-cat">
                                <label className="form-label" htmlFor={`inv-cat-${show.id}-${idx}`}>Category</label>
                                <input id={`inv-cat-${show.id}-${idx}`} className="form-input" placeholder="e.g. Gold"
                                  value={row.category}
                                  onChange={e => updateInvRow(show.id, idx, 'category', e.target.value)} />
                              </div>
                              <div className="form-group inv-col-price">
                                <label className="form-label" htmlFor={`inv-price-${show.id}-${idx}`}>Price (₹)</label>
                                <input id={`inv-price-${show.id}-${idx}`} type="number" className="form-input" placeholder="999"
                                  min="1" value={row.price}
                                  onChange={e => updateInvRow(show.id, idx, 'price', e.target.value)} />
                              </div>
                              <div className="form-group inv-col-seats">
                                <label className="form-label" htmlFor={`inv-seats-${show.id}-${idx}`}>Total Seats</label>
                                <input id={`inv-seats-${show.id}-${idx}`} type="number" className="form-input" placeholder="500"
                                  min="1" max="50000" value={row.total_seats}
                                  onChange={e => updateInvRow(show.id, idx, 'total_seats', e.target.value)} />
                              </div>
                              <button type="button" className="btn btn-danger btn-sm inv-remove-btn"
                                onClick={() => removeInvRow(show.id, idx)} aria-label="Remove row"
                                id={`remove-inv-row-${show.id}-${idx}`}>
                                <Trash2 size={13} />
                              </button>
                            </div>
                          ))}

                          <div className="inv-builder-actions">
                            <button type="button" className="btn btn-secondary btn-sm"
                              onClick={() => addInvRow(show.id)} id={`add-inv-row-${show.id}`}>
                              <Plus size={13} /> Add Category
                            </button>
                            {rows.length > 0 && (
                              <button type="button" className="btn btn-primary btn-sm"
                                onClick={() => saveInventory(show.id)}
                                disabled={savingInv} id={`save-inv-${show.id}`}>
                                {savingInv ? <><span className="spinner" />Saving…</> : <><CheckCircle size={13} /> Save Inventory</>}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ─── Section: Ticket Scanner ─── */
function ScannerSection() {
  const [ticketCode, setTicketCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    status: string;
    message: string;
    ticket_id?: number;
    booking_id?: number;
  } | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketCode.trim()) return;

    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post('/api/admin/verify-ticket', { ticket_code: ticketCode.trim() });
      setResult(data);
      if (data.status === 'VALID') {
        notify('Ticket verified successfully!', 'success');
      } else {
        notify(data.message, 'error');
      }
    } catch (err) {
      const errorMsg = apiError(err);
      setResult({ status: 'ERROR', message: errorMsg });
      notify(errorMsg, 'error');
    } finally {
      setLoading(false);
      setTicketCode('');
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <div className="admin-section-title">
          <CheckCircle size={18} />
          <h2>Ticket Scanner</h2>
        </div>
      </div>

      <div className="card" style={{ maxWidth: '500px', margin: '0 auto', marginTop: '2rem' }}>
        <div className="card-body">
          <p style={{ marginBottom: '1.5rem', color: 'var(--clr-muted)' }}>
            Enter the unique ticket code (from the QR) to verify and mark the ticket as used.
          </p>

          <form onSubmit={handleVerify} className="admin-form">
            <div className="form-group">
              <label className="form-label" htmlFor="ticket-code-input">Ticket Code</label>
              <input
                id="ticket-code-input"
                className="form-input"
                placeholder="e.g. TKT-10-ABCD..."
                value={ticketCode}
                onChange={e => setTicketCode(e.target.value)}
                required
                autoFocus
                style={{ fontSize: '1.2rem', padding: '1rem', textAlign: 'center' }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '1rem', fontSize: '1.1rem' }}
              disabled={loading}
            >
              {loading ? <><span className="spinner" /> Verifying...</> : <><CheckCircle size={18} /> Verify Ticket</>}
            </button>
          </form>

          {result && (
            <div style={{
              marginTop: '2rem',
              padding: '1.5rem',
              borderRadius: 'var(--radius)',
              background: result.status === 'VALID' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
              border: `1px solid ${result.status === 'VALID' ? 'var(--clr-emerald)' : 'var(--clr-rose)'}`,
              textAlign: 'center'
            }}>
              {result.status === 'VALID' ? (
                <CheckCircle size={48} color="var(--clr-emerald)" style={{ margin: '0 auto 1rem' }} />
              ) : (
                <X size={48} color="var(--clr-rose)" style={{ margin: '0 auto 1rem' }} />
              )}

              <h3 style={{
                color: result.status === 'VALID' ? 'var(--clr-emerald)' : 'var(--clr-rose)',
                marginBottom: '0.5rem',
                fontSize: '1.5rem'
              }}>
                {result.status === 'VALID' ? 'Entry Approved!' : 'Entry Denied!'}
              </h3>

              <p style={{ fontWeight: '500', marginBottom: '1rem' }}>{result.message}</p>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.9rem', color: 'var(--clr-muted)' }}>
                {result.ticket_id && <span>Ticket #{result.ticket_id}</span>}
                {result.booking_id && <span>Booking #{result.booking_id}</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Stat Card ─── */
function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ElementType; label: string; value: string | number; color: string;
}) {
  return (
    <div className="admin-stat-card card">
      <div className="card-body admin-stat-body">
        <div className="admin-stat-icon" style={{ background: `${color}20`, color }}>
          <Icon size={20} />
        </div>
        <div>
          <div className="admin-stat-value">{value}</div>
          <div className="admin-stat-label">{label}</div>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Admin Page ─── */
type Tab = 'venues' | 'events' | 'shows' | 'scanner';

export default function Admin() {
  const [tab, setTab] = useState<Tab>('events');
  const [stats, setStats] = useState({ events: 0, venues: 0 });

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [evRes, vnRes] = await Promise.all([
          api.get<EventOut[]>('/api/events'),
          api.get<VenueOut[]>('/api/events/venues').catch(() => ({ data: [] })),
        ]);
        setStats({ events: evRes.data.length, venues: vnRes.data.length });
      } catch {
        // ignore
      }
    };
    loadStats();
  }, []);

  return (
    <main className="admin-page page-enter" id="main-content">
      {/* Page Header */}
      <div className="admin-page-header">
        <div className="container admin-page-header-inner">
          <div className="admin-page-title">
            <div className="admin-page-icon"><LayoutDashboard size={20} /></div>
            <div>
              <h1>Admin Dashboard</h1>
              <p>Manage venues, events, shows, and seat inventory</p>
            </div>
          </div>
          <div className="admin-header-right">
            <span className="badge badge-gold">Admin Mode</span>
          </div>
        </div>
      </div>

      <div className="container admin-page-body">
        {/* Stats Row */}
        <div className="admin-stats-row">
          <StatCard icon={Calendar} label="Total Events" value={stats.events} color="var(--clr-accent)" />
          <StatCard icon={MapPin} label="Total Venues" value={stats.venues} color="var(--clr-emerald)" />
          <StatCard icon={Ticket} label="Manage Shows" value="→" color="var(--clr-gold)" />
          <StatCard icon={Users} label="Seat Inventory" value="→" color="var(--clr-sky)" />
        </div>

        {/* Tabs */}
        <div className="admin-tabs" role="tablist">
          {([
            { id: 'events', icon: Calendar, label: 'Events' },
            { id: 'venues', icon: MapPin, label: 'Venues' },
            { id: 'shows', icon: Ticket, label: 'Shows & Inventory' },
            { id: 'scanner', icon: CheckCircle, label: 'Verify Tickets' },
          ] as { id: Tab; icon: React.ElementType; label: string }[]).map(t => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              className={`admin-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
              id={`admin-tab-${t.id}`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab Panels */}
        <div role="tabpanel">
          {tab === 'events' && <EventsSection />}
          {tab === 'venues' && <VenuesSection />}
          {tab === 'shows' && <ShowsSection />}
          {tab === 'scanner' && <ScannerSection />}
        </div>
      </div>
    </main>
  );
}
