import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hc_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth
export const loginUser = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
}
export const registerUser = (data) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')

// Patients
export const getMyProfile = () => api.get('/patients/me')
export const updateMyProfile = (data) => api.put('/patients/me', data)
export const listPatients = () => api.get('/patients/')
export const getPatient = (id) => api.get(`/patients/${id}`)

// Visits
export const getVisits = (patientId) => api.get(`/patients/${patientId}/visits`)
export const addVisit = (patientId, data) => api.post(`/patients/${patientId}/visits`, data)

// Medications
export const getMedications = (patientId) => api.get(`/patients/${patientId}/medications`)
export const addMedication = (patientId, data) => api.post(`/patients/${patientId}/medications`, data)

// Predictions
export const getPredictions = (patientId) => api.get(`/patients/${patientId}/predictions`)
export const predictDiabetes = (data, patientId) =>
  api.post(`/predict/diabetes${patientId ? `?patient_id=${patientId}` : ''}`, data)
export const predictHeart = (data, patientId) =>
  api.post(`/predict/heart${patientId ? `?patient_id=${patientId}` : ''}`, data)
export const predictXray = (formData, patientId) =>
  api.post(`/predict/xray${patientId ? `?patient_id=${patientId}` : ''}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

// Chatbot
export const sendChatMessage = (message, history) =>
  api.post('/chatbot/chat', { message, history, include_patient_context: true })

// Admin
export const listAllUsers = () => api.get('/admin/users')
export const updateUserStatus = (userId, isActive) =>
  api.patch(`/admin/users/${userId}/status`, { is_active: isActive })

// Full patient profile (doctor view)
export const getFullPatientProfile = (patientId) =>
  api.get(`/admin/patients/${patientId}/full`)

export default api