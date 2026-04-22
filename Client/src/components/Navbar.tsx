import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Ticket, Menu, X, LogOut, User, LayoutDashboard, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/useAuth';
import './Navbar.css';

export default function Navbar() {
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setDropdownOpen(false);
  };

  return (
    <header className="navbar" role="banner">
      <div className="container navbar-inner">
        {/* Logo */}
        <Link to="/" className="navbar-logo" aria-label="EventVault home">
          <div className="navbar-logo-icon">
            <Ticket size={18} />
          </div>
          <span className="navbar-logo-text">Event<strong>Vault</strong></span>
        </Link>

        {/* Desktop Nav */}
        <nav className="navbar-links" aria-label="Main navigation">
          <NavLink to="/events" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Events
          </NavLink>
          {isAuthenticated && (
            <NavLink to="/bookings" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              My Bookings
            </NavLink>
          )}
          {isAdmin && (
            <NavLink to="/admin" className={({ isActive }) => isActive ? 'nav-link active nav-admin' : 'nav-link nav-admin'}>
              Admin
            </NavLink>
          )}
        </nav>

        {/* Auth Area */}
        <div className="navbar-auth">
          {isAuthenticated ? (
            <div className="user-menu">
              <button
                className="user-menu-trigger"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                aria-haspopup="true"
                aria-expanded={dropdownOpen}
                id="user-menu-btn"
              >
                <div className="user-avatar" aria-hidden="true">
                  {user?.full_name.charAt(0).toUpperCase()}
                </div>
                <span className="user-name">{user?.full_name.split(' ')[0]}</span>
                <ChevronDown size={14} className={dropdownOpen ? 'chevron open' : 'chevron'} />
              </button>

              {dropdownOpen && (
                <div className="user-dropdown" role="menu" aria-labelledby="user-menu-btn">
                  <div className="dropdown-header">
                    <p className="dropdown-name">{user?.full_name}</p>
                    <p className="dropdown-email">{user?.email}</p>
                  </div>
                  <div className="dropdown-divider" />
                  <Link
                    to="/me"
                    className="dropdown-item"
                    role="menuitem"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <User size={15} /> Profile
                  </Link>
                  <Link
                    to="/bookings"
                    className="dropdown-item"
                    role="menuitem"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <Ticket size={15} /> My Bookings
                  </Link>
                  {isAdmin && (
                    <Link
                      to="/admin"
                      className="dropdown-item"
                      role="menuitem"
                      onClick={() => setDropdownOpen(false)}
                    >
                      <LayoutDashboard size={15} /> Admin Panel
                    </Link>
                  )}
                  <div className="dropdown-divider" />
                  <button className="dropdown-item danger" onClick={handleLogout} role="menuitem">
                    <LogOut size={15} /> Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-ghost btn-sm">Sign In</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Get Started</Link>
            </div>
          )}

          {/* Mobile Toggle */}
          <button
            className="mobile-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="mobile-menu" role="dialog" aria-label="Mobile navigation">
          <nav className="mobile-nav">
            <NavLink to="/events" className="mobile-nav-link" onClick={() => setMenuOpen(false)}>Events</NavLink>
            {isAuthenticated && (
              <NavLink to="/bookings" className="mobile-nav-link" onClick={() => setMenuOpen(false)}>My Bookings</NavLink>
            )}
            {isAdmin && (
              <NavLink to="/admin" className="mobile-nav-link mobile-admin" onClick={() => setMenuOpen(false)}>Admin</NavLink>
            )}
            <div className="mobile-divider" />
            {isAuthenticated ? (
              <button className="mobile-nav-link danger" onClick={handleLogout}>Sign Out</button>
            ) : (
              <>
                <Link to="/login" className="mobile-nav-link" onClick={() => setMenuOpen(false)}>Sign In</Link>
                <Link to="/register" className="mobile-nav-link accent" onClick={() => setMenuOpen(false)}>Get Started</Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
