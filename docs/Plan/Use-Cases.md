# Use Cases

1. Scan Device for Work Artifacts
2. Extract Metadata from Artifacts
3. Categorize Artifacts by Type
4. Track Project Evolution Over Time
5. Generate Productivity Metrics
6. Visualize Work Portfolio
7. Generate Résumé Highlights / Summary
8. Export Portfolio or Dashboard
9. Manage Data Privacy and Permissions
10. Identify Skill Trends

## Use Case 1: Scan Device for Work Artifacts
**Primary actor:** User \
**Description:** The user initiates a scan of their computer to automatically detect files, repositories, and media artifacts relevant to their work.\
**Precondition:** The system has access permissions to scan the device.\
**Postcondition:** A set of detected artifacts is stored in the system for analysis.

**Main Scenario:**
1. User selects “Scan Device” option
2. System requests permission for directories to scan
3. User confirms scan scope (e.g., whole computer, selected drives, or specific folders)
4. System searches for eligible artifacts (documents, code, media, etc.)
5. System lists detected artifacts
6. User reviews and confirms which artifacts to include in the analysis


**Extensions:**
1. Scan interrupted → system notifies user and allows resume.
2. No artifacts found → system suggests expanding scan scope.
3. User deselects certain folders → system excludes them from future scans.

## Use Case 2: Extract Metadata from Artifacts
**Primary actor:** System\
**Description:** After scanning, the system extracts metadata (timestamps, file types, file size, edit history, and related tools).\
**Precondition:** Artifacts have been scanned and selected by the user.\
**Postcondition:** Metadata is stored and linked to each artifact.

**Main Scenario:**
1. System processes detected artifacts
2. System extracts available metadata
3. Metadata is stored in the database


**Extensions:**
1. Some metadata is inaccessible due to permissions → notify user.

## Use Case 3: Categorize Artifacts by Type
**Primary actor:** System\
**Description:** The system classifies scanned artifacts into categories such as programming code, written documents, or media files.\
**Precondition:** Metadata extraction is complete.\
**Postcondition:** Each artifact is tagged with a category.\

**Main Scenario:**
1. System checks file extension and content signatures
2. Artifacts are grouped by category


**Extensions:**
1. Unrecognized file type → system asks user to classify manually.

## Use Case 4: Track Project Evolution Over Time
**Primary actor:** User\
**Description:** The system organizes scanned artifacts into a timeline view, showing progression and evolution of work.\
**Precondition:** Scanned artifacts and metadata are available.\
**Postcondition:** A project timeline is displayed.\

**Main Scenario:**
1. User clicks “View Project Evolution”
2. System maps artifacts by creation and modification dates
3. Timeline is displayed


**Extensions:**
1. User filters by artifact type or folder.

## Use Case 5: Generate Productivity Metrics
**Primary actor:** System\
**Description:** The system calculates work statistics from scanned artifacts.\
**Precondition:** Artifacts and metadata exist.
**Postcondition:** Productivity metrics are generated.

**Main Scenario:**


1. User selects “Productivity Metrics”
2. System analyzes frequency, number of edits, lines of code, and volume of work
3. Metrics displayed as charts and numbers


**Extensions:**
1. User applies filters for date range, file type, or specific folders.

## Use Case 6: Visualize Work Portfolio
**Primary actor:** User\
**Description:** The system generates a dashboard view of scanned artifacts, categorized projects, and metrics.\
**Precondition:** Scanned data is available.\
**Postcondition:** Dashboard displayed.\

**Main Scenario:**


1. User navigates to “Dashboard”
2. System loads portfolio visualization (projects, highlights, metrics)


**Extensions:**
1. User customizes dashboard design.

## Use Case 7: Generate Résumé Highlights
**Primary actor:** User\
**Description:** The system generates résumé-friendly highlights from scanned artifacts.\
**Precondition:** Projects and artifacts have been scanned.\
**Postcondition:** A set of résumé-ready points are created.

**Main Scenario:**
1. User clicks “Résumé Highlights”
2. System extracts key skills, project outcomes, and impact
3. Summary displayed for user to copy or edit


**Extensions:**
1. User manually edits suggested points. (?)

## Use Case 8: Export Portfolio or Dashboard
**Primary actor:** User\
**Description:** User exports the scanned analysis results in a chosen format.\
**Precondition:** Dashboard or portfolio view exists.\
**Postcondition:** Exported file (PDF/HTML/link) created.\
**Main Scenario:**
1. User clicks “Export Portfolio”
2. System generates chosen export format
3. Exported file or link is provided


**Extensions:**
1. Large export → system recommends limiting scope.

## Use Case 9: Manage Data Privacy and Permissions
**Primary actor:** User\
**Description:** The user configures what data is included in scans and how much detail is stored.\
**Precondition:** Scanning system is active.\
**Postcondition:** Privacy preferences applied.

**Main Scenario:**
1. User opens “Privacy Settings”
2. User excludes folders, file types, or metadata fields
3. System respects preferences in future scans


**Extensions:**
1. User switches to “Anonymous Mode” → only aggregated data stored. (?)

## Use Case 10: Identify Skill Trends
**Primary actor:** System\
**Description:** The system detects frequently used tools, languages, or file types across scanned history.\
**Precondition:** Metadata extracted.\
**Postcondition:** A report of skill trends generated.\

**Main Scenario:**
1. User clicks “Skill Trends”
2. System analyzes artifacts for patterns (e.g., programming languages used)
3. System generates trend visualization


**Extensions:**
1. User filters by time period.