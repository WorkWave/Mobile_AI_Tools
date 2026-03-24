# /design-doc — Design Document Generator

Generate a WorkWave MOB Design document following the established 27-section template and publish it directly to Confluence via the Atlassian MCP server. Automatically links the published page back to the originating Jira story.

Run after implementation as a **Detail Design** document covering all 27 sections with populated content where available.

---

## Step 1 — Collect Inputs

Ask all five questions upfront before doing any analysis:
1. Jira story number
2. Confluence space key for the engineering design doc (e.g. MOB, PPM)
3. Confluence parent page URL or page ID for the engineering design doc
4. Confluence space key for the product-facing summary doc
5. Confluence parent page URL or page ID for the product-facing summary doc

---

## Step 2 — Gather Context

Pull from all available sources simultaneously:
- Jira story via Atlassian MCP
- Figma design via Figma MCP (if story has a Figma URL)
- spec.md from `/specs/{feature}/spec.md` if it exists
- Current branch diff and changed files if implementation exists

If neither spec.md nor implementation code is found, ask the user for a brief description of the feature and its implementation approach.

---

## Step 3 — Generate Page Title

Generate a title from the spec and story content:

```
[Feature Name] — Detail Design
```

Example: `Offline Job Sync — Detail Design`

Present the title and ask the user to confirm or change it before proceeding to Step 4.

---

## Step 4 — Generate Document Content

Follow the WorkWave MOB Design Template — all 27 sections in order, including the full Table of Contents.

**Section population rules:**

| Sections | Rule |
|---|---|
| 1, 2, 3, 4, 5, 6, 7, 21, 24, 25, 26 | Fully populate |
| 8, 9, 10, 13, 15 | Populate if signals present |
| 11, 12, 14, 16, 17, 18, 19, 20, 22, 23, 27 | Stub with guiding questions |

**Signals that trigger conditional sections:**
- Section 8 (Security): auth, permissions, sensitive data mentioned
- Section 9 (Data Privacy): PII or customer data mentioned
- Section 10 (i18n/l10n): UI text or locale-specific behaviour mentioned
- Section 13 (Billing): feature flags, modules, or billing mentioned
- Section 15 (Performance): scale, load, or performance requirements mentioned

**Stubbed sections format:**
```
> ⚠️ To be completed by author.
> [guiding questions from template]
```

**Section-specific notes:**
- Section 3: use Mermaid diagram syntax where appropriate
- Section 4: use Mermaid sequence diagram syntax; include error scenarios
- Section 6: use Mermaid class diagram syntax where appropriate
- Section 7: include HTTP method, path, request/response shape, and backward compatibility notes
- Section 24: seed risks table from adversarial check findings if available in the session context
- Section 26: populate with unresolved questions from spec and AC gaps

---

## Step 5 — Confirm and Publish Engineering Doc

Present the confirmed title and ask the user to proceed.

Use the Atlassian MCP to create the Confluence page with:
- Space: as provided in Step 1
- Parent page: as provided in Step 1
- Title: confirmed in Step 3
- Content: full document from Step 4

After successful creation, link the page back to the Jira story:
1. Attempt to create a Confluence page link on the Jira story using the Atlassian MCP (`createIssueLink` or equivalent remote link with type "Confluence Page")
2. If that is not supported or fails, fall back to adding the Confluence page URL as a remote link on the story via `getJiraIssueRemoteIssueLinks` / remote link API

---

## Step 6 — Generate and Publish Product-Facing Summary

Generate a separate, non-technical summary document intended for product managers, stakeholders, and non-engineering audiences.

**Title format:**
```
[Feature Name] — What Was Built
```

**Document structure:**

### Overview
One to two paragraphs in plain language: what the feature does, why it was built, and what problem it solves for users or the business.

### What Changed
A bulleted list of user-visible changes and new capabilities. Avoid technical implementation details. Focus on behaviour and outcomes.

### Affected Areas
Which parts of the product or workflows are affected (e.g. "Job scheduling screen", "Offline mode", "Invoice generation"). Use product terminology, not code paths.

### Known Limitations or Follow-On Work
Any known gaps, deferred scope, or future work the product team should be aware of. Keep it brief and factual.

### Links
- Jira story
- Engineering design doc (published in Step 5)
- Figma designs (if applicable)

**Tone and style rules:**
- Write for a non-technical reader
- No code snippets, class names, or architecture jargon
- Use present tense ("The app now supports…")
- Keep the document under one page

Use the Atlassian MCP to publish this document to the product-facing Confluence space provided in Step 1, then link it on the Jira story using the same strategy as Step 5 (linked page first, URL fallback).

---

## Step 7 — Handle Publish Failure

If either Confluence MCP call fails, output the failed document to the terminal with a clear message asking the user to paste it manually. Do not lose the generated content.

---

## Output (on success)

```
✅ Engineering design doc published to Confluence
Title: [page title]
URL: [confluence page URL]
Space: [space key]

✅ Product-facing summary published to Confluence
Title: [feature name] — What Was Built
URL: [confluence page URL]
Space: [product space key]

✅ Confluence links added to Jira story [story number]
```
