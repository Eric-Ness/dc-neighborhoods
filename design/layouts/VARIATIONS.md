# Round 2: variations on Layout C

The owner picked **Layout C (Civic Dashboard)** as the direction: numbers-first, scannable, a utility-app feel. They are not attached to its details, and asked for 3-4 *creative* variations. Each designer takes the direction somewhere distinct. Be bold; a safe copy of C is a wasted slot.

Read first:
- `design/layouts/BRIEF.md`: content sections, data rules, build rules. All still apply.
- `design/layouts/facts.json`: the only data source. It has new fields: `lead_sentence`, plus exact condo figures in `homes`.
- `design/layouts/C-civic-dashboard.html` and its generator `src/C_civic_dashboard.py`: the starting point. Reuse its data-prep code freely.

## Keep from C

- Numbers lead, every number shows its comparison, and the page is scannable in seconds.
- The rodent-complaints lead, but **open it with the written `lead_sentence`** so the top reads like a finding, not bare numbers. (The owner liked this from Layout A.)
- A "From the archives" history moment: the Delafield/Cafritz fact and the 1926 OCR clipping with its source.
- All BRIEF sections, the sponsor slot and the independence footer.

## Fix from C

- At desktop width, C's map card left a large empty area beside the long project list. Make the desktop composition balanced.
- Never write "approx": facts.json now has exact figures.

## Must work at both sizes

Design for a **390px phone and a 1440px desktop equally**. The owner will judge both. No horizontal scroll at 375px. Dark mode is optional.

## Deliverable

`design/layouts/<ID>-<slug>.html` plus the generator `design/layouts/src/<ID>_<slug>.py`. Put a label at the very top: "LAYOUT <ID>: <name>". Final reply: ≤100 words covering the idea, what makes it different from C, and one trade-off.
