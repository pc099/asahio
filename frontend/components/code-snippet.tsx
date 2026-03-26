"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface CodeSnippetProps {
  code: string;
  language?: string;
  title?: string;
  className?: string;
}

export function CodeSnippet({ code, language = "bash", title, className }: CodeSnippetProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("rounded-lg border border-border bg-card overflow-hidden", className)}>
      <div className="flex items-center justify-between border-b border-border bg-muted/50 px-4 py-2">
        <span className="text-xs font-medium text-muted-foreground">
          {title || language}
        </span>
        <button
          onClick={handleCopy}
          className="rounded p-1 hover:bg-muted transition-colors"
          aria-label="Copy code"
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <Copy className="h-3.5 w-3.5 text-muted-foreground" />
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4">
        <code className="text-xs font-mono text-foreground">{code}</code>
      </pre>
    </div>
  );
}

interface InlineCodeProps {
  children: string;
  onClick?: () => void;
}

export function InlineCode({ children, onClick }: InlineCodeProps) {
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <code
      onClick={handleClick}
      className={cn(
        "inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-foreground cursor-pointer hover:bg-muted/70 transition-colors",
        copied && "text-emerald-500"
      )}
    >
      {children}
      {copied && <Check className="h-3 w-3" />}
    </code>
  );
}
