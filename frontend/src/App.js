import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import NavBar from './components/NavBar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EquipmentListPage from './pages/EquipmentListPage';
import MyRequestsPage from './pages/MyRequestsPage';
import ManageRequestsPage from './pages/ManageRequestsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import EquipmentFormPage from './pages/EquipmentFormPage';

const RequireAuth = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

// Normalize the role once per render
const useNormalizedRole = () =>
  (localStorage.getItem('userRole') || '').trim().toLowerCase();

function App() {
  const role = useNormalizedRole();

  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/"
          element={
            <RequireAuth>
              <EquipmentListPage />
            </RequireAuth>
          }
        />

        <Route
          path="/requests"
          element={
            <RequireAuth>
              {(localStorage.getItem('userRole') || '').trim().toLowerCase() === 'admin'
                ? <ManageRequestsPage />
                : <MyRequestsPage />}
            </RequireAuth>
          }
        />

        <Route
          path="/analytics"
          element={
            <RequireAuth>
              {role === 'admin' ? <AnalyticsPage /> : <Navigate to="/" replace />}
            </RequireAuth>
          }
        />

        <Route
          path="/equipment/new"
          element={
            <RequireAuth>
              <EquipmentFormPage />
            </RequireAuth>
          }
        />

        <Route
          path="/equipment/edit/:id"
          element={
            <RequireAuth>
              <EquipmentFormPage />
            </RequireAuth>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;

