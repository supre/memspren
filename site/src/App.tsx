import { Routes, Route } from 'react-router-dom'
import HomePage from '@/pages/HomePage'
import UpdatesPage from '@/pages/UpdatesPage'
import PublicationsPage from '@/pages/PublicationsPage'
import HowToPage from '@/pages/HowToPage'
import Nav from '@/components/layout/Nav'
import Footer from '@/components/layout/Footer'
import metadata from '@/data/metadata.json'

export default function App() {
  return (
    <div className="bg-surface text-on-surface font-body selection:bg-primary selection:text-on-primary min-h-screen antialiased">
      <Nav version={metadata.version} />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/updates" element={<UpdatesPage />} />
        <Route path="/publications" element={<PublicationsPage />} />
        <Route path="/how-to" element={<HowToPage />} />
      </Routes>
      <Footer version={metadata.version} />
    </div>
  )
}
