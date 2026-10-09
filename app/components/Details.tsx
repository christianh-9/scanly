import { cn, scoreTone, toneText } from "~/lib/utils";
import { AlertIcon, CheckIcon, ChevronIcon } from "./Icons";

type Tip = { type: "good" | "improve"; tip: string; explanation: string };

const SECTIONS = [
  { key: "toneAndStyle", title: "Tone & style" },
  { key: "content", title: "Content" },
  { key: "structure", title: "Structure" },
  { key: "skills", title: "Skills" },
] as const;

const TipItem = ({ tip }: { tip: Tip }) => (
  <li className="flex gap-3">
    {tip.type === "good"
      ? <CheckIcon className="mt-0.5 shrink-0 text-pass" />
      : <AlertIcon className="mt-0.5 shrink-0 text-warn" />}
    <div>
      <p className="text-sm font-medium">
        <span className="sr-only">{tip.type === "good" ? "Working: " : "Fix: "}</span>
        {tip.tip}
      </p>
      <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-muted">{tip.explanation}</p>
    </div>
  </li>
);

const Details = ({ feedback }: { feedback: Feedback }) => {
  // the weakest category opens first
  const weakest = SECTIONS.reduce((a, b) => (feedback[b.key].score < feedback[a.key].score ? b : a)).key;

  return (
    <section aria-label="Detailed feedback" className="panel divide-y divide-line">
      {SECTIONS.map(({ key, title }) => {
        const { score, tips } = feedback[key];
        const fixes = tips.filter((t) => t.type === "improve");
        const wins = tips.filter((t) => t.type === "good");
        return (
          <details key={key} open={key === weakest} className="group">
            <summary className="flex cursor-pointer list-none items-center gap-4 px-5 py-4 transition-colors hover:bg-hover [&::-webkit-details-marker]:hidden">
              <span className="flex-1 font-semibold">{title}</span>
              <span className="text-sm text-subtle">
                {fixes.length > 0 ? `${fixes.length} to fix` : "Nothing to fix"}
              </span>
              <span className={cn("w-8 text-right font-medium num", toneText[scoreTone(score)])}>{score}</span>
              <ChevronIcon className="text-subtle transition-transform duration-200 group-open:rotate-180" />
            </summary>
            <div className="flex flex-col gap-6 px-5 pb-5 pt-1">
              {fixes.length > 0 && (
                <ul className="flex flex-col gap-4">{fixes.map((t, i) => <TipItem key={i} tip={t} />)}</ul>
              )}
              {wins.length > 0 && (
                <div>
                  <h3 className="mb-3 text-xs font-medium text-subtle">What's working</h3>
                  <ul className="flex flex-col gap-4">{wins.map((t, i) => <TipItem key={i} tip={t} />)}</ul>
                </div>
              )}
            </div>
          </details>
        );
      })}
    </section>
  );
};

export default Details;
