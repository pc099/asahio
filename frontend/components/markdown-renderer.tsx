"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { cn } from "@/lib/utils";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="absolute right-2 top-2 rounded p-1.5 hover:bg-muted transition-colors"
      aria-label="Copy code"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-emerald-400" />
      ) : (
        <Copy className="h-3.5 w-3.5 text-muted-foreground" />
      )}
    </button>
  );
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn("prose prose-sm max-w-none dark:prose-invert", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Headings
          h1: ({ node, ...props }) => (
            <h1 className="text-3xl font-bold tracking-tight text-foreground mt-8 mb-4" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-2xl font-bold text-foreground mt-6 mb-3 border-b border-border pb-2" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-semibold text-foreground mt-5 mb-2" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-lg font-medium text-foreground mt-4 mb-2" {...props} />
          ),
          // Paragraphs and text
          p: ({ node, ...props }) => (
            <p className="text-sm text-muted-foreground leading-relaxed my-3" {...props} />
          ),
          // Lists
          ul: ({ node, ...props }) => (
            <ul className="my-3 ml-6 list-disc text-sm text-muted-foreground space-y-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="my-3 ml-6 list-decimal text-sm text-muted-foreground space-y-1" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-muted-foreground" {...props} />
          ),
          // Code blocks and inline code
          code: ({ node, inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || "");
            const codeContent = String(children).replace(/\n$/, "");

            if (!inline && match) {
              return (
                <div className="relative my-4 rounded-lg border border-border bg-muted/30 overflow-hidden">
                  <div className="flex items-center justify-between border-b border-border bg-muted/50 px-4 py-2">
                    <span className="text-xs font-medium text-muted-foreground">{match[1]}</span>
                    <CopyButton text={codeContent} />
                  </div>
                  <pre className="overflow-x-auto p-4">
                    <code className={cn("text-xs", className)} {...props}>
                      {children}
                    </code>
                  </pre>
                </div>
              );
            }

            if (!inline) {
              return (
                <div className="relative my-4 rounded-lg border border-border bg-muted/30 overflow-hidden">
                  <CopyButton text={codeContent} />
                  <pre className="overflow-x-auto p-4">
                    <code className="text-xs" {...props}>
                      {children}
                    </code>
                  </pre>
                </div>
              );
            }

            return (
              <code
                className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-foreground"
                {...props}
              >
                {children}
              </code>
            );
          },
          // Links
          a: ({ node, ...props }) => (
            <a
              className="text-asahio hover:text-asahio-dark underline underline-offset-2 transition-colors"
              target={props.href?.startsWith("http") ? "_blank" : undefined}
              rel={props.href?.startsWith("http") ? "noreferrer" : undefined}
              {...props}
            />
          ),
          // Tables
          table: ({ node, ...props }) => (
            <div className="my-4 overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="border-b border-border bg-muted/50" {...props} />
          ),
          tbody: ({ node, ...props }) => (
            <tbody className="divide-y divide-border" {...props} />
          ),
          tr: ({ node, ...props }) => <tr {...props} />,
          th: ({ node, ...props }) => (
            <th className="px-4 py-2 text-left font-medium text-foreground" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-4 py-2 text-muted-foreground" {...props} />
          ),
          // Blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="my-4 border-l-4 border-asahio bg-asahio/5 pl-4 py-3 italic text-muted-foreground"
              {...props}
            />
          ),
          // Horizontal rules
          hr: ({ node, ...props }) => <hr className="my-6 border-border" {...props} />,
          // Strong and em
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-foreground" {...props} />
          ),
          em: ({ node, ...props }) => <em className="italic" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
