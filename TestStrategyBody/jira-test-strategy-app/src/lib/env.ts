import { z } from "zod";

const envSchema = z.object({
  JIRA_BASE_URL: z.string().url(),
  JIRA_EMAIL: z.string().email(),
  JIRA_API_TOKEN: z.string().min(1),
  GROQ_API_KEY: z.string().min(1),
  GROQ_MODEL: z.string().default("llama-3.3-70b-versatile"),
});

// Skip validation during `next build` — env vars are only available at runtime.
// Set them in your deployment platform (e.g. Vercel environment variables).
const isBuildPhase = process.env.NEXT_PHASE === "phase-production-build";

export const env = isBuildPhase
  ? ({} as z.infer<typeof envSchema>)
  : envSchema.parse({
      JIRA_BASE_URL: process.env.JIRA_BASE_URL,
      JIRA_EMAIL: process.env.JIRA_EMAIL,
      JIRA_API_TOKEN: process.env.JIRA_API_TOKEN,
      GROQ_API_KEY: process.env.GROQ_API_KEY,
      GROQ_MODEL: process.env.GROQ_MODEL,
    });
