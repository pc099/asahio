# P1 Items Progress Summary

**Date:** March 26, 2026
**Status:** 1 of 7 complete (14%)

---

## Overview

P1 items are required before first customer go-live. They provide production confidence, operator visibility, and advanced intervention controls.

**All P0 items complete:** ✅
**Now working on:** P1 tier (production readiness)

---

## ⏳ P1-1: Fleet Mode Overview Page - **PENDING**

**Priority:** High (operator visibility)

**Scope:**
- New page: `frontend/app/(dashboard)/[orgSlug]/fleet/page.tsx`
- Shows all agents grouped by intervention mode
- Donut chart showing mode distribution
- Intervention summary stats (total interventions, by type)
- Backend endpoint `GET /interventions/fleet-overview` already exists ✅

**Effort:** M (1-2 sessions)

**Implementation Plan:**
1. Create new fleet page route
2. Call `getFleetOverview()` API (backend already exists)
3. Display agents grouped by intervention mode
4. Add donut chart for mode distribution (recharts or similar)
5. Show intervention summary stats table
6. Add navigation link in sidebar

---

## ⏳ P1-2: Evidence Panel on Agent Detail - **PENDING**

**Priority:** High (operator decision-making)

**Scope:**
- Add "Evidence" tab to agent detail page
- Show mode eligibility data: baseline confidence, observation count, suggested next mode
- Display reasons for mode suggestion
- API `getModeEligibility()` already exists ✅

**Effort:** M (1-2 sessions)

**Location:** `frontend/app/(dashboard)/[orgSlug]/agents/[agentId]/page.tsx`

---

## ⏳ P1-3: Autonomous Authorization Flow - **PENDING**

**Priority:** High (safety control)

**Scope:**
- When mode eligibility suggests AUTONOMOUS and operator clicks "Upgrade"
- Show confirmation dialog with risk acknowledgment
- Call `transitionMode()` with `operator_authorized: true`
- Requires explicit operator approval for AUTONOMOUS mode

**Effort:** M (1-2 sessions)

**Depends On:** P1-2 (Evidence Panel)

---

## ⏳ P1-4: Per-Agent Intervention Thresholds - **PENDING**

**Priority:** Medium (customization)

**Scope:**
- **Backend:**
  - Add `intervention_thresholds` JSONB column to Agent model
  - Alembic migration required
  - Service: merge agent-specific thresholds over defaults
- **Frontend:**
  - Threshold editor on agent detail page
  - Allow customizing risk thresholds per agent

**Effort:** M (1-2 sessions)

**Phase:** 4B

---

## ⏳ P1-5: WebSocket/SSE Live Trace - **PENDING**

**Priority:** Medium (real-time visibility)

**Scope:**
- **Backend:** SSE endpoint `GET /traces/live?agent_id=...`
- **Frontend:** EventSource connection on traces page
- Auto-append new trace rows in real-time
- No page refresh needed

**Effort:** L (2-4 sessions)

**Phase:** 4E

---

## ⏳ P1-6: GET /aba/org/overview Endpoint - **PENDING**

**Priority:** Medium (ABA dashboard)

**Scope:**
- Aggregate endpoint returning:
  - Total agents under observation
  - Average baseline confidence
  - Total observations
  - Top anomalies
  - Hallucination rate distribution
- Single JSON response
- Used by ABA dashboard page

**Effort:** S (< 1 session)

**Phase:** 3E

---

## ✅ P1-7: Session Graph Explorer (Detail View) - **COMPLETE**

**File:** `frontend/app/(dashboard)/[orgSlug]/traces/page.tsx`

**Implementation:**
- Traces page has Sessions tab ✅
- Clicking a session opens side panel with dependency graph ✅
- Uses `SessionGraphPanel` component ✅
- Calls `getSessionGraph()` when session selected ✅

**Already in Production:** ✅

**Note:** Marked as DONE in NEXT_STEPS.md (line 49)

---

## Summary

| Item | Status | Effort | Phase |
|------|--------|--------|-------|
| P1-1: Fleet Mode Overview Page | ⏳ Pending | M | 4D |
| P1-2: Evidence Panel on Agent Detail | ⏳ Pending | M | 4D |
| P1-3: Autonomous Authorization Flow | ⏳ Pending | M | 4D |
| P1-4: Per-Agent Intervention Thresholds | ⏳ Pending | M | 4B |
| P1-5: WebSocket/SSE Live Trace | ⏳ Pending | L | 4E |
| P1-6: GET /aba/org/overview | ⏳ Pending | S | 3E |
| P1-7: Session Graph Explorer | ✅ Complete | M | 4E |

**Progress:** 14% complete (1 of 7)

---

## Next Actions

### Immediate (This Session)

1. **P1-1: Fleet Mode Overview Page** (1-2 sessions)
   - Create new route: `frontend/app/(dashboard)/[orgSlug]/fleet/page.tsx`
   - Verify `GET /interventions/fleet-overview` endpoint exists in backend
   - Build page with:
     - Agent list grouped by intervention mode
     - Donut chart for mode distribution
     - Intervention summary table
   - Add sidebar navigation link

2. **P1-2: Evidence Panel** (1-2 sessions)
   - Add "Evidence" tab to agent detail page
   - Call `getModeEligibility()` API
   - Display baseline confidence, observation count
   - Show suggested next mode with reasons

3. **P1-3: Authorization Flow** (1-2 sessions)
   - Add upgrade button on evidence panel
   - Build confirmation dialog
   - Wire up `transitionMode()` call

### Short-Term (Next 2-3 Sessions)

4. **P1-6: ABA Overview Endpoint** (< 1 session)
   - Backend: `GET /aba/org/overview`
   - Aggregate org-level ABA stats
   - Return single JSON response

5. **P1-4: Agent Thresholds** (1-2 sessions)
   - Backend migration for `intervention_thresholds` column
   - Service layer merge logic
   - Frontend threshold editor

### Medium-Term (Next Week)

6. **P1-5: SSE Live Trace** (2-4 sessions)
   - Backend SSE endpoint
   - Frontend EventSource integration
   - Real-time trace updates

---

## Build Order (Recommended)

Week 1 (This Week):
- P1-1 (fleet overview)
- P1-2 (evidence panel)
- P1-3 (auth flow)
- P1-6 (ABA overview endpoint)

Week 2:
- P1-4 (agent thresholds)
- P1-5 (SSE live trace)

**After P1 Complete:** Move to P2 items (infrastructure hardening)

---

## Completion Target

**Target:** End of Week 2 (by April 5, 2026)
**Estimated Effort:** 6-10 sessions
**Blocking:** First customer go-live

---

*Created March 26, 2026 · P0 complete, moving to P1*
