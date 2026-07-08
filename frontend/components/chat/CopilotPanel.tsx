"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { sendCopilotChat } from "@/lib/api";
import type { CopilotChatMessage } from "@/lib/types";

const SUGGESTED_PROMPTS = [
  "Why did power output drop around 03:00?",
  "Generate a shift handover summary for the last few hours.",
  "Are there any active alarms right now?",
];

export function CopilotPanel() {
  const [open, setOpen] = useState(true);
  const [messages, setMessages] = useState<CopilotChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const res = await sendCopilotChat(trimmed, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, toolTrace: res.tool_trace }]);
    } catch {
      setError("Copilot request failed -- is Ollama running (`ollama serve`)?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-surface-border bg-surface">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-xs font-semibold uppercase tracking-wide text-foreground/60">AI operator copilot</span>
        <span className="text-foreground/40">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="flex flex-col gap-3 border-t border-surface-border p-4">
          {messages.length === 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-foreground/50">
                Ask about station performance, alarms, or request a shift summary.
              </p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => send(p)}
                    className="rounded-full border border-surface-border px-3 py-1 text-xs text-foreground/70 hover:border-accent-teal hover:text-accent-teal"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.length > 0 && (
            <div className="flex max-h-96 flex-col gap-3 overflow-y-auto">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                      m.role === "user" ? "bg-accent-teal/15 text-foreground" : "bg-background/60 text-foreground"
                    }`}
                  >
                    {m.role === "assistant" ? (
                      <div className="text-sm [&_li]:my-0.5 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_p]:my-1 [&_strong]:font-semibold [&_strong]:text-foreground [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-4">
                        <ReactMarkdown>{m.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    )}
                    {m.toolTrace && m.toolTrace.length > 0 && (
                      <details className="mt-2 text-xs text-foreground/50">
                        <summary className="cursor-pointer select-none">
                          {m.toolTrace.length} tool call{m.toolTrace.length > 1 ? "s" : ""} used
                        </summary>
                        <div className="mt-1 flex flex-col gap-1">
                          {m.toolTrace.map((t, ti) => (
                            <pre key={ti} className="overflow-x-auto rounded bg-background/80 p-2 text-[10px]">
                              {t.name}({JSON.stringify(t.args)})
                              {"\n->  "}
                              {JSON.stringify(t.result)}
                            </pre>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-lg bg-background/60 px-3 py-2 text-sm text-foreground/50">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-accent-teal" />
                    consulting historian...
                  </div>
                </div>
              )}
            </div>
          )}

          {loading && messages.length === 0 && (
            <div className="flex items-center gap-2 text-sm text-foreground/50">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent-teal" />
              consulting historian...
            </div>
          )}

          {error && <p className="text-xs text-accent-red">{error}</p>}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask the copilot..."
              disabled={loading}
              className="flex-1 rounded-md border border-surface-border bg-background/40 px-3 py-2 text-sm text-foreground placeholder:text-foreground/30 focus:border-accent-teal focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-md bg-accent-teal/15 px-4 py-2 text-sm font-medium text-accent-teal disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
