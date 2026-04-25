import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, Ticket, AlertCircle, Shield } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/useAuth';
import type { TokenResponse } from '../types';
import './Auth.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/events';

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
      const { data } = await api.post<TokenResponse>('/api/auth/login', form);
      await login(data.access_token);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      // Handle different error response formats
      let msg = 'Invalid email or password.';

      if (typeof err === 'object' && err !== null && 'response' in err) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const response = (err as { response?: { data?: unknown; status?: number; statusText?: string } }).response;

        if (response?.data) {
          const data = response.data;

          if (typeof data === 'object' && data !== null && 'detail' in data) {
            const detail = (data as { detail?: unknown }).detail;

            if (typeof detail === 'string') {
              // FastAPI HTTPException format
              msg = detail;
            } else if (Array.isArray(detail)) {
              // Pydantic validation error format
              const firstError = detail[0];
              msg =
                typeof firstError === 'object' &&
                firstError !== null &&
                'msg' in firstError &&
                typeof (firstError as { msg?: unknown }).msg === 'string'
                  ? (firstError as { msg: string }).msg
                  : 'Invalid input data.';
            } else {
              // Other formats
              msg = JSON.stringify(data);
            }
          } else {
            msg = JSON.stringify(data);
          }
        } else {
          msg = `Error ${response?.status ?? 'Unknown'}: ${response?.statusText ?? 'Request failed'}`;
        }
      } else if (typeof err === 'object' && err !== null && 'request' in err) {
        // The request was made but no response was received
        msg = 'Network error. Please check your connection.';
      } else if (err instanceof Error) {
        // Something happened in setting up the request
        msg = err.message || 'An unexpected error occurred.';
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
        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-logo"><Ticket size={20} /></div>
          <span className="auth-logo-text">Event<strong>Vault</strong></span>
        </div>

        <div className="auth-card card">
          <div className="card-body auth-card-body">
            <div className="auth-header">
              <h1>Welcome back</h1>
              <p>Sign in to your account to continue</p>
            </div>

            {error && (
              <div className="alert alert-error" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form" noValidate>
              <div className="form-group">
                <label className="form-label" htmlFor="login-email">Email address</label>
                <div className="input-wrap">
                  <Mail size={16} className="input-icon" aria-hidden="true" />
                  <input
                    id="login-email"
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

              <div className="form-group">
                <label className="form-label" htmlFor="login-password">Password</label>
                <div className="input-wrap">
                  <Lock size={16} className="input-icon" aria-hidden="true" />
                  <input
                    id="login-password"
                    name="password"
                    type={showPass ? 'text' : 'password'}
                    className="form-input with-icon with-suffix"
                    placeholder="••••••••"
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
                    id="toggle-password-visibility"
                  >
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-full btn-lg"
                disabled={loading}
                id="login-submit-btn"
              >
                {loading ? <><span className="spinner" />Signing in…</> : 'Sign In'}
              </button>
            </form>

            <p className="auth-switch">
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">Create one</Link>
            </p>
            <p className="auth-switch">
              <Shield size={13} className="auth-inline-icon" aria-hidden="true" />
              Admin user?{' '}
              <Link to="/admin/login" className="auth-link">Sign in as admin</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}