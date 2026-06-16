import type { JiraIssue } from "@/lib/jira/types";

export function buildTestStrategyPrompt(issue: JiraIssue): string {
  return `Generate a QA test strategy for the following Jira issue.

Issue Key: ${issue.key}
Summary: ${issue.summary}
Type: ${issue.issueType}
Priority: ${issue.priority}
Status: ${issue.status}
Labels: ${issue.labels.join(", ") || "none"}
Components: ${issue.components.join(", ") || "none"}

Description:
${issue.description ?? "No description provided."}

Produce a Markdown test strategy with exactly these sections, in this order:
1. Scope
2. Test Approach
3. Test Scenarios
4. Risk Areas
5. Automation Candidates
6. Test Data Needs

Base every section strictly on the information above. If information needed for a section is
missing from the issue, state that explicitly rather than inventing details.`;
}
