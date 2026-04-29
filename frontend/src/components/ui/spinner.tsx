import { cn } from '@/lib/utils'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground/25 border-t-muted-foreground',
        className,
      )}
      aria-label="Loading"
      role="status"
    />
  )
}

