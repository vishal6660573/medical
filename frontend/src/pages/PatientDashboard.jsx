import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getMyProfile, getVisits, getMedications, getPredictions, updateMyProfile } from '../services/api'
import { Activity, Heart, Scan, FileText, Pill, BarChart2, Edit2, Save, X } from 'lucide-react'
import toast from 'react-hot-toast'

function RiskBar({ probability, riskLevel }) {
  const pct = Math.round((probability || 0) * 100)
  const isHigh = riskLevel === 'High'
  return (
    <div className={`risk-bar-wrap ${isHigh ? 'risk-high' : 'risk-low'}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span className={`badge ${isHigh ? 'badge-high' : 'badge-low'}`}>{riskLevel}</span>
        <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-mid)' }}>{pct}%</span>
      </div>
      <div className="risk-bar-bg">
        <div className="risk-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function PatientDashboard() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [visits, setVisits] = useState([])
  const [meds, setMeds] = useState([])
  const [preds, setPreds] = useState([])
  const [tab, setTab] = useState('overview')
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getMyProfile(), ]).then(([p]) => {
      setProfile(p.data)
      setEditForm(p.data)
      return p.data
    }).then(async (p) => {
      const pid = p.id
      const [v, m, pr] = await Promise.all([getVisits(pid), getMedications(pid), getPredictions(pid)])
      setVisits(v.data)
      setMeds(m.data)
      setPreds(pr.data)
    }).catch(() => toast.error('Failed to load profile'))
    .finally(() => setLoading(false))
  }, [])

  const saveProfile = async () => {
    try {
      const { data } = await updateMyProfile(editForm)
      setProfile(data)
      setEditing(false)
      toast.success('Profile updated')
    } catch { toast.error('Update failed') }
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}><div className="spinner" /></div>
  )

  return (
    <div className="page-enter">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 className="page-title">Welcome, {user?.full_name?.split(' ')[0]} 👋</h1>
          <p className="page-sub">Your health summary and records</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to="/patient/predict/diabetes" className="btn btn-secondary btn-sm"><Activity size={14} /> Run Prediction</Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: 28 }}>
        <div className="stat-card">
          <div className="stat-value">{visits.length}</div>
          <div className="stat-label">Total Visits</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{meds.filter(m => m.is_active).length}</div>
          <div className="stat-label">Active Medications</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{preds.length}</div>
          <div className="stat-label">AI Predictions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: profile?.blood_group ? 'var(--red)' : 'var(--text-dim)' }}>
            {profile?.blood_group || '—'}
          </div>
          <div className="stat-label">Blood Group</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {[['overview','Overview'],['visits','Visits'],['medications','Medications'],['predictions','Predictions'],['profile','Profile']].map(([k,l]) => (
          <button key={k} className={`tab ${tab === k ? 'active' : ''}`} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>

      {/* Overview */}
      {tab === 'overview' && (
        <div className="grid-2" style={{ gap: 20 }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <FileText size={16} color="var(--teal)" />
              <span className="section-title" style={{ margin: 0 }}>Recent Visits</span>
            </div>
            {visits.slice(0, 3).length ? visits.slice(0, 3).map(v => (
              <div key={v.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{v.chief_complaint}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-mid)', marginTop: 2 }}>
                  {v.diagnosis || 'Diagnosis pending'} · {new Date(v.visit_date).toLocaleDateString()}
                </div>
              </div>
            )) : <div className="empty">No visits yet</div>}
          </div>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <BarChart2 size={16} color="var(--teal)" />
              <span className="section-title" style={{ margin: 0 }}>Recent Predictions</span>
            </div>
            {preds.slice(0, 3).length ? preds.slice(0, 3).map(p => (
              <div key={p.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 500, textTransform: 'capitalize' }}>{p.prediction_type}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-mid)' }}>{new Date(p.created_at).toLocaleDateString()}</span>
                </div>
                <RiskBar probability={p.probability} riskLevel={p.risk_level} />
              </div>
            )) : <div className="empty">No predictions yet</div>}
          </div>
        </div>
      )}

      {/* Visits */}
      {tab === 'visits' && (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Complaint</th><th>Diagnosis</th><th>Doctor</th><th>Follow-up</th></tr></thead>
              <tbody>
                {visits.length ? visits.map(v => (
                  <tr key={v.id}>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>{new Date(v.visit_date).toLocaleDateString()}</td>
                    <td>{v.chief_complaint}</td>
                    <td style={{ color: 'var(--text-mid)' }}>{v.diagnosis || '—'}</td>
                    <td style={{ color: 'var(--text-mid)' }}>{v.doctor_name || '—'}</td>
                    <td style={{ color: 'var(--text-mid)' }}>{v.follow_up_date || '—'}</td>
                  </tr>
                )) : <tr><td colSpan={5}><div className="empty">No visits recorded</div></td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Medications */}
      {tab === 'medications' && (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th><th>Prescribed By</th><th>Status</th></tr></thead>
              <tbody>
                {meds.length ? meds.map(m => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 500 }}>{m.name}</td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>{m.dosage || '—'}</td>
                    <td>{m.frequency || '—'}</td>
                    <td>{m.duration || '—'}</td>
                    <td style={{ color: 'var(--text-mid)' }}>{m.prescribed_by || '—'}</td>
                    <td><span className={`badge ${m.is_active ? 'badge-low' : 'badge-info'}`}>{m.is_active ? 'Active' : 'Completed'}</span></td>
                  </tr>
                )) : <tr><td colSpan={6}><div className="empty">No medications prescribed</div></td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Predictions */}
      {tab === 'predictions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {preds.length ? preds.map(p => (
            <div className="card card-sm" key={p.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {p.prediction_type === 'diabetes' && <Activity size={16} color="var(--teal)" />}
                  {p.prediction_type === 'heart' && <Heart size={16} color="var(--red)" />}
                  {p.prediction_type === 'xray' && <Scan size={16} color="var(--amber)" />}
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{p.prediction_type} Analysis</span>
                </div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>{new Date(p.created_at).toLocaleString()}</span>
              </div>
              <RiskBar probability={p.probability} riskLevel={p.risk_level} />
            </div>
          )) : <div className="empty">No predictions yet. <Link to="/patient/predict/diabetes" style={{ color: 'var(--teal)' }}>Run one now →</Link></div>}
        </div>
      )}

      {/* Profile */}
      {tab === 'profile' && (
        <div className="card" style={{ maxWidth: 600 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <span className="section-title" style={{ margin: 0 }}>Personal Information</span>
            {!editing
              ? <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}><Edit2 size={13} /> Edit</button>
              : <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary btn-sm" onClick={saveProfile}><Save size={13} /> Save</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setEditing(false)}><X size={13} /></button>
                </div>
            }
          </div>
          {editing ? (
            <div className="grid-2">
              {[['date_of_birth','Date of Birth','text'],['phone','Phone','text'],['emergency_contact','Emergency Contact','text']].map(([k,l,t]) => (
                <div className="form-group" key={k}>
                  <label className="form-label">{l}</label>
                  <input className="form-input" type={t} value={editForm[k] || ''} onChange={e => setEditForm({ ...editForm, [k]: e.target.value })} />
                </div>
              ))}
              <div className="form-group">
                <label className="form-label">Gender</label>
                <select className="form-input" value={editForm.gender || ''} onChange={e => setEditForm({ ...editForm, gender: e.target.value })}>
                  <option value="">Select</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Blood Group</label>
                <select className="form-input" value={editForm.blood_group || ''} onChange={e => setEditForm({ ...editForm, blood_group: e.target.value })}>
                  <option value="">Select</option>
                  {['A+','A-','B+','B-','O+','O-','AB+','AB-'].map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: '1/-1' }}>
                <label className="form-label">Address</label>
                <input className="form-input" value={editForm.address || ''} onChange={e => setEditForm({ ...editForm, address: e.target.value })} />
              </div>
              <div className="form-group" style={{ gridColumn: '1/-1' }}>
                <label className="form-label">Allergies</label>
                <input className="form-input" value={editForm.allergies || ''} onChange={e => setEditForm({ ...editForm, allergies: e.target.value })} />
              </div>
            </div>
          ) : (
            <div className="grid-2" style={{ gap: '12px 24px' }}>
              {[
                ['Full Name', profile?.full_name],
                ['Email', profile?.email],
                ['Date of Birth', profile?.date_of_birth || '—'],
                ['Gender', profile?.gender || '—'],
                ['Blood Group', profile?.blood_group || '—'],
                ['Phone', profile?.phone || '—'],
                ['Emergency Contact', profile?.emergency_contact || '—'],
                ['Allergies', profile?.allergies || '—'],
              ].map(([l, v]) => (
                <div key={l}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>{l}</div>
                  <div style={{ fontSize: '0.9rem' }}>{v}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
