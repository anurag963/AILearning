import { env } from "@/lib/env";
import type { JiraIssue } from "@/lib/jira/types";

export class JiraNotFoundError extends Error {}
export class JiraAuthError extends Error {}

interface AdfNode {
  type: string;
  text?: string;
  content?: AdfNode[];
}

function adfToPlainText(node: AdfNode | null | undefined): string {
  if (!node) return "";

  const lines: string[] = [];

  function walk(n: AdfNode) {
    if (n.type === "text" && n.text) {
      lines.push(n.text);
    }
    if (n.content) {
      for (const child of n.content) {
        walk(child);
      }
    }
    if (n.type === "paragraph" || n.type === "heading" || n.type === "listItem") {
      lines.push("\n");
    }
  }

  walk(node);
  return lines.join("").replace(/\n{3,}/g, "\n\n").trim();
}

export async function getIssue(issueKey: string): Promise<JiraIssue> {
  const auth = Buffer.from(`${env.JIRA_EMAIL}:${env.JIRA_API_TOKEN}`).toString("base64");

  const response = await fetch(
    `${env.JIRA_BASE_URL}/rest/api/3/issue/${issueKey}`,
    {
      headers: {
        Authorization: `Basic ${auth}`,
        Accept: "application/json",
      },
      cache: "no-store",
    }
  );

  if (response.status === 404) {
    throw new JiraNotFoundError(`Issue ${issueKey} not found`);
  }
  if (response.status === 401 || response.status === 403) {
    throw new JiraAuthError("Jira authentication failed");
  }
  if (!response.ok) {
    throw new Error(`Jira API error: ${response.status}`);
  }

  const data = await response.json();

  return {
    key: data.key,
    summary: data.fields.summary,
    description: adfToPlainText(data.fields.description) || null,
    issueType: data.fields.issuetype?.name ?? "Unknown",
    priority: data.fields.priority?.name ?? "Unset",
    status: data.fields.status?.name ?? "Unknown",
    labels: data.fields.labels ?? [],
    components: (data.fields.components ?? []).map((c: { name: string }) => c.name),
  };
}
