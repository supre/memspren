import { useState } from 'react'
import type { Update } from '@/lib/updates'
import UpdateCard from './UpdateCard'
import UpdateModal from './UpdateModal'

export default function UpdatesList({ updates }: { updates: Update[] }) {
  const [modalUpdate, setModalUpdate] = useState<Update | null>(null)

  const sorted = [...updates].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  return (
    <>
      <div className="grid gap-6 md:gap-8">
        {sorted.map((update) => (
          <UpdateCard key={update.id} update={update} onOpenModal={setModalUpdate} />
        ))}
      </div>
      <UpdateModal update={modalUpdate} onClose={() => setModalUpdate(null)} />
    </>
  )
}
