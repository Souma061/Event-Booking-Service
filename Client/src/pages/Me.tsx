import { User, Mail, Phone, Calendar, Shield } from 'lucide-react';
import { useAuth } from '../context/useAuth';

export default function Me() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <main className="page-enter" style={{ flex: 1, padding: 'var(--space-2xl) 0' }}>
      <div className="container" style={{ maxWidth: '600px' }}>
        <div style={{ marginBottom: 'var(--space-xl)', textAlign: 'center' }}>
          <div 
            style={{ 
              width: '96px', 
              height: '96px', 
              borderRadius: '50%', 
              background: 'linear-gradient(135deg, var(--clr-accent) 0%, var(--clr-accent-2) 100%)',
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              fontSize: '2.5rem',
              fontWeight: '800',
              margin: '0 auto var(--space-md)',
              color: 'var(--clr-white)',
              boxShadow: '0 8px 32px rgba(124, 111, 255, 0.3)'
            }}
          >
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '8px' }}>{user.full_name}</h1>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <span className={`badge ${user.role === 'ADMIN' ? 'badge-gold' : 'badge-emerald'}`}>
              {user.role}
            </span>
            {user.is_active && (
              <span className="badge badge-sky">Active Account</span>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <h3 style={{ fontSize: '1.125rem', marginBottom: 'var(--space-md)', color: 'var(--clr-text-2)' }}>
              Profile Information
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--clr-border)' }}>
                <div style={{ color: 'var(--clr-text-3)' }}><User size={18} /></div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Full Name</p>
                  <p style={{ fontWeight: '500' }}>{user.full_name}</p>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--clr-border)' }}>
                <div style={{ color: 'var(--clr-text-3)' }}><Mail size={18} /></div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email Address</p>
                  <p style={{ fontWeight: '500' }}>{user.email}</p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--clr-border)' }}>
                <div style={{ color: 'var(--clr-text-3)' }}><Phone size={18} /></div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Phone Number</p>
                  <p style={{ fontWeight: '500' }}>{user.phone || 'Not provided'}</p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--clr-border)' }}>
                <div style={{ color: 'var(--clr-text-3)' }}><Shield size={18} /></div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Account Role</p>
                  <p style={{ fontWeight: '500' }}>{user.role}</p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0' }}>
                <div style={{ color: 'var(--clr-text-3)' }}><Calendar size={18} /></div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Member Since</p>
                  <p style={{ fontWeight: '500' }}>{new Date(user.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </main>
  );
}
