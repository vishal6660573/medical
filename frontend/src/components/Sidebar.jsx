import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Activity, User, Users, FileText, Pill, BarChart2, LogOut, Heart, Scan, Home, Shield } from 'lucide-react'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  const initials = user?.full_name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
  const isDoctor = user?.role === 'doctor' || user?.role === 'admin'
  const isAdmin  = user?.role === 'admin'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-dot" />
        <span className="sidebar-logo-text">MediSense</span>
      </div>

      <nav className="sidebar-nav">
        <span className="sidebar-section">Overview</span>

        {isDoctor ? (
          <NavLink to="/doctor" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Home size={16}/> Dashboard
          </NavLink>
        ) : (
          <NavLink to="/patient" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Home size={16}/> Dashboard
          </NavLink>
        )}

        {isDoctor && (
          <>
            <span className="sidebar-section" style={{ marginTop:12 }}>Patients</span>
            <NavLink to="/doctor/patients" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Users size={16}/> All Patients
            </NavLink>
          </>
        )}

        <span className="sidebar-section" style={{ marginTop:12 }}>Predictions</span>
        <NavLink to={isDoctor ? '/doctor/predict/diabetes' : '/patient/predict/diabetes'}
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Activity size={16}/> Diabetes
        </NavLink>
        <NavLink to={isDoctor ? '/doctor/predict/heart' : '/patient/predict/heart'}
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Heart size={16}/> Heart Disease
        </NavLink>
        <NavLink to={isDoctor ? '/doctor/predict/xray' : '/patient/predict/xray'}
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Scan size={16}/> X-Ray Analysis
        </NavLink>

        {!isDoctor && (
          <>
            <span className="sidebar-section" style={{ marginTop:12 }}>My Records</span>
            <NavLink to="/patient/visits" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <FileText size={16}/> Visit History
            </NavLink>
            <NavLink to="/patient/medications" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Pill size={16}/> Medications
            </NavLink>
            <NavLink to="/patient/predictions" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <BarChart2 size={16}/> Prediction History
            </NavLink>
          </>
        )}

        {isAdmin && (
          <>
            <span className="sidebar-section" style={{ marginTop:12 }}>Administration</span>
            <NavLink to="/admin" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Shield size={16}/> Admin Panel
            </NavLink>
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.full_name}</div>
            <div className="sidebar-user-role">{user?.role}</div>
          </div>
        </div>
        <button className="sidebar-link btn-danger" style={{ marginTop:4 }} onClick={handleLogout}>
          <LogOut size={16}/> Sign Out
        </button>
      </div>
    </aside>
  )
}
