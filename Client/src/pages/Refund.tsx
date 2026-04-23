import React from 'react';

export default function Refund() {
  return (
    <main className="container page-enter" style={{ padding: 'var(--space-2xl) var(--space-md)', maxWidth: '800px', margin: '0 auto', color: 'var(--clr-text)' }}>
      <h1 style={{ marginBottom: 'var(--space-xl)', color: 'var(--clr-accent)' }}>Refund & Cancellation Policy</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', lineHeight: '1.8', color: 'var(--clr-text-secondary)' }}>
        <p>Thank you for buying tickets at EventVault.</p>
        
        <h3 style={{ color: 'var(--clr-text)' }}>Cancellation by User</h3>
        <p>Due to the digital and time-sensitive nature of event tickets, <strong>all ticket sales are generally final and non-refundable</strong> unless otherwise specified by the specific Event Organizer.</p>
        <p>If you wish to cancel your booking, you must contact us at least 48 hours before the event start time. Approval of any cancellation or refund request is strictly at the discretion of the Event Organizer.</p>
        
        <h3 style={{ color: 'var(--clr-text)' }}>Cancellation by Organizer</h3>
        <p>In the event that a show, concert, or match is officially cancelled or postponed by the Event Organizer, users will be entitled to a full refund of the ticket price. Convenience fees or payment gateway fees may be non-refundable.</p>
        
        <h3 style={{ color: 'var(--clr-text)' }}>Refund Processing</h3>
        <p>Approved refunds will be processed automatically to the original method of payment (Credit Card, Debit Card, or UPI) within 5 to 7 business days.</p>
        
        <h3 style={{ color: 'var(--clr-text)' }}>Contact Us</h3>
        <p>If you have any questions about our Returns and Refunds Policy, please contact us.</p>
      </div>
    </main>
  );
}
