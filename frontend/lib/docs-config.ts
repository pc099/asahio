export interface DocSection {
  id: string;
  title: string;
  description: string;
  category: "getting-started" | "api" | "sdk" | "guides" | "examples";
  file: string;
  icon?: string;
}

export const DOC_SECTIONS: DocSection[] = [
  {
    id: "quickstart",
    title: "Quickstart",
    description: "Get started with ASAHIO in 5 minutes",
    category: "getting-started",
    file: "guides/QUICKSTART.md",
  },
  {
    id: "api-reference",
    title: "API Reference",
    description: "Complete API documentation for all 90+ endpoints",
    category: "api",
    file: "api/API_REFERENCE.md",
  },
  {
    id: "sdk-guide",
    title: "SDK Guide",
    description: "Comprehensive Python SDK documentation",
    category: "sdk",
    file: "sdk/SDK_GUIDE.md",
  },
  {
    id: "code-examples",
    title: "Code Examples",
    description: "Runnable examples for common use cases",
    category: "examples",
    file: "examples/README.md",
  },
  {
    id: "example-basic",
    title: "Example: Basic Usage",
    description: "Simple chat completions and cost analysis",
    category: "examples",
    file: "examples/01_basic_usage.py",
  },
  {
    id: "example-agents",
    title: "Example: Agent Management",
    description: "Creating and tracking agents",
    category: "examples",
    file: "examples/02_agent_management.py",
  },
  {
    id: "example-tools",
    title: "Example: Tool Use",
    description: "Function calling and tool execution",
    category: "examples",
    file: "examples/03_tool_use.py",
  },
  {
    id: "example-sessions",
    title: "Example: Sessions & Traces",
    description: "Multi-turn conversations and observability",
    category: "examples",
    file: "examples/04_sessions_and_traces.py",
  },
  {
    id: "example-analytics",
    title: "Example: Analytics & Cost",
    description: "Cost monitoring and fleet analytics",
    category: "examples",
    file: "examples/05_analytics_and_cost.py",
  },
];

export const DOC_CATEGORIES = [
  { id: "getting-started", label: "Getting Started" },
  { id: "api", label: "API Reference" },
  { id: "sdk", label: "SDK" },
  { id: "examples", label: "Examples" },
] as const;

export function getDocsByCategory(category: string): DocSection[] {
  return DOC_SECTIONS.filter((doc) => doc.category === category);
}

export function getAllDocs(): DocSection[] {
  return DOC_SECTIONS;
}
