"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  BookOpen,
  FileText,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { DOC_SECTIONS, DOC_CATEGORIES, type DocSection } from "@/lib/docs-config";

export default function DocsPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

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
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="h-5 w-5 text-asahio" />
          <h1 className="text-2xl font-bold">Documentation</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Complete API reference, SDK guides, and code examples for the ASAHIO platform
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
        {/* Sidebar navigation */}
        <aside className="hidden w-64 shrink-0 lg:block">
          <nav className="space-y-6 sticky top-4">
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

        {/* Mobile category selector */}
        <div className="mb-4 flex gap-2 overflow-x-auto lg:hidden">
          {DOC_CATEGORIES.map((category) => {
            const docsInCategory = DOC_SECTIONS.filter((d) => d.category === category.id);
            if (docsInCategory.length === 0) return null;

            return (
              <button
                key={category.id}
                onClick={() => setActiveCategory(category.id)}
                className={cn(
                  "shrink-0 rounded-full px-4 py-1.5 text-xs font-medium transition-colors",
                  activeCategory === category.id
                    ? "bg-asahio text-white"
                    : "bg-muted text-muted-foreground hover:bg-muted/70"
                )}
              >
                {category.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-20 rounded-lg border border-border bg-card">
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

          {/* Mobile doc selector */}
          <div className="mt-4 lg:hidden">
            <select
              value={activeDoc || ""}
              onChange={(e) => {
                const doc = DOC_SECTIONS.find((d) => d.id === e.target.value);
                if (doc) {
                  setActiveCategory(doc.category);
                  setActiveDoc(doc.id);
                }
              }}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            >
              {filteredDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
