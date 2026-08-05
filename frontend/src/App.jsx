import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import TopBar from './components/TopBar.jsx'
import Starfield from './components/Starfield.jsx'
import Dashboard from './pages/Dashboard.jsx'
import UploadPage from './pages/UploadPage.jsx'
import AnalysisPage from './pages/AnalysisPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import FootprintPage from './pages/FootprintPage.jsx'
import LogsPage from './pages/LogsPage.jsx'

export default function App() {
  const location = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])

  return (
    <div className="relative min-h-screen text-sentinel-text terminal-grid scanlines">
      <Starfield />
      <TopBar />
      <main className="relative z-10 max-w-[1500px] mx-auto px-4 md:px-8 pt-24 pb-16">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan" element={<UploadPage />} />
          <Route path="/analysis/:id" element={<AnalysisPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/footprint" element={<FootprintPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  )
}
