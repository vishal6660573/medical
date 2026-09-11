import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listPatients, getVisits, getMedications, getPredictions, addVisit, addMedication } from '../services/api'
import { Users, FileText, Pill, BarChart2, Activity, Heart, Scan, Search, Plus, X, ExternalLink } from 'lucide-react'
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
      <div className="risk-bar-bg"><div className="risk-bar-fill" style={{ width: `${pct}%` }} /></div>
    </div>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position:'fixed',inset:0,background:'#000a',display:'flex',alignItems:'center',justifyContent:'center',zIndex:100,padding:24 }}>
      <div className="card" style={{ width:'100%',maxWidth:480,maxHeight:'90vh',overflowY:'auto' }}>
        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20 }}>
          <span style={{ fontWeight:600 }}>{title}</span>
          <button className="btn btn-secondary btn-sm" onClick={onClose}><X size={14}/></button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function DoctorDashboard() {
  const [patients, setPatients] = useState([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [tab, setTab] = useState('visits')
  const [visits, setVisits] = useState([])
  const [meds, setMeds] = useState([])
  const [preds, setPreds] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    listPatients()
      .then(r => setPatients(r.data))
      .catch(() => toast.error('Failed to load patients'))
      .finally(() => setLoading(false))
  }, [])

  const selectPatient = async (p) => {
    setSelected(p); setTab('visits')
    const [v, m, pr] = await Promise.all([getVisits(p.id), getMedications(p.id), getPredictions(p.id)])
    setVisits(v.data); setMeds(m.data); setPreds(pr.data)
  }

  const submitVisit = async () => {
    try {
      await addVisit(selected.id, form)
      const { data } = await getVisits(selected.id)
      setVisits(data); setModal(null); setForm({})
      toast.success('Visit added')
    } catch { toast.error('Failed to add visit') }
  }

  const submitMed = async () => {
    try {
      await addMedication(selected.id, form)
      const { data } = await getMedications(selected.id)
      setMeds(data); setModal(null); setForm({})
      toast.success('Medication prescribed')
    } catch { toast.error('Failed to prescribe') }
  }

  const filtered = patients.filter(p =>
    p.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.email?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="page-enter">
      <h1 className="page-title">Doctor Dashboard</h1>
      <p className="page-sub">Manage patients, view records, and run AI diagnostics</p>

      {/* Stats */}
      <div className="grid-3" style={{ marginBottom: 28 }}>
        <div className="stat-card"><div className="stat-value">{patients.length}</div><div className="stat-label">Total Patients</div></div>
        <div className="stat-card"><div className="stat-value">{visits.length}</div><div className="stat-label">Visits (selected)</div></div>
        <div className="stat-card"><div className="stat-value">{preds.length}</div><div className="stat-label">Predictions (selected)</div></div>
      </div>

      <div style={{ display:'grid',gridTemplateColumns:'300px 1fr',gap:20,alignItems:'start' }}>

        {/* Patient list */}
        <div className="card" style={{ padding:0,overflow:'hidden' }}>
          <div style={{ padding:'16px 16px 12px',borderBottom:'1px solid var(--border)' }}>
            <div style={{ position:'relative' }}>
              <Search size={14} style={{ position:'absolute',left:10,top:'50%',transform:'translateY(-50%)',color:'var(--text-dim)' }}/>
              <input className="form-input" placeholder="Search patients..." style={{ paddingLeft:32 }}
                value={search} onChange={e => setSearch(e.target.value)}/>
            </div>
          </div>
          <div style={{ maxHeight:500,overflowY:'auto' }}>
            {loading
              ? <div style={{ padding:24,textAlign:'center' }}><div className="spinner"/></div>
              : filtered.length
                ? filtered.map(p => (
                  <div key={p.id}
                    style={{ borderBottom:'1px solid var(--border)',background:selected?.id===p.id?'var(--teal-dim)':'transparent',transition:'background 0.1s' }}>
                    {/* Patient row — clickable for quick select */}
                    <div onClick={() => selectPatient(p)} style={{ padding:'12px 16px',cursor:'pointer' }}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                        <div style={{ fontWeight:500,fontSize:'0.875rem' }}>{p.full_name}</div>
                        {/* Full profile link */}
                        <button
                          onClick={e => { e.stopPropagation(); navigate(`/doctor/patients/${p.id}`) }}
                          title="View full profile"
                          style={{ background:'none',border:'none',cursor:'pointer',color:'var(--teal)',padding:4,borderRadius:4,display:'flex',alignItems:'center' }}
                        >
                          <ExternalLink size={13}/>
                        </button>
                      </div>
                      <div style={{ fontSize:'0.75rem',color:'var(--text-mid)',marginTop:2 }}>{p.email}</div>
                      {p.blood_group && <span className="badge badge-info" style={{ marginTop:6,fontSize:'0.68rem' }}>{p.blood_group}</span>}
                    </div>
                  </div>
                ))
                : <div className="empty">No patients found</div>}
          </div>
        </div>

        {/* Patient detail panel */}
        {selected ? (
          <div>
            <div className="card" style={{ marginBottom:16 }}>
              <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                <div>
                  <div style={{ display:'flex',alignItems:'center',gap:10 }}>
                    <h2 style={{ fontSize:'1.1rem',fontWeight:700 }}>{selected.full_name}</h2>
                    {/* Full profile button */}
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => navigate(`/doctor/patients/${selected.id}`)}
                    >
                      <ExternalLink size={13}/> Full Profile
                    </button>
                  </div>
                  <p style={{ color:'var(--text-mid)',fontSize:'0.8rem' }}>{selected.email} · {selected.gender||'Gender unknown'} · {selected.blood_group||'Blood group unknown'}</p>
                  {selected.allergies && <p style={{ fontSize:'0.78rem',color:'var(--amber)',marginTop:4 }}>⚠ Allergies: {selected.allergies}</p>}
                </div>
                <div style={{ display:'flex',gap:8,flexWrap:'wrap',justifyContent:'flex-end' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/doctor/predict/diabetes?patient_id=${selected.id}`)}><Activity size={13}/> Diabetes</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/doctor/predict/heart?patient_id=${selected.id}`)}><Heart size={13}/> Heart</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/doctor/predict/xray?patient_id=${selected.id}`)}><Scan size={13}/> X-Ray</button>
                </div>
              </div>
            </div>

            <div className="tabs">
              {[['visits','Visits'],['medications','Medications'],['predictions','Predictions']].map(([k,l]) => (
                <button key={k} className={`tab ${tab===k?'active':''}`} onClick={() => setTab(k)}>{l}</button>
              ))}
            </div>

            {tab==='visits' && (
              <div className="card">
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16 }}>
                  <span className="section-title" style={{ margin:0 }}>Visit History</span>
                  <button className="btn btn-primary btn-sm" onClick={() => { setForm({}); setModal('visit') }}><Plus size={13}/> Add Visit</button>
                </div>
                <div className="table-wrap"><table>
                  <thead><tr><th>Date</th><th>Complaint</th><th>Diagnosis</th><th>Notes</th><th>Follow-up</th></tr></thead>
                  <tbody>
                    {visits.length ? visits.map(v => (
                      <tr key={v.id}>
                        <td className="mono" style={{ fontSize:'0.78rem' }}>{new Date(v.visit_date).toLocaleDateString()}</td>
                        <td>{v.chief_complaint}</td>
                        <td style={{ color:'var(--text-mid)' }}>{v.diagnosis||'—'}</td>
                        <td style={{ color:'var(--text-mid)',maxWidth:180,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis' }}>{v.notes||'—'}</td>
                        <td style={{ color:'var(--text-mid)' }}>{v.follow_up_date||'—'}</td>
                      </tr>
                    )) : <tr><td colSpan={5}><div className="empty">No visits yet</div></td></tr>}
                  </tbody>
                </table></div>
              </div>
            )}

            {tab==='medications' && (
              <div className="card">
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16 }}>
                  <span className="section-title" style={{ margin:0 }}>Medications</span>
                  <button className="btn btn-primary btn-sm" onClick={() => { setForm({}); setModal('med') }}><Plus size={13}/> Prescribe</button>
                </div>
                <div className="table-wrap"><table>
                  <thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th><th>Status</th></tr></thead>
                  <tbody>
                    {meds.length ? meds.map(m => (
                      <tr key={m.id}>
                        <td style={{ fontWeight:500 }}>{m.name}</td>
                        <td className="mono" style={{ fontSize:'0.78rem' }}>{m.dosage||'—'}</td>
                        <td>{m.frequency||'—'}</td>
                        <td>{m.duration||'—'}</td>
                        <td><span className={`badge ${m.is_active?'badge-low':'badge-info'}`}>{m.is_active?'Active':'Done'}</span></td>
                      </tr>
                    )) : <tr><td colSpan={5}><div className="empty">No medications</div></td></tr>}
                  </tbody>
                </table></div>
              </div>
            )}

            {tab==='predictions' && (
              <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
                {preds.length ? preds.map(p => (
                  <div className="card card-sm" key={p.id}>
                    <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12 }}>
                      <div style={{ display:'flex',alignItems:'center',gap:8 }}>
                        {p.prediction_type==='diabetes'&&<Activity size={15} color="var(--teal)"/>}
                        {p.prediction_type==='heart'&&<Heart size={15} color="var(--red)"/>}
                        {p.prediction_type==='xray'&&<Scan size={15} color="var(--amber)"/>}
                        <span style={{ fontWeight:600,textTransform:'capitalize' }}>{p.prediction_type}</span>
                      </div>
                      <span style={{ fontSize:'0.75rem',color:'var(--text-dim)' }}>{new Date(p.created_at).toLocaleString()}</span>
                    </div>
                    <RiskBar probability={p.probability} riskLevel={p.risk_level}/>
                  </div>
                )) : <div className="empty">No predictions for this patient yet</div>}
              </div>
            )}
          </div>
        ) : (
          <div className="card" style={{ display:'flex',alignItems:'center',justifyContent:'center',minHeight:300 }}>
            <div className="empty">
              <Users size={32} style={{ margin:'0 auto 12px',display:'block',opacity:0.2 }}/>
              Select a patient from the left to view their records
            </div>
          </div>
        )}
      </div>

      {modal==='visit' && (
        <Modal title="Add Visit Record" onClose={() => setModal(null)}>
          {[['chief_complaint','Chief Complaint / Reason'],['diagnosis','Diagnosis'],['notes','Notes'],['follow_up_date','Follow-up Date']].map(([k,l]) => (
            <div className="form-group" key={k}>
              <label className="form-label">{l}</label>
              <input className="form-input" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
            </div>
          ))}
          <button className="btn btn-primary btn-full" onClick={submitVisit}>Save Visit</button>
        </Modal>
      )}

      {modal==='med' && (
        <Modal title="Prescribe Medication" onClose={() => setModal(null)}>
          {[['name','Medicine Name *'],['dosage','Dosage (e.g. 500mg)'],['frequency','Frequency (e.g. twice daily)'],['duration','Duration (e.g. 7 days)'],['notes','Notes']].map(([k,l]) => (
            <div className="form-group" key={k}>
              <label className="form-label">{l}</label>
              <input className="form-input" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
            </div>
          ))}
          <button className="btn btn-primary btn-full" onClick={submitMed}>Prescribe</button>
        </Modal>
      )}
    </div>
  )
}
