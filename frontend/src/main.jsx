import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0d1520',
            color: '#e8f4f8',
            border: '1px solid #1a2d45',
            fontFamily: "'IBM Plex Sans', sans-serif",
            fontSize: '0.875rem',
          },
          success: { iconTheme: { primary: '#10d98a', secondary: '#0d1520' } },
          error:   { iconTheme: { primary: '#f1535a', secondary: '#0d1520' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
