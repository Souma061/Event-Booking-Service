import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, Eye, EyeOff, Lock, Mail, Shield, Ticket } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/useAuth';
import type { TokenResponse } from '../types';
import './Auth.css';

export default function AdminLogin() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/admin';

  const [form, setForm] = useState({ email: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const { data } = await api.post<TokenResponse>('/api/auth/admin/login', form);
      await login(data.access_token);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      // Handle different error response formats
      let msg = 'Admin sign in failed.';

      const isRecord = (value: unknown): value is Record<string, unknown> =>
        typeof value === 'object' && value !== null;

      if (isRecord(err)) {
        const response = isRecord(err['response']) ? err['response'] : null;

        if (response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          const data = response['data'];

          if (isRecord(data)) {
            const detail = data['detail'];

            if (typeof detail === 'string') {
              // FastAPI HTTPException format
              msg = detail;
            } else if (Array.isArray(detail)) {
              // Pydantic validation error format
              const firstError = detail[0];
              if (isRecord(firstError) && typeof firstError['msg'] === 'string') {
                msg = firstError['msg'];
              } else {
                msg = 'Invalid input data.';
              }
            } else {
              // Other formats
              msg = JSON.stringify(data);
            }
          } else {
            const status = typeof response['status'] === 'number' ? response['status'] : 'Unknown';
            const statusText = typeof response['statusText'] === 'string' ? response['statusText'] : 'Error';
            msg = `Error ${status}: ${statusText}`;
          }
        } else if (err['request']) {
          // The request was made but no response was received
          msg = 'Network error. Please check your connection.';
        } else if (typeof err['message'] === 'string') {
          // Something happened in setting up the request
          msg = err['message'];
        } else {
          msg = 'An unexpected error occurred.';
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }

      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page page-enter" id="main-content">
      <div className="auth-glow" aria-hidden="true" />
      <div className="auth-container">
        <div className="auth-brand">
          <div className="auth-logo"><Ticket size={20} /></div>
          <span className="auth-logo-text">Event<strong>Vault</strong></span>
        </div>

        <div className="auth-card card">
          <div className="card-body auth-card-body">
            <div className="auth-header">
              <div className="auth-role-icon" aria-hidden="true">
                <Shield size={22} />
              </div>
              <h1>Admin sign in</h1>
              <p>Use an administrator account to access the control panel</p>
            </div>

            {error && (
              <div className="alert alert-error" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form" noValidate>
              <div className="form-group">
                <label className="form-label" htmlFor="admin-email">Email address</label>
                <div className="input-wrap">
                  <Mail size={16} className="input-icon" aria-hidden="true" />
                  <input
                    id="admin-email"
                    name="email"
                    type="email"
                    className="form-input with-icon"
                    placeholder="admin@example.com"
                    value={form.email}
                    onChange={handleChange}
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="admin-password">Password</label>
                <div className="input-wrap">
                  <Lock size={16} className="input-icon" aria-hidden="true" />
                  <input
                    id="admin-password"
                    name="password"
                    type={showPass ? 'text' : 'password'}
                    className="form-input with-icon with-suffix"
                    placeholder="Admin password"
                    value={form.password}
                    onChange={handleChange}
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    className="input-suffix-btn"
                    onClick={() => setShowPass(!showPass)}
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    id="admin-toggle-password-visibility"
                  >
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-full btn-lg"
                disabled={loading}
                id="admin-login-submit-btn"
              >
                {loading ? <><span className="spinner" />Signing in...</> : 'Sign In as Admin'}
              </button>
            </form>

            <p className="auth-switch">
              Customer account?{' '}
              <Link to="/login" className="auth-link">Use normal sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}