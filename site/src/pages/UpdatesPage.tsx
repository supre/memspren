import UpdatesList from '@/components/updates/UpdatesList'
import RevealWrapper from '@/components/ui/RevealWrapper'
import updatesData from '@/data/updates.json'
import type { Update } from '@/lib/updates'

const updates = updatesData as Update[]

export default function UpdatesPage() {
  return (
    <main className="min-h-screen pt-36 pb-16">
      <div className="max-w-3xl mx-auto px-8">
        <RevealWrapper>
          <div className="mb-12">
            <h1 className="text-4xl md:text-5xl font-headline italic text-primary glow-text mb-3">Updates</h1>
            <p className="text-on-surface/50 font-light">
              What I'm working on, what's frustrating, and where things are headed.
            </p>
          </div>
          <div className="section-glow mb-12" />
        </RevealWrapper>

        <UpdatesList updates={updates} />
      </div>
    </main>
  )
}
