import { useState } from 'react'
import { Link } from 'react-router-dom'
import RevealWrapper from '@/components/ui/RevealWrapper'
import UpdateModal from '@/components/updates/UpdateModal'
import type { Update } from '@/lib/updates'

const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`
}

export default function RecentUpdates({ updates }: { updates: Update[] }) {
  const [modalUpdate, setModalUpdate] = useState<Update | null>(null)

  const recent = [...updates]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 3)

  return (
    <section className="py-24 md:py-32 relative">
      <div className="max-w-5xl mx-auto px-8">
        <RevealWrapper>
          <div className="section-glow mb-20" />
        </RevealWrapper>

        <RevealWrapper>
          <div className="text-center mb-24">
            <h2 className="text-5xl font-headline italic text-primary glow-text">Updates</h2>
            <p className="text-on-surface/50 mt-4 tracking-[0.2em] uppercase text-xs">What's happening with MemSpren</p>
          </div>
        </RevealWrapper>

        <RevealWrapper>
          <div className="relative">
            {/* Center vertical line */}
            <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-primary/30 to-transparent hidden md:block" />

            {recent.map((update, i) => {
              const isFirst = i === 0
              const isRight = i % 2 === 0

              const dotClass = isFirst
                ? 'border-primary ring-4 ring-primary/20'
                : 'border-primary/40'
              const cardBorder = isFirst ? 'border-l-primary' : 'border-l-primary/40'
              const dateColor = isFirst ? 'text-primary' : 'text-primary/70'
              const titleColor = isFirst ? 'text-primary' : 'text-primary/70'
              const justify = isRight ? 'md:justify-end' : 'md:justify-start'

              return (
                <div key={update.id} className={`relative flex ${justify} items-center group mb-10`}>
                  {/* Center dot */}
                  <div className={`absolute left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-surface border-2 ${dotClass} hidden md:block z-10`} />

                  {/* Card */}
                  <button
                    onClick={() => setModalUpdate(update)}
                    className={`glass-card rounded-2xl p-8 w-full md:w-[45%] border-l-4 ${cardBorder} relative overflow-hidden text-left transition-all duration-300 hover:border-l-primary group/card`}
                  >
                    <div className="absolute inset-0 hud-scanline opacity-10 pointer-events-none" />
                    <span className={`font-label text-[0.6rem] ${dateColor} font-bold tracking-[0.3em] mb-3 block`}>
                      {formatDate(update.date)}
                    </span>
                    <h4 className={`text-xl font-headline font-semibold ${titleColor} italic group-hover/card:text-primary transition-colors`}>
                      {update.title}
                    </h4>
                  </button>
                </div>
              )
            })}

            {/* View all — centered terminal node */}
            <div className="flex flex-col items-center gap-3 mt-4">
              <div className="w-4 h-4 rounded-full bg-surface border-2 border-primary/20 hidden md:block" />
              <Link
                to="/updates"
                className="flex items-center gap-2 text-on-surface/40 hover:text-primary font-label text-xs uppercase tracking-[0.2em] transition-all group no-underline px-5 py-2 rounded-full border border-primary/10 hover:border-primary/30 bg-surface/60 backdrop-blur-sm"
              >
                View all updates
                <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </Link>
            </div>

          </div>
        </RevealWrapper>
      </div>

      <UpdateModal update={modalUpdate} onClose={() => setModalUpdate(null)} />
    </section>
  )
}
