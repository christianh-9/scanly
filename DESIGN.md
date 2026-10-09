---
name: Scanly
description: Resume review that reads like a build result, a score and a blunt verdict first, the evidence beside it.
colors:
  bg: "#0a0a0a"
  raised: "#111111"
  hover: "#1a1a1a"
  line: "#262626"
  line-strong: "#3d3d3d"
  fg: "#ededed"
  muted: "#a1a1a1"
  subtle: "#8a8a8a"
  accent: "#3291ff"
  pass: "#4cc38a"
  warn: "#f5a524"
  fail: "#ff5f56"
  fail-strong: "#c9252b"
typography:
  display:
    fontFamily: "Geist Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "clamp(4rem, 10vw, 6rem)"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.04em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.33
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  label:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.43
  caption:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.33
  numeric:
    fontFamily: "Geist Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontWeight: 500
    fontFeature: "tnum"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  full: "9999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "32px"
  2xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.fg}"
    textColor: "{colors.bg}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.fg}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "36px"
  button-secondary-hover:
    backgroundColor: "{colors.hover}"
  button-danger:
    backgroundColor: "{colors.fail-strong}"
    textColor: "#ffffff"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "36px"
  button-icon:
    textColor: "{colors.subtle}"
    rounded: "{rounded.md}"
    size: "32px"
  button-icon-hover:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.fg}"
  field:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.fg}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  panel:
    backgroundColor: "{colors.raised}"
    rounded: "{rounded.lg}"
  nav:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.fg}"
    height: "56px"
  score-bar:
    backgroundColor: "{colors.line}"
    rounded: "{rounded.full}"
    height: "6px"
---

# Design System: Scanly

## Overview

**Creative North Star: "The Build Log"**

Scanly presents a resume review the way a deploy dashboard presents a build: a single result, stated plainly, with the log and the evidence one glance away. The ground is near-black, surfaces separate by hairline borders rather than shadow, and the only voices allowed to carry color are interaction (blue) and the score bands (green, amber, red). Everything else is grayscale text on gray hairlines, so a colored number is always a verdict and never decoration.

Density is product-UI dense, not marketing-airy: 14px body, 36px controls, rows of 12px vertical padding, one container at 1024px. Type is Geist for language and Geist Mono for every number, so scores, sizes, timers, and file names read as measurements. The pinned reference is Vercel's product UI; the build follows it in material (hairlines, white primary button, mono numerals) and refuses the pastel-gradient SaaS card grid with score rings.

Motion is nearly absent by design. There is one authored animation (score bars fill once when a review opens) plus functional feedback: color transitions on hover, a spinner, skeleton pulses. All of it yields to `prefers-reduced-motion`.

**Key Characteristics:**
- Near-black ground, hairline borders, flat surfaces.
- White primary button; blue reserved for focus and active interaction.
- Green/amber/red mean score band and nothing else (one exception: the destructive confirm).
- Every number set in Geist Mono with tabular figures.
- Verdict before evidence: the score and a plain sentence lead every review.

## Colors

A grayscale world with two tightly fenced signal systems: one interaction blue, and a three-step score scale.

### Primary
- **Interaction Blue** (accent): focus rings (2px outline, 2px offset), focused field borders, the active drag state of the dropzone (border plus 5% tint), text selection (35% mix), and the caret. It never fills a button and never marks content.

### Secondary
- **Pass Green** (pass): scores of 70 and above, score-bar fills in that band, and "working" check icons in tips and the analysis log.
- **Warn Amber** (warn): scores 50 to 69, and the alert icon on items to fix.
- **Fail Red** (fail): scores below 50, inline error messages, failed log steps.
- **Destructive Red** (fail-strong): the background of the destructive confirm button only. Darker than Fail Red so white text clears 4.5:1.

### Neutral
- **Ink Ground** (bg): the page background and nav (at 80% with backdrop blur).
- **Raised Charcoal** (raised): panels, fields, secondary buttons, dialogs.
- **Hover Charcoal** (hover): row and summary hover fills, icon-button hover, skeleton blocks.
- **Hairline** (line): every border and divider, and the empty track of score bars.
- **Strong Hairline** (line-strong): hover borders on fields and secondary buttons, dashed dropzone and empty-state borders, pending log dots, scrollbar thumb.
- **Paper White Text** (fg): primary text and the primary button fill.
- **Muted Gray** (muted): secondary copy, field labels, explanations.
- **Subtle Gray** (subtle): tertiary text, placeholders, dates, the "/100" denominator, icon-button rest color.

### Named Rules
**The Band-Only Rule.** Green, amber, and red appear only where `scoreTone` assigns them: score numbers, score bars, and tip/log status icons. Fail Red additionally marks error text, which is the same meaning (failed). Destructive Red appears on the destructive confirm button and nowhere else.

**The Blue Is a Cursor Rule.** Blue marks where the user is acting (focus, drag, selection, caret). Links and buttons do not turn blue; links go from muted to fg on hover.

**The Thresholds Live in One Place Rule.** Score bands are pass at 70 and above, warn at 50 to 69, fail below 50, defined once in `scoreTone`. Never re-derive them in a component.

## Typography

**Display Font:** Geist Mono (with ui-monospace, SFMono-Regular, Menlo)
**Body Font:** Geist (with ui-sans-serif, system-ui)
**Label/Mono Font:** Geist Mono, for all numerals

**Character:** A neutral grotesk for sentences and a matching mono for measurements; the pairing makes every number feel instrumented.

### Hierarchy
- **Display** (500, clamp(4rem, 10vw, 6rem), line-height 1, -0.04em, mono, tabular): the overall score on the review page only, colored by band, followed by "/100" in 20px Subtle Gray.
- **Headline** (600, 24px rising to 30px at sm, tight tracking): page titles ("Reviews", "New review") and the verdict sentence under the score (24px, balanced wrap).
- **Title** (600, 16px): panel headings, dialog titles, review-page header, detail section summaries.
- **Body** (400, 14px, 20px line): nearly all UI copy. Tip explanations use relaxed leading and cap at 65ch; page intros cap at 60ch.
- **Label** (500, 14px): button text, field labels (in Muted Gray), panel-bar headings ("Analysis log", "Resume").
- **Caption** (400, 12px): file-size hints, log status, the "What's working" sub-heading.

### Named Rules
**The Numbers Are Mono Rule.** Any score, count, size, timer, or file name renders in Geist Mono with tabular figures. Prose never does.

**The Sentence-Case Rule.** Headings and labels are sentence case at normal tracking. No uppercase, letter-spaced labels.

## Layout

One centered container (max 1024px, 16px side padding, 24px from sm). Page sections sit at 40px top and bottom, 56px from sm. Pages open with a headline and one muted sentence, then content 32px below.

The review page is a two-column grid at lg (5fr resume preview, 7fr verdict and evidence, 40px gap); the preview column is sticky 96px from the top. Below lg the verdict comes first and the resume preview follows, capped at 60vh. The upload page pairs the form with a fixed 340px analysis-log column at lg; on small screens the log stacks below and the page scrolls to it on submit (instantly under reduced motion).

Rhythm: 8px between label and field, 20px between form groups, 16px to 20px inside panels, 32px between stacked review blocks. History renders as a divided list inside one panel, not a card grid; rows hide the verdict below md and the date below sm.

## Elevation & Depth

Flat. Depth comes from three tonal steps (ground, raised, hover) and hairline borders. The sticky nav uses 80% ground with backdrop blur instead of a shadow. The one shadow in the system belongs to the modal dialog, which floats over a 70% black scrim.

### Shadow Vocabulary
- **Modal lift** (`box-shadow: 0 16px 48px rgba(0,0,0,0.6)`): the confirmation dialog only.

### Named Rules
**The Hairline, Not Shadow Rule.** Panels, rows, fields, and buttons separate by a 1px Hairline border and a tonal step. Shadows are reserved for content that sits above the page (modals).

## Shapes

Small, consistent radii: 4px for thumbnails and skeleton blocks, 6px for buttons, fields, icon buttons, and focus rings, 8px for panels and the dialog, full round for score bars, log dots, and circular icon wells. Borders are always 1px; dashed Strong Hairline marks a drop target or an empty state.

## Components

### Buttons
Quiet and compact; the primary button is the brightest object on screen.
- **Shape:** gently rounded (6px), 36px tall, 16px horizontal padding, 14px medium label, 8px icon gap.
- **Primary:** Paper White fill with Ink Ground text; hover goes to pure white. One per view. In the nav it shrinks to 32px tall with 12px padding.
- **Secondary:** Raised Charcoal with a Hairline border; hover lifts to Hover Charcoal and Strong Hairline.
- **Danger:** Destructive Red with white text, hover brightens 10%. Used for the delete confirm and the wipe action.
- **Icon:** 32px square, Subtle Gray glyph, hover fills Hover Charcoal and turns text fg. Always carries an aria-label.
- **Hover / Focus:** 150ms color transitions only. Focus is the global 2px blue outline. Disabled drops to 50% opacity.

### Cards / Containers
- **Corner Style:** 8px.
- **Background:** Raised Charcoal.
- **Shadow Strategy:** none (see Elevation).
- **Border:** 1px Hairline; internal sections divide with Hairline rules.
- **Internal Padding:** 16px to 20px; panel header bars are 10px by 16px with a 14px medium title.

### Inputs / Fields
- **Style:** Raised Charcoal, 1px Hairline border, 6px radius, 8px by 12px padding, 14px text, Subtle Gray placeholder. Labels sit above in 14px medium Muted Gray.
- **Hover / Focus:** border to Strong Hairline on hover, Interaction Blue on focus (no glow, no ring).
- **Error / Disabled:** errors are a 14px Fail Red line below with `role="alert"`; the whole form disables through a fieldset while processing.
- **Dropzone:** dashed Strong Hairline, 6px radius, centered 40px circular icon well; on drag the border turns blue over a 5% blue tint.

### Navigation
Sticky 56px bar on 80% ground with backdrop blur and a Hairline bottom border. Wordmark left (semibold, tight), a compact primary "New review" button right, hidden on the upload page itself.

### Score Readout (signature)
The verdict block: the overall score in Display mono colored by band, "/100" beside it, then the verdict sentence as a headline. Beneath, five category rows on a 110px / 1fr / 36px grid: Muted label, a 6px full-round bar (Hairline track, band-colored fill), and the band-colored mono number. Bars fill once from the left over 900ms on an expo-out curve, staggered 70ms per row, and do not animate under reduced motion.

### Analysis Log (signature)
A panel with a header bar ("Analysis log", plus status and a mono elapsed timer) over an ordered list of steps at 14px. Pending steps are Subtle Gray with a small Strong Hairline dot; the active step shows a spinner in fg; done steps get a green check; a failed step turns Fail Red with an alert icon.

### Detail Sections
Native disclosure rows inside one divided panel: semibold title, a Subtle "N to fix" count, the band-colored mono score, and a chevron that rotates 180 degrees on open. The weakest category opens by default. Fixes list first with amber alert icons; "What's working" follows with green checks and Muted text.

### Icons
Lucide paths inlined as 16px SVG, 1.75 stroke, round caps and joins, `currentColor`. One stroke weight for the whole app.

## Do's and Don'ts

### Do:
- **Do** color a number only through `scoreTone`: pass at 70 and above, warn at 50 to 69, fail below 50.
- **Do** set every score, count, size, and timer in Geist Mono with tabular figures.
- **Do** separate surfaces with a 1px Hairline (#262626) border and a tonal step, not a shadow.
- **Do** lead any review surface with the score and a plain verdict sentence, evidence after.
- **Do** keep one Paper White primary button per view; everything else is secondary or icon.
- **Do** gate any new motion behind `prefers-reduced-motion`, as the bar fill and upload scroll already are.

### Don't:
- **Don't** use blue for links, fills, or content highlights; it marks focus, drag, selection, and caret only.
- **Don't** use green, amber, or red for decoration, categories, or branding; red as a fill is only for the destructive confirm.
- **Don't** draw score rings or gauges; scores are a big mono number and flat horizontal bars.
- **Don't** add gradients, pastel tints, or a card grid for the review history; it is a divided list in one panel.
- **Don't** add uppercase letter-spaced labels or small headings above headings.
- **Don't** add shadows to panels, rows, or buttons; the modal is the only lifted surface.
