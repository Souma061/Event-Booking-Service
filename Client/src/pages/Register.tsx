import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Phone, Ticket, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { TokenResponse } from '../types';
import './Auth.css';

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  });
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
      // Register
      await api.post('/api/auth/register', {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone,
        password: form.password,
      });
      // Auto-login
      const { data } = await api.post<TokenResponse>('/api/auth/login', {
        email: form.email,
        password: form.password,
      });
      setSuccess(true);
      await login(data.access_token);
      setTimeout(() => navigate('/events'), 1200);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Registration failed. Please try again.');
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
