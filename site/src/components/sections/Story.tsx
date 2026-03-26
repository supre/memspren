import { useState } from 'react'
import RevealWrapper from '@/components/ui/RevealWrapper'

interface StepProps {
  num: string
  title: string
  subtitle: string
  isFirst?: boolean
  isOpen: boolean
  onToggle: () => void
  children: React.ReactNode
}

function Step({ num, title, subtitle, isFirst = false, isOpen, onToggle, children }: StepProps) {
  return (
    <div className="stepper-step relative pl-16 md:pl-20 pb-8">
      <button
        className={`stepper-node absolute left-0 md:left-1 w-10 h-10 md:w-11 md:h-11 rounded-full bg-surface border-2 flex items-center justify-center z-10 cursor-pointer hover:ring-4 hover:ring-primary/20 transition-all ${isOpen ? 'border-primary ring-4 ring-primary/20' : isFirst ? 'border-primary' : 'border-primary/40'}`}
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <span className={`font-label font-bold text-xs ${isOpen || isFirst ? 'text-primary' : 'text-primary/60'}`}>{num}</span>
      </button>
      <button className="stepper-title w-full text-left cursor-pointer group" onClick={onToggle}>
        <div className="flex items-center gap-4">
          <h3 className="text-xl md:text-2xl font-headline italic text-on-surface/80 group-hover:text-primary transition-colors">{title}</h3>
          <span
            className="material-symbols-outlined text-primary/40 text-lg stepper-arrow"
            style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
          >
            expand_more
          </span>
        </div>
        <p className="text-on-surface/40 text-sm mt-1 font-light">{subtitle}</p>
      </button>
      <div
        className="stepper-content overflow-hidden transition-all duration-400 ease-in-out"
        style={{ maxHeight: isOpen ? '2000px' : '0px' }}
      >
        <div className="space-y-6 text-base md:text-lg text-on-surface/60 leading-relaxed font-light pt-8">
          {children}
        </div>
      </div>
    </div>
  )
}

export default function Story() {
  const [openStep, setOpenStep] = useState<number | null>(null)

  function toggle(n: number) {
    setOpenStep(openStep === n ? null : n)
  }

  return (
    <section id="story" className="py-24 md:py-32 relative">
      <div className="max-w-4xl mx-auto px-8">
        <RevealWrapper>
          <div className="section-glow mb-20" />
        </RevealWrapper>

        <RevealWrapper>
          <h2 className="text-4xl md:text-5xl font-headline italic text-primary glow-text mb-6">The Story</h2>
          <p className="text-on-surface/50 text-base md:text-lg font-light leading-relaxed max-w-2xl mb-16">
            MemSpren started because I was stuck. As someone with ADHD, my head is always full — dozens of thoughts competing at once, a constant cognitive load that never lets up. I kept losing track of what I needed to do, kept feeling like I had no momentum, no clarity on what to execute or how.
          </p>
          <p className="text-on-surface/50 text-base md:text-lg font-light leading-relaxed max-w-2xl mb-16">
            I read books, studied strategies, noted patterns I wanted to implement — then forgot what to implement and how to experiment with what actually works for me. Everything became overwhelming. I journaled on paper and forgot where I wrote what. I tried Evernote, Notion, Bear, Apple Notes — they all worked, and I kept losing track at the same time. My own perfectionist tendencies made it worse: I was never moving toward my goals, just endlessly reorganizing.
          </p>
          <p className="text-on-surface/50 text-base md:text-lg font-light leading-relaxed max-w-2xl mb-16">
            That's where MemSpren came in — not as another note-taking app, but as an execution system. A cognitive second brain that helps me figure out what I need to do and keeps me making progress, even when my own mind won't cooperate.
          </p>
        </RevealWrapper>

        <RevealWrapper>
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-5 md:left-6 top-0 bottom-0 w-[1px] bg-gradient-to-b from-primary/40 via-primary/20 to-transparent" />

            <Step num="01" title="The cost of a scattered mind" subtitle="It's not about the tools — it's about what you lose." isFirst isOpen={openStep === 1} onToggle={() => toggle(1)}>
              <p>The worst part isn't losing a note. It's the feeling that you're not moving. You have goals, you have ideas, you have strategies — but the evidence of progress is invisible. Even to you.</p>
              <p>You finish a week and can't point to what changed. You had a breakthrough insight on Tuesday, but by Friday it's buried under new inputs and you can't remember what it connected to. The threads between your ideas exist — you can feel them forming — but nothing holds them together.</p>
              <p>And when you can't see your own momentum, your brain fills the gap with doubt. Am I stuck? Am I wasting time? Am I actually getting anywhere? The cognitive load of that uncertainty is heavier than the work itself.</p>
              <p className="text-on-surface/40 text-sm italic">It's not a productivity problem. It's a visibility problem.</p>
            </Step>

            <Step num="02" title="The problem was never your discipline" subtitle="Productivity tools solve the wrong problem." isOpen={openStep === 2} onToggle={() => toggle(2)}>
              <p>It was never your system. It was never the app. The problem is that you can't see your own thinking.</p>
              <p>When your ideas sit in silos — notes here, conversations there, reflections somewhere else — you lose something more important than organization. You lose the ability to see patterns forming. You lose momentum, not because you stopped working, but because the evidence of your progress is invisible. Even to you.</p>
              <p>Productivity tools have been solving the wrong problem for decades. They optimize for storage and retrieval. But the real need isn't <span className="text-on-surface/40 italic">"find that note I wrote."</span></p>
              <div className="glass-card rounded-2xl p-8 md:p-10 my-2">
                <p className="text-primary font-headline italic text-lg md:text-xl leading-relaxed">The real need is: show me how my ideas connect. Show me what I'm actually focused on. Show me that the scattered conversations I had this week are weaving into something coherent.</p>
              </div>
              <p>The problem is visibility. And until you solve for visibility, no amount of discipline, no new app, no better system will close the gap.</p>
            </Step>

            <Step num="03" title="How this started" subtitle="An engineer who builds systems — except for his own mind." isOpen={openStep === 3} onToggle={() => toggle(3)}>
              <p>I'm a software engineer. Distributed systems, cloud infrastructure, AI systems. I spend my days inside complex architectures where the relationships between components matter more than the components themselves.</p>
              <p className="text-on-surface/80 text-xl font-headline italic">And yet I couldn't architect my own thinking.</p>
              <p>I knew the problem was structural. My ideas weren't bad — they were disconnected. What I needed wasn't another app with better UX. I needed extraction rules, linking logic, and memory management patterns that could take the raw mess of daily thinking and turn it into something structured. Automatically. Without me maintaining anything.</p>
              <div className="glass-card rounded-2xl p-8 md:p-10 my-2">
                <p className="text-on-surface/70 leading-relaxed">So I built it. An AI skill that processes brain dumps, extracts entities, builds relationships, and syncs everything to an Obsidian knowledge graph. I ran it on my own thinking daily.</p>
              </div>
              <p>Within weeks, the graph started showing me connections I hadn't consciously made. Clusters of related ideas I didn't know were forming. A map of what I was <em>actually</em> focused on — not what I thought I was focused on.</p>
              <p className="text-primary/80 font-headline italic text-lg">That became MemSpren.</p>
            </Step>

            <Step num="04" title="One sentence in. Five linked notes out." subtitle="How a brain dump becomes a knowledge graph." isOpen={openStep === 4} onToggle={() => toggle(4)}>
              <p>You send a brain dump. It can be messy. It should be messy. A Telegram message, a voice transcription, a raw paragraph of whatever is on your mind.</p>
              <div className="glass-card rounded-2xl p-8 md:p-10 my-2 border-l-2 border-l-primary/40">
                <p className="text-on-surface/50 text-xs font-label uppercase tracking-widest mb-3">Brain dump</p>
                <p className="text-on-surface/80 font-headline italic text-base leading-relaxed">"I talked to John about career moves and he mentioned graph theory. That connects to what I was reading about knowledge graphs last week. Also need to follow up with the team about the deployment pipeline."</p>
              </div>
              <p>MemSpren processes that single input and produces:</p>
              <div className="space-y-3 my-2">
                <div className="flex items-start gap-3"><span className="entity-arrow mt-1 text-sm">→</span><p>A person entity: <span className="text-primary/90 font-medium">John</span>, with a relationship to career strategy and graph theory</p></div>
                <div className="flex items-start gap-3"><span className="entity-arrow mt-1 text-sm">→</span><p>A concept: <span className="text-primary/90 font-medium">graph theory</span>, linked to your existing notes on knowledge graphs</p></div>
                <div className="flex items-start gap-3"><span className="entity-arrow mt-1 text-sm">→</span><p>A project reference: <span className="text-primary/90 font-medium">deployment pipeline</span>, tagged as requiring follow-up</p></div>
                <div className="flex items-start gap-3"><span className="entity-arrow mt-1 text-sm">→</span><p>A temporal event: <span className="text-primary/90 font-medium">today's conversation</span>, timestamped and connected to all of the above</p></div>
                <div className="flex items-start gap-3"><span className="entity-arrow mt-1 text-sm">→</span><p>Typed relationships between every entity: John ↔ career strategy, graph theory ↔ knowledge graphs, deployment pipeline ↔ follow-up</p></div>
              </div>
              <p>You didn't create any of those notes. You didn't add tags. You didn't build links. You talked. MemSpren extracted, linked, and structured.</p>
              <p>Every brain dump adds nodes and edges to your Obsidian graph. Over days and weeks, scattered inputs become visible clusters. The graph grows while you think.</p>
              <p className="text-primary/80 font-headline italic text-lg">That is what visibility looks like.</p>
            </Step>

            <Step num="05" title="Open source. Your thinking stays yours." subtitle="No lock-in. Portable. Yours forever." isOpen={openStep === 5} onToggle={() => toggle(5)}>
              <p>MemSpren is a methodology that runs as a skill inside AI agent platforms. It produces standard Obsidian markdown files — portable, readable, yours. The tools are open. The vault is yours. There is no lock-in.</p>
              <p>If you've been looking for a way to stop re-explaining yourself to every new AI conversation, to stop manually linking every note, to actually see how your ideas connect without maintaining the connections yourself — the methodology is here. It's being refined through daily use. And it works.</p>
              <div className="grid md:grid-cols-3 gap-4 mt-4">
                <a href="#setup" className="glass-card glass-card-hover rounded-2xl p-6 transition-all duration-300 group no-underline block">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4 border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-xl">terminal</span>
                  </div>
                  <h4 className="text-sm font-headline font-semibold text-primary mb-2 italic">Ready to start?</h4>
                  <p className="text-on-surface/50 text-xs leading-relaxed mb-4">Prerequisites, installation, your first brain dump.</p>
                  <span className="flex items-center text-primary font-bold text-[0.6rem] uppercase tracking-widest gap-2">How to Get Started <span className="material-symbols-outlined text-xs group-hover:translate-x-1 transition-transform">arrow_forward</span></span>
                </a>
                <a href="#publications" className="glass-card glass-card-hover rounded-2xl p-6 transition-all duration-300 group no-underline block">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4 border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-xl">article</span>
                  </div>
                  <h4 className="text-sm font-headline font-semibold text-primary mb-2 italic">Want proof it's real?</h4>
                  <p className="text-on-surface/50 text-xs leading-relaxed mb-4">Every article documenting the methodology.</p>
                  <span className="flex items-center text-primary font-bold text-[0.6rem] uppercase tracking-widest gap-2">Publications <span className="material-symbols-outlined text-xs group-hover:translate-x-1 transition-transform">arrow_forward</span></span>
                </a>
                <a href="https://github.com/supre/memspren" target="_blank" rel="noopener noreferrer" className="glass-card glass-card-hover rounded-2xl p-6 transition-all duration-300 group no-underline block">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4 border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-xl">code</span>
                  </div>
                  <h4 className="text-sm font-headline font-semibold text-primary mb-2 italic">Want to follow along?</h4>
                  <p className="text-on-surface/50 text-xs leading-relaxed mb-4">The code, the skills, the vault structure. All open.</p>
                  <span className="flex items-center text-primary font-bold text-[0.6rem] uppercase tracking-widest gap-2">GitHub <span className="material-symbols-outlined text-xs group-hover:translate-x-1 transition-transform">arrow_forward</span></span>
                </a>
              </div>
            </Step>
          </div>
        </RevealWrapper>
      </div>
    </section>
  )
}
