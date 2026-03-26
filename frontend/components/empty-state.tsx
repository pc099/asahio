import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary";
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  codeSnippet?: {
    language: string;
    code: string;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  codeSnippet,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-12 text-center", className)}>
      <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-asahio/10">
        <Icon className="h-8 w-8 text-asahio" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mb-6 max-w-md text-sm text-muted-foreground">{description}</p>

      {codeSnippet && (
        <div className="mb-6 w-full max-w-xl rounded-lg border border-border bg-card overflow-hidden">
          <div className="border-b border-border bg-muted/50 px-4 py-2 text-left">
            <span className="text-xs font-medium text-muted-foreground">{codeSnippet.language}</span>
          </div>
          <pre className="overflow-x-auto p-4 text-left">
            <code className="text-xs font-mono text-foreground">{codeSnippet.code}</code>
          </pre>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        {action && (
          <button
            onClick={action.onClick}
            className={cn(
              "rounded-lg px-6 py-2.5 text-sm font-medium transition-colors",
              action.variant === "secondary"
                ? "border border-border text-foreground hover:bg-muted"
                : "bg-asahio text-white hover:bg-asahio-dark"
            )}
          >
            {action.label}
          </button>
        )}
        {secondaryAction && (
          <button
            onClick={secondaryAction.onClick}
            className="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
          >
            {secondaryAction.label}
          </button>
        )}
      </div>
    </div>
  );
}
