import { useEffect, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'

const SEEN_KEY = 'memspren-status-seen-v1'
const ARTICLE_URL = 'https://innerodyssey.substack.com/p/how-i-gamified-my-grief-and-earned'
const SUBSTACK_EMBED = 'https://innerodyssey.substack.com/embed'

function hasSeen() {
  try { return localStorage.getItem(SEEN_KEY) === '1' } catch { return false }
}
function markSeen() {
  try { localStorage.setItem(SEEN_KEY, '1') } catch { /* private mode: ignore */ }
}

export default function StatusBanner() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!hasSeen()) setOpen(true)
  }, [])

  function onOpenChange(next: boolean) {
    setOpen(next)
    if (!next) markSeen()
  }

  return (
    <>
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 w-[92%] max-w-md">
        <button
          onClick={() => setOpen(true)}
          className="w-full glass-card rounded-full border border-primary/30 px-5 py-2.5 flex items-center justify-center gap-3 shadow-[0_0_24px_rgba(131,213,198,0.12)] cursor-pointer hover:border-primary/60 transition-colors"
        >
          <span className="material-symbols-outlined text-primary/80 text-base shrink-0">pause_circle</span>
          <span className="text-on-surface/80 text-xs md:text-sm">
            MemSpren is paused · <span className="text-primary underline underline-offset-2 font-semibold">Status</span>
          </span>
        </button>
      </div>

      <Dialog.Root open={open} onOpenChange={onOpenChange}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-surface/80 backdrop-blur-sm" />
          <Dialog.Content
            className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-[92vw] max-w-lg max-h-[88vh] overflow-y-auto custom-scroll glass-card rounded-2xl p-7 md:p-9 focus:outline-none"
            aria-describedby="status-body"
          >
            <div className="flex items-start justify-between gap-4 mb-5">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-2xl">pause_circle</span>
                <Dialog.Title className="text-2xl md:text-3xl font-headline italic text-primary leading-tight">
                  MemSpren is paused
                </Dialog.Title>
              </div>
              <Dialog.Close className="shrink-0 text-on-surface/30 hover:text-on-surface/70 transition-colors mt-1" aria-label="Close">
                <span className="material-symbols-outlined text-2xl">close</span>
              </Dialog.Close>
            </div>

            <div id="status-body" className="space-y-4 text-on-surface/70 text-sm md:text-base leading-relaxed font-light">
              <p>
                I stepped away in April 2026, after my father passed away. When I came back, a simpler system was
                working better for me than what I'd built, so MemSpren is on the back burner while I rethink it.
              </p>
              <p>
                <span className="text-on-surface/90 font-normal">What's here:</span> the OpenClaw skill and{' '}
                <code className="text-primary/90">memcli</code> at v0.4, and the Claude skill at v0.3. The code and docs
                still work as described, but there won't be new features for now.
              </p>
              <p>
                The idea behind MemSpren was always bigger than how I built it, and it still holds. I'm working out how
                to restart it from a different angle.
              </p>
              <a
                href={ARTICLE_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-primary font-semibold hover:brightness-125 no-underline"
              >
                Read how I'm gamifying my life to rebuild momentum post grief
                <span className="material-symbols-outlined text-base">arrow_outward</span>
              </a>
              <p className="pt-2">
                Until then, I'll share the journey, what I'm working on and any MemSpren updates in my newsletter.
              </p>
            </div>

            <div className="mt-4 rounded-xl overflow-hidden bg-white">
              <iframe
                src={SUBSTACK_EMBED}
                title="Subscribe to Inner Odyssey on Substack"
                width="100%"
                height="150"
                style={{ border: 0, display: 'block' }}
                loading="lazy"
              />
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  )
}
