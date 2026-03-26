"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  BookOpen,
  Rocket,
  Code2,
  Terminal,
  Search,
  FileText,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { DOC_SECTIONS, DOC_CATEGORIES, type DocSection } from "@/lib/docs-config";

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PublicDocsPage() {
  const [activeCategory, setActiveCategory] = useState<string>("getting-started");
  const [activeDoc, setActiveDoc] = useState<string | null>(null);
  const [docContent, setDocContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  // Load first doc in category when category changes
  useEffect(() => {
    const docsInCategory = DOC_SECTIONS.filter((d) => d.category === activeCategory);
    if (docsInCategory.length > 0) {
      setActiveDoc(docsInCategory[0].id);
    }
  }, [activeCategory]);

  // Load doc content when active doc changes
  useEffect(() => {
    if (!activeDoc) return;

    const loadContent = async () => {
      setLoading(true);
      try {
        const section = DOC_SECTIONS.find((s) => s.id === activeDoc);
        if (!section) return;

        const response = await fetch(`/content/docs/${section.file}`);
        if (!response.ok) {
          console.error("Failed to load doc:", response.statusText);
          setDocContent("# Error\n\nFailed to load documentation. Please try again later.");
          return;
        }

        const content = await response.text();

        // If it's a Python file, wrap it in a code block
        if (section.file.endsWith(".py")) {
          setDocContent("```python\n" + content + "\n```");
        } else {
          setDocContent(content);
        }
      } catch (error) {
        console.error("Error loading doc:", error);
        setDocContent("# Error\n\nFailed to load documentation. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    loadContent();
  }, [activeDoc]);

  const filteredDocs = search
    ? DOC_SECTIONS.filter(
        (doc) =>
          doc.title.toLowerCase().includes(search.toLowerCase()) ||
          doc.description.toLowerCase().includes(search.toLowerCase())
      )
    : DOC_SECTIONS.filter((doc) => doc.category === activeCategory);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={28} height={28} className="rounded-md" />
            <span className="text-xl font-bold tracking-tight text-asahio">ASAHIO</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/sign-in"
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/sign-up"
              className="rounded-lg bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio-dark transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 pt-28 pb-20">
        {/* Header */}
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-wide text-asahio">Documentation</p>
          <h1 className="mt-2 text-4xl font-bold">ASAHIO Platform Docs</h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            The control plane for production AI systems. Route, cache, observe, and intervene on every LLM call.
          </p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search documentation..."
              className="w-full rounded-lg border border-border bg-background pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-asahio focus:border-transparent"
            />
          </div>
        </div>

        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="hidden w-64 shrink-0 lg:block">
            <nav className="space-y-6">
              {DOC_CATEGORIES.map((category) => {
                const docsInCategory = DOC_SECTIONS.filter((d) => d.category === category.id);
                if (docsInCategory.length === 0) return null;

                return (
                  <div key={category.id}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {category.label}
                    </h3>
                    <div className="space-y-1">
                      {docsInCategory.map((doc) => (
                        <button
                          key={doc.id}
                          type="button"
                          onClick={() => {
                            setActiveCategory(doc.category);
                            setActiveDoc(doc.id);
                          }}
                          className={cn(
                            "flex w-full items-start gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors",
                            activeDoc === doc.id
                              ? "bg-asahio/10 text-asahio font-medium"
                              : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                          )}
                        >
                          <FileText className="mt-0.5 h-4 w-4 shrink-0" />
                          <div className="min-w-0">
                            <div className="truncate">{doc.title}</div>
                            <div className="text-xs text-muted-foreground truncate">{doc.description}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </nav>
          </aside>

          {/* Content */}
          <div className="min-w-0 flex-1">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-asahio border-t-transparent" />
              </div>
            ) : docContent ? (
              <div className="rounded-lg border border-border bg-card p-8">
                <MarkdownRenderer content={docContent} />
              </div>
            ) : (
              <div className="rounded-lg border border-border bg-card p-8 text-center">
                <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground">Select a document from the sidebar to get started</p>
              </div>
            )}
          </div>
        </div>

        {/* CTA */}
        <section className="mt-16 rounded-xl border border-asahio/30 bg-asahio/5 p-8 text-center">
          <h2 className="text-2xl font-bold mb-3">Ready to start?</h2>
          <p className="text-muted-foreground mb-6">
            Create a free account to get your API key and access the full dashboard.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/sign-up"
              className="rounded-lg bg-asahio px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-asahio-dark"
            >
              Create Account
            </Link>
            <Link
              href="/sign-in"
              className="rounded-lg border border-border px-6 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              Sign In
            </Link>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="border-t border-border bg-card px-6 py-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={18} height={18} className="rounded" />
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} ASAHIO. All rights reserved.
            </p>
          </div>
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Home
          </Link>
        </div>
      </footer>
    </div>
  );
}
