import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { loginUser } from '../services/api'
import toast from 'react-hot-toast'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handle = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await loginUser(form.email, form.password)
      login(data)
      toast.success(`Welcome back, ${data.full_name}`)
      navigate(data.role === 'doctor' || data.role === 'admin' ? '/doctor' : '/patient')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card page-enter">
        <div className="auth-logo">
          <div className="auth-logo-dot" />
          <span className="auth-logo-text">MediSense</span>
        </div>

        <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 6 }}>Sign in</h1>
        <p style={{ color: 'var(--text-mid)', fontSize: '0.875rem', marginBottom: 28 }}>
          Access your healthcare dashboard
        </p>

        <form onSubmit={handle}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="doctor@hospital.com"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <button className="btn btn-primary btn-full" type="submit" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

        <hr className="divider" style={{ margin: '24px 0' }} />
        <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-mid)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--teal)', textDecoration: 'none', fontWeight: 500 }}>
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
