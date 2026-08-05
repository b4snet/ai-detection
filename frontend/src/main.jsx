import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { SentinelProvider } from './context/SentinelContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <SentinelProvider>
        <App />
      </SentinelProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
