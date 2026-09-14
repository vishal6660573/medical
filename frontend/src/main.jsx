import React from 'react'
import ReactDOM from 'react-dom/client'
//ReactDOM is responsible for connecting React to the actual HTML DOM in the browser
import { BrowserRouter } from 'react-router-dom'
//This comes from React Router. It allows your React application to have multiple URLs/pages without doing a full browser reload.
import { Toaster } from 'react-hot-toast'
//react-hot-toast is a library for displaying notification messages.
import App from './App'
//This imports your main React component.
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
