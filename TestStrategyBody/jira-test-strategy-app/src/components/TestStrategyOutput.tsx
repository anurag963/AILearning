"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function TestStrategyOutput({ strategy }: { strategy: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(strategy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <CardTitle>Test Strategy</CardTitle>
        <Button onClick={handleCopy} className="bg-gray-600 hover:bg-gray-700">
          {copied ? "Copied!" : "Copy"}
        </Button>
      </div>
      <div className="prose prose-sm mt-3 max-w-none">
        <ReactMarkdown>{strategy}</ReactMarkdown>
      </div>
    </Card>
  );
}
