"use client";

import React from "react";
import { useParams, usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { ErrorBoundary } from "@/components/error-boundary";
import { CommandMenu } from "@/components/command-menu";
import { useKeyboardShortcuts } from "@/lib/hooks/use-keyboard-shortcuts";

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  useKeyboardShortcuts(orgSlug);

  React.useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <CommandMenu orgSlug={orgSlug} />
      <Sidebar
        orgSlug={orgSlug}
        currentPath={pathname}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader
          orgSlug={orgSlug}
          onMenuToggle={() => setSidebarOpen((open) => !open)}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
