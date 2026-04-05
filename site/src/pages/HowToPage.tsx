import { useState, useEffect, useRef } from 'react'
import UpdateModal from '@/components/updates/UpdateModal'
import updatesData from '@/data/updates.json'
import type { Update } from '@/lib/updates'

const v03Update = (updatesData as Update[]).find(u => u.id === '2026-03-26-v03-direction') ?? null

const sections = [
  { id: 'setup', label: 'Installation & Setup' },
  { id: 'openclaw-setup', label: 'OpenClaw Setup' },
  { id: 'telegram', label: 'Telegram with Claude' },
]

function useActiveSection() {
  const [active, setActive] = useState('setup')

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id)
        })
      },
      { rootMargin: '-20% 0px -70% 0px' }
    )
    sections.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [])

  return active
}

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function DocSection({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="mb-20 scroll-mt-28">
      <h2 className="text-3xl md:text-4xl font-headline italic text-primary glow-text mb-2">{title}</h2>
      <div className="section-glow mt-6 mb-10" />
      <div className="prose-doc">
        {children}
      </div>
    </section>
  )
}

function Step({ num, color = 'primary', children }: { num: string; color?: string; children: React.ReactNode }) {
  const colorClass = color === 'cyan' ? 'text-accent-cyan' : 'text-primary'
  return (
    <div className="flex items-start gap-4">
      <span className={`font-label font-bold text-xs mt-1 shrink-0 ${colorClass}`}>{num}</span>
      <div className="text-on-surface/70 text-sm leading-relaxed">{children}</div>
    </div>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="text-primary/80 bg-primary/10 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
}

function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="glass-card rounded-2xl p-6 flex items-start gap-4 my-6">
      <span className="material-symbols-outlined text-primary/60 text-xl mt-0.5 shrink-0">info</span>
      <p className="text-on-surface/60 text-sm leading-relaxed">{children}</p>
    </div>
  )
}

function SubHeading({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-headline italic text-on-surface/80 mb-4 mt-10">{children}</h3>
}

export default function HowToPage() {
  const active = useActiveSection()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [modalUpdate, setModalUpdate] = useState<Update | null>(null)
  const sidebarRef = useRef<HTMLDivElement>(null)

  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-6xl mx-auto px-8">
        {/* Page header */}
        <div className="mb-12 pt-8">
          <h1 className="text-4xl md:text-5xl font-headline italic text-primary glow-text mb-3">How-to</h1>
          <p className="text-on-surface/50 font-light">Everything you need to set up and understand MemSpren.</p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 flex gap-12 relative">
        {/* Sidebar, sticky on desktop, collapsible on mobile */}
        <aside className="hidden lg:block w-52 shrink-0">
          <nav className="sticky top-28 space-y-1">
            <p className="font-label text-[0.6rem] uppercase tracking-[0.2em] text-on-surface/30 mb-4">On this page</p>
            {sections.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-label transition-all ${
                  active === id
                    ? 'text-primary bg-primary/10 border-l-2 border-primary'
                    : 'text-on-surface/40 hover:text-on-surface/70 hover:bg-primary/5 border-l-2 border-transparent'
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Mobile section nav */}
        <div className="lg:hidden fixed bottom-6 right-6 z-40" ref={sidebarRef}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="glass-card rounded-full w-12 h-12 flex items-center justify-center text-primary shadow-lg"
            aria-label="Jump to section"
          >
            <span className="material-symbols-outlined text-xl">toc</span>
          </button>
          {sidebarOpen && (
            <div className="glass-card rounded-2xl p-4 absolute bottom-14 right-0 w-56 space-y-1 shadow-xl">
              {sections.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => { scrollTo(id); setSidebarOpen(false) }}
                  className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-label transition-all ${
                    active === id ? 'text-primary bg-primary/10' : 'text-on-surface/50 hover:text-primary'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Main content */}
        <main className="flex-1 min-w-0 pb-32">

          {/* SETUP */}
          <DocSection id="setup" title="Installation & Setup">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              MemSpren runs as a skill inside an AI agent platform. Pick the one that matches your setup. Both produce the same Obsidian vault output.
            </p>

            <Note>
              You need <a href="https://obsidian.md" target="_blank" rel="noopener noreferrer" className="text-primary hover:brightness-125 no-underline">Obsidian</a> installed with a vault already created, and Git installed for version-safe sync. That's it.
            </Note>

            <SubHeading>Option A: Claude Skill (Claude Code users)</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-2">
              Uses Claude's native file tools to read and write directly to your vault. No external CLI, no Python environment, no configuration files.
            </p>
            <div className="glass-card rounded-xl px-5 py-3 flex items-center gap-3 mb-6 border border-primary/30">
              <span className="material-symbols-outlined text-primary/70 text-base shrink-0">pause_circle</span>
              <p className="text-on-surface/80 text-sm font-semibold italic leading-relaxed">
                Paused at v0.3 to reduce overhead.{' '}
                <button
                  onClick={() => setModalUpdate(v03Update)}
                  className="text-primary hover:brightness-125 underline underline-offset-2 transition-colors cursor-pointer bg-transparent border-none p-0 text-sm font-semibold italic"
                >
                  Details
                </button>
              </p>
            </div>
            <div className="space-y-4 mb-6">
              <Step num="01">Open Claude Code in <strong className="text-on-surface/80">Cowork mode</strong> and point it at your Obsidian vault folder as the working directory.</Step>
              <Step num="02">Load the skill file: <Code>memspren.skill</Code> from the <Code>claude/</Code> folder in the repo.</Step>
              <Step num="03">Start a conversation. On first use Claude will walk you through vault initialisation, creating the folder structure and your personal profile note.</Step>
              <Step num="04">Send your first brain dump. Any raw thought, note, or summary. Claude processes it, extracts entities, and writes the linked notes into your vault.</Step>
            </div>
            <a href="https://github.com/supre/memspren/tree/main/claude" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group no-underline w-fit">
              Claude skill repo <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_outward</span>
            </a>

            <SubHeading>Option B: OpenClaw Skill (local-first AI)</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-6">
              Runs entirely on your machine. OpenClaw has browser control and file access built in, which enables batch sync and background processing.
            </p>
            <div className="space-y-4 mb-6">
              <Step num="01" color="cyan">Copy the <Code>openclaw/</Code> folder from the repo into <Code>~/.openclaw/skills/</Code>.</Step>
              <Step num="02" color="cyan">Restart OpenClaw to load the skill.</Step>
              <Step num="03" color="cyan">Point it to your Obsidian vault path. OpenClaw walks you through the rest in about two minutes.</Step>
            </div>
            <a href="https://github.com/supre/memspren/tree/main/openclaw" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-accent-cyan font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group no-underline w-fit">
              OpenClaw skill repo <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_outward</span>
            </a>
          </DocSection>

          {/* OPENCLAW SETUP */}
          <DocSection id="openclaw-setup" title="OpenClaw Setup">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              The OpenClaw skill uses a deterministic Lobster pipeline for sync. All vault writes happen in a structured, reviewable pipeline rather than ad-hoc LLM calls. This section covers everything you need to get it running.
            </p>

            <Note>
              Currently macOS only. The sync pipeline uses shell tools and paths that assume a Mac environment.
            </Note>

            <SubHeading>Prerequisites</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01" color="cyan">
                Install <strong className="text-on-surface/80">uv</strong>, which manages Python versions and packages:
                {' '}<Code>brew install uv</Code> or follow the{' '}
                <a href="https://docs.astral.sh/uv/getting-started/installation/" target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:brightness-125">uv install guide</a>.
              </Step>
              <Step num="02" color="cyan">
                Install <strong className="text-on-surface/80">Git</strong>, required for version-safe vault snapshots:{' '}
                <Code>xcode-select --install</Code> or <Code>brew install git</Code>.
              </Step>
              <Step num="03" color="cyan">
                Have an <strong className="text-on-surface/80">Obsidian vault</strong> on your machine. A new empty vault works fine; the setup command creates all the structure.
              </Step>
            </div>

            <SubHeading>Install OpenClaw plugins</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-4">
              The sync pipeline requires two OpenClaw plugins: <strong className="text-on-surface/70">Lobster</strong> (the workflow runner) and <strong className="text-on-surface/70">llm-task</strong> (the LLM invocation primitive). Install and enable both:
            </p>
            <div className="glass-card rounded-2xl p-6 font-mono text-xs text-on-surface/60 leading-relaxed space-y-1 mb-4">
              <p><span className="text-on-surface/30"># install the plugins</span></p>
              <p>openclaw plugins install lobster</p>
              <p>openclaw plugins install llm-task</p>
              <p className="mt-2"><span className="text-on-surface/30"># enable them</span></p>
              <p>openclaw plugins enable lobster</p>
              <p>openclaw plugins enable llm-task</p>
              <p className="mt-2"><span className="text-on-surface/30"># restart the gateway to load the plugins</span></p>
              <p>openclaw gateway restart</p>
            </div>

            <SubHeading>Install the skill</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01" color="cyan">
                Clone the repo and copy the <Code>openclaw/</Code> folder into your OpenClaw skills directory. OpenClaw will not load the skill unless it lives here:
                <div className="mt-2 font-mono text-xs bg-surface/20 border border-white/5 rounded-lg px-4 py-3 text-on-surface/70">
                  cp -r openclaw/ ~/.openclaw/skills/memspren/
                </div>
              </Step>
              <Step num="02" color="cyan">
                Install <Code>memcli</Code>, the Python CLI that drives every pipeline step. Install it as a global uv tool so Lobster can call it from any directory:
                <div className="mt-2 font-mono text-xs bg-surface/20 border border-white/5 rounded-lg px-4 py-3 text-on-surface/70 space-y-1">
                  <p>cd ~/.openclaw/skills/memspren/</p>
                  <p className="mt-1"><span className="text-on-surface/30"># install globally; editable mode picks up code changes without reinstalling</span></p>
                  <p>uv tool install --editable .</p>
                  <p className="mt-2"><span className="text-on-surface/30"># verify</span></p>
                  <p>memcli --help</p>
                </div>
              </Step>
              <Step num="03" color="cyan">
                Scaffold your vault. Run once to create folders, seed files, and the config file:
                <div className="mt-2 font-mono text-xs bg-surface/20 border border-white/5 rounded-lg px-4 py-3 text-on-surface/70">
                  memcli setup --vault-path /path/to/vault --vault-name "Vault Name"
                </div>
              </Step>
              <Step num="04" color="cyan">
                Restart the OpenClaw gateway to load the skill:
                <div className="mt-2 font-mono text-xs bg-surface/20 border border-white/5 rounded-lg px-4 py-3 text-on-surface/70">
                  openclaw gateway restart
                </div>
              </Step>
            </div>

            <Note>
              <Code>uv tool install</Code> places <Code>memcli</Code> in <Code>~/.local/bin/</Code>, globally accessible. If you update the source code, the editable install picks up changes automatically. If you add or change dependencies in <Code>pyproject.toml</Code>, reinstall with <Code>uv tool install --reinstall --editable .</Code>
            </Note>

            <SubHeading>Run the tests</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-4">
              Verify the pipeline is wired correctly before your first sync:
            </p>
            <div className="glass-card rounded-2xl p-6 font-mono text-xs text-on-surface/60 leading-relaxed space-y-1">
              <p><span className="text-on-surface/30"># from openclaw/</span></p>
              <p>uv run pytest scripts/memcli/tests/ -v</p>
            </div>
            <p className="text-on-surface/50 text-xs mt-3 leading-relaxed">
              All tests create throwaway vaults under <Code>/tmp</Code>, nothing touches your real vault.
            </p>
          </DocSection>

          {/* TELEGRAM */}
          <DocSection id="telegram" title="Telegram with Claude">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              Claude Code can receive Telegram messages directly, which means you can send brain dumps from your phone without opening a laptop. The setup uses a Telegram bot and Claude's MCP Telegram plugin.
            </p>

            <Note>
              This works with the Claude Skill path only. You need an active Claude Code session running. The Telegram bot routes messages into it.
            </Note>

            <SubHeading>Create a Telegram bot</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01">Open Telegram and start a conversation with <strong className="text-on-surface/80">@BotFather</strong>.</Step>
              <Step num="02">Send <Code>/newbot</Code> and follow the prompts. Give it a name and username.</Step>
              <Step num="03">BotFather returns a bot token. Copy it, you'll need it in the next step.</Step>
            </div>

            <SubHeading>Configure the Claude Code Telegram channel</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01">In a Claude Code session, run the <Code>/telegram:configure</Code> skill. Paste in your bot token when prompted.</Step>
              <Step num="02">Open Telegram and send a message to your new bot. Claude Code will receive an incoming pairing request.</Step>
              <Step num="03">Run <Code>/telegram:access</Code> in Claude Code to approve your Telegram user ID.</Step>
              <Step num="04">Send a test message. Claude should respond directly in Telegram.</Step>
            </div>

            <Note>
              The Telegram channel runs through Claude Code's MCP server. Messages from approved users arrive as context in Claude's conversation. It can read, respond, and write files all from a single Telegram message.
            </Note>

            <SubHeading>Sending brain dumps from Telegram</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed">
              Once configured, just message your bot with any brain dump: a meeting note, a stray thought, a to-do, or a longer reflection. Claude processes it with the MemSpren skill loaded and writes the linked notes into your vault automatically. You don't need to be at your computer.
            </p>
          </DocSection>

        </main>
      </div>

      <UpdateModal update={modalUpdate} onClose={() => setModalUpdate(null)} />
    </div>
  )
}
