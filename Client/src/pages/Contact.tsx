import React from 'react';

export default function Contact() {
  return (
    <main className="container page-enter" style={{ padding: 'var(--space-2xl) var(--space-md)', maxWidth: '800px', margin: '0 auto', color: 'var(--clr-text)' }}>
      <h1 style={{ marginBottom: 'var(--space-xl)', color: 'var(--clr-accent)' }}>Contact Us</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', lineHeight: '1.8', color: 'var(--clr-text-secondary)' }}>
        <p>If you have any questions, concerns, or need assistance with your event bookings, we are here to help!</p>
        
        <div className="card" style={{ padding: 'var(--space-xl)', marginTop: 'var(--space-md)', background: 'var(--clr-surface)' }}>
          <h3 style={{ color: 'var(--clr-text)', marginBottom: 'var(--space-md)' }}>Get in Touch</h3>
          <p><strong>Email:</strong> support@eventvault.com</p>
          <p><strong>Phone:</strong> +91 98765 43210</p>
          <p><strong>Address:</strong><br />
            EventVault Technologies Pvt. Ltd.<br />
            123 Startup Hub, Tech Park,<br />
            Bengaluru, Karnataka 560001,<br />
            India
          </p>
        </div>
        
        <p style={{ marginTop: 'var(--space-xl)' }}>Our support team is available Monday to Friday, 9:00 AM to 6:00 PM IST.</p>
      </div>
    </main>
  );
}
