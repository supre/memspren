import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

const GitHubIcon = () => (
  <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
  </svg>
)

const navLinks = [
  { label: 'Story', to: '/#story', homeAnchor: '#story' },
  { label: 'Publications', to: '/publications' },
  { label: 'Updates', to: '/updates' },
]

interface NavProps {
  version: string
}

export default function Nav({ version }: NavProps) {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  const isHome = location.pathname === '/'

  function close() { setIsOpen(false) }

  function isActive(to: string) {
    if (to.startsWith('/#')) return false
    return location.pathname === to
  }

  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-[92%] max-w-4xl">
      <div className="glass-card rounded-full px-8 py-3 flex justify-between items-center">
        <Link to="/" className="font-headline text-2xl font-bold text-primary italic glow-text no-underline">
          MemSpren
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-x-8">
          {navLinks.map(({ label, to, homeAnchor }) => {
            const active = isActive(to)
            const linkClass = `font-label text-xs uppercase tracking-[0.2em] transition-all ${active ? 'text-primary' : 'text-on-surface/60 hover:text-primary'}`
            // Story: use hash anchor when on home page
            if (homeAnchor && isHome) {
              return <a key={label} href={homeAnchor} className={linkClass}>{label}</a>
            }
            return <Link key={label} to={to} className={linkClass}>{label}</Link>
          })}
        </div>

        <div className="hidden md:flex items-center gap-4">
          <a href="https://github.com/supre/memspren" target="_blank" rel="noopener noreferrer" className="text-on-surface/40 hover:text-primary transition-colors" title="GitHub">
            <GitHubIcon />
          </a>
          <span className="font-label text-xs text-on-surface/30 tracking-widest">{version}</span>
        </div>

        {/* Mobile burger */}
        <button
          className="md:hidden text-primary/60 hover:text-primary transition-colors"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Menu"
        >
          <span className="material-symbols-outlined text-2xl">{isOpen ? 'close' : 'menu'}</span>
        </button>
      </div>

      {/* Mobile slide menu */}
      <div
        className="md:hidden glass-card rounded-2xl mt-3 overflow-hidden transition-all duration-300"
        style={{ maxHeight: isOpen ? '400px' : '0', opacity: isOpen ? 1 : 0 }}
      >
        <div className="flex flex-col py-4">
          {navLinks.map(({ label, to, homeAnchor }) => {
            const active = isActive(to)
            const cls = `font-label text-sm uppercase tracking-[0.2em] px-8 py-3 hover:bg-primary/10 hover:text-primary transition-colors no-underline ${active ? 'text-primary' : 'text-on-surface/60'}`
            if (homeAnchor && isHome) {
              return <a key={label} href={homeAnchor} onClick={close} className={cls}>{label}</a>
            }
            return <Link key={label} to={to} onClick={close} className={cls}>{label}</Link>
          })}
          <div className="border-t border-primary/10 mx-8 my-2" />
          <a href="https://github.com/supre/memspren" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-on-surface/50 px-8 py-3 hover:bg-primary/10 hover:text-primary transition-colors no-underline">
            <GitHubIcon />
            <span className="font-label text-sm uppercase tracking-[0.2em]">GitHub</span>
          </a>
          <div className="px-8 py-3">
            <span className="font-label text-xs text-on-surface/30 tracking-widest">{version}</span>
          </div>
        </div>
      </div>
    </nav>
  )
}
