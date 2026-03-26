import type { Update } from '@/lib/updates'
import { shouldExpand } from '@/lib/updates'

interface UpdateCardProps {
  update: Update
  onOpenModal: (update: Update) => void
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
  return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`
}

export default function UpdateCard({ update, onOpenModal }: UpdateCardProps) {
  const expanded = shouldExpand(update.details)

  return (
    <div className="glass-card glass-card-hover rounded-2xl p-8 relative overflow-hidden transition-all duration-300">
      <div className="absolute inset-0 hud-scanline opacity-10 pointer-events-none" />
      <span className="font-label text-[0.6rem] text-primary font-bold tracking-[0.3em] block mb-3">
        {formatDate(update.date)}
      </span>
      <h3 className="text-xl md:text-2xl font-headline italic text-primary mb-4 leading-tight">
        {update.title}
      </h3>
      {expanded ? (
        <>
          <p className="text-on-surface/60 text-sm leading-relaxed font-light mb-5">
            {update.summary}
          </p>
          <button
            onClick={() => onOpenModal(update)}
            className="flex items-center gap-2 text-primary font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group"
          >
            Read more
            <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_forward</span>
          </button>
        </>
      ) : (
        <p className="text-on-surface/60 text-sm leading-relaxed font-light">
          {update.details}
        </p>
      )}
    </div>
  )
}
