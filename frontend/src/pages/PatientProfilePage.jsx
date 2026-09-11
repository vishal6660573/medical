import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getFullPatientProfile, addVisit, addMedication, predictDiabetes, predictHeart } from '../services/api'
import { ArrowLeft, User, Phone, MapPin, AlertTriangle, Activity, Heart, FileText, Pill, BarChart2, Plus, X, Scan } from 'lucide-react'
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
    <div style={{ position:'fixed',inset:0,background:'#000b',display:'flex',alignItems:'center',justifyContent:'center',zIndex:100,padding:24 }}>
      <div className="card" style={{ width:'100%',maxWidth:500,maxHeight:'90vh',overflowY:'auto' }}>
        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20 }}>
          <span style={{ fontWeight:600 }}>{title}</span>
          <button className="btn btn-secondary btn-sm" onClick={onClose}><X size={14}/></button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function PatientProfilePage() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('overview')
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState({})
  const [predResult, setPredResult] = useState(null)
  const [predLoading, setPredLoading] = useState(false)

  const load = async () => {
    try { const { data: d } = await getFullPatientProfile(patientId); setData(d) }
    catch { toast.error('Failed to load patient profile') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [patientId])

  const submitVisit = async () => {
    try { await addVisit(patientId, form); toast.success('Visit added'); setModal(null); setForm({}); load() }
    catch { toast.error('Failed to add visit') }
  }

  const submitMed = async () => {
    try { await addMedication(patientId, form); toast.success('Prescribed'); setModal(null); setForm({}); load() }
    catch { toast.error('Failed to prescribe') }
  }

  const runPrediction = async (type) => {
    setPredLoading(true); setPredResult(null)
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([k,v]) => [k, parseFloat(v)]))
      const res = type === 'diabetes'
        ? await predictDiabetes(payload, parseInt(patientId))
        : await predictHeart(payload, parseInt(patientId))
      setPredResult({ ...res.data, type }); toast.success('Prediction saved'); load()
    } catch { toast.error('Prediction failed') }
    finally { setPredLoading(false) }
  }

  if (loading) return <div style={{ display:'flex',justifyContent:'center',paddingTop:80 }}><div className="spinner"/></div>
  if (!data) return <div className="empty">Patient not found</div>

  const { profile, visits, medications, predictions } = data
  const activeMeds = medications.filter(m => m.is_active)

  return (
    <div className="page-enter">
      {/* Back + title */}
      <div style={{ display:'flex',alignItems:'center',gap:12,marginBottom:24 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}><ArrowLeft size={14}/> Back</button>
        <div>
          <h1 className="page-title" style={{ margin:0 }}>{profile.full_name}</h1>
          <p style={{ color:'var(--text-mid)',fontSize:'0.85rem' }}>{profile.email}</p>
        </div>
      </div>

      {/* Summary card */}
      <div className="card" style={{ marginBottom:24 }}>
        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:16 }}>
          <div style={{ display:'flex',gap:16,alignItems:'center' }}>
            <div style={{ width:64,height:64,borderRadius:'50%',background:'var(--teal-mid)',border:'2px solid var(--teal)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'1.5rem',fontWeight:700,color:'var(--teal)' }}>
              {profile.full_name?.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}
            </div>
            <div>
              <div style={{ display:'flex',gap:8,flexWrap:'wrap',marginBottom:6 }}>
                {profile.blood_group && <span className="badge badge-high">{profile.blood_group}</span>}
                {profile.gender && <span className="badge badge-info" style={{ textTransform:'capitalize' }}>{profile.gender}</span>}
                {profile.date_of_birth && <span className="badge badge-amber">DOB: {profile.date_of_birth}</span>}
              </div>
              <div style={{ display:'flex',gap:16,flexWrap:'wrap' }}>
                {profile.phone && <span style={{ fontSize:'0.8rem',color:'var(--text-mid)',display:'flex',alignItems:'center',gap:4 }}><Phone size={12}/>{profile.phone}</span>}
                {profile.address && <span style={{ fontSize:'0.8rem',color:'var(--text-mid)',display:'flex',alignItems:'center',gap:4 }}><MapPin size={12}/>{profile.address}</span>}
                {profile.emergency_contact && <span style={{ fontSize:'0.8rem',color:'var(--text-mid)',display:'flex',alignItems:'center',gap:4 }}><Phone size={12}/>Emergency: {profile.emergency_contact}</span>}
              </div>
            </div>
          </div>
          <div style={{ display:'flex',gap:8,flexWrap:'wrap' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => { setForm({}); setPredResult(null); setModal('diabetes') }}><Activity size={13}/> Diabetes</button>
            <button className="btn btn-secondary btn-sm" onClick={() => { setForm({}); setPredResult(null); setModal('heart') }}><Heart size={13}/> Heart</button>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/doctor/predict/xray?patient_id=${patientId}`)}><Scan size={13}/> X-Ray</button>
            <button className="btn btn-primary btn-sm" onClick={() => { setForm({}); setModal('visit') }}><Plus size={13}/> Add Visit</button>
            <button className="btn btn-secondary btn-sm" onClick={() => { setForm({}); setModal('med') }}><Pill size={13}/> Prescribe</button>
          </div>
        </div>
        {profile.allergies && (
          <div style={{ marginTop:16,padding:'10px 14px',borderRadius:8,background:'#f5a62315',border:'1px solid #f5a62340',display:'flex',alignItems:'center',gap:8 }}>
            <AlertTriangle size={15} color="var(--amber)"/>
            <span style={{ fontSize:'0.85rem',color:'var(--amber)' }}><strong>Allergies:</strong> {profile.allergies}</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom:24 }}>
        <div className="stat-card"><div className="stat-value">{visits.length}</div><div className="stat-label">Total Visits</div></div>
        <div className="stat-card"><div className="stat-value">{activeMeds.length}</div><div className="stat-label">Active Meds</div></div>
        <div className="stat-card"><div className="stat-value">{predictions.length}</div><div className="stat-label">AI Predictions</div></div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize:'1.2rem',color:predictions.some(p=>p.risk_level==='High')?'var(--red)':'var(--green)' }}>
            {predictions.some(p=>p.risk_level==='High')?'At Risk':'Stable'}
          </div>
          <div className="stat-label">Overall Status</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {[['overview','Overview'],['visits','Visits'],['medications','Medications'],['predictions','Predictions']].map(([k,l]) => (
          <button key={k} className={`tab ${tab===k?'active':''}`} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>

      {tab==='overview' && (
        <div className="grid-2" style={{ gap:20 }}>
          <div className="card">
            <div style={{ display:'flex',alignItems:'center',gap:8,marginBottom:16 }}><FileText size={16} color="var(--teal)"/><span className="section-title" style={{ margin:0 }}>Recent Visits</span></div>
            {visits.slice(0,4).length ? visits.slice(0,4).map(v => (
              <div key={v.id} style={{ padding:'10px 0',borderBottom:'1px solid var(--border)' }}>
                <div style={{ display:'flex',justifyContent:'space-between' }}>
                  <span style={{ fontSize:'0.875rem',fontWeight:500 }}>{v.chief_complaint}</span>
                  <span style={{ fontSize:'0.75rem',color:'var(--text-dim)' }}>{new Date(v.visit_date).toLocaleDateString()}</span>
                </div>
                {v.diagnosis && <div style={{ fontSize:'0.78rem',color:'var(--text-mid)',marginTop:2 }}>{v.diagnosis}</div>}
                {v.doctor_name && <div style={{ fontSize:'0.72rem',color:'var(--teal)',marginTop:2 }}>Dr. {v.doctor_name}</div>}
              </div>
            )) : <div className="empty">No visits yet</div>}
          </div>
          <div className="card">
            <div style={{ display:'flex',alignItems:'center',gap:8,marginBottom:16 }}><BarChart2 size={16} color="var(--teal)"/><span className="section-title" style={{ margin:0 }}>Recent Predictions</span></div>
            {predictions.slice(0,4).length ? predictions.slice(0,4).map(p => (
              <div key={p.id} style={{ padding:'10px 0',borderBottom:'1px solid var(--border)' }}>
                <div style={{ display:'flex',justifyContent:'space-between',marginBottom:6 }}>
                  <span style={{ fontSize:'0.875rem',fontWeight:500,textTransform:'capitalize' }}>{p.prediction_type}</span>
                  <span style={{ fontSize:'0.75rem',color:'var(--text-dim)' }}>{new Date(p.created_at).toLocaleDateString()}</span>
                </div>
                <RiskBar probability={p.probability} riskLevel={p.risk_level}/>
              </div>
            )) : <div className="empty">No predictions yet</div>}
          </div>
          <div className="card">
            <div style={{ display:'flex',alignItems:'center',gap:8,marginBottom:16 }}><Pill size={16} color="var(--teal)"/><span className="section-title" style={{ margin:0 }}>Active Medications</span></div>
            {activeMeds.length ? activeMeds.map(m => (
              <div key={m.id} style={{ padding:'10px 0',borderBottom:'1px solid var(--border)',display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                <div><div style={{ fontSize:'0.875rem',fontWeight:500 }}>{m.name}</div><div style={{ fontSize:'0.75rem',color:'var(--text-mid)' }}>{m.dosage} · {m.frequency}</div></div>
                <span className="badge badge-low">Active</span>
              </div>
            )) : <div className="empty">No active medications</div>}
          </div>
          <div className="card">
            <div style={{ display:'flex',alignItems:'center',gap:8,marginBottom:16 }}><User size={16} color="var(--teal)"/><span className="section-title" style={{ margin:0 }}>Patient Info</span></div>
            {[['Full Name',profile.full_name],['Email',profile.email],['Date of Birth',profile.date_of_birth||'—'],['Gender',profile.gender||'—'],['Blood Group',profile.blood_group||'—'],['Phone',profile.phone||'—'],['Emergency Contact',profile.emergency_contact||'—'],['Allergies',profile.allergies||'—']].map(([l,v]) => (
              <div key={l} style={{ display:'flex',justifyContent:'space-between',padding:'6px 0',borderBottom:'1px solid var(--border)' }}>
                <span style={{ fontSize:'0.72rem',color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'0.04em' }}>{l}</span>
                <span style={{ fontSize:'0.85rem',fontWeight:500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab==='visits' && (
        <div className="card">
          <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16 }}>
            <span className="section-title" style={{ margin:0 }}>All Visits ({visits.length})</span>
            <button className="btn btn-primary btn-sm" onClick={() => { setForm({}); setModal('visit') }}><Plus size={13}/> Add Visit</button>
          </div>
          <div className="table-wrap"><table>
            <thead><tr><th>Date</th><th>Complaint</th><th>Diagnosis</th><th>Doctor</th><th>Notes</th><th>Follow-up</th></tr></thead>
            <tbody>
              {visits.length ? visits.map(v => (
                <tr key={v.id}>
                  <td className="mono" style={{ fontSize:'0.78rem',whiteSpace:'nowrap' }}>{new Date(v.visit_date).toLocaleDateString()}</td>
                  <td style={{ fontWeight:500 }}>{v.chief_complaint}</td>
                  <td style={{ color:'var(--text-mid)' }}>{v.diagnosis||'—'}</td>
                  <td style={{ color:'var(--text-mid)' }}>{v.doctor_name||'—'}</td>
                  <td style={{ color:'var(--text-mid)',maxWidth:160,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap' }}>{v.notes||'—'}</td>
                  <td style={{ color:'var(--text-mid)' }}>{v.follow_up_date||'—'}</td>
                </tr>
              )) : <tr><td colSpan={6}><div className="empty">No visits recorded</div></td></tr>}
            </tbody>
          </table></div>
        </div>
      )}

      {tab==='medications' && (
        <div className="card">
          <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16 }}>
            <span className="section-title" style={{ margin:0 }}>All Medications ({medications.length})</span>
            <button className="btn btn-primary btn-sm" onClick={() => { setForm({}); setModal('med') }}><Plus size={13}/> Prescribe</button>
          </div>
          <div className="table-wrap"><table>
            <thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th><th>Prescribed By</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              {medications.length ? medications.map(m => (
                <tr key={m.id}>
                  <td style={{ fontWeight:500 }}>{m.name}</td>
                  <td className="mono" style={{ fontSize:'0.78rem' }}>{m.dosage||'—'}</td>
                  <td>{m.frequency||'—'}</td>
                  <td>{m.duration||'—'}</td>
                  <td style={{ color:'var(--text-mid)' }}>{m.prescribed_by||'—'}</td>
                  <td className="mono" style={{ fontSize:'0.78rem' }}>{new Date(m.prescribed_at).toLocaleDateString()}</td>
                  <td><span className={`badge ${m.is_active?'badge-low':'badge-info'}`}>{m.is_active?'Active':'Done'}</span></td>
                </tr>
              )) : <tr><td colSpan={7}><div className="empty">No medications</div></td></tr>}
            </tbody>
          </table></div>
        </div>
      )}

      {tab==='predictions' && (
        <div>
          <div style={{ display:'flex',gap:8,marginBottom:16 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => { setForm({}); setPredResult(null); setModal('diabetes') }}><Activity size={13}/> Diabetes Test</button>
            <button className="btn btn-secondary btn-sm" onClick={() => { setForm({}); setPredResult(null); setModal('heart') }}><Heart size={13}/> Heart Test</button>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/doctor/predict/xray?patient_id=${patientId}`)}><Scan size={13}/> X-Ray</button>
          </div>
          <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
            {predictions.length ? predictions.map(p => (
              <div className="card card-sm" key={p.id} style={{ borderLeft:`3px solid ${p.risk_level==='High'?'var(--red)':'var(--green)'}` }}>
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10 }}>
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
            )) : <div className="empty">No predictions yet</div>}
          </div>
        </div>
      )}

      {/* Modals */}
      {modal==='visit' && (
        <Modal title="Add Visit Record" onClose={() => setModal(null)}>
          {[['chief_complaint','Chief Complaint *'],['diagnosis','Diagnosis'],['notes','Clinical Notes'],['follow_up_date','Follow-up Date']].map(([k,l]) => (
            <div className="form-group" key={k}><label className="form-label">{l}</label>
              <input className="form-input" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
            </div>
          ))}
          <button className="btn btn-primary btn-full" onClick={submitVisit}>Save Visit</button>
        </Modal>
      )}

      {modal==='med' && (
        <Modal title="Prescribe Medication" onClose={() => setModal(null)}>
          {[['name','Medicine Name *'],['dosage','Dosage'],['frequency','Frequency'],['duration','Duration'],['notes','Notes']].map(([k,l]) => (
            <div className="form-group" key={k}><label className="form-label">{l}</label>
              <input className="form-input" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
            </div>
          ))}
          <button className="btn btn-primary btn-full" onClick={submitMed}>Prescribe</button>
        </Modal>
      )}

      {modal==='diabetes' && (
        <Modal title="Diabetes Risk Prediction" onClose={() => { setModal(null); setPredResult(null) }}>
          <div className="grid-2">
            {[['pregnancies','Pregnancies'],['glucose','Glucose'],['blood_pressure','Blood Pressure'],['skin_thickness','Skin Thickness'],['insulin','Insulin'],['bmi','BMI'],['diabetes_pedigree_function','Pedigree Fn'],['age','Age']].map(([k,l]) => (
              <div className="form-group" key={k}><label className="form-label">{l}</label>
                <input className="form-input" type="number" step="any" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
              </div>
            ))}
          </div>
          <button className="btn btn-primary btn-full" onClick={() => runPrediction('diabetes')} disabled={predLoading}>
            {predLoading ? <><span className="spinner"/> Analyzing...</> : <><Activity size={14}/> Run Prediction</>}
          </button>
          {predResult?.type==='diabetes' && (
            <div style={{ marginTop:16,padding:14,borderRadius:8,background:predResult.risk_level==='High'?'#f1535a15':'#10d98a15',border:`1px solid ${predResult.risk_level==='High'?'#f1535a30':'#10d98a30'}` }}>
              <div style={{ fontWeight:600,marginBottom:8 }}>{predResult.risk_level==='High'?'⚠️ High Risk':'✅ Low Risk'}</div>
              <RiskBar probability={predResult.probability} riskLevel={predResult.risk_level}/>
              {predResult.saved && <p style={{ fontSize:'0.75rem',color:'var(--teal)',marginTop:8 }}>✓ Saved to patient record</p>}
            </div>
          )}
        </Modal>
      )}

      {modal==='heart' && (
        <Modal title="Heart Disease Prediction" onClose={() => { setModal(null); setPredResult(null) }}>
          <div className="grid-2">
            {[['age','Age'],['sex','Sex(0=F,1=M)'],['cp','Chest Pain(0-3)'],['trestbps','Resting BP'],['chol','Cholesterol'],['fbs','FBS>120(0/1)'],['restecg','ECG(0-2)'],['thalach','Max HR'],['exang','Ex.Angina(0/1)'],['oldpeak','ST Dep'],['slope','Slope(0-2)'],['ca','Vessels(0-4)'],['thal','Thal(0-3)']].map(([k,l]) => (
              <div className="form-group" key={k}><label className="form-label">{l}</label>
                <input className="form-input" type="number" step="any" value={form[k]||''} onChange={e => setForm({...form,[k]:e.target.value})}/>
              </div>
            ))}
          </div>
          <button className="btn btn-primary btn-full" onClick={() => runPrediction('heart')} disabled={predLoading}>
            {predLoading ? <><span className="spinner"/> Analyzing...</> : <><Heart size={14}/> Run Prediction</>}
          </button>
          {predResult?.type==='heart' && (
            <div style={{ marginTop:16,padding:14,borderRadius:8,background:predResult.risk_level==='High'?'#f1535a15':'#10d98a15',border:`1px solid ${predResult.risk_level==='High'?'#f1535a30':'#10d98a30'}` }}>
              <div style={{ fontWeight:600,marginBottom:8 }}>{predResult.risk_level==='High'?'⚠️ High Cardiac Risk':'✅ Low Cardiac Risk'}</div>
              <RiskBar probability={predResult.probability} riskLevel={predResult.risk_level}/>
              {predResult.saved && <p style={{ fontSize:'0.75rem',color:'var(--teal)',marginTop:8 }}>✓ Saved to patient record</p>}
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}
