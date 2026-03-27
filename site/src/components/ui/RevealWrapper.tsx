import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

interface RevealWrapperProps {
  children: ReactNode
  stagger?: boolean
  className?: string
}

export default function RevealWrapper({ children, stagger = false, className = '' }: RevealWrapperProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
        })
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const baseClass = stagger ? 'reveal-stagger' : 'reveal'

  return (
    <div ref={ref} className={`${baseClass} ${className}`}>
      {children}
    </div>
  )
}
