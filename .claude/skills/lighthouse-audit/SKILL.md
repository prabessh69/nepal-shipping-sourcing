---
name: lighthouse-audit
description: Run Lighthouse performance, accessibility, SEO, and best practices audits on web pages.
---
When auditing a web page for performance, SEO, or accessibility:
1. Run `npx lighthouse <URL> --output=json --output-path=./lighthouse-report.json --chrome-flags="--headless"`
2. Read the scores and top diagnostics from `./lighthouse-report.json`.
3. Fix the highest-impact issues in the codebase and re-run to verify improvements.
