/**
 * Typed API client for the ASAHIO backend.
 * All endpoints return typed responses â€” no `any`.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface OverviewResponse {
  period: string;
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_without_asahi: number;
  total_cost_with_asahi: number;
  total_savings_usd: number;
  average_savings_pct: number;
  cache_hit_rate: number;
  cache_hits: { tier1: number; tier2: number; tier3: number };
  avg_latency_ms: number;
  p99_latency_ms: number | null;
  savings_delta_pct: number;
  requests_delta_pct: number;
}

export interface SavingsDataPoint {
  timestamp: string;
  cost_without_asahi: number;
  cost_with_asahi: number;
  savings_usd: number;
  requests: number;
}

export interface ModelBreakdown {
  model: string;
  requests: number;
  total_cost: number;
  total_savings: number;
}

export interface RequestLogEntry {
  id: string;
  model_requested: string | null;
  model_used: string;
  request_id?: string | null;
  provider: string | null;
  routing_mode: string | null;
  input_tokens: number;
  output_tokens: number;
  cost_without_asahi: number;
  cost_with_asahi: number;
  savings_usd: number;
  savings_pct: number | null;
  cache_hit: boolean;
  cache_tier: string | null;
  latency_ms: number | null;
  status_code: number;
  created_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface ApiKeyItem {
  id: string;
  name: string;
  environment: string;
  prefix: string;
  last_four: string;
  scopes: string[];
  allowed_models: string[] | null;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiKeyCreateResponse {
  id: string;
  name: string;
  raw_key: string;
  prefix: string;
  last_four: string;
  environment: string;
  scopes: string[];
  created_at: string;
}

export interface OrgResponse {
  id: string;
  name: string;
  slug: string;
  plan: string;
  monthly_request_limit: number;
  monthly_token_limit: number;
  created_at: string;
}

export interface MemberResponse {
  user_id: string;
  email: string;
  name: string | null;
  role: string;
  joined_at: string;
}

export interface UsageResponse {
  period_start: string;
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  monthly_request_limit: number;
  monthly_token_limit: number;
  requests_pct: number;
  tokens_pct: number;
}

export interface CachePerformance {
  total_requests: number;
  cache_hit_rate: number;
  tiers: {
    exact: { hits: number; rate: number };
    semantic: { hits: number; rate: number };
    intermediate: { hits: number; rate: number };
  };
}

export interface LatencyPercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  avg: number;
}

export interface ForecastResponse {
  forecast_days: number;
  projected_cost_usd: number;
  projected_savings_usd: number;
  projected_requests: number;
  daily_avg_cost: number;
  daily_avg_savings: number;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  ip_address: string | null;
}

export interface CompletionMetadata {
  cache_hit: boolean;
  cache_tier: string | null;
  model_requested: string | null;
  model_used: string;
  request_id?: string | null;
  provider?: string | null;
  routing_mode?: string | null;
  intervention_mode?: string | null;
  agent_id?: string | null;
  agent_session_id?: string | null;
  session_id?: string | null;
  model_endpoint_id?: string | null;
  cost_without_asahio: number;
  cost_with_asahio: number;
  cost_without_asahi: number;
  cost_with_asahi: number;
  savings_usd: number;
  savings_pct: number;
  routing_reason: string;
  routing_factors?: Record<string, unknown>;
  routing_confidence?: number | null;
  policy_action?: string | null;
  policy_reason?: string | null;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  model: string;
  choices: Array<{
    index: number;
    message: { role: string; content: string };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  asahio: CompletionMetadata;
  asahi?: CompletionMetadata;
}

export interface BillingPlan {
  id: string;
  name: string;
  monthly_request_limit: number;
  monthly_token_limit: number;
  monthly_budget_usd: number | null;
  price_monthly_usd: number | null;
  features: string[];
}

export interface BillingSubscription {
  plan: string;
  plan_name: string;
  status: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  stripe_price_id: string | null;
  billing_email: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  monthly_request_limit: number;
  monthly_token_limit: number;
  monthly_budget_usd: number | null;
  price_monthly_usd: number | null;
  features: string[];
  meter_name: string;
  stripe_enabled: boolean;
}

export interface BillingUsage {
  month: string;
  requests_used: number;
  tokens_used: number;
  spend_usd: number;
  request_limit: number;
  token_limit: number;
  request_usage_pct: number;
  token_usage_pct: number;
}

export interface InvoiceItem {
  id: string;
  amount_paid: number;
  amount_due: number;
  currency: string;
  status: string;
  hosted_invoice_url: string | null;
  created_at: string;
}

export interface AgentItem {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  routing_mode: string;
  intervention_mode: string;
  model_endpoint_id: string | null;
  is_active: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at?: string | null;
}

export interface ModelEndpointItem {
  id: string;
  name: string;
  endpoint_type: string;
  provider: string;
  model_id: string;
  endpoint_url: string | null;
  secret_reference: string | null;
  default_headers: Record<string, string>;
  capability_flags: Record<string, unknown>;
  fallback_model_id: string | null;
  health_status: string;
  last_health_error: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface RoutingDecisionItem {
  id: string;
  agent_id: string | null;
  call_trace_id: string | null;
  routing_mode: string | null;
  intervention_mode: string | null;
  selected_model: string | null;
  selected_provider: string | null;
  confidence: number | null;
  decision_summary: string | null;
  factors: Record<string, unknown>;
  created_at: string;
}
// â”€â”€ Token Getter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

let _getToken: (() => Promise<string | null>) | null = null;

export function setTokenGetter(fn: () => Promise<string | null>) {
  _getToken = fn;
}

// â”€â”€ API Client â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export type ApiOptions = {
  token?: string;
  orgSlug?: string;
};

async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
    ...extraHeaders,
  };

  const authToken = token ?? (await _getToken?.()) ?? undefined;
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers, credentials: "omit" });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    const isNetwork = msg.includes("fetch") || msg.includes("Failed to fetch") || msg.includes("Load failed");
    const hint = isNetwork
      ? `Cannot reach ${API_BASE}. Open ${API_BASE}/health in a new tab â€” if that works, add this siteâ€™s origin (see address bar) to CORS_ORIGINS on the backend.`
      : msg;
    throw new Error(hint);
  }

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API Error ${response.status}: ${body || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

function orgHeaders(orgSlug?: string): Record<string, string> | undefined {
  return orgSlug ? { "X-Org-Slug": orgSlug } : undefined;
}

// â”€â”€ Auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function signup(data: {
  email: string;
  name?: string;
  clerk_user_id?: string;
  org_name?: string;
}) {
  return fetchApi<{ user_id: string; email: string; org_id: string; org_slug: string }>(
    "/auth/signup",
    { method: "POST", body: JSON.stringify(data) }
  );
}

export async function login(data: { clerk_user_id: string }) {
  return fetchApi<{
    user_id: string;
    email: string;
    name: string | null;
    organisations: Array<{
      org_id: string;
      org_slug: string;
      org_name: string;
      role: string;
      plan: string;
    }>;
  }>("/auth/login", { method: "POST", body: JSON.stringify(data) });
}

// â”€â”€ Organisations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function getOrg(slug: string, token?: string) {
  return fetchApi<OrgResponse>(`/orgs/${slug}`, {}, token);
}

export async function getOrgMembers(slug: string, token?: string) {
  return fetchApi<MemberResponse[]>(`/orgs/${slug}/members`, {}, token);
}

export async function getOrgUsage(slug: string, token?: string) {
  return fetchApi<UsageResponse>(`/orgs/${slug}/usage`, {}, token);
}

// â”€â”€ API Keys â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function listKeys(token?: string, orgSlug?: string) {
  return fetchApi<ApiKeyItem[]>("/keys", {}, token, orgHeaders(orgSlug));
}

export async function createKey(
  data: { name: string; environment?: string; scopes?: string[] },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<ApiKeyCreateResponse>(
    "/keys",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function revokeKey(keyId: string, token?: string, orgSlug?: string) {
  return fetchApi<void>(
    `/keys/${keyId}`,
    { method: "DELETE" },
    token,
    orgHeaders(orgSlug)
  );
}

export async function rotateKey(keyId: string, token?: string, orgSlug?: string) {
  return fetchApi<ApiKeyCreateResponse>(
    `/keys/${keyId}/rotate`,
    { method: "POST" },
    token,
    orgHeaders(orgSlug)
  );
}

// â”€â”€ Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function getAnalyticsOverview(
  period: string = "30d",
  token?: string,
  orgSlug?: string
) {
  return fetchApi<OverviewResponse>(
    `/analytics/overview?period=${period}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getSavingsTimeSeries(
  period: string = "30d",
  granularity: string = "day",
  token?: string,
  orgSlug?: string
) {
  return fetchApi<{ data: SavingsDataPoint[] }>(
    `/analytics/savings?period=${period}&granularity=${granularity}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getModelBreakdown(
  period: string = "30d",
  token?: string,
  orgSlug?: string
) {
  return fetchApi<{ data: ModelBreakdown[] }>(
    `/analytics/models?period=${period}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getCachePerformance(
  period: string = "30d",
  token?: string,
  orgSlug?: string
) {
  return fetchApi<CachePerformance>(
    `/analytics/cache?period=${period}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getLatencyPercentiles(
  period: string = "30d",
  token?: string,
  orgSlug?: string
) {
  return fetchApi<LatencyPercentiles>(
    `/analytics/latency?period=${period}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getRequestLogs(
  params: {
    page?: number;
    limit?: number;
    model?: string;
    cache_hit?: boolean;
  } = {},
  token?: string,
  orgSlug?: string
) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.model) searchParams.set("model", params.model);
  if (params.cache_hit !== undefined)
    searchParams.set("cache_hit", String(params.cache_hit));
  return fetchApi<PaginatedResponse<RequestLogEntry>>(
    `/analytics/requests?${searchParams}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export async function getForecast(days: number = 30, token?: string, orgSlug?: string) {
  return fetchApi<ForecastResponse>(
    `/analytics/forecast?days=${days}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

export interface Recommendation {
  type: string;
  title: string;
  description: string;
  impact: string;
}

export async function getRecommendations(token?: string, orgSlug?: string) {
  return fetchApi<{ recommendations: Recommendation[] }>(
    "/analytics/recommendations",
    {},
    token,
    orgHeaders(orgSlug)
  );
}

// â”€â”€ Audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function getAuditLog(
  params: { page?: number; limit?: number } = {},
  token?: string,
  orgSlug?: string
) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.limit) searchParams.set("limit", String(params.limit));
  return fetchApi<PaginatedResponse<AuditLogEntry>>(
    `/governance/audit?${searchParams}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}

// â”€â”€ Gateway â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function getCompletionMetadata(response: ChatCompletionResponse) {
  return response.asahio ?? response.asahi!;
}

export async function chatCompletions(
  data: {
    model?: string;
    messages: Array<{ role: string; content: string }>;
    routing_mode?: string;
    intervention_mode?: string;
    quality_preference?: string;
    latency_preference?: string;
    agent_id?: string;
    session_id?: string;
    model_endpoint_id?: string;
  },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<ChatCompletionResponse>(
    "/v1/chat/completions",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function getBillingPlans(token?: string, orgSlug?: string) {
  return fetchApi<BillingPlan[]>("/billing/plans", {}, token, orgHeaders(orgSlug));
}

export async function getBillingSubscription(token?: string, orgSlug?: string) {
  return fetchApi<BillingSubscription>("/billing/subscription", {}, token, orgHeaders(orgSlug));
}

export async function getBillingUsage(token?: string, orgSlug?: string) {
  return fetchApi<BillingUsage>("/billing/usage", {}, token, orgHeaders(orgSlug));
}

export async function getBillingInvoices(token?: string, orgSlug?: string) {
  return fetchApi<{ data: InvoiceItem[] }>("/billing/invoices", {}, token, orgHeaders(orgSlug));
}

export async function createBillingCheckout(
  data: { plan: string; success_url: string; cancel_url: string },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<{ checkout_url: string; mode: string }>(
    "/billing/checkout",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function createBillingPortal(
  data: { return_url: string },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<{ portal_url: string; mode: string }>(
    "/billing/portal",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function listAgents(token?: string, orgSlug?: string) {
  return fetchApi<{ data: AgentItem[] }>("/agents", {}, token, orgHeaders(orgSlug));
}

export async function createAgent(
  data: {
    name: string;
    slug?: string;
    description?: string;
    routing_mode?: string;
    intervention_mode?: string;
    model_endpoint_id?: string | null;
    metadata?: Record<string, unknown>;
  },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<AgentItem>(
    "/agents",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function listModelEndpoints(token?: string, orgSlug?: string) {
  return fetchApi<{ data: ModelEndpointItem[] }>("/models", {}, token, orgHeaders(orgSlug));
}

export async function registerModelEndpoint(
  data: {
    name: string;
    endpoint_type?: string;
    provider?: string;
    model_id: string;
    endpoint_url?: string;
    secret_reference?: string;
    default_headers?: Record<string, string>;
    capability_flags?: Record<string, unknown>;
    fallback_model_id?: string;
    validate_health?: boolean;
  },
  token?: string,
  orgSlug?: string
) {
  return fetchApi<{ id: string; health_status: string }>(
    "/models/register",
    { method: "POST", body: JSON.stringify(data) },
    token,
    orgHeaders(orgSlug)
  );
}

export async function getRoutingDecisions(
  params: { agent_id?: string; limit?: number } = {},
  token?: string,
  orgSlug?: string
) {
  const searchParams = new URLSearchParams();
  if (params.agent_id) searchParams.set("agent_id", params.agent_id);
  if (params.limit) searchParams.set("limit", String(params.limit));
  return fetchApi<{ data: RoutingDecisionItem[] }>(
    `/routing/decisions?${searchParams}`,
    {},
    token,
    orgHeaders(orgSlug)
  );
}



