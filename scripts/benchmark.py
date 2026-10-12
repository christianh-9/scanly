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
    parser.add_argument("--passes", type=int, default=2, help="times to send each resume")
    args = parser.parse_args()

    pdfs = sorted(SAMPLES.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs in {SAMPLES}")

    totals, gemini_times, fallbacks, failures = [], [], 0, 0
    print(f"{len(pdfs)} resumes x {args.passes} passes against {args.url}\n")
    print(f"{'run':>4}  {'file':<28} {'status':>6} {'total':>8} {'gemini':>8}  model (fallback)")

    with httpx.Client(timeout=300) as http:
        run = 0
        for _ in range(args.passes):
            for pdf in pdfs:
                run += 1
                start = time.perf_counter()
                r = http.post(
                    f"{args.url}/api/analyze",
                    files={"resume": (pdf.name, pdf.read_bytes(), "application/pdf")},
                    data={"jobTitle": JOB_TITLE, "jobDescription": JOB_DESCRIPTION},
                )
                elapsed = time.perf_counter() - start

                if r.status_code != 200:
                    failures += 1
                    print(f"{run:>4}  {pdf.name[:28]:<28} {r.status_code:>6} {elapsed:>7.1f}s {'':>8}  {r.text[:60]}")
                    continue

                steps, descs = parse_server_timing(r.headers.get("server-timing", ""))
                totals.append(elapsed)
                gemini_times.append(steps.get("gemini", 0.0))
                fallback = descs.get("fallback", "")
                if fallback:
                    fallbacks += 1
                model = descs.get("model", "?") + (f"  (skipped {fallback})" if fallback else "")
                print(f"{run:>4}  {pdf.name[:28]:<28} {r.status_code:>6} {elapsed:>7.1f}s {steps.get('gemini', 0):>7.1f}s  {model}")

    print()
    if totals:
        t, g = summarize(totals), summarize(gemini_times)
        print(f"total   median {t['median']:.1f}s   p90 {t['p90']:.1f}s   (n={len(totals)})")
        print(f"gemini  median {g['median']:.1f}s   p90 {g['p90']:.1f}s")
    print(f"fallback runs: {fallbacks}   failed runs: {failures}")


if __name__ == "__main__":
    main()
