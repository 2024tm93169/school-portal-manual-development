import React, { useState, useEffect } from 'react';

function MyRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');

  const fetchRequests = async () => {
    try {
      const res = await fetch('/api/requests', {
        headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
      });
      const data = await res.json();
      if (res.ok) setRequests(data);
      else setError(data.error || 'Failed to fetch requests');
    } catch (err) { setError('Network error'); }
  };

  useEffect(() => { fetchRequests(); }, []);

  return (
    <div style={{ padding: '0 20px' }}>
      <h2>My Requests</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table border="1" cellPadding="8" cellSpacing="0">
        <thead><tr><th>Item</th><th>Status</th><th>Requested Date</th><th>Approved Date</th><th>Returned Date</th></tr></thead>
        <tbody>
          {requests.map(req => (
            <tr key={req.id}>
              <td>{req.item_name}</td>
              <td>{req.status}</td>
              <td>{req.request_date || '-'}</td>
              <td>{req.approve_date || '-'}</td>
              <td>{req.return_date || '-'}</td>
            </tr>
          ))}
          {requests.length === 0 && !error && <tr><td colSpan="5">No requests made yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export default MyRequestsPage;
