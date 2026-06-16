import { NextResponse } from "next/server";
import { getIssue, JiraNotFoundError, JiraAuthError } from "@/lib/jira/client";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ issueKey: string }> }
) {
  const { issueKey } = await params;

  try {
    const issue = await getIssue(issueKey);
    return NextResponse.json({ issue });
  } catch (error) {
    if (error instanceof JiraNotFoundError) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
    if (error instanceof JiraAuthError) {
      return NextResponse.json({ error: error.message }, { status: 401 });
    }
    return NextResponse.json({ error: "Failed to fetch Jira issue" }, { status: 500 });
  }
}
