"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

export function useKeyboardShortcuts(orgSlug: string) {
  const router = useRouter();
  const pendingG = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.isContentEditable
      ) {
        return;
      }

      if (e.metaKey || e.ctrlKey || e.altKey) return;

      const key = e.key.toLowerCase();
      if (!pendingG.current) {
        if (key === "g") {
          pendingG.current = true;
          if (timer.current) clearTimeout(timer.current);
          timer.current = setTimeout(() => {
            pendingG.current = false;
          }, 1000);
        }
        return;
      }

      pendingG.current = false;
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }

      const routes: Record<string, string> = {
        d: `/${orgSlug}/dashboard`,
        g: `/${orgSlug}/gateway`,
        c: `/${orgSlug}/cache`,
        a: `/${orgSlug}/analytics`,
        b: `/${orgSlug}/billing`,
        k: `/${orgSlug}/keys`,
        s: `/${orgSlug}/settings`,
      };

      const route = routes[key];
      if (route) {
        e.preventDefault();
        router.push(route);
      }
    };

    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      if (timer.current) clearTimeout(timer.current);
    };
  }, [orgSlug, router]);
}
