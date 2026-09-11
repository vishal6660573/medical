import { useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { predictXray } from '../services/api'
import { Scan, Upload, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function XrayPrediction() {
  const [params] = useSearchParams()
  const patientId = params.get('patient_id')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef()

  const handleFile = (f) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
  }

  const submit = async () => {
    if (!file) return toast.error('Please upload an X-ray image')
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await predictXray(fd, patientId)
      setResult(data)
      toast.success('X-ray analysis complete')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally { setLoading(false) }
  }

  const isAbnormal = result?.disease && result.disease !== 'NORMAL'
  const pct = result ? Math.round(result.confidence * 100) : 0

  return (
    <div className="page-enter" style={{ maxWidth: 600 }}>
      <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:6 }}>
        <Scan size={22} color="var(--amber)" />
        <h1 className="page-title" style={{ margin:0 }}>X-Ray Analysis</h1>
      </div>
      <p className="page-sub">Upload a chest X-ray for AI-powered pneumonia/COVID detection</p>
      {patientId && <div className="badge badge-info" style={{ marginBottom:16 }}>Linked to Patient #{patientId}</div>}

      <div className="card" style={{ marginBottom: result ? 20 : 0 }}>
        {/* Drop zone */}
        <div onClick={() => inputRef.current.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if(f) handleFile(f) }}
          style={{ border:`2px dashed ${preview ? 'var(--border-glow)' : 'var(--border)'}`,
            borderRadius:'var(--radius-lg)', padding:'32px 24px', textAlign:'center',
            cursor:'pointer', transition:'all 0.2s', background: preview ? 'var(--teal-dim)' : 'transparent' }}>
          <input ref={inputRef} type="file" accept="image/*" style={{ display:'none' }}
            onChange={e => { const f = e.target.files[0]; if(f) handleFile(f) }} />
          {preview ? (
            <img src={preview} alt="X-ray preview"
              style={{ maxHeight:280,maxWidth:'100%',borderRadius:8,objectFit:'contain' }} />
          ) : (
            <>
              <Upload size={32} style={{ color:'var(--text-dim)',marginBottom:12 }} />
              <p style={{ fontWeight:500,marginBottom:4 }}>Drop X-ray image here</p>
              <p style={{ fontSize:'0.8rem',color:'var(--text-mid)' }}>or click to browse · PNG, JPG, JPEG</p>
            </>
          )}
        </div>

        {file && (
          <p style={{ fontSize:'0.78rem',color:'var(--text-mid)',marginTop:10 }}>
            📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </p>
        )}

        <button className="btn btn-primary btn-full" onClick={submit} disabled={loading || !file} style={{ marginTop:16 }}>
          {loading ? <><span className="spinner" /> Analyzing X-ray...</> : <><Scan size={15}/> Analyze X-Ray</>}
        </button>
      </div>

      {result && (
        <div className="card page-enter" style={{ borderColor: isAbnormal ? 'var(--amber)' : 'var(--green)' }}>
          <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:16 }}>
            {isAbnormal ? <AlertCircle size={22} color="var(--amber)" /> : <CheckCircle size={22} color="var(--green)" />}
            <span style={{ fontSize:'1.1rem',fontWeight:700 }}>
              {result.disease}
            </span>
          </div>
          <div style={{ display:'flex',alignItems:'center',gap:16 }}>
            <div style={{ position:'relative',width:80,height:80,flexShrink:0 }}>
              <svg viewBox="0 0 36 36" style={{ transform:'rotate(-90deg)',width:80,height:80 }}>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" strokeWidth="3.2"/>
                <circle cx="18" cy="18" r="15.9" fill="none"
                  stroke={isAbnormal ? 'var(--amber)' : 'var(--green)'} strokeWidth="3.2"
                  strokeDasharray={`${pct} ${100-pct}`} strokeLinecap="round"/>
              </svg>
              <div style={{ position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
                fontFamily:'var(--font-mono)',fontWeight:700,fontSize:'1rem',
                color: isAbnormal ? 'var(--amber)' : 'var(--green)' }}>{pct}%</div>
            </div>
            <div>
              <p style={{ fontSize:'0.875rem',color:'var(--text-mid)',marginBottom:4 }}>Model Confidence</p>
              <p style={{ fontSize:'0.875rem' }}>
                {isAbnormal
                  ? `AI detected ${result.disease} with ${pct}% confidence. Recommend immediate clinical review and specialist consultation.`
                  : `X-ray appears normal with ${pct}% confidence. No significant pulmonary abnormalities detected.`}
              </p>
              {result.saved && <p style={{ fontSize:'0.75rem',color:'var(--teal)',marginTop:8 }}>✓ Result saved to patient record #{result.prediction_record_id}</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
