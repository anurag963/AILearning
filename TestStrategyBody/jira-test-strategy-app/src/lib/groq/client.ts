import Groq from "groq-sdk";
import { env } from "@/lib/env";
import type { JiraIssue } from "@/lib/jira/types";
import { buildTestStrategyPrompt } from "@/lib/groq/prompt";

const groq = new Groq({ apiKey: env.GROQ_API_KEY });

export async function generateTestStrategy(issue: JiraIssue): Promise<string> {
  const completion = await groq.chat.completions.create({
    model: env.GROQ_MODEL,
    messages: [
      { role: "system", content: "You are a senior QA test architect." },
      { role: "user", content: buildTestStrategyPrompt(issue) },
    ],
    temperature: 0.3,
  });

  const content = completion.choices[0]?.message?.content;
  if (!content) {
    throw new Error("Groq returned an empty response");
  }
  return content;
}
