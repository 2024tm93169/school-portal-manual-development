import React, { useEffect, useState, useCallback } from 'react';

export default function ManageRequestsPage() {
  const role = (localStorage.getItem('userRole') || '').trim().toLowerCase();
  const token = localStorage.getItem('token') || '';

  // Guard: if somehow routed here but not admin, render a clear message
  if (role !== 'admin') {
    return (
      <div style={{ padding: '0 20px' }}>
        <h2>Manage Requests</h2>
        <p style={{ color: 'crimson' }}>You are not an admin. Current role: <b>{String(role)}</b></p>
      </div>
    );
  }

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  const authHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  });

  const normalize = (r) => ({
    ...r,
    status: String(r.status || '').trim().toUpperCase(),
    item_name: r.item_name || r.itemName || '-',
    user_name: r.user_name || r.userName || '-',
    user_email: r.user_email || r.userEmail || '-',
  });

  const load = useCallback(async () => {
    setLoading(true);
    setErr('');
    try {
      const res = await fetch('/api/requests', {
        method: 'GET',
        headers: authHeaders(),
        cache: 'no-store',
      });
      const text = await res.text();
      let data = [];
      try { data = text ? JSON.parse(text) : []; } catch (e) {
        console.error('Bad JSON from /api/requests:', text);
      }
      if (!res.ok) {
        setErr((data && data.error) ? data.error : `Failed to load (HTTP ${res.status})`);
        setRows([]);
        return;
      }
      const normalized = Array.isArray(data) ? data.map(normalize) : [];
      setRows(normalized);
      // Debug log
      console.log('Loaded requests:', normalized);
    } catch (e) {
      console.error('GET /api/requests failed', e);
      setErr('Network error loading requests');
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const act = async (id, action) => {
    try {
      const path =
        action === 'approve' ? `/api/requests/${id}/approve` :
        action === 'reject'  ? `/api/requests/${id}/reject`  :
        action === 'return'  ? `/api/requests/${id}/return`  : null;

      if (!path) return;
      console.log('POST', path);

      const res = await fetch(path, {
        method: 'POST',
        headers: authHeaders(),
      });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch {}

      if (!res.ok) {
        const msg = (data && data.error) ? data.error : `Action ${action} failed (HTTP ${res.status})`;
        console.error('Action error:', msg, 'Response:', text);
        alert(msg);
        return;
      }

      // Success → reload table
      await load();
    } catch (e) {
      console.error('Action network error', e);
      alert('Network error performing action');
    }
  };

  return (
    <div style={{ padding: '0 20px' }}>
      <h2>Manage Requests</h2>

      {/* Tiny debug banner to confirm role + counts */}
      <div style={{ fontSize: 12, color: '#555', marginBottom: 10 }}>
        Role: <b>{role}</b> | Rows: <b>{rows.length}</b> | First status:{' '}
        <b>{rows[0]?.status || 'n/a'}</b>
      </div>

      {loading && <p>Loading…</p>}
      {err && <p style={{ color: 'crimson' }}>{err}</p>}

      <table border="1" cellPadding="8" cellSpacing="0" style={{ width: '100%', maxWidth: 900 }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Item</th>
            <th>Requested By</th>
            <th>Status</th>
            <th>Requested</th>
            <th>Approved</th>
            <th>Returned</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {!loading && rows.length === 0 && !err && (
            <tr><td colSpan="8">No requests to display.</td></tr>
          )}

          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.item_name}</td>
              <td>{r.user_name} ({r.user_email})</td>
              <td>{r.status}</td>
              <td>{r.request_date || '-'}</td>
              <td>{r.approve_date || '-'}</td>
              <td>{r.return_date || '-'}</td>
              <td>
                {r.status === 'PENDING' && (
                  <>
                    <button onClick={() => act(r.id, 'approve')}>Approve</button>{' '}
                    <button onClick={() => act(r.id, 'reject')}>Reject</button>
                  </>
                )}
                {r.status === 'APPROVED' && (
                  <button onClick={() => act(r.id, 'return')}>Mark Returned</button>
                )}
                {r.status !== 'PENDING' && r.status !== 'APPROVED' && <em>—</em>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
