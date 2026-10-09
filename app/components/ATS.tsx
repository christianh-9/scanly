import { cn, scoreTone, toneText } from "~/lib/utils";
import { AlertIcon, CheckIcon } from "./Icons";

const ATS = ({
  score,
  suggestions,
}: {
  score: number;
  suggestions: { type: "good" | "improve"; tip: string }[];
}) => {
  // problems first; that's what the visitor came for
  const sorted = [...suggestions].sort((a, b) => (a.type === b.type ? 0 : a.type === "improve" ? -1 : 1));

  return (
    <section aria-labelledby="ats" className="panel">
      <div className="flex items-baseline justify-between gap-4 border-b border-line px-5 py-4">
        <div>
          <h2 id="ats" className="font-semibold">Applicant tracking systems</h2>
          <p className="mt-0.5 text-sm text-muted">How cleanly software can parse and rank this resume.</p>
        </div>
        <span className={cn("text-lg font-medium num", toneText[scoreTone(score)])}>{score}</span>
      </div>
      <ul className="flex flex-col gap-3 px-5 py-4">
        {sorted.map((s, i) => (
          <li key={i} className="flex gap-3 text-sm">
            {s.type === "good"
              ? <CheckIcon className="mt-0.5 shrink-0 text-pass" />
              : <AlertIcon className="mt-0.5 shrink-0 text-warn" />}
            <span className={s.type === "good" ? "text-muted" : "text-fg"}>
              <span className="sr-only">{s.type === "good" ? "Working: " : "Fix: "}</span>
              {s.tip}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ATS;
