import { useRef } from 'react'
import { Link } from 'react-router-dom'
import RevealWrapper from '@/components/ui/RevealWrapper'

interface Publication {
  title: string
  medium: string
  context: string
  url: string
  date: string
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[d.getMonth()]} ${d.getFullYear()}`
}

export default function PublicationsCarousel({ publications }: { publications: Publication[] }) {
  const trackRef = useRef<HTMLDivElement>(null)
  const sorted = [...publications]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 4)

  function scroll(dir: 'prev' | 'next') {
    if (!trackRef.current) return
    const card = trackRef.current.querySelector('a') as HTMLElement | null
    if (!card) return
    const amount = card.offsetWidth + 32 // card width + gap
    trackRef.current.scrollBy({ left: dir === 'next' ? amount : -amount, behavior: 'smooth' })
  }

  return (
    <section id="publications" className="py-24 md:py-32 relative">
      <div className="max-w-5xl mx-auto px-8">
        <RevealWrapper>
          <div className="section-glow mb-20" />
        </RevealWrapper>

        <RevealWrapper>
          <div className="text-center mb-16">
            <h2 className="text-5xl font-headline italic text-primary glow-text">Publications</h2>
            <p className="text-on-surface/50 mt-4 tracking-[0.2em] uppercase text-xs">Documenting the methodology as it's built</p>
          </div>
        </RevealWrapper>

        {/* Controls row */}
        <RevealWrapper className="flex items-center justify-between mb-8">
          <Link
            to="/publications"
            className="flex items-center gap-2 text-primary font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group"
          >
            All publications
            <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_forward</span>
          </Link>
          <div className="flex gap-2">
            <button
              onClick={() => scroll('prev')}
              className="w-9 h-9 rounded-full glass-card glass-card-hover flex items-center justify-center text-on-surface/50 hover:text-primary transition-colors"
              aria-label="Previous"
            >
              <span className="material-symbols-outlined text-lg">chevron_left</span>
            </button>
            <button
              onClick={() => scroll('next')}
              className="w-9 h-9 rounded-full glass-card glass-card-hover flex items-center justify-center text-on-surface/50 hover:text-primary transition-colors"
              aria-label="Next"
            >
              <span className="material-symbols-outlined text-lg">chevron_right</span>
            </button>
          </div>
        </RevealWrapper>

        {/* Carousel track */}
        <div
          ref={trackRef}
          className="flex gap-8 overflow-x-auto pb-4 snap-x snap-mandatory scroll-smooth"
          style={{ scrollbarWidth: 'none' }}
        >
          {sorted.map((pub) => (
            <a
              key={pub.url}
              href={pub.url}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-card glass-card-hover rounded-2xl p-8 transition-all duration-300 group no-underline flex-none snap-start"
              style={{ width: 'clamp(280px, 70vw, 380px)' }}
            >
              <div className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-[0.6rem] font-label uppercase tracking-widest text-primary/70">
                  {pub.medium}
                </span>
                <span className="text-on-surface/30 text-xs">{formatDate(pub.date)}</span>
              </div>
              <h3 className="text-xl font-headline italic text-on-surface/80 group-hover:text-primary transition-colors mb-3 leading-snug">{pub.title}</h3>
              <p className="text-on-surface/40 text-sm leading-relaxed font-light">{pub.context}</p>
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}
