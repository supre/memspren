import RevealWrapper from '@/components/ui/RevealWrapper'

export default function Setup() {
  return (
    <section id="setup" className="py-24 md:py-32 relative">
      <div className="max-w-4xl mx-auto px-8">
        <RevealWrapper>
          <div className="section-glow mb-20" />
        </RevealWrapper>

        <RevealWrapper>
          <div className="text-center mb-16">
            <h2 className="text-5xl font-headline italic text-primary glow-text">Quick Setup</h2>
            <p className="text-on-surface/50 mt-4 tracking-[0.2em] uppercase text-xs">Zero to running in under 5 minutes</p>
          </div>
        </RevealWrapper>

        <RevealWrapper stagger className="grid md:grid-cols-2 gap-8">
          {/* Claude Skill */}
          <div className="glass-card rounded-2xl p-10 relative overflow-hidden">
            <div className="absolute inset-0 hud-scanline opacity-10 pointer-events-none" />
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 border border-primary/20">
              <span className="material-symbols-outlined text-primary text-2xl">psychology</span>
            </div>
            <h3 className="text-2xl font-headline font-semibold text-primary mb-4 italic">Claude Skill</h3>
            <p className="text-on-surface/50 text-sm leading-relaxed mb-6">For Claude Code users. Uses Claude's native file tools — no CLI required.</p>
            <ol className="space-y-4 text-on-surface/60 text-sm leading-relaxed">
              <li className="flex items-start gap-3">
                <span className="font-label text-primary font-bold text-xs mt-0.5">01</span>
                <span>Open Claude Code in Cowork mode and select your Obsidian vault folder</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-label text-primary font-bold text-xs mt-0.5">02</span>
                <span>Load <code className="text-primary/80 bg-primary/10 px-1.5 py-0.5 rounded text-xs">managing-second-brain.skill</code> from the <code className="text-primary/80 bg-primary/10 px-1.5 py-0.5 rounded text-xs">claude/</code> folder</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-label text-primary font-bold text-xs mt-0.5">03</span>
                <span>Start a conversation — Claude guides you through setup on first use</span>
              </li>
            </ol>
          </div>

          {/* OpenClaw Skill */}
          <div className="glass-card rounded-2xl p-10 relative overflow-hidden">
            <div className="absolute inset-0 hud-scanline opacity-10 pointer-events-none" />
            <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 flex items-center justify-center mb-6 border border-accent-cyan/20">
              <span className="material-symbols-outlined text-accent-cyan text-2xl">terminal</span>
            </div>
            <h3 className="text-2xl font-headline font-semibold text-accent-cyan mb-4 italic">OpenClaw Skill</h3>
            <p className="text-on-surface/50 text-sm leading-relaxed mb-6">For local-first AI. Runs on your machine with browser control, file access, and batch sync.</p>
            <ol className="space-y-4 text-on-surface/60 text-sm leading-relaxed">
              <li className="flex items-start gap-3">
                <span className="font-label text-accent-cyan font-bold text-xs mt-0.5">01</span>
                <span>Copy the <code className="text-accent-cyan/80 bg-accent-cyan/10 px-1.5 py-0.5 rounded text-xs">openclaw/</code> folder to <code className="text-accent-cyan/80 bg-accent-cyan/10 px-1.5 py-0.5 rounded text-xs">~/.openclaw/skills/</code></span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-label text-accent-cyan font-bold text-xs mt-0.5">02</span>
                <span>Restart OpenClaw to load the skill</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-label text-accent-cyan font-bold text-xs mt-0.5">03</span>
                <span>Point it to your Obsidian vault — OpenClaw guides you through setup (~2 min)</span>
              </li>
            </ol>
          </div>
        </RevealWrapper>

        {/* Prerequisites + full docs link */}
        <RevealWrapper className="mt-8">
          <div className="glass-card rounded-2xl p-8">
            <div className="flex items-start justify-between gap-6 flex-wrap">
              <div className="flex items-start gap-4">
                <span className="material-symbols-outlined text-primary/60 text-xl mt-0.5">info</span>
                <div className="text-on-surface/50 text-sm leading-relaxed">
                  <p className="text-on-surface/70 font-medium mb-2">Prerequisites</p>
                  <p>
                    <a href="https://obsidian.md" target="_blank" rel="noopener noreferrer" className="text-primary hover:brightness-125 transition-all no-underline">Obsidian</a> installed with a vault created. Git installed (for version-safe sync). That's it.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </RevealWrapper>
      </div>
    </section>
  )
}
