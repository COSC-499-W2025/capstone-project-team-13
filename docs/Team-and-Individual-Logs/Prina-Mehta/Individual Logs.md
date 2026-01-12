## Log 1:
## Date Range: Weeks 3 - Sept 15-21, 2025

## ![week 1 features](week1tasks.png)

## Recap on your week's goals

During this period, our team discussed and refined the functional and non-functional requirements for the project. My personal focus was on researching similar projects online to better understand common requirements and best practices that could be relevant to our work. This helped me think critically about what features might be necessary and what constraints we should consider. My goals for the week were mainly to contribute to shaping our requirements document and ensure I had enough context to give meaningful input. 

## Log 2:
## Date Range: Week 4 - Sept 22-28, 2025

## ![week 1 features](week2tasks.jpg)

## Recap on your week's goals

This week, I worked closely with my team on building the system architecture and developing the project proposal. My main contributions included identifying and listing all the use cases for our system, as well as creating the workload distribution table to ensure tasks were divided fairly and efficiently among team members. I also took part in every team meeting, where I actively contributed to discussions, shared ideas, and provided feedback.

## Log 3:
## Date Range: Week 5 - Sept 29-Oct 5, 2025

## ![week 1 features](week3tasks.jpg)

## Recap on your week's goals

This week, I helped design the Data Flow Diagram by creating the processes and mapping out how data moves between them. I worked on building the diagram in Figma, making sure it was clear, well-organized, and visually consistent with our project standards.

## Log 4:
## Date Range: Week 5 - Oct 5 - Oct 12, 2025

## ![week 1 features](week4tasks.jpg)

## Recap on your week's goals

This week, I updated the Kanban board and, together with Maya, assigned tasks to everyone in the group. I also attended the team meeting on Monday. On the development side, I added a zip file handler and created as well as reviewed and approved pull requests on GitHub. I also researched which frameworks would be best suited for our project.

## Log 5:
## Date Range: Week 5 - Oct 13 - Oct 19, 2025

## ![week 1 features](week5tasks.png)

## Recap on your week's goals

This week, I worked on issue #2 on the Kanban board. I focused on building the feature that prompts users to enter a file path and then processes the file based on its format. The system can now handle multiple file types including `.csv`, `.json`, `.txt`, `.py`, and `.zip`. It also automatically performs the correct parsing or reading operations for each. Additionally, I implemented detailed error handling to manage invalid inputs and potential edge cases, along with unit tests to verify that the feature behaves reliably across scenarios. For next week, I plan to implement functionality for storing user configurations and start analyzing project files to extract useful insights and support upcoming features.

## Log 6:
## Date Range: Week 6 - Oct 20 - Oct 26, 2025

## ![week 1 features](week6tasks.png)

## Recap on your week's goals

### What I Worked On This Week
This week, I completed a major database refactor. I expanded the Project model with 15+ new fields (importance scoring, featured flags, skills/tags, user customization), enhanced the File and Contributor models with additional metadata and contribution tracking, and introduced a new Keyword model for skill extraction. I also added thorough test coverage for all changes.

### Plan for Next Week
Next week, I will research AI/LLM integration opportunities for our system, focusing on how we can use AI-driven analysis in our artifact mining workflow while preserving user privacy and consent.

## Log 7:
## Date Range: Week 7 - Oct 27 - Nov 2, 2025

## ![week 1 features](week7tasks.png)

## Recap on your week's goals

### What I Worked On This Week
This week, I focused on implementing the basic AI integration for our system through the Google Gemini 2.5 Flash API, emphasizing cost optimization and performance monitoring. I successfully integrated rate limiting, response caching, cost tracking and usage monitoring features, along with a console dashboard for better visibility and management (https://github.com/COSC-499-W2025/capstone-project-team-13/issues/97). In addition, I developed a comprehensive test suite to ensure the reliability of the AI functionality. Alongside this, I rewrote the "main.py" file to implement a more complete project analysis pipeline - adding consent checks, file format validation, project duplication handling, database integration, and dynamic routing to analyzers based on content type (code, text, or media). This overhaul was aimed at improving the overall user experience and laying a stronger foundation for future AI-driven features (https://github.com/COSC-499-W2025/capstone-project-team-13/issues/110).

### Plan for Next Week
Next week, my goal is to build upon the current AI foundation and implement AI-generated project descriptions and enhance the existing "summarizeProjects.py" (https://github.com/COSC-499-W2025/capstone-project-team-13/issues/111). On the content generation side, I will work on developing professional project descriptions, resume bullet points, and skill highlight summaries using template-based prompt engineering for consistency (https://github.com/COSC-499-W2025/capstone-project-team-13/issues/112).    

## Log 8:
## Date Range: Week 8 - Nov 3 - Nov 9, 2025

## ![week 1 features](week8tasks.png)

## Recap on your week's goals

### What I Worked On This Week
This week, I worked on issues https://github.com/COSC-499-W2025/capstone-project-team-13/issues/111, https://github.com/COSC-499-W2025/capstone-project-team-13/issues/112, https://github.com/COSC-499-W2025/capstone-project-team-13/issues/113. I focused on building the complete AI analysis infrastructure. I implemented the ai_project_analyzer — a module capable of conducting technical project evaluations by detecting OOP principles, design patterns, algorithmic complexity, and data structures. This analyzer also identifies demonstrable skills and supports batch processing with smart caching to minimize API costs. To ensure robustness, I developed a comprehensive test suite with detailed test cases covering skill extraction, OOP detection, caching, and error handling. I also extended the database schema to support AI-generated analysis data by adding new fields.

Overall, this week was about laying down the backbone for intelligent project analysis and ensuring the system performs reliably under real workloads.

### Plan for Next Week
Next week, I plan to begin work on issue https://github.com/COSC-499-W2025/capstone-project-team-13/issues/114 — AI-assisted project ranking, along with whichever tasks the team prioritizes following our next meeting.   

## Log 9:
## Date Range: Week 9 - Nov 17 - Nov 23, 2025

## ![week 1 features](week9tasks.png)

## Recap on your week's goals

### What I Worked On This Week
This week, I focused on expanding our system’s ability to manage and persist user-specific configurations (issue https://github.com/COSC-499-W2025/capstone-project-team-13/issues/13). I added full functionality to store consent tracking, privacy settings, scanning preferences, AI configuration, analysis toggles, output preferences. 

### Plan for Next Week
Next week, I plan to ensure that the end-to-end user flow works smoothly and that the system behaves as intended across all major steps. Alongside that, I will take on any additional tasks the team decides to prioritize during our meeting.

## Log 10:
## Date Range: Week 10 - Nov 24 - Nov 30, 2025

## ![week 1 features](week10tasks.png)

## Recap on your week's goals

### What I Worked On This Week
This week, I worked on the deletion module(issue https://github.com/COSC-499-W2025/capstone-project-team-13/issues/25). Specifically, I implemented safe deletion features for AI-generated insights, added automatic detection for files used across multiple projects, and set up default protection for shared files with an option to force-delete when needed. I also added clearer warnings and previews to help users understand what will be removed. Alongside this, I spent time preparing for our Milestone 1 presentation next week.

### Plan for Next Week
Next week, I am planning to do some refactoring and take on whatever other tasks the team prioritizes during our meeting.


## Log 11:
## Date Range: Week 11 - Dec 1 - Dec 7, 2025

## ![week 1 features](week10tasks.png)

## Recap on your week's goals

### What I Worked On This Week
The AI analysis option was constantly returning an “AI quota exceeded” error even when that was not true. I fixed this issue, and the system now correctly returns detailed-analysis for coding projects instead of failing with a false quota error.

### Plan for Next Week
After the break, I will work on whatever the team


## Log 12:
## Date Range: Term 2 Week 1 - Jan 5 - Jan 11, 2026

## ![week 1 features](T2week1tasks.png)

## Recap on your week's goals

### What I Worked On This Week
I did not make any meaningful progress toward the project over the Christmas break.

### Plan for Next Week
Next week, I plan to fix the user configuration handling. Although the config file and integration file exist and user preferences are stored in the database, the system still prompts for user permission every time. I’ll focus on correcting this behavior so stored configurations are properly respected.
I’ll also begin working on the requirement to recognize duplicate files and ensure that only a single instance is maintained in the system.
