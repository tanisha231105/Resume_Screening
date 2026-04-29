import { Link, Outlet, useLocation } from 'react-router-dom'
import { FileSearch, Sparkles } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export function AppShell() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div className="min-h-svh bg-gradient-to-b from-background to-muted/30">
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur">
        <div className="container flex h-14 items-center justify-between">
          <Link to="/" className="group flex items-center gap-2">
            <div className="grid h-9 w-9 place-items-center rounded-lg border bg-card shadow-sm transition-transform duration-200 group-hover:-translate-y-0.5">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-tight">
                ResumeIQ
              </div>
              <div className="text-xs text-muted-foreground">
                ATS Screener · Skill Gaps
              </div>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              to="/"
              className={cn(
                'text-sm text-muted-foreground transition-colors hover:text-foreground',
                isHome && 'text-foreground',
              )}
            >
              Analyze
            </Link>
            <Button asChild variant="outline" size="sm">
              <a
                href="https://github.com/"
                target="_blank"
                rel="noreferrer"
                className="gap-2"
              >
                <FileSearch className="h-4 w-4" />
                View code
              </a>
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-10">
        <Outlet />
      </main>
    </div>
  )
}

