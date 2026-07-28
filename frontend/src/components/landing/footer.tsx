import { Logo } from "@/components/logo";

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-4 lg:px-8">
        <div className="lg:col-span-2">
          <Logo />
          <p className="mt-4 max-w-sm text-sm text-muted-foreground">
            Your personal AI financial workspace. Built for calm, thoughtful decisions with your money —
            in your language, at your pace.
          </p>
        </div>
        {[
          { title: "Product", items: ["Workspace", "AI Team", "Knowledge Hub", "Insights"] },
          { title: "Company", items: ["About", "Privacy", "Security", "Contact"] },
        ].map((col) => (
          <div key={col.title}>
            <p className="text-sm font-semibold text-foreground">{col.title}</p>
            <ul className="mt-4 space-y-2">
              {col.items.map((i) => (
                <li key={i}>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    {i}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-start justify-between gap-2 px-4 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:px-6 lg:px-8">
          <p>© 2026 FinSarthi. Educational information — not financial advice.</p>
          <p>Made with care in India 🇮🇳</p>
        </div>
      </div>
    </footer>
  );
}
