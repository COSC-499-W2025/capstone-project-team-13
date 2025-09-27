# Project Task Assignments

There are 15 tasks in total, with subgroups of two people working on each task together, so each person works on 5 tasks.

| Requirement | Description | Test Cases | Who | H/M/E |
|-------------|-------------|------------|-----|-------|
| **Device Scanning** | System scans the user's device for artifacts (files, repos, media). User must approve scan permissions. | • Positive: Start scan → system lists detected files<br>• Positive: User limits scan to folder → only that folder scanned<br>• Negative: User denies permission → system blocks scan and displays error | Prina | Hard |
| **Keyword-based Scanning** | Scanner searches device for artifacts based on user-provided keywords. | • Positive: Search for "project" → returns all files with matching metadata<br>• Negative: Enter empty keyword → system displays validation error | Tolu<br>Illina | Medium |
| **File Size Threshold Scanning** | Scanner filters files above or below a given size. | • Positive: User sets >1MB filter → only large files included<br>• Negative: User enters invalid threshold (e.g., text input) → system rejects input | Maya<br>Prina | Easy |
| **Categorize Artifacts by Type** | System classifies scanned files (code, document, media, design sketch). | • Positive: .py → Code, .jpg → Media<br>• Negative: Unknown file extension → system asks user to categorize | Sana<br>Illina | Medium |
| **Extract Metadata** | Extracts metadata (author, modified date, usage frequency). | • Positive: File opened multiple times → time spent tracked<br>• Negative: Metadata unavailable → placeholder values inserted | Maya<br>Illina | Hard |
| **User Dashboard** | User views dashboard with summaries and filters. | • Positive: Dashboard loads weekly activity summary<br>• Positive: User filters by "Code" → only code artifacts shown<br>• Negative: Dashboard fails to load → system displays fallback message | Maya<br>Sana | Hard |
| **Organization by Content Similarity** | Group artifacts based on textual/code similarity. | • Positive: Similar design sketches grouped together<br>• Negative: No similarity detected → no grouping applied | Tolu<br>Illina | Hard |
| **Tagging by Predefined Groups** | System tags artifacts with default categories. | • Positive: System applies "Academic Project" tag<br>• Negative: Tagging rules conflict → user prompted to resolve | Tolu | Medium |
| **Duplicate File Detection** | Recognize and flag duplicate files. | • Positive: Identical files flagged<br>• Negative: False positive detection → user can mark "Not duplicate" | Sana | Medium |
| **Generate Productivity Metrics** | Provide stats on artifact creation frequency, types, and trends. | • Positive: Weekly summary shows correct counts<br>• Negative: Empty dataset → system shows "No data available" | Maya<br>Prina | Medium |
| **Visual Portfolio** | Visualize project history, graphs, and summaries. | • Positive: Graph displays evolution of code commits<br>• Negative: Graph fails to load → system shows backup text summary | Maya<br>Tolu | Medium |
| **Résumé Highlights** | System auto-generates résumé-friendly text from artifacts. | • Positive: Extracted skills and contributions displayed<br>• Negative: No artifacts available → system suggests manual input | Sana<br>Illina | Medium |
| **Export Portfolio/Dashboard** | Export artifacts or summaries to PDF/HTML. | • Positive: Export generates valid PDF<br>• Negative: File too large → system prompts to filter data | Sana<br>Tolu | Easy |
| **Privacy Management** | User configures permissions before scans. | • Positive: User hides folder → scanner skips it<br>• Negative: User revokes permission mid-scan → system cancels gracefully | Prina | Medium |
| **Skill Trend Analysis** | Detect tools/languages used most often over time. | • Positive: System correctly identifies Python dominance<br>• Negative: No trend detected → system displays "No trends found" | Prina | Medium |