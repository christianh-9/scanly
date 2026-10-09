import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";
import { usePuterStore } from "./lib/puter";
import { useEffect } from "react";

export const links: Route.LinksFunction = () => [
  { rel: "icon", href: "/favicon.ico"},
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Geist:wght@400..700&family=Geist+Mono:wght@400..600&display=swap",
  },
];

const DESIGN_CONTRACT = `<!--
THESIS: A blunt verdict, shown like a build result: the score and a plain sentence first, the evidence beside it. Refuses the pastel-gradient SaaS card grid with score rings.
OWN-WORLD: Near-black ground, hairline #262626 borders, Geist and Geist Mono, white primary buttons, blue only for interaction, green/amber/red only for score bands, plus red on the destructive confirm button.
STORY: The visitor uploads, watches an analysis log run like a deploy, reads a verdict they cannot misread, then checks it against their resume.
FIRST VIEWPORT: Review page: resume preview left; right, the overall score huge in mono with a one-line verdict, five category bars beneath.
FORM: Vercel product UI (user-pinned reference), seed 7d832dfe.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
-->`;

export function Layout({ children }: { children: React.ReactNode }) {
  const { init } = usePuterStore()

  useEffect(() => {
    init()
  }, [init])

  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <template id="design-contract" dangerouslySetInnerHTML={{ __html: DESIGN_CONTRACT }} />
        <script src="https://js.puter.com/v2/"></script>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1>{message}</h1>
      <p>{details}</p>
      {stack && (
        <pre className="w-full p-4 overflow-x-auto">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  );
}
