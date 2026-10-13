"""Benchmark /api/analyze with the resumes in scripts/sample_resumes/.

Run from the project root, with the backend running locally:
    server/.venv/bin/python scripts/benchmark.py
    server/.venv/bin/python scripts/benchmark.py --passes 2 --url http://localhost:8001

Requests are sent one at a time so we measure single-request latency, not queueing.
Every run uses the same job title and description so only the backend code changes between benchmarks.
"""
import argparse
import statistics
import time
from pathlib import Path

import httpx

SAMPLES = Path(__file__).parent / "sample_resumes"
JOB_TITLE = "Software Engineer"
JOB_DESCRIPTION = (
    "We are hiring a software engineer to build web applications with React, TypeScript and Python. "
    "You will design APIs, write tests, and work with product and design to ship features."
)


def summarize(times: list[float]) -> dict[str, float]:
    """Return the median and 90th percentile of a list of durations in seconds.

    Example: summarize([10, 12, 11, 30, 13]) -> {"median": 12, "p90": ...}

    TODO:
    - median: the middle value once sorted (the statistics module has a function for this)
    - p90: the value 90% of runs are faster than. statistics.quantiles(data, n=10) splits the data
      into 10 equal groups and returns the 9 cut points between them; which one is p90?
    - think about the edge cases: what should happen with an empty list? with a single value?
      (statistics.quantiles needs at least 2 values)
    """
    if not times:
        return {"median": 0.0, "p90": 0.0}
    if len(times) == 1:
        return {"median": times[0], "p90": times[0]}
    return {
        "median": statistics.median(times),
        # 9 cut points between 10 equal groups; the last one (index 8, i.e. -1) is the 90th percentile
        "p90": statistics.quantiles(times, n=10, method="inclusive")[-1],
    }


def parse_server_timing(header: str) -> tuple[dict[str, float], dict[str, str]]:
    """'gemini;dur=24310.0, model;desc="x", fallback;desc="y:503"'
    -> ({"gemini": 24.31}, {"model": "x", "fallback": "y:503"})   (durations converted to seconds)"""
    steps, descs = {}, {}
    for part in header.split(","):
        name, *params = [p.strip() for p in part.split(";")]
        for p in params:
            key, _, value = p.partition("=")
            if key == "dur":
                steps[name] = float(value) / 1000
            elif key == "desc":
                descs[name] = value.strip('"')
    return steps, descs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8001")
    parser.add_argument("--compare", help="second backend URL; requests alternate between --url and this one, "
                                          "so Gemini's load changes hit both equally")
    parser.add_argument("--passes", type=int, default=2, help="times to send each resume")
    parser.add_argument("--interval", type=float, default=4.5,
                        help="minimum seconds between request starts, to stay under per-minute rate limits "
                             "(free tier: Flash-Lite 15/min -> 4.5, Flash 5/min -> 12.5). Waiting is not counted in timings.")
    parser.add_argument("--save", type=Path, help="directory to save each response's JSON, for quality comparison")
    args = parser.parse_args()

    pdfs = sorted(SAMPLES.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs in {SAMPLES}")
    targets = [args.url] + ([args.compare] if args.compare else [])
    stats = {url: {"totals": [], "gemini": [], "fallbacks": 0, "failures": 0} for url in targets}
    if args.save:
        args.save.mkdir(parents=True, exist_ok=True)

    print(f"{len(pdfs)} resumes x {args.passes} passes against {', '.join(targets)}\n")
    print(f"{'run':>4}  {'file':<28} {'target':<6} {'status':>6} {'total':>8} {'gemini':>8}  input  model (fallback)")

    with httpx.Client(timeout=300) as http:
        run, last_start = 0, float("-inf")
        for p in range(args.passes):
            for pdf in pdfs:
                for t, url in enumerate(targets):
                    run += 1
                    label = "A" if t == 0 else "B"
                    s = stats[url]
                    # pace requests; this sleep happens before the timer starts, so it never inflates a measurement
                    time.sleep(max(0.0, args.interval - (time.perf_counter() - last_start)))
                    start = last_start = time.perf_counter()
                    r = http.post(
                        f"{url}/api/analyze",
                        files={"resume": (pdf.name, pdf.read_bytes(), "application/pdf")},
                        data={"jobTitle": JOB_TITLE, "jobDescription": JOB_DESCRIPTION},
                    )
                    elapsed = time.perf_counter() - start

                    if r.status_code != 200:
                        s["failures"] += 1
                        print(f"{run:>4}  {pdf.name[:28]:<28} {label:<6} {r.status_code:>6} {elapsed:>7.1f}s {'':>8}  {r.text[:60]}")
                        continue

                    steps, descs = parse_server_timing(r.headers.get("server-timing", ""))
                    s["totals"].append(elapsed)
                    s["gemini"].append(steps.get("gemini", 0.0))
                    fallback = descs.get("fallback", "")
                    if fallback:
                        s["fallbacks"] += 1
                    if args.save:
                        (args.save / f"{label}-pass{p + 1}-{pdf.stem}.json").write_text(r.text)
                    model = descs.get("model", "?") + (f"  (skipped {fallback})" if fallback else "")
                    print(f"{run:>4}  {pdf.name[:28]:<28} {label:<6} {r.status_code:>6} {elapsed:>7.1f}s "
                          f"{steps.get('gemini', 0):>7.1f}s  {descs.get('input', '-'):<5}  {model}")

    print()
    for t, url in enumerate(targets):
        s = stats[url]
        print(f"[{'A' if t == 0 else 'B'}] {url}")
        if s["totals"]:
            tot, gem = summarize(s["totals"]), summarize(s["gemini"])
            print(f"    total   median {tot['median']:.1f}s   p90 {tot['p90']:.1f}s   (n={len(s['totals'])})")
            print(f"    gemini  median {gem['median']:.1f}s   p90 {gem['p90']:.1f}s")
        print(f"    fallback runs: {s['fallbacks']}   failed runs: {s['failures']}")


if __name__ == "__main__":
    main()
