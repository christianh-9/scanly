"""Generate fictional benchmark resumes into scripts/sample_resumes/ (people and companies are made up).

Run from the project root:  server/.venv/bin/python scripts/make_sample_resumes.py
Needs Google Chrome (prints HTML to PDF) and macOS `sips` (for the image-only "scanned" resume).
"""
import html
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).parent / "sample_resumes"

CSS = """
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; color: #111; margin: 0; line-height: 1.35; }
.page { padding: 36px 44px; }
h1 { font-size: 20pt; margin: 0; } .contact { color: #444; margin: 2px 0 10px; }
h2 { font-size: 11pt; text-transform: uppercase; letter-spacing: .5px; border-bottom: 1px solid #999; margin: 14px 0 6px; }
.role { display: flex; justify-content: space-between; font-weight: bold; margin-top: 6px; }
.sub { font-style: italic; color: #333; } ul { margin: 3px 0 4px 18px; padding: 0; } li { margin: 1px 0; }
.cols { display: flex; gap: 22px; } .side { width: 32%; background: #f2f4f7; padding: 14px; } .main { flex: 1; }
table { border-collapse: collapse; width: 100%; } td, th { border: 1px solid #bbb; padding: 3px 6px; text-align: left; }
"""


def esc(s):
    return html.escape(s)


def jobs_html(jobs):
    out = []
    for title, org, dates, bullets in jobs:
        out.append(f'<div class="role"><span>{esc(title)}, {esc(org)}</span><span>{esc(dates)}</span></div>')
        out.append("<ul>" + "".join(f"<li>{esc(b)}</li>" for b in bullets) + "</ul>")
    return "".join(out)


def single_column(r):
    sections = [f"<h2>{esc(name)}</h2>{body}" for name, body in r["sections"]]
    return f'<div class="page"><h1>{esc(r["name"])}</h1><div class="contact">{esc(r["contact"])}</div>{"".join(sections)}</div>'


def two_column(r):
    side = "".join(f"<h2>{esc(n)}</h2>{b}" for n, b in r["side"])
    main = "".join(f"<h2>{esc(n)}</h2>{b}" for n, b in r["sections"])
    return (f'<div class="page"><h1>{esc(r["name"])}</h1><div class="contact">{esc(r["contact"])}</div>'
            f'<div class="cols"><div class="side">{side}</div><div class="main">{main}</div></div></div>')


def ul(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def p(text):
    return f"<p>{esc(text)}</p>"


RESUMES = [
    ("01-strong-new-grad-swe", single_column, {
        "name": "Maya Okafor", "contact": "maya.okafor@example.com · (555) 201-4432 · github.com/mayaokafor · Austin, TX",
        "sections": [
            ("Education", p("B.S. Computer Science, University of Texas at Austin, May 2026. GPA 3.8. Coursework: Data Structures, Distributed Systems, Databases, HCI.")),
            ("Experience", jobs_html([
                ("Software Engineering Intern", "Brightline Health", "May 2025 – Aug 2025", [
                    "Built a React + TypeScript appointment dashboard used by 40 clinic staff, replacing a spreadsheet workflow.",
                    "Designed three REST endpoints in FastAPI with Pydantic validation; added 28 pytest tests (92% coverage on the new module).",
                    "Cut dashboard load time from 3.1 s to 1.2 s by paginating queries and adding a Postgres index."]),
                ("Teaching Assistant, Data Structures", "UT Austin", "Jan 2024 – May 2026", [
                    "Led weekly labs for 35 students and wrote autograder tests for 6 assignments in Python."])])),
            ("Projects", jobs_html([
                ("TripSplit", "React, Node.js, PostgreSQL", "2025", [
                    "Expense-splitting web app with 300+ monthly users; implemented auth, receipt OCR upload and CI on GitHub Actions."])])),
            ("Skills", p("TypeScript, JavaScript, Python, React, Node.js, FastAPI, PostgreSQL, Docker, Git, Jest, pytest, AWS (S3, Lambda)")),
        ]}),
    ("02-midlevel-backend-2-pages", single_column, {
        "name": "Daniel Reyes", "contact": "daniel.reyes@example.com · (555) 330-1290 · linkedin.com/in/danielreyes-dev · Denver, CO",
        "sections": [
            ("Summary", p("Backend engineer with 5 years building high-traffic Python and Go services, payment systems and internal developer tooling.")),
            ("Experience", jobs_html([
                ("Senior Software Engineer", "Ledgerly", "2023 – Present", [
                    "Own the payments ledger service (Go, PostgreSQL) processing 2.4M transactions per day at 99.98% availability.",
                    "Led migration from a monolith to 6 services behind gRPC; reduced p95 latency from 480 ms to 140 ms.",
                    "Introduced idempotency keys and outbox pattern, eliminating duplicate charges (previously ~30 per month).",
                    "Mentor 3 engineers; run the backend interview loop and wrote the team's API design guide.",
                    "Built a load-testing harness with k6 that runs nightly and flags regressions over 10%."]),
                ("Software Engineer", "Ledgerly", "2021 – 2023", [
                    "Built the merchant onboarding API in Python/Django, integrating KYC vendors and webhook retries.",
                    "Added structured logging and OpenTelemetry tracing across 12 endpoints; cut incident triage time roughly in half.",
                    "Wrote data backfill jobs in Airflow for 80M historical records with zero downtime."]),
                ("Software Engineer", "CivicStack", "2019 – 2021", [
                    "Developed REST APIs for a permit-tracking platform used by 14 city governments.",
                    "Implemented role-based access control and audit logging to meet SOC 2 requirements.",
                    "Containerized services with Docker and moved deployments to Kubernetes on GKE.",
                    "Maintained a Celery task queue handling 50k background jobs per day."]),
                ("Junior Developer", "Pixel & Pine Agency", "2018 – 2019", [
                    "Built WordPress and Django sites for 20+ small-business clients.",
                    "Automated client report generation with Python scripts, saving about 6 hours a week."])])),
            ("Projects", jobs_html([
                ("pgwatch-lite (open source)", "Go", "2022 – Present", [
                    "Lightweight Postgres query monitor with 1.1k GitHub stars; accepts community contributions."]),
                ("Conference talk", "PyCon US", "2024", ["Presented \"Idempotency in Practice\" to ~400 attendees."])])),
            ("Skills", p("Go, Python, Django, FastAPI, PostgreSQL, Redis, Kafka, gRPC, Docker, Kubernetes, Terraform, AWS, GCP, OpenTelemetry, k6")),
            ("Education", p("B.S. Software Engineering, Colorado State University, 2018")),
        ]}),
    ("03-weak-vague-swe", single_column, {
        "name": "Tyler Brooks", "contact": "tylerbrooks99@example.com",
        "sections": [
            ("Objective", p("Looking for a job in software where I can use my skills and grow. Hard worker and team player who is passionate about technology.")),
            ("Experience", jobs_html([
                ("Developer", "Freelance", "2022 - now", [
                    "Responsible for making websites for people.", "Worked on various projects using different technologys.",
                    "Helped with fixing bugs and stuff."]),
                ("Sales Associate", "Best Electronics", "2020 - 2022", [
                    "Responsible for helping customers.", "Responsible for the store being clean."])])),
            ("Skills", p("HTML, CSS, Javascript, react, python, Microsoft Office, communication, leadership, problem solving, fast learner")),
            ("Education", p("Some college, Lakeside Community College")),
        ]}),
    ("04-data-analyst", single_column, {
        "name": "Priya Raman", "contact": "priya.raman@example.com · (555) 118-7720 · Chicago, IL",
        "sections": [
            ("Experience", jobs_html([
                ("Data Analyst", "Northwind Retail", "2022 – Present", [
                    "Built Tableau dashboards tracking sales across 120 stores; adopted by regional managers for weekly reviews.",
                    "Wrote SQL models in dbt over Snowflake, replacing 15 manual Excel reports.",
                    "Ran A/B test analysis for checkout changes that lifted conversion 3.4%."]),
                ("Business Analyst Intern", "Harbor Insurance", "Summer 2021", [
                    "Cleaned and analyzed claims data in Python (pandas) to identify fraud patterns."])])),
            ("Skills", p("SQL, Python (pandas, scikit-learn), dbt, Snowflake, Tableau, Excel, statistics, A/B testing")),
            ("Education", p("B.S. Statistics, University of Illinois, 2022")),
        ]}),
    ("05-product-designer", single_column, {
        "name": "Lena Fischer", "contact": "lena@example.com · lenafischer.design · Portland, OR",
        "sections": [
            ("Experience", jobs_html([
                ("Product Designer", "Fieldnote", "2021 – Present", [
                    "Redesigned onboarding for a note-taking app, raising day-7 retention from 31% to 44%.",
                    "Built and maintain a Figma design system of 90 components used by 4 product squads.",
                    "Ran 25 usability interviews per quarter and turned findings into roadmap proposals."]),
                ("Visual Designer", "Studio Ember", "2019 – 2021", [
                    "Designed brand identities and marketing sites for 15 clients."])])),
            ("Skills", p("Figma, prototyping, user research, design systems, accessibility (WCAG), basic HTML/CSS")),
            ("Education", p("B.F.A. Graphic Design, Pacific Northwest College of Art, 2019")),
        ]}),
    ("06-frontend-two-column", two_column, {
        "name": "Jordan Kim", "contact": "jordan.kim@example.com · (555) 642-9081 · jordankim.dev · Seattle, WA",
        "side": [
            ("Skills", ul(["React / Next.js", "TypeScript", "Tailwind CSS", "GraphQL", "Jest, Playwright", "Web performance", "Accessibility"])),
            ("Education", p("B.S. Informatics, University of Washington, 2022")),
            ("Links", p("github.com/jordankim · dribbble.com/jkim")),
        ],
        "sections": [
            ("Experience", jobs_html([
                ("Frontend Engineer", "Cobalt Learning", "2022 – Present", [
                    "Rebuilt the course player in Next.js; Lighthouse performance from 54 to 93.",
                    "Led accessibility audit and fixes, reaching WCAG 2.1 AA across 40 pages.",
                    "Created a shared component library adopted by 3 teams, cutting UI bug reports by a third."]),
                ("Frontend Intern", "Rainier Maps", "Summer 2021", [
                    "Built interactive map filters in React and Mapbox GL."])])),
            ("Projects", jobs_html([("Palette Pal", "Next.js, OpenAI API", "2024", ["Color palette generator with 2k weekly visitors."])])),
        ]}),
    ("07-teacher-to-bootcamp-dev", single_column, {
        "name": "Marcus Allen", "contact": "marcus.allen@example.com · (555) 774-3315 · Atlanta, GA",
        "sections": [
            ("Summary", p("Former high school math teacher, now a full-stack developer after completing a 16-week coding bootcamp.")),
            ("Projects", jobs_html([
                ("GradeBook Lite", "React, Express, MongoDB", "2025", [
                    "Gradebook app for teachers with CSV import and charts; piloted by 4 teachers at my former school."]),
                ("Bootcamp capstone: SnackSwap", "React, Node.js, PostgreSQL", "2025", [
                    "Team of 4; I built the REST API, JWT auth and deployment on Render."])])),
            ("Experience", jobs_html([
                ("Math Teacher", "Westlake High School", "2017 – 2024", [
                    "Taught Algebra II and AP Statistics to 150 students a year; AP pass rate rose from 58% to 74%.",
                    "Introduced Python in the statistics curriculum and ran an after-school coding club."])])),
            ("Skills", p("JavaScript, React, Node.js, Express, PostgreSQL, MongoDB, Git, HTML/CSS")),
            ("Education", p("Full-Stack Web Development Certificate, CodeForge Bootcamp, 2025 · B.S. Mathematics, Georgia State University, 2017")),
        ]}),
    ("08-sparse-intern", single_column, {
        "name": "Sofia Martinez", "contact": "sofia.m@example.com",
        "sections": [
            ("Education", p("B.S. Computer Science (in progress), Arizona State University, expected 2028")),
            ("Projects", jobs_html([("Personal website", "HTML, CSS", "2025", ["Made a personal website."])])),
            ("Skills", p("Java, Python, HTML")),
        ]}),
    ("09-senior-fullstack-long", single_column, {
        "name": "Elena Petrova", "contact": "elena.petrova@example.com · (555) 909-2210 · github.com/epetrova · New York, NY",
        "sections": [
            ("Summary", p("Full-stack engineer and tech lead with 10 years shipping B2B SaaS products in React, TypeScript, Python and Node.js.")),
            ("Experience", jobs_html([
                ("Staff Software Engineer", "Quillmark", "2022 – Present", [
                    "Tech lead for a 7-person team building collaborative document editing (React, CRDTs, WebSockets).",
                    "Designed the permissions model used by 3,000 enterprise customers; zero access-control incidents since launch.",
                    "Drove TypeScript strict-mode migration across 400k lines of frontend code.",
                    "Set up feature-flag and canary release process, reducing rollback rate from 9% to 2%."]),
                ("Senior Software Engineer", "Quillmark", "2019 – 2022", [
                    "Built the public REST and webhook API (Node.js, PostgreSQL) now used by 600 integrations.",
                    "Cut monthly cloud spend by $18k by right-sizing databases and adding Redis caching."]),
                ("Software Engineer", "Helio Analytics", "2016 – 2019", [
                    "Built React dashboards and Python ETL pipelines for marketing analytics.",
                    "Implemented SSO (SAML, OIDC) for enterprise clients."]),
                ("Software Engineer", "Bluepeak Systems", "2014 – 2016", [
                    "Maintained a Rails e-commerce platform and wrote its first automated test suite."]),
                ("Web Developer Intern", "Metro Daily News", "Summer 2013", [
                    "Built interactive election-night graphics in D3.js."])])),
            ("Projects", jobs_html([
                ("tiny-crdt", "TypeScript", "2021", ["Open-source CRDT library, 2.3k GitHub stars."]),
                ("Speaker", "React Summit", "2023", ["Talk on real-time collaboration architecture."])])),
            ("Skills", p("TypeScript, React, Node.js, Python, PostgreSQL, Redis, WebSockets, GraphQL, AWS, Terraform, CI/CD, system design, mentoring")),
            ("Education", p("B.S. Computer Science, Cornell University, 2014")),
        ]}),
    ("10-devops-table-skills", single_column, {
        "name": "Ahmed Hassan", "contact": "ahmed.hassan@example.com · (555) 251-6604 · Toronto, ON",
        "sections": [
            ("Skills", "<table><tr><th>Area</th><th>Tools</th></tr>"
                       "<tr><td>Cloud</td><td>AWS (EKS, RDS, IAM), GCP</td></tr>"
                       "<tr><td>Infrastructure as code</td><td>Terraform, Pulumi, Ansible</td></tr>"
                       "<tr><td>Containers</td><td>Docker, Kubernetes, Helm</td></tr>"
                       "<tr><td>CI/CD</td><td>GitHub Actions, ArgoCD, Jenkins</td></tr>"
                       "<tr><td>Observability</td><td>Prometheus, Grafana, Datadog</td></tr>"
                       "<tr><td>Languages</td><td>Python, Bash, Go</td></tr></table>"),
            ("Experience", jobs_html([
                ("DevOps Engineer", "Maplewave", "2021 – Present", [
                    "Migrated 30 services to EKS with Helm and ArgoCD; deploys went from weekly to 20+ per day.",
                    "Wrote Terraform modules for all AWS infrastructure; new environments spin up in 25 minutes.",
                    "Built Grafana SLO dashboards and on-call runbooks, cutting mean time to recovery from 70 to 25 minutes."]),
                ("Systems Administrator", "Lakeshore College", "2018 – 2021", [
                    "Managed 200 Linux servers and automated patching with Ansible."])])),
            ("Certifications", p("AWS Certified Solutions Architect – Associate (2022) · Certified Kubernetes Administrator (2023)")),
            ("Education", p("Diploma, Computer Systems Technology, Seneca College, 2018")),
        ]}),
]


def chrome(*args):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", *args],
                   check=True, capture_output=True)


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, template, data in RESUMES:
            page = Path(tmp) / f"{name}.html"
            page.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{template(data)}")
            chrome(f"--print-to-pdf={OUT / (name + '.pdf')}", page.as_uri())
            print("wrote", name + ".pdf")

        # "scanned" copy of resume 1: screenshot -> image-only PDF with no text layer
        first = Path(tmp) / f"{RESUMES[0][0]}.html"
        png = Path(tmp) / "scan.png"
        chrome(f"--screenshot={png}", "--window-size=816,1056", first.as_uri())
        subprocess.run(["sips", "-s", "format", "pdf", str(png), "--out", str(OUT / "11-scanned-image-only.pdf")],
                       check=True, capture_output=True)
        print("wrote 11-scanned-image-only.pdf")


if __name__ == "__main__":
    main()
