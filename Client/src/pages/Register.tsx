import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Phone, Ticket, AlertCircle, CheckCircle, Shield } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/useAuth';
import type { TokenResponse } from '../types';
import './Auth.css';

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/events';

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    admin_secret: '',
  });
  const [isAdminRegistration, setIsAdminRegistration] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setError('');
  };

  const validate = () => {
    if (!form.full_name.trim()) return 'Full name is required.';
    if (!form.email.includes('@')) return 'Enter a valid email address.';
    if (!/^\+?[\d\s-]{7,15}$/.test(form.phone)) return 'Enter a valid phone number.';
    if (form.password.length < 6) return 'Password must be at least 6 characters.';
    if (form.password !== form.confirm_password) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationErr = validate();
    if (validationErr) { setError(validationErr); return; }

    setLoading(true);
    setError('');
    try {
      const payload: Record<string, string> = {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone,
        password: form.password,
      };
      if (isAdminRegistration && form.admin_secret) {
        payload.admin_secret = form.admin_secret;
      }

      await api.post('/api/auth/register', payload);
      // Auto-login
      const { data } = await api.post<TokenResponse>('/api/auth/login', {
        email: form.email,
        password: form.password,
      });
      setSuccess(true);
      await login(data.access_token);
      setTimeout(() => navigate(from, { replace: true }), 1200);
    } catch (err: unknown) {
      // Handle different error response formats
      let msg = 'Registration failed. Please try again.';
      
      if (typeof err === 'object' && err !== null) {
        const error = err as {
          response?: {
            data?: {
              detail?: unknown;
            };
            status: number;
            statusText: string;
          };
          request?: unknown;
          message?: string;
        };

        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          if (error.response.data) {
            if (typeof error.response.data.detail === 'string') {
              // FastAPI HTTPException format
              msg = error.response.data.detail;
            } else if (Array.isArray(error.response.data.detail)) {
              // Pydantic validation error format
              const firstError = error.response.data.detail[0] as { msg?: string };
              msg = firstError.msg || 'Invalid input data.';
            } else {
              // Other formats
              msg = JSON.stringify(error.response.data);
            }
          } else {
            msg = `Error ${error.response.status}: ${error.response.statusText}`;
          }
        } else if (error.request) {
          // The request was made but no response was received
          msg = 'Network error. Please check your connection.';
        } else {
          // Something happened in setting up the request
          msg = error.message || 'An unexpected error occurred.';
        }
      } else {
        msg = 'An unexpected error occurred.';
      }
      
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page page-enter" id="main-content">
      <div className="auth-glow" aria-hidden="true" />
      <div className="auth-container auth-container--wide">
        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-logo"><Ticket size={20} /></div>
          <span className="auth-logo-text">Event<strong>Vault</strong></span>
        </div>

        <div className="auth-card card">
          <div className="card-body auth-card-body">
            <div className="auth-header">
              <h1>Create your account</h1>
              <p>Join thousands of event-goers today</p>
            </div>

            {error && (
              <div className="alert alert-error" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="alert alert-success" role="status">
                <CheckCircle size={16} />
                <span>Account created! Redirecting…</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form" noValidate>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-name">Full name</label>
                  <div className="input-wrap">
                    <User size={16} className="input-icon" aria-hidden="true" />
                    <input
                      id="reg-name"
                      name="full_name"
                      type="text"
                      className="form-input with-icon"
                      placeholder="Jane Doe"
                      value={form.full_name}
                      onChange={handleChange}
                      autoComplete="name"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="reg-phone">Phone number</label>
                  <div className="input-wrap">
                    <Phone size={16} className="input-icon" aria-hidden="true" />
                    <input
                      id="reg-phone"
                      name="phone"
                      type="tel"
                      className="form-input with-icon"
                      placeholder="+91 98765 43210"
                      value={form.phone}
                      onChange={handleChange}
                      autoComplete="tel"
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="reg-email">Email address</label>
                <div className="input-wrap">
                  <Mail size={16} className="input-icon" aria-hidden="true" />
                  <input
                    id="reg-email"
                    name="email"
                    type="email"
                    className="form-input with-icon"
                    placeholder="you@example.com"
                    value={form.email}
                    onChange={handleChange}
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-password">Password</label>
                  <div className="input-wrap">
                    <Lock size={16} className="input-icon" aria-hidden="true" />
                    <input
                      id="reg-password"
                      name="password"
                      type={showPass ? 'text' : 'password'}
                      className="form-input with-icon with-suffix"
                      placeholder="Min 6 characters"
                      value={form.password}
                      onChange={handleChange}
                      autoComplete="new-password"
                      required
                    />
                    <button
                      type="button"
                      className="input-suffix-btn"
                      onClick={() => setShowPass(!showPass)}
                      aria-label={showPass ? 'Hide password' : 'Show password'}
                      id="reg-toggle-pass"
                    >
                      {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="reg-confirm">Confirm password</label>
                  <div className="input-wrap">
                    <Lock size={16} className="input-icon" aria-hidden="true" />
                    <input
                      id="reg-confirm"
                      name="confirm_password"
                      type={showPass ? 'text' : 'password'}
                      className="form-input with-icon"
                      placeholder="Repeat password"
                      value={form.confirm_password}
                      onChange={handleChange}
                      autoComplete="new-password"
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  id="admin-toggle" 
                  checked={isAdminRegistration} 
                  onChange={(e) => setIsAdminRegistration(e.target.checked)} 
                  style={{ cursor: 'pointer' }}
                />
                <label htmlFor="admin-toggle" className="form-label" style={{ margin: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Shield size={14} color="var(--clr-gold)" />
                  Register as Admin
                </label>
              </div>

              {isAdminRegistration && (
                <div className="form-group slide-down">
                  <label className="form-label" htmlFor="reg-admin-secret">Admin Secret Key</label>
                  <div className="input-wrap">
                    <Shield size={16} className="input-icon" aria-hidden="true" color="var(--clr-gold)" />
                    <input
                      id="reg-admin-secret"
                      name="admin_secret"
                      type="password"
                      className="form-input with-icon"
                      placeholder="Enter the secret key to get admin rights"
                      value={form.admin_secret}
                      onChange={handleChange}
                      required={isAdminRegistration}
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="btn btn-primary btn-full btn-lg"
                disabled={loading || success}
                id="register-submit-btn"
              >
                {loading ? <><span className="spinner" />Creating account…</> : 'Create Account'}
              </button>
            </form>

            <p className="auth-switch">
              Already have an account?{' '}
              <Link to="/login" className="auth-link">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}