import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Sidebar from './components/Sidebar'
import ChatbotWidget from './components/ChatbotWidget'

import Login from './pages/Login'
import Register from './pages/Register'
import PatientDashboard from './pages/PatientDashboard'
import DoctorDashboard from './pages/DoctorDashboard'
import PatientProfilePage from './pages/PatientProfilePage'
import AdminPanel from './pages/AdminPanel'
import DiabetesPrediction from './pages/DiabetesPrediction'
import HeartPrediction from './pages/HeartPrediction'
import XrayPrediction from './pages/XrayPrediction'

function AppLayout({ children }) {
  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">{children}</main>
      <ChatbotWidget />
    </div>
  )
}

function AppRoutes() {
  const { user } = useAuth()
  const isDoctor = user?.role === 'doctor' || user?.role === 'admin'

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Root redirect */}
      <Route path="/" element={
        user ? <Navigate to={isDoctor ? '/doctor' : '/patient'} replace />
             : <Navigate to="/login" replace />
      } />

      {/* ── Patient routes ── */}
      <Route path="/patient" element={
        <PrivateRoute roles={['patient']}>
          <AppLayout><PatientDashboard /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/patient/predict/diabetes" element={
        <PrivateRoute roles={['patient']}>
          <AppLayout><DiabetesPrediction /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/patient/predict/heart" element={
        <PrivateRoute roles={['patient']}>
          <AppLayout><HeartPrediction /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/patient/predict/xray" element={
        <PrivateRoute roles={['patient']}>
          <AppLayout><XrayPrediction /></AppLayout>
        </PrivateRoute>
      } />

      {/* ── Doctor routes ── */}
      <Route path="/doctor" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><DoctorDashboard /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/doctor/patients" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><DoctorDashboard /></AppLayout>
        </PrivateRoute>
      } />
      {/* Full patient profile — doctor clicks from dashboard */}
      <Route path="/doctor/patients/:patientId" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><PatientProfilePage /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/doctor/predict/diabetes" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><DiabetesPrediction /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/doctor/predict/heart" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><HeartPrediction /></AppLayout>
        </PrivateRoute>
      } />
      <Route path="/doctor/predict/xray" element={
        <PrivateRoute roles={['doctor', 'admin']}>
          <AppLayout><XrayPrediction /></AppLayout>
        </PrivateRoute>
      } />

      {/* ── Admin routes ── */}
      <Route path="/admin" element={
        <PrivateRoute roles={['admin']}>
          <AppLayout><AdminPanel /></AppLayout>
        </PrivateRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
