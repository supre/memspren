import * as Dialog from '@radix-ui/react-dialog'
import type { Update } from '@/lib/updates'

interface UpdateModalProps {
  update: Update | null
  onClose: () => void
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
  return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`
}

export default function UpdateModal({ update, onClose }: UpdateModalProps) {
  return (
    <Dialog.Root open={!!update} onOpenChange={(open) => { if (!open) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-surface/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-[92vw] max-w-2xl max-h-[80vh] overflow-y-auto custom-scroll glass-card rounded-2xl p-8 md:p-10 focus:outline-none"
          aria-describedby="update-details"
        >
          {update && (
            <>
              <div className="flex items-start justify-between gap-4 mb-6">
                <div>
                  <span className="font-label text-[0.6rem] text-primary font-bold tracking-[0.3em] block mb-2">
                    {formatDate(update.date)}
                  </span>
                  <Dialog.Title className="text-2xl md:text-3xl font-headline italic text-primary leading-tight">
                    {update.title}
                  </Dialog.Title>
                </div>
                <Dialog.Close
                  className="shrink-0 text-on-surface/30 hover:text-on-surface/70 transition-colors mt-1"
                  aria-label="Close"
                >
                  <span className="material-symbols-outlined text-2xl">close</span>
                </Dialog.Close>
              </div>
              <div id="update-details" className="text-on-surface/70 text-base leading-relaxed whitespace-pre-wrap font-light">
                {update.details}
              </div>
            </>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
