import { Link } from 'react-router-dom';
import { Ticket, Github, Twitter, Instagram } from 'lucide-react';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer" role="contentinfo">
      <div className="container footer-inner">
        {/* Brand */}
        <div className="footer-brand">
          <Link to="/" className="footer-logo" aria-label="EventVault">
            <div className="footer-logo-icon"><Ticket size={16} /></div>
            <span>Event<strong>Vault</strong></span>
          </Link>
          <p className="footer-tagline">Discover, book, and experience the best events near you.</p>
          <div className="footer-social">
            <a href="#" aria-label="GitHub" className="social-link"><Github size={17} /></a>
            <a href="#" aria-label="Twitter" className="social-link"><Twitter size={17} /></a>
            <a href="#" aria-label="Instagram" className="social-link"><Instagram size={17} /></a>
          </div>
        </div>

        {/* Links */}
        <div className="footer-links-grid">
          <div className="footer-col">
            <h4 className="footer-col-title">Product</h4>
            <nav>
              <Link to="/events" className="footer-link">Browse Events</Link>
              <Link to="/bookings" className="footer-link">My Bookings</Link>
              <Link to="/register" className="footer-link">Create Account</Link>
            </nav>
          </div>
          <div className="footer-col">
            <h4 className="footer-col-title">Support</h4>
            <nav>
              <a href="#" className="footer-link">Help Center</a>
              <a href="#" className="footer-link">Contact Us</a>
              <a href="#" className="footer-link">Cancellation Policy</a>
            </nav>
          </div>
          <div className="footer-col">
            <h4 className="footer-col-title">Legal</h4>
            <nav>
              <a href="#" className="footer-link">Privacy Policy</a>
              <a href="#" className="footer-link">Terms of Service</a>
              <a href="#" className="footer-link">Cookie Policy</a>
            </nav>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container footer-bottom-inner">
          <p>© {new Date().getFullYear()} EventVault. All rights reserved.</p>
          <p>Built with ♥ for live experiences</p>
        </div>
      </div>
    </footer>
  );
}
