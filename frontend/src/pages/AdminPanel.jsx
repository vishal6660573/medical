import { useEffect, useState } from 'react'
import { listAllUsers, updateUserStatus } from '../services/api'
import { Shield, UserCheck, UserX, Users } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AdminPanel() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const load = async () => {
    try { const { data } = await listAllUsers(); setUsers(data) }
    catch { toast.error('Failed to load users') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const toggleStatus = async (user) => {
    try {
      await updateUserStatus(user.id, !user.is_active)
      toast.success(`${user.full_name} ${!user.is_active ? 'activated' : 'deactivated'}`)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update')
    }
  }

  const filtered = users.filter(u => filter === 'all' || u.role === filter)
  const counts = {
    all: users.length,
    patient: users.filter(u => u.role === 'patient').length,
    doctor: users.filter(u => u.role === 'doctor').length,
    admin: users.filter(u => u.role === 'admin').length,
  }

  return (
    <div className="page-enter">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <Shield size={22} color="var(--teal)" />
        <h1 className="page-title" style={{ margin: 0 }}>Admin Panel</h1>
      </div>
      <p className="page-sub">Manage all users — activate, deactivate, and monitor roles</p>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="stat-card"><div className="stat-value">{counts.all}</div><div className="stat-label">Total Users</div></div>
        <div className="stat-card"><div className="stat-value">{counts.patient}</div><div className="stat-label">Patients</div></div>
        <div className="stat-card"><div className="stat-value">{counts.doctor}</div><div className="stat-label">Doctors</div></div>
        <div className="stat-card"><div className="stat-value" style={{ color: 'var(--green)' }}>{users.filter(u => u.is_active).length}</div><div className="stat-label">Active</div></div>
      </div>

      {/* Filter tabs */}
      <div className="tabs">
        {[['all','All'],['patient','Patients'],['doctor','Doctors'],['admin','Admins']].map(([k,l]) => (
          <button key={k} className={`tab ${filter===k?'active':''}`} onClick={() => setFilter(k)}>
            {l} <span style={{ fontSize:'0.72rem',marginLeft:4,opacity:0.6 }}>({counts[k]||0})</span>
          </button>
        ))}
      </div>

      <div className="card">
        {loading ? (
          <div style={{ display:'flex',justifyContent:'center',padding:40 }}><div className="spinner"/></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr>
              </thead>
              <tbody>
                {filtered.length ? filtered.map(u => (
                  <tr key={u.id}>
                    <td style={{ fontWeight: 500 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 30, height: 30, borderRadius: '50%',
                          background: 'var(--teal-dim)', border: '1px solid var(--teal)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.7rem', fontWeight: 700, color: 'var(--teal)', flexShrink: 0
                        }}>
                          {u.full_name?.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}
                        </div>
                        {u.full_name}
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-mid)', fontSize: '0.85rem' }}>{u.email}</td>
                    <td>
                      <span className={`badge ${u.role==='doctor'?'badge-info':u.role==='admin'?'badge-amber':'badge-low'}`}
                        style={{ textTransform: 'capitalize' }}>
                        {u.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${u.is_active ? 'badge-low' : 'badge-high'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-secondary'}`}
                        onClick={() => toggleStatus(u)}
                        style={{ display: 'flex', alignItems: 'center', gap: 5 }}
                      >
                        {u.is_active
                          ? <><UserX size={13}/> Deactivate</>
                          : <><UserCheck size={13}/> Activate</>}
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr><td colSpan={5}><div className="empty">No users found</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
