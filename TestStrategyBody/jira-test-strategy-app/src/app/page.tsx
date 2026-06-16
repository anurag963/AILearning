"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { IssueSummaryCard } from "@/components/IssueSummaryCard";
import { TestStrategyOutput } from "@/components/TestStrategyOutput";
import type { JiraIssue } from "@/lib/jira/types";

type RequestState = "idle" | "loading" | "error" | "success";

export default function Home() {
  const [issueKey, setIssueKey] = useState("");
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [issue, setIssue] = useState<JiraIssue | null>(null);
  const [strategy, setStrategy] = useState<string | null>(null);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setError(null);
    setIssue(null);
    setStrategy(null);

    try {
      const response = await fetch("/api/strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issueKey: issueKey.trim().toUpperCase() }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error ?? "Something went wrong");
        setState("error");
        return;
      }

      setIssue(data.issue);
      setStrategy(data.strategy);
      setState("success");
    } catch {
      setError("Network error. Please try again.");
      setState("error");
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Jira Test Strategy Generator</h1>
        <p className="mt-1 text-sm text-gray-600">
          Enter a Jira issue key to fetch its details and generate an AI test strategy.
        </p>
      </div>

      <form onSubmit={handleGenerate} className="flex gap-2">
        <Input
          value={issueKey}
          onChange={(e) => setIssueKey(e.target.value)}
          placeholder="e.g. PROJ-123"
          required
        />
        <Button type="submit" disabled={state === "loading"}>
          {state === "loading" ? "Generating..." : "Generate Strategy"}
        </Button>
      </form>

      {state === "error" && error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {state === "loading" && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}

      {state === "success" && issue && strategy && (
        <div className="flex flex-col gap-4">
          <IssueSummaryCard issue={issue} />
          <TestStrategyOutput strategy={strategy} />
        </div>
      )}
    </main>
  );
}
