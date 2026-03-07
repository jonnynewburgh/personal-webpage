import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import ApplicationForm from './pages/ApplicationForm.jsx';
import ApplicationDetail from './pages/ApplicationDetail.jsx';
import ReviewResults from './pages/ReviewResults.jsx';
import AdverseActionNotice from './pages/AdverseActionNotice.jsx';
import PolicyManagement from './pages/PolicyManagement.jsx';

function NavBar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-900 text-white px-4 py-3 flex items-center justify-between shadow">
      <div className="flex items-center gap-6">
        <Link to="/" className="font-bold text-lg tracking-tight">JIFLA Loan Review</Link>
        <Link to="/" className="text-blue-200 hover:text-white text-sm">Dashboard</Link>
        <Link to="/applications/new" className="text-blue-200 hover:text-white text-sm">New Application</Link>
        <Link to="/policy" className="text-blue-200 hover:text-white text-sm">Policy</Link>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-blue-300">{user?.username}</span>
        <button onClick={handleLogout} className="bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-xs">
          Sign Out
        </button>
      </div>
    </nav>
  );
}

function ProtectedLayout({ user, onLogout, children }) {
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar user={user} onLogout={onLogout} />
      <main className="flex-1 p-4 max-w-6xl mx-auto w-full">{children}</main>
      <footer className="text-center text-xs text-gray-400 py-3 border-t">
        JIFLA Loan Review Tool — Confidential. For authorized staff only.
      </footer>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        if (data.authenticated) setUser(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen text-gray-500">Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login onLogin={setUser} />} />
        <Route path="/" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <Dashboard />
          </ProtectedLayout>
        } />
        <Route path="/applications/new" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <ApplicationForm />
          </ProtectedLayout>
        } />
        <Route path="/applications/:id" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <ApplicationDetail />
          </ProtectedLayout>
        } />
        <Route path="/applications/:id/edit" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <ApplicationForm />
          </ProtectedLayout>
        } />
        <Route path="/reviews/:reviewId" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <ReviewResults />
          </ProtectedLayout>
        } />
        <Route path="/applications/:id/adverse-action" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <AdverseActionNotice />
          </ProtectedLayout>
        } />
        <Route path="/policy" element={
          <ProtectedLayout user={user} onLogout={() => setUser(null)}>
            <PolicyManagement />
          </ProtectedLayout>
        } />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
