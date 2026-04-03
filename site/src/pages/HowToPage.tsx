import { useState, useEffect, useRef } from 'react'

const sections = [
  { id: 'setup', label: 'Installation & Setup' },
  { id: 'openclaw-setup', label: 'OpenClaw Setup' },
  { id: 'create-agent', label: 'Create an Agent' },
  { id: 'telegram', label: 'Telegram with Claude' },
  { id: 'architecture', label: 'Architecture' },
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
        {/* Sidebar — sticky on desktop, collapsible on mobile */}
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

          {/* ── SETUP ─────────────────────────────────────── */}
          <DocSection id="setup" title="Installation & Setup">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              MemSpren runs as a skill inside an AI agent platform. Pick the one that matches your setup — both produce the same Obsidian vault output.
            </p>

            <Note>
              You need <a href="https://obsidian.md" target="_blank" rel="noopener noreferrer" className="text-primary hover:brightness-125 no-underline">Obsidian</a> installed with a vault already created, and Git installed for version-safe sync. That's it.
            </Note>

            <SubHeading>Option A — Claude Skill (Claude Code users)</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-6">
              Uses Claude's native file tools to read and write directly to your vault. No external CLI, no Python environment, no configuration files.
            </p>
            <div className="space-y-4 mb-6">
              <Step num="01">Open Claude Code in <strong className="text-on-surface/80">Cowork mode</strong> and point it at your Obsidian vault folder as the working directory.</Step>
              <Step num="02">Load the skill file: <Code>managing-second-brain.skill</Code> from the <Code>claude/</Code> folder in the repo.</Step>
              <Step num="03">Start a conversation. On first use Claude will walk you through vault initialisation — creating the folder structure and your personal profile note.</Step>
              <Step num="04">Send your first brain dump. Any raw thought, note, or summary. Claude processes it, extracts entities, and writes the linked notes into your vault.</Step>
            </div>
            <a href="https://github.com/supre/memspren/tree/main/claude" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group no-underline w-fit">
              Claude skill repo <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_outward</span>
            </a>

            <SubHeading>Option B — OpenClaw Skill (local-first AI)</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-6">
              Runs entirely on your machine. OpenClaw has browser control and file access built in, which enables batch sync and background processing.
            </p>
            <div className="space-y-4 mb-6">
              <Step num="01" color="cyan">Copy the <Code>openclaw/</Code> folder from the repo into <Code>~/.openclaw/skills/</Code>.</Step>
              <Step num="02" color="cyan">Restart OpenClaw to load the skill.</Step>
              <Step num="03" color="cyan">Point it to your Obsidian vault path — OpenClaw walks you through the rest in about two minutes.</Step>
            </div>
            <a href="https://github.com/supre/memspren/tree/main/openclaw" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-accent-cyan font-bold text-[0.65rem] uppercase tracking-widest hover:brightness-125 transition-all group no-underline w-fit">
              OpenClaw skill repo <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_outward</span>
            </a>
          </DocSection>

          {/* ── OPENCLAW SETUP ────────────────────────────── */}
          <DocSection id="openclaw-setup" title="OpenClaw Setup">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              The OpenClaw skill uses a deterministic Lobster pipeline for sync — all vault writes happen in a structured, reviewable pipeline rather than ad-hoc LLM calls. This section covers everything you need to get it running.
            </p>

            <Note>
              Currently macOS only. The sync pipeline uses shell tools and paths that assume a Mac environment.
            </Note>

            <SubHeading>Prerequisites</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01" color="cyan">
                Install <strong className="text-on-surface/80">uv</strong> — the Python package manager used to run the pipeline:
                {' '}<Code>brew install uv</Code> or follow the{' '}
                <a href="https://docs.astral.sh/uv/getting-started/installation/" target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:brightness-125">uv install guide</a>.
              </Step>
              <Step num="02" color="cyan">
                Install <strong className="text-on-surface/80">Lobster</strong> — the workflow engine that drives the sync pipeline. Follow the{' '}
                <a href="https://github.com/openclaw/lobster" target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:brightness-125">Lobster install guide</a>.
              </Step>
              <Step num="03" color="cyan">
                Install <strong className="text-on-surface/80">Git</strong> — required for version-safe vault snapshots:{' '}
                <Code>xcode-select --install</Code> or <Code>brew install git</Code>.
              </Step>
              <Step num="04" color="cyan">
                Have an <strong className="text-on-surface/80">Obsidian vault</strong> on your machine. A new empty vault works fine — the setup command creates all the structure.
              </Step>
            </div>

            <SubHeading>Install the skill</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01" color="cyan">
                Clone the repo or download the <Code>openclaw/</Code> folder. Copy it into your OpenClaw skills directory:
                {' '}<Code>~/.openclaw/skills/memspren/</Code>
              </Step>
              <Step num="02" color="cyan">
                Bootstrap the Python environment. All dependencies are declared in <Code>openclaw/pyproject.toml</Code> — there is no <Code>requirements.txt</Code> or <Code>setup.py</Code>. From inside the <Code>openclaw/</Code> folder run:
                <div className="mt-2 font-mono text-xs bg-surface/20 border border-white/5 rounded-lg px-4 py-3 text-on-surface/70 space-y-1">
                  <p><span className="text-on-surface/30"># install runtime + dev deps into a local venv</span></p>
                  <p>uv sync --extra dev</p>
                  <p className="mt-2"><span className="text-on-surface/30"># verify — should print all available commands</span></p>
                  <p>uv run -m scripts.memcli --help</p>
                </div>
              </Step>
              <Step num="03" color="cyan">Restart OpenClaw. The skill loads automatically from the skills directory.</Step>
              <Step num="04" color="cyan">Start a conversation and say "set up my second brain". The setup protocol runs once and walks you through vault path, check-in time, and sync schedule.</Step>
            </div>

            <Note>
              <strong className="text-on-surface/80">Single source of truth for deps:</strong> <Code>pyproject.toml</Code> at the <Code>openclaw/</Code> root defines everything — runtime deps, dev deps, entry points, and test config. You never need <Code>pip install</Code> directly. <Code>uv sync</Code> handles the venv; <Code>uv run</Code> activates it automatically for every pipeline step.
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
              All tests create throwaway vaults under <Code>/tmp</Code> — nothing touches your real vault.
            </p>

            <SubHeading>What setup creates</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-4">
              The setup command scaffolds your vault idempotently — safe to re-run, never overwrites existing content:
            </p>
            <div className="glass-card rounded-2xl p-6 font-mono text-xs text-on-surface/60 leading-relaxed">
              <p className="text-primary/70 mb-1">vault/</p>
              <p className="ml-4">Work/Projects/    <span className="text-on-surface/30">← deadline-driven work</span></p>
              <p className="ml-4">Work/Ideas/       <span className="text-on-surface/30">← lightweight captures</span></p>
              <p className="ml-4">Work/KT/          <span className="text-on-surface/30">← knowledge transfers</span></p>
              <p className="ml-4">People/           <span className="text-on-surface/30">← everyone you interact with</span></p>
              <p className="ml-4">Log/Daily/        <span className="text-on-surface/30">← daily notes</span></p>
              <p className="ml-4">Log/Weekly/       <span className="text-on-surface/30">← weekly reviews</span></p>
              <p className="ml-4">Notes/Learnings/  <span className="text-on-surface/30">← resources, reference</span></p>
              <p className="ml-4">Notes/Patterns/   <span className="text-on-surface/30">← recurring observations</span></p>
              <p className="ml-4">Vision/           <span className="text-on-surface/30">← values, long-term vision</span></p>
              <p className="ml-4">Strategy/         <span className="text-on-surface/30">← quarterly goals</span></p>
              <p className="ml-4">Tasks/            <span className="text-on-surface/30">← unified task inbox</span></p>
              <p className="ml-4">Inbox/            <span className="text-on-surface/30">← unsorted captures</span></p>
              <p className="ml-4">Archive/          <span className="text-on-surface/30">← nothing ever deleted</span></p>
              <p className="ml-4">.second-brain/    <span className="text-on-surface/30">← memory, buffers, config</span></p>
            </div>
          </DocSection>

          {/* ── CREATE AN AGENT ───────────────────────────── */}
          <DocSection id="create-agent" title="Create an Agent">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              The sync pipeline routes LLM work to two named agents. You need to create these in OpenClaw before running your first sync.
            </p>

            <SubHeading>The two pipeline agents</SubHeading>
            <div className="space-y-4 mb-8">
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 shrink-0 mt-0.5">
                    <span className="material-symbols-outlined text-primary text-base">model_training</span>
                  </div>
                  <div>
                    <p className="font-label font-bold text-sm text-primary mb-1">memspren-heavy</p>
                    <p className="text-on-surface/60 text-sm leading-relaxed">Handles extraction, insight refinement, and entity planning. Use Sonnet or Opus — this agent reads raw brain dumps and makes structural decisions about your vault.</p>
                  </div>
                </div>
              </div>
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 shrink-0 mt-0.5">
                    <span className="material-symbols-outlined text-primary text-base">electric_bolt</span>
                  </div>
                  <div>
                    <p className="font-label font-bold text-sm text-primary mb-1">memspren-light</p>
                    <p className="text-on-surface/60 text-sm leading-relaxed">Handles goal tracking, task updates, hot-memory, entity content writing, and linking. Use Haiku or Sonnet — high volume, lower complexity.</p>
                  </div>
                </div>
              </div>
            </div>

            <SubHeading>Create the agents in OpenClaw</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01" color="cyan">Open OpenClaw and go to the Agents panel.</Step>
              <Step num="02" color="cyan">Create a new agent named exactly <Code>memspren-heavy</Code>. Set the model to Sonnet or Opus and enable the <Code>lobster</Code> and <Code>llm-task</Code> tools.</Step>
              <Step num="03" color="cyan">Create a second agent named <Code>memspren-light</Code>. Set the model to Haiku or Sonnet with the same tools enabled.</Step>
              <Step num="04" color="cyan">Verify with: <Code>openclaw agents list</Code> — both should appear with status <Code>ready</Code>.</Step>
            </div>

            <Note>
              If neither agent exists when sync runs, all pipeline directives fall back to your default OpenClaw agent. The sync will still work — it'll just be slower and less cost-efficient.
            </Note>
          </DocSection>

          {/* ── TELEGRAM ──────────────────────────────────── */}
          <DocSection id="telegram" title="Telegram with Claude">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              Claude Code can receive Telegram messages directly, which means you can send brain dumps from your phone without opening a laptop. The setup uses a Telegram bot and Claude's MCP Telegram plugin.
            </p>

            <Note>
              This works with the Claude Skill path only. You need an active Claude Code session running — the Telegram bot routes messages into it.
            </Note>

            <SubHeading>Create a Telegram bot</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01">Open Telegram and start a conversation with <strong className="text-on-surface/80">@BotFather</strong>.</Step>
              <Step num="02">Send <Code>/newbot</Code> and follow the prompts — give it a name and username.</Step>
              <Step num="03">BotFather returns a bot token. Copy it — you'll need it in the next step.</Step>
            </div>

            <SubHeading>Configure the Claude Code Telegram channel</SubHeading>
            <div className="space-y-4 mb-8">
              <Step num="01">In a Claude Code session, run the <Code>/telegram:configure</Code> skill. Paste in your bot token when prompted.</Step>
              <Step num="02">Open Telegram and send a message to your new bot. Claude Code will receive an incoming pairing request.</Step>
              <Step num="03">Run <Code>/telegram:access</Code> in Claude Code to approve your Telegram user ID.</Step>
              <Step num="04">Send a test message. Claude should respond directly in Telegram.</Step>
            </div>

            <Note>
              The Telegram channel runs through Claude Code's MCP server. Messages from approved users arrive as context in Claude's conversation — it can read, respond, and write files all from a single Telegram message.
            </Note>

            <SubHeading>Sending brain dumps from Telegram</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed">
              Once configured, just message your bot with any brain dump — a meeting note, a stray thought, a to-do, or a longer reflection. Claude processes it with the MemSpren skill loaded and writes the linked notes into your vault automatically. You don't need to be at your computer.
            </p>
          </DocSection>

          {/* ── ARCHITECTURE ──────────────────────────────── */}
          <DocSection id="architecture" title="Architecture">
            <p className="text-on-surface/60 text-base leading-relaxed mb-8">
              MemSpren is not an app — it's a set of protocols that run inside an AI agent. Understanding the layers helps you know what's happening when you send a brain dump.
            </p>

            <SubHeading>The three layers</SubHeading>
            <div className="space-y-6 mb-10">
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-base">psychology</span>
                  </span>
                  <h4 className="font-headline italic text-primary text-lg">1. memory Layer</h4>
                </div>
                <p className="text-on-surface/60 text-sm leading-relaxed">
                  The skill's persistent context: your personal profile, entity extraction rules, relationship types, and the running knowledge graph in Obsidian. This is what makes every session aware of prior context — Claude isn't starting from scratch each time.
                </p>
              </div>

              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-base">swap_horiz</span>
                  </span>
                  <h4 className="font-headline italic text-primary text-lg">2. Buffer Layer</h4>
                </div>
                <p className="text-on-surface/60 text-sm leading-relaxed">
                  A rotating in-session buffer that accumulates brain dumps before syncing. Batching inputs reduces vault write frequency and lets the extraction pass see multiple related inputs at once, improving link quality.
                </p>
              </div>

              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-base">sync</span>
                  </span>
                  <h4 className="font-headline italic text-primary text-lg">3. Sync Layer</h4>
                </div>
                <p className="text-on-surface/60 text-sm leading-relaxed">
                  Manages writing extracted entities and relationships into Obsidian markdown files. Handles merge conflicts when both the vault and the buffer have updated the same note, using field-level merging rather than last-write-wins.
                </p>
              </div>
            </div>

            <SubHeading>What happens on a brain dump</SubHeading>
            <div className="space-y-3 mb-8">
              <div className="flex items-start gap-3">
                <span className="entity-arrow mt-1 text-sm">→</span>
                <p className="text-on-surface/60 text-sm leading-relaxed">Input lands in the buffer (Telegram message, conversation, or direct text)</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="entity-arrow mt-1 text-sm">→</span>
                <p className="text-on-surface/60 text-sm leading-relaxed">Extraction pass: people, concepts, projects, and events are identified and typed</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="entity-arrow mt-1 text-sm">→</span>
                <p className="text-on-surface/60 text-sm leading-relaxed">Relationship pass: links between extracted entities are built and typed (e.g. <em>person ↔ project</em>, <em>concept ↔ concept</em>)</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="entity-arrow mt-1 text-sm">→</span>
                <p className="text-on-surface/60 text-sm leading-relaxed">Sync writes entity notes and updates the daily log in the vault, preserving prior content</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="entity-arrow mt-1 text-sm">→</span>
                <p className="text-on-surface/60 text-sm leading-relaxed">Obsidian graph view reflects the new connections immediately</p>
              </div>
            </div>

            <SubHeading>Vault structure</SubHeading>
            <p className="text-on-surface/60 text-sm leading-relaxed mb-4">
              MemSpren writes to a predictable folder hierarchy inside your Obsidian vault:
            </p>
            <div className="glass-card rounded-2xl p-6 font-mono text-xs text-on-surface/60 leading-relaxed">
              <p className="text-primary/70 mb-1">vault/</p>
              <p className="ml-4">Work/Projects/   <span className="text-on-surface/30">← deadline-driven work</span></p>
              <p className="ml-4">Work/Ideas/      <span className="text-on-surface/30">← lightweight captures</span></p>
              <p className="ml-4">People/          <span className="text-on-surface/30">← everyone you interact with</span></p>
              <p className="ml-4">Log/Daily/       <span className="text-on-surface/30">← daily notes, created during sync</span></p>
              <p className="ml-4">Notes/Learnings/ <span className="text-on-surface/30">← resources, reference material</span></p>
              <p className="ml-4">Tasks/           <span className="text-on-surface/30">← unified task inbox</span></p>
              <p className="ml-4">Archive/         <span className="text-on-surface/30">← nothing ever deleted</span></p>
              <p className="ml-4">.second-brain/   <span className="text-on-surface/30">← memory, buffers, config (hidden)</span></p>
            </div>
          </DocSection>

        </main>
      </div>
    </div>
  )
}
