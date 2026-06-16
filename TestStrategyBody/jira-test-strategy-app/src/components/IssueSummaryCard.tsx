import { Card, CardTitle } from "@/components/ui/card";
import type { JiraIssue } from "@/lib/jira/types";

export function IssueSummaryCard({ issue }: { issue: JiraIssue }) {
  return (
    <Card>
      <CardTitle>
        {issue.key} — {issue.summary}
      </CardTitle>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm text-gray-600 sm:grid-cols-4">
        <div>
          <dt className="font-medium text-gray-500">Type</dt>
          <dd>{issue.issueType}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">Priority</dt>
          <dd>{issue.priority}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">Status</dt>
          <dd>{issue.status}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">Components</dt>
          <dd>{issue.components.join(", ") || "—"}</dd>
        </div>
      </dl>
      {issue.description && (
        <p className="mt-3 whitespace-pre-wrap text-sm text-gray-700">{issue.description}</p>
      )}
      {issue.labels.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {issue.labels.map((label) => (
            <span
              key={label}
              className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
            >
              {label}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}
