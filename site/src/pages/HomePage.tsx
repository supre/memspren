import Hero from '@/components/sections/Hero'
import Story from '@/components/sections/Story'
import PublicationsCarousel from '@/components/sections/PublicationsCarousel'
import RecentUpdates from '@/components/sections/RecentUpdates'
import Setup from '@/components/sections/Setup'
import metadata from '@/data/metadata.json'
import publications from '@/data/publications.json'
import updatesData from '@/data/updates.json'
import type { Update } from '@/lib/updates'

export default function HomePage() {
  return (
    <main>
      <Hero version={metadata.version} />
      <Story />
      <Setup />
      <PublicationsCarousel publications={publications} />
      <RecentUpdates updates={updatesData as Update[]} />
    </main>
  )
}
