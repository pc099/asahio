"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Users } from "lucide-react";
import { getOrgMembers } from "@/lib/api";
import { cn } from "@/lib/utils";

const roleColors: Record<string, string> = {
  owner: "bg-asahio/20 text-asahio",
  admin: "bg-blue-500/20 text-blue-400",
  member: "bg-muted text-muted-foreground",
};

export default function TeamPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data: members, isLoading } = useQuery({
    queryKey: ["org-members", orgSlug],
    queryFn: () => getOrgMembers(orgSlug),
    enabled: Boolean(orgSlug),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Team</h1>
        <p className="text-sm text-muted-foreground">View team members in your organisation</p>
      </div>

      <div className="flex gap-4 border-b border-border">
        <Link
          href={`/${orgSlug}/settings`}
          className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          General
        </Link>
        <div className="border-b-2 border-asahio px-4 py-2 text-sm font-medium text-asahio">
          Team
        </div>
        <Link
          href={`/${orgSlug}/settings/security`}
          className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Security
        </Link>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        {isLoading ? (
          <div className="animate-pulse space-y-4 p-6">
            {[1, 2, 3].map((item) => (
              <div key={item} className="h-12 rounded bg-muted" />
            ))}
          </div>
        ) : !members || members.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-3">
            <Users className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No team members found.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="px-4 py-3">Member</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Joined</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr
                  key={member.user_id}
                  className="border-b border-border transition-colors last:border-0 hover:bg-muted/50"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-asahio/20 text-xs font-medium text-asahio">
                        {(member.name || member.email).charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-foreground">{member.name || "-"}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{member.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        roleColors[member.role] || roleColors.member
                      )}
                    >
                      {member.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(member.joined_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
