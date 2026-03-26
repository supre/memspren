import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export default function ScrollToTop() {
  const { pathname, hash } = useLocation()

  useEffect(() => {
    if (hash) {
      // Let the page render first, then scroll to the anchor
      const id = hash.slice(1)
      const attempt = (tries: number) => {
        const el = document.getElementById(id)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        } else if (tries > 0) {
          setTimeout(() => attempt(tries - 1), 80)
        }
      }
      attempt(5)
    } else {
      window.scrollTo(0, 0)
    }
  }, [pathname, hash])

  return null
}
