import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getIssue, JiraNotFoundError, JiraAuthError } from "@/lib/jira/client";
import { generateTestStrategy } from "@/lib/groq/client";

const requestSchema = z.object({
  issueKey: z.string().regex(/^[A-Z][A-Z0-9]+-\d+$/, "Invalid Jira issue key format"),
});

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = requestSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid issue key" }, { status: 400 });
  }

  try {
    const issue = await getIssue(parsed.data.issueKey);
    const strategy = await generateTestStrategy(issue);
    return NextResponse.json({ issue, strategy });
  } catch (error) {
    if (error instanceof JiraNotFoundError) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
    if (error instanceof JiraAuthError) {
      return NextResponse.json({ error: error.message }, { status: 401 });
    }
    if (error instanceof Error && error.message.includes("429")) {
      return NextResponse.json(
        { error: "Groq rate limit reached. Please try again shortly." },
        { status: 429 }
      );
    }
    return NextResponse.json({ error: "Failed to generate test strategy" }, { status: 500 });
  }
}
