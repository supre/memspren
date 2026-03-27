export default function Hero({ version }: { version: string }) {
  return (
    <header id="top" className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Full-bleed background image */}
      <div className="absolute inset-0 z-0">
        <img alt="MemSpren Spren" className="w-full h-full object-cover opacity-60" src="/memspren-spren.png" />
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-surface/40" />
      </div>

      <div className="relative z-10 max-w-3xl mx-auto px-8 text-center">
        {/* Brand mark */}
        <div className="hero-animate inline-block px-5 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-[0.6rem] font-label tracking-[0.4em] uppercase mb-10 backdrop-blur-md">
          Second Brain Framework · {version}
        </div>

        {/* Brand name */}
        <h1 className="hero-animate hero-animate-delay-1 text-6xl md:text-8xl font-headline italic leading-[0.95] text-primary mb-8 glow-text tracking-tight">
          MemSpren
        </h1>

        {/* Hook */}
        <p className="hero-animate hero-animate-delay-2 text-xl md:text-2xl text-on-surface/70 max-w-2xl mx-auto leading-relaxed font-light font-headline italic">
          You already have the thoughts.<br />
          You just can't see how they connect.
        </p>

        {/* CTAs */}
        <div className="hero-animate hero-animate-delay-3 flex flex-wrap justify-center gap-6 mt-16">
          <a href="#setup" className="bg-primary text-on-primary px-10 py-4 rounded-full font-bold uppercase tracking-widest text-xs flex items-center gap-3 hover:shadow-[0_0_30px_rgba(131,213,198,0.4)] transition-all no-underline">
            Get Started
            <span className="material-symbols-outlined text-lg">terminal</span>
          </a>
          <a href="#story" className="px-10 py-4 rounded-full border border-primary/20 text-primary font-bold uppercase tracking-widest text-xs hover:bg-primary/10 transition-colors backdrop-blur-sm no-underline">
            Read the Story
          </a>
        </div>

        {/* Scroll cue */}
        <div className="mt-12 scroll-cue">
          <span className="material-symbols-outlined text-primary/30 text-3xl">expand_more</span>
        </div>
      </div>
    </header>
  )
}
