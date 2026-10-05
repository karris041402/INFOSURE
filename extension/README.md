# InfoSure Chrome extension (Phase 1: highlighted text)

Manifest V3. Click the InfoSure icon to open a **side panel that stays open** while you browse. Highlight a health claim on the page and the text appears in the panel's field **live**; click **Check** to see the claim, the model's estimate, the evidence check, the sources, and a feedback option. You can also type or paste text into the field.

## Run it

1. Start the backend from the repo root (the dev model is for testing only):
   ```
   $env:INFOSURE_MODEL_VERSION = "v0.0-dev"
   py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```
   If you have validated evidence, build the index first: `py -m backend.app.review index build`.
2. In Chrome open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**, and choose this `extension/` folder. After changing any extension file, click the refresh icon on its card.
3. Click the InfoSure icon (pin it from the puzzle-piece menu) to open the panel, then highlight text on the page. The line under the text box says **"Connected to this page"** when highlights can be read. If the page was open before the extension was loaded, the panel adds its page script itself; if it still says it cannot read highlights, the page is a blocked one (browser pages, the Web Store, PDFs, local files) and you should type or paste the text.

## Behavior

- The field follows the highlight of the **active tab**. Highlights in background tabs are ignored; switching tabs shows that tab's current highlight.
- Clearing a highlight does not wipe the field.
- Opening the panel while text is already highlighted checks it right away. Later highlights only fill the field; you press **Check** (or Ctrl+Enter).
- A new highlight resets the view to the start screen, because the previous result no longer matches the field.

## What the panel shows (v0.3 redesign)

From top to bottom:

| Part | What it is |
|---|---|
| Header | Logo, name, and an **EN / TL** switch (English or Tagalog; remembered; switching re-renders the current result with no new request). |
| Input card | The text box that fills as you highlight, a connection light ("Connected to this page" or why highlights cannot be read), and the **Check** button. |
| **Model verdict (the main card)** | The model's output, large: **Reliable** (green shield) or **Misinformation** (red shield), a one-line meaning, a 3-step confidence meter (low / medium / high, never a percentage), and a tag saying it is an estimate, not verified. |
| Evidence check | Below the verdict: a chip (Supported / Contradicted / Not enough evidence), a one-line agreement strip (**agree**, **disagree** in amber, or **no matching evidence**), and one card per retrieved passage with source, domain, date, whether it supports or contradicts the claim, "Show more", and "Open source". |
| How to read this | Collapsible plain-language explanation of model vs evidence and what to do when they disagree. |
| Was this right? | Three icon buttons (thumbs up **Yes**, thumbs down **No**, **Flag**). A spinner shows while saving; the chosen answer is highlighted and the others dim, with a green "Saved for review" strip. If saving fails the buttons come back with a red error so you can retry. Stored as Pending for human review. |
| Actions | **Copy summary** (verdict, evidence, claim, source links) and **New check**. |
| Not a health topic / No checkable health claim | Neutral cards when nothing is verified. |
| Empty start screen | How it works, two **example claims** to click, and **Recent checks** (last 5, click to re-run). |
| Loading / error | Skeleton placeholders while checking; an error card with **Try again**. |

Notes:
- Recent checks are stored only in this browser (`localStorage`) and can be cleared from the start screen.
- Tagalog wording was written by the assistant and should be reviewed by a native speaker.
- Light and dark themes follow the system; motion is off if the system asks for reduced motion.

## Files

`manifest.json`, `background.js` (opens the panel on icon click), `content.js` (reports highlights from pages), `sidepanel.html` / `sidepanel.css` / `sidepanel.js` (the UI, the connection check, and the API calls).

## Notes and limits

- **Privacy:** `content.js` runs on every http(s) page but only passes the highlighted text to the extension's own side panel. Nothing goes to the InfoSure server until you press Check (or open the panel on an existing highlight). The extension asks for permission to read and change pages on all sites (content script plus `scripting`, used only to add `content.js` to tabs that were open before the extension).
- The server address is fixed to `http://127.0.0.1:8000` (`sidepanel.js` and `host_permissions`). Extension pages with that host permission need no CORS setup on the backend.
- Needs a recent Chrome (side panel API, Chrome 114+).
- Does not work on `chrome://` pages, the Chrome Web Store, or other pages Chrome blocks; use the text box there. Highlights inside iframes update the field live, but the first read when opening the panel only looks at the page's main frame.
- Feedback is stored as Pending through `/feedback` and never retrains anything without human validation.
- The confidence bands (below 0.6 low, below 0.75 medium) are placeholders for an uncalibrated score.
- Phase 2 (automatic page scan) is not built.
