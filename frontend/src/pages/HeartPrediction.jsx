import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { predictHeart } from '../services/api'
import { Heart, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const FIELDS = [
  { key:'age',      label:'Age',                      hint:'1–120',   type:'number', step:1   },
  { key:'sex',      label:'Sex (0=Female, 1=Male)',   hint:'0 or 1',  type:'number', step:1   },
  { key:'cp',       label:'Chest Pain Type (0–3)',    hint:'0–3',     type:'number', step:1   },
  { key:'trestbps', label:'Resting BP (mmHg)',        hint:'50–250',  type:'number', step:1   },
  { key:'chol',     label:'Serum Cholesterol (mg/dL)',hint:'100–600', type:'number', step:1   },
  { key:'fbs',      label:'Fasting Blood Sugar > 120',hint:'0 or 1',  type:'number', step:1   },
  { key:'restecg',  label:'Resting ECG (0–2)',        hint:'0–2',     type:'number', step:1   },
  { key:'thalach',  label:'Max Heart Rate',           hint:'50–250',  type:'number', step:1   },
  { key:'exang',    label:'Exercise Angina (0/1)',    hint:'0 or 1',  type:'number', step:1   },
  { key:'oldpeak',  label:'ST Depression',            hint:'0.0–10',  type:'number', step:0.1 },
  { key:'slope',    label:'ST Slope (0–2)',           hint:'0–2',     type:'number', step:1   },
  { key:'ca',       label:'Major Vessels (0–4)',      hint:'0–4',     type:'number', step:1   },
  { key:'thal',     label:'Thalassemia (0–3)',        hint:'0–3',     type:'number', step:1   },
]

export default function HeartPrediction() {
  const [params] = useSearchParams()
  const patientId = params.get('patient_id')
  const [form, setForm] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([k,v]) => [k, parseFloat(v)]))
      const { data } = await predictHeart(payload, patientId)
      setResult(data)
      toast.success('Prediction complete')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediction failed')
    } finally { setLoading(false) }
  }

  const isHigh = result?.risk_level === 'High'
  const pct = result ? Math.round(result.probability * 100) : 0

  return (
    <div className="page-enter" style={{ maxWidth: 700 }}>
      <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:6 }}>
        <Heart size={22} color="var(--red)" />
        <h1 className="page-title" style={{ margin:0 }}>Heart Disease Prediction</h1>
      </div>
      <p className="page-sub">Analyze cardiac risk using our Random Forest diagnostic model</p>
      {patientId && <div className="badge badge-info" style={{ marginBottom:16 }}>Linked to Patient #{patientId}</div>}

      <div className="card" style={{ marginBottom: result ? 20 : 0 }}>
        <form onSubmit={submit}>
          <div className="grid-2">
            {FIELDS.map(f => (
              <div className="form-group" key={f.key}>
                <label className="form-label">{f.label}</label>
                <input className="form-input" type={f.type} step={f.step} placeholder={f.hint}
                  value={form[f.key] || ''} onChange={e => setForm({...form,[f.key]:e.target.value})} required />
              </div>
            ))}
          </div>
          <button className="btn btn-primary btn-full" type="submit" disabled={loading} style={{ marginTop:8 }}>
            {loading ? <><span className="spinner" /> Analyzing...</> : <><Heart size={15}/> Run Prediction</>}
          </button>
        </form>
      </div>

      {result && (
        <div className="card page-enter" style={{ borderColor: isHigh ? 'var(--red)' : 'var(--green)' }}>
          <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:16 }}>
            {isHigh ? <AlertCircle size={22} color="var(--red)" /> : <CheckCircle size={22} color="var(--green)" />}
            <span style={{ fontSize:'1.1rem',fontWeight:700 }}>
              {isHigh ? 'High Cardiac Risk Detected' : 'Low Cardiac Risk'}
            </span>
          </div>
          <div style={{ display:'flex',alignItems:'center',gap:16 }}>
            <div style={{ position:'relative',width:80,height:80,flexShrink:0 }}>
              <svg viewBox="0 0 36 36" style={{ transform:'rotate(-90deg)',width:80,height:80 }}>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" strokeWidth="3.2"/>
                <circle cx="18" cy="18" r="15.9" fill="none"
                  stroke={isHigh ? 'var(--red)' : 'var(--green)'} strokeWidth="3.2"
                  strokeDasharray={`${pct} ${100-pct}`} strokeLinecap="round"/>
              </svg>
              <div style={{ position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
                fontFamily:'var(--font-mono)',fontWeight:700,fontSize:'1rem',
                color: isHigh ? 'var(--red)' : 'var(--green)' }}>{pct}%</div>
            </div>
            <div>
              <p style={{ fontSize:'0.875rem',color:'var(--text-mid)',marginBottom:4 }}>Cardiac Risk Probability</p>
              <p style={{ fontSize:'0.875rem' }}>
                {isHigh
                  ? 'Significant cardiac risk markers detected. Recommend ECG, stress test, and cardiology consultation.'
                  : 'Cardiac risk appears low based on current parameters. Maintain healthy lifestyle habits.'}
              </p>
              {result.saved && <p style={{ fontSize:'0.75rem',color:'var(--teal)',marginTop:8 }}>✓ Result saved to patient record #{result.prediction_record_id}</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
