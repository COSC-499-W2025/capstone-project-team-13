# Functional Requirements

## 1. Project Upload and File Discovery
- The system shall allow users to upload files and ZIP archives through a web interface
- The system shall support code files, documents, images, and media files across common extensions
- The system shall automatically detect project type (code, text, or media) from uploaded content
- The system shall detect and reject duplicate uploads using path matching and content hashing
- The system shall support incremental uploads — adding new files to an existing project
- The system shall provide a guest mode allowing file analysis without an account (results not saved)

## 2. Metadata Extraction and Classification
- The system shall extract file metadata including size, file count, languages, frameworks, and date ranges
- The system shall automatically classify projects by type: code, text, or media
- The system shall identify programming languages and frameworks from code projects
- The system shall extract skills and tools from project content using keyword extraction (NLTK/RAKE)
- The system shall extract contributor information from Git repositories
- The system shall calculate an importance score for each project based on extracted metrics

## 3. Content Analysis and Intelligence
- The system shall analyze projects using non-AI methods by default (language detection, keyword extraction, LOC counting)
- The system shall support optional AI-powered analysis via Google Gemini when the user grants AI consent
- The system shall generate AI descriptions, tech stack summaries, and role suggestions per project
- The system shall detect duplicate file content across projects and flag shared files
- The system shall organize projects into a portfolio with stats, summaries, and rankings

## 4. User Dashboard and Visualization
- The system shall provide a central dashboard showing project count, skill count, and top projects
- The system shall display a skill co-occurrence graph and diversity score across projects
- The system shall display an activity heatmap showing project activity by date
- The system shall display a skills timeline showing when each skill was first and last used
- The system shall provide a web showcase view of the user's top 3 projects by importance score
- The system shall support public portfolio sharing with an opt-in visibility toggle

## 5. Resume Generation and Export
- The system shall allow users to create and manage multiple named resumes
- The system shall generate resume bullet points for each project using rule-based or AI methods
- The system shall allow users to edit, regenerate, and reorder resume bullets inline
- The system shall support drag-and-drop reordering of resume sections
- The system shall integrate education entries, work history, and skills into the resume
- The system shall calculate ATS scores for resume bullet points
- The system shall export resumes as PDF or DOCX, respecting user-defined section order and labels
- The system shall provide a live page count estimate during resume editing
- The system shall gate saving behind a dirty-state check to prevent accidental data loss

## 6. Portfolio and Project Customization
- The system shall allow users to add custom descriptions, thumbnails, and role labels to projects
- The system shall allow users to mark projects as featured or hidden
- The system shall allow users to add manual evidence to projects: metrics, feedback, and achievements
- The system shall support auto-extraction of evidence from project files
- The system shall allow inline editing of portfolio project fields

## 7. Interview Preparation
- The system shall generate STAR-format behavioral interview answers from the user's projects
- The system shall allow users to select a target role and choose which projects to draw from
- The system shall support custom role input beyond the predefined role list
- The system shall allow users to copy generated answers to clipboard

## 8. Privacy, Security, and Access Control
- The system shall require explicit user consent before scanning or storing file content
- The system shall require explicit AI consent before sending content to external AI services
- The system shall support configurable privacy settings including excluded folders, excluded file types, and anonymous mode
- The system shall enforce JWT-based authentication with 30-day token expiry
- The system shall enforce ownership checks on all user data — unauthorized access returns 403
- The system shall support guest access for project analysis without account creation
- The system shall allow users to delete projects, AI insights, and cached analysis data independently
