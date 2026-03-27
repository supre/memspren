import RevealWrapper from '@/components/ui/RevealWrapper'

interface Publication {
  title: string
  medium: string
  type: string
  context: string
  url: string
  date: string
  tags: string[]
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[d.getMonth()]} ${d.getFullYear()}`
}

export default function Publications({ publications }: { publications: Publication[] }) {
  const sorted = [...publications].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  return (
    <section id="publications" className="py-24 md:py-32 relative">
      <div className="max-w-5xl mx-auto px-8">
        <RevealWrapper>
          <div className="section-glow mb-20" />
        </RevealWrapper>

        <RevealWrapper className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16">
          <div>
            <h2 className="text-4xl md:text-5xl font-headline italic text-primary glow-text">Publications</h2>
            <p className="text-on-surface/40 mt-3 text-sm font-light">Documenting the methodology as it's built.</p>
          </div>
          <div className="flex gap-6 mt-6 md:mt-0">
            <a href="https://dev.to/supreet_s" target="_blank" rel="noopener noreferrer" className="text-on-surface/40 hover:text-primary transition-colors text-sm font-label uppercase tracking-widest">dev.to</a>
            <a href="https://innerodyssey.substack.com" target="_blank" rel="noopener noreferrer" className="text-on-surface/40 hover:text-primary transition-colors text-sm font-label uppercase tracking-widest">Substack</a>
          </div>
        </RevealWrapper>

        <RevealWrapper stagger className="grid md:grid-cols-2 gap-8">
          {sorted.map((pub) => (
            <a
              key={pub.url}
              href={pub.url}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-card glass-card-hover rounded-2xl p-8 transition-all duration-300 group no-underline block"
            >
              <div className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-[0.6rem] font-label uppercase tracking-widest text-primary/70">
                  {pub.medium}
                </span>
                <span className="text-on-surface/30 text-xs">{formatDate(pub.date)}</span>
              </div>
              <h3 className="text-xl font-headline italic text-on-surface/80 group-hover:text-primary transition-colors mb-3">{pub.title}</h3>
              <p className="text-on-surface/40 text-sm leading-relaxed font-light">{pub.context}</p>
            </a>
          ))}
        </RevealWrapper>
      </div>
    </section>
  )
}
