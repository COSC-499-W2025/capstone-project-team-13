# Use Cases

1. Upload Work Artifacts
2. Extract Metadata from Artifacts
3. Categorize Artifacts by Type
4. Track Project Evolution Over Time
5. Generate Productivity Metrics
6. Visualize Work Portfolio
7. Generate Résumé Highlights
8. Export Résumé
9. Manage Data Privacy and Permissions
10. Identify Skill Trends
11. Build and Customize a Résumé
12. Prepare for Interviews

---

## Use Case 1: Upload Work Artifacts
**Primary actor:** User  
**Description:** The user uploads a file or ZIP archive through the web interface to have it scanned and analyzed.  
**Precondition:** The user has granted file access consent.  
**Postcondition:** The artifact is scanned, classified, and stored in the system for analysis.

**Main Scenario:**
1. User navigates to the Upload page
2. User drags and drops a file or clicks to browse
3. System detects project type (code, text, or media) from file content
4. System scans and extracts metadata, languages, skills, and metrics
5. Project is stored and appears in the user's Projects list

**Extensions:**
1. Duplicate detected by path or content hash → system notifies user, skips re-upload
2. No supported files found → system returns a skipped status with explanation
3. User not logged in → system offers guest analysis mode (results not saved)
4. File access consent not granted → system blocks upload and prompts user to grant consent

---

## Use Case 2: Extract Metadata from Artifacts
**Primary actor:** System  
**Description:** After upload, the system extracts metadata and project characteristics from the artifact.  
**Precondition:** A file or ZIP has been successfully uploaded.  
**Postcondition:** Metadata is stored and linked to the project record.

**Main Scenario:**
1. System processes the uploaded file
2. System extracts file count, size, languages, frameworks, skills, LOC, and date ranges
3. System calculates an importance score based on extracted metrics
4. Metadata is stored in the database and displayed on the project page

**Extensions:**
1. AI consent granted → system additionally generates an AI description and tech stack summary via Gemini
2. Git repository detected → system extracts contributor information and commit history

---

## Use Case 3: Categorize Artifacts by Type
**Primary actor:** System  
**Description:** The system classifies uploaded artifacts into one of three project types: code, text, or media.  
**Precondition:** File upload is complete.  
**Postcondition:** The project is tagged with a type and routed to the appropriate scanner.

**Main Scenario:**
1. System checks file extensions and content signatures
2. System assigns type: code, text, or media
3. Appropriate scanner is invoked (coding, text document, or media scanner)
4. For ZIP archives containing mixed content, system uses majority type detection

**Extensions:**
1. Mixed content detected → system defaults to code scanner
2. Unrecognized content → system falls back to code scanner so a project entry is still created

---

## Use Case 4: Track Project Evolution Over Time
**Primary actor:** User  
**Description:** The user views a timeline of their projects and skills showing progression over time.  
**Precondition:** At least one project with date metadata exists.  
**Postcondition:** A timeline or heatmap view is displayed.

**Main Scenario:**
1. User navigates to the Portfolio or Skills page
2. System maps projects and skills by creation and modification dates
3. User views the activity heatmap (daily activity across a year) and skills timeline (first/last seen per skill)

**Extensions:**
1. User navigates between years on the heatmap using prev/next controls
2. User filters the skills timeline by minimum project count

---

## Use Case 5: Generate Productivity Metrics
**Primary actor:** System  
**Description:** The system calculates work statistics and skill analytics from the user's projects.  
**Precondition:** At least one project exists.  
**Postcondition:** Metrics are displayed on the Dashboard and Skills pages.

**Main Scenario:**
1. User navigates to the Dashboard or Skills page
2. System calculates total projects, total skills, and skill diversity score
3. System identifies top skills, most common skill pairs (co-occurrence), and project type distribution
4. Metrics are displayed as stat cards and visualizations

**Extensions:**
1. User navigates to the Analytics page for deeper skill co-occurrence analysis

---

## Use Case 6: Visualize Work Portfolio
**Primary actor:** User  
**Description:** The system generates a portfolio view of the user's projects with stats, rankings, and showcase options.  
**Precondition:** At least one project exists.  
**Postcondition:** Portfolio is displayed and optionally made public.

**Main Scenario:**
1. User navigates to the Portfolio page
2. System loads stored portfolio or regenerates from current project data
3. User views top projects, stats, summary text, and all projects sorted by importance score
4. User can toggle between private and public portfolio visibility

**Extensions:**
1. User edits project fields inline (description, role, featured status, hidden status)
2. User navigates to Web Showcase to view top 3 projects with evolution timelines
3. Other users can browse public portfolios at `/public-portfolios`

---

## Use Case 7: Generate Résumé Highlights
**Primary actor:** User  
**Description:** The system generates résumé-friendly bullet points from a project's analyzed content.  
**Precondition:** The project has been scanned and the user is authenticated.  
**Postcondition:** Bullet points are stored and associated with the project and resume.

**Main Scenario:**
1. User navigates to the Résumé Builder page
2. User selects a project and clicks generate
3. System produces bullet points from project metadata using rule-based generation
4. User reviews bullets and optionally triggers AI enhancement via Gemini

**Extensions:**
1. AI consent granted → user can use AI-generate or AI-enhance for higher quality bullets
2. User edits bullets inline and saves manually
3. User views ATS score for the generated bullets

---

## Use Case 8: Export Résumé
**Primary actor:** User  
**Description:** The user exports their assembled résumé as a PDF or DOCX file.  
**Precondition:** A résumé exists with at least some content.  
**Postcondition:** A formatted résumé file is downloaded by the user.

**Main Scenario:**
1. User assembles résumé with projects, education, work history, and skills
2. User clicks Download PDF or Download DOCX
3. System saves the current résumé state (including section order and labels) to the database
4. System generates and streams the file to the user

**Extensions:**
1. User checks the live page count before downloading to ensure the résumé fits one page
2. User reorders sections via drag-and-drop before exporting

---

## Use Case 9: Manage Data Privacy and Permissions
**Primary actor:** User  
**Description:** The user configures consent settings and controls what data is stored and analyzed.  
**Precondition:** User is on the Upload page or Settings page.  
**Postcondition:** Privacy preferences are applied to future scans and analyses.

**Main Scenario:**
1. User opens consent controls (Upload page sidebar or Settings)
2. User grants or revokes file access consent and AI consent independently
3. System respects preferences — file upload blocked without basic consent, AI features blocked without AI consent
4. User can configure excluded folders, excluded file types, and anonymous mode in Settings

**Extensions:**
1. User deletes individual projects, AI insights, or cached analysis data from the Deletion Manager
2. User revokes AI consent → AI features are disabled but existing data is retained

---

## Use Case 10: Identify Skill Trends
**Primary actor:** System  
**Description:** The system detects frequently used tools and languages across the user's project history and displays trends.  
**Precondition:** At least one project with extracted skills exists.  
**Postcondition:** Skill trends and co-occurrence data are displayed.

**Main Scenario:**
1. User navigates to the Skills page
2. System aggregates skills across all projects, ranked by frequency
3. User views skill co-occurrence pairs, diversity score, and top skills
4. User clicks a skill to see which projects use it

**Extensions:**
1. User navigates to the Skills Timeline to see first/last seen dates per skill
2. User filters the timeline by skill name or minimum project count

---

## Use Case 11: Build and Customize a Résumé
**Primary actor:** User  
**Description:** The user creates and manages named résumés, customizing content, layout, and section order.  
**Precondition:** User is authenticated.  
**Postcondition:** A saved résumé exists with user-defined structure and content.

**Main Scenario:**
1. User creates a new résumé or selects an existing one from the list
2. User adds project bullets, education entries, work history, and skills
3. User reorders sections via drag-and-drop
4. User renames section labels inline
5. User saves the résumé — system persists section order and labels to the database

**Extensions:**
1. User duplicates an existing résumé to create a variation
2. User renames or deletes a résumé (last résumé cannot be deleted)
3. System warns user of unsaved changes before navigating away (dirty state check)

---

## Use Case 12: Prepare for Interviews
**Primary actor:** User  
**Description:** The system generates personalized STAR-format behavioral interview answers from the user's projects.  
**Precondition:** User is authenticated and has at least one project.  
**Postcondition:** A set of STAR answers is generated and displayed.

**Main Scenario:**
1. User navigates to the Interview Prep page
2. User selects a target role from a predefined list or enters a custom role
3. User selects which projects to draw from
4. System sends project summaries to Gemini and receives 4 STAR-format answers covering key behavioral themes
5. User reviews answers in an expandable accordion view

**Extensions:**
1. User copies an answer to clipboard with one click
2. User regenerates answers with a different role or project selection
