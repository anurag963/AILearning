# Jira Test Strategy Generator

Fetches Jira issue details by issue key and generates a QA test strategy using Groq AI.
Built with Next.js (App Router, TypeScript), Tailwind CSS, and deployable on Vercel.

## Stack

| Layer            | Technology                                |
|------------------|---------------------------------------------|
| Framework        | Next.js 16 (App Router, TypeScript)          |
| UI               | Tailwind CSS                                 |
| Jira Integration | Jira Cloud REST API v3 (`/rest/api/3/issue`)  |
| AI Provider      | Groq API (`groq-sdk`, `llama-3.3-70b-versatile`) |
| Validation       | Zod                                          |
| Markdown         | react-markdown                              |
| Hosting          | Vercel                                       |

## Project Structure

```
src/
├── app/
│   ├── page.tsx                 Form + results UI
│   └── api/
│       ├── jira/[issueKey]/route.ts   GET Jira issue details
│       └── strategy/route.ts          POST -> fetch issue + generate strategy
├── components/
│   ├── IssueSummaryCard.tsx
│   ├── TestStrategyOutput.tsx
│   └── ui/ (Button, Input, Card, Skeleton)
└── lib/
    ├── env.ts                  Zod-validated environment config
    ├── jira/ (client.ts, types.ts)
    └── groq/ (client.ts, prompt.ts)
```

## Setup

```bash
npm install

cp .env.example .env.local
# fill in JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, GROQ_API_KEY

npm run dev
```

Open [http://localhost:3000](http://localhost:3000), enter a Jira issue key (e.g. `PROJ-123`), and
click "Generate Strategy".

## Environment Variables

| Variable         | Description                                              |
|-------------------|-----------------------------------------------------------|
| `JIRA_BASE_URL`   | Your Jira Cloud site, e.g. `https://your-domain.atlassian.net` |
| `JIRA_EMAIL`      | Email associated with your Jira API token                |
| `JIRA_API_TOKEN`  | Jira API token ([create one](https://id.atlassian.com/manage-profile/security/api-tokens)) |
| `GROQ_API_KEY`    | Groq API key ([create one](https://console.groq.com/keys)) |
| `GROQ_MODEL`      | Optional, defaults to `llama-3.3-70b-versatile`           |

All credentials are read server-side only (`src/lib/env.ts`) and never sent to the browser.

## Deploy on Vercel

```bash
vercel
vercel env add JIRA_BASE_URL
vercel env add JIRA_EMAIL
vercel env add JIRA_API_TOKEN
vercel env add GROQ_API_KEY
vercel --prod
```

Or set the same variables in the Vercel dashboard under Project Settings -> Environment Variables.

## Top 5 Troubleshooting

1. **401/403 from Jira** - invalid email/API token, or the token's account lacks permission to view the issue.
2. **404 from Jira** - wrong issue key, wrong project, or the issue belongs to a different Jira site than `JIRA_BASE_URL`.
3. **Groq 429** - rate limit hit; the app surfaces a "try again shortly" message, retry after a short delay.
4. **Env validation errors at startup** - a required variable is missing from `.env.local` (local) or Project Settings (Vercel).
5. **Empty/malformed strategy output** - verify `GROQ_MODEL` is a valid Groq model name and `GROQ_API_KEY` is active.
