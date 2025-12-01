# Team Logs

## Weeks 3 - Sept 15-21, 2025
The features included in this milestone were to work together as a group, setting up necessary documentation such as google drive folder, setting up our capstone repository to work on our individual and team logs, working on our project requirements, and creating a project backlog within our repository. Due to the early stages of the project, the rest is unable to be done at the moment. 


Usernames -> Names

JacksonWilson99 -> Jackson Wilson
MayaKnu7 -> Maya Knutsvig
T’Olu Akinwande -> T’Olu Akinwande 
illinai -> Illina Islam
prinamehta -> Prina Mehta
sshah-git -> Sana Shah

## Project board
![alt text](teamLogImages/Week1TeamLog.png)

## Week 4 - Sept 22-28, 2025
The features for this week’s milestone was to revisit our project requirements, and construct our software architecture diagram. Collectively, each of our team members contributed to refining the requirements for our project, as well as discussing and suggesting ideas for the different components in our system architecture diagram. Additionally, our team worked on our project proposal/project plan document, in which we specified our tech stack, functional requirements, and assigned tasks to each of our team members. 


## Week 5 - Sept 29 - Oct 5, 2025
T'olu Akinwande - DFD level 0, Sept 29 - Oct 5

Jackson Wilson - DFD Level 0, Sept 29 - Oct 5

Maya Knutsvig - DFD Level 0, Sept 29 - Oct 5

Prina Mehta - - DFD Level 1, Sept 29 - Oct 5

Illina Islam - DFD Level 1, Sept 29 - Oct 5

Sana Shah - DFD Level 1, Sept 29 - Oct 5


This week, our team revisited the project requirements and worked on developing our Data Flow Diagram (DFD) as part of clarifying the system design. We collaborated on refining the components, discussing how data, processes, and flows would be represented in the diagram. 

## Week 6 - Oct 6 - Oct 12, 2025

GitHub Usernames:

JacksonWilson99 -> Jackson Wilson, 
MayaKnu7 -> Maya Knutsvig, 
T’Olu Akinwande -> T’Olu Akinwande , 
illinai -> Illina Islam, 
prinamehta -> Prina Mehta, 
sshah-git -> Sana Shah

This week, our team revised and made changes to our system architecture diagram, and data flow diagrams, reflecting the finalized project requirements. We also divided up the first few functions of our backend that we needed to implement, and assigned them to each of our team members, as well as updated our github repository. Some functions that our team started developing are checking file formats, distinguishing individual projects from collaborative projects, adding permissions to collect and analyze the users data, as well as permissions to use external services for analysis. Our team also worked on developing a “testConsole” skeleton to test our functions.



Project Board: ![alt text](teamLogImages/week6ProjectBoard.png)


## Week 7 Team Log  
**Date Range:** Oct 13 – Oct 19, 2025  

| Team Member | Work Completed / Focus This Week | Related Issue # |
|--------------|----------------------------------|-----------------|
| **T’Olu Akinwande** | Developed and tested the `extrapolate_individual_contributions()` function to estimate member contribution percentages across parsed projects (issue #16). Also revised the `projectCollabType` function (issue #14) to replace dummy data with real metadata fields and reviewed PRs for alignment and code consistency. | #14, #16 |
| **Prina Mehta** | Implemented file-path input and parsing pipeline so the system automatically reads and processes CSV, JSON, TXT, PY, and ZIP formats. Enhanced directory-crawler logic for multi-file projects. | #2 |
| **Maya Knutsvig** | Completed framework/language identifier module to detect project type based on codebase structure (e.g., Python vs web). Integrated detection with the file-parser output. | #8 |
| **Jackson Wilson** | Built RAKE-based keyword extraction system for text files to summarize important phrases and skills. Updated `testConsole.py` for manual testing and added sample data for validation. | #52 |
| **Illina Islam** | Implemented `projects` database schema for storing project and metadata entries using SQLAlchemy. Updated `README.md` and began connecting database to processing pipeline. | #13 |
| **Sana Shah** | Created `visualMediaAnalyzer` function to scan media files and infer which design software was used, mapping outputs to associated skills. Initial implementation complete (no AI integration yet). | #54 |

---
<img width="1462" height="852" alt="Screenshot 2025-10-19 205419" src="https://github.com/user-attachments/assets/d98ae752-02aa-4347-984c-954a4af6b2f0" />



Burnup Chart:
<img width="995" height="498" alt="image" src="https://github.com/user-attachments/assets/ef5a91f6-1bc3-49d8-b720-de6990ccd191" />

In-Progress Tasks: 
<img width="1127" height="257" alt="image" src="https://github.com/user-attachments/assets/14c5c78f-d28a-47e1-80a6-70f37c317271" />

Completed Tasks:
<img width="917" height="487" alt="image" src="https://github.com/user-attachments/assets/8e3033f9-0273-4aef-bd17-a799e1500490" />



# Test Report
All tests were written in Python and executed successfully.  
Unit tests were created for each major function (e.g., `extrapolate_individual_contributions()`, `fileParser`, `projectCollabType`).  
Manual testing through `testConsole.py` also confirmed that all modules work as expected with sample project data.
<img width="781" height="783" alt="image" src="https://github.com/user-attachments/assets/b0aadf72-3a1f-48f4-92ff-33b0ad365587" />


### Reflection Points
**What went well:**  
- The new modular approach helped integrate multiple features smoothly.  
- Each member worked independently on key components that connected successfully during testing.  
- Collaboration during PR reviews improved overall code consistency.  

**What didn’t go as planned:**  
- Merge conflicts across multiple branches slowed integration.  
- The database still isn’t fully connected to other system components.  
- Some manual testing processes (like the console dashboard) remain time-intensive.




  

## Week 12 Team Log  

Project Board:<img width="1516" height="795" alt="image" src="https://github.com/user-attachments/assets/820105d0-7cf4-4fe4-9184-6ddf35ec8949" />

**Date Range:** Nov 23 - Nov 30, 2025  
**Team Member** | **Work Completed / Focus This Week** | **Related Issue #** |
|------------------|--------------------------------------|---------------------|
| **T’Olu Akinwande** | Improved Git-based collaboration detection and integrated fixes into ProjectCollabType. Developed the new **AI Project Ranking** feature, added scoring logic, semantic/skill-based evaluation, and created a full test suite and clean PR. | #14, #114 |
| **Prina Mehta** | Worked on the **deletion module**, adding safe deletion of AI-generated insights, shared-file detection, protection rules, and clearer warnings/previews. Also prepared for next week’s Milestone 1 presentation. | #25 |
| **Maya Knutsvig** | Added **textDocumentScanner** and **visualMediaAnalyzer** to `main.py` (they were previously unused). Updated scanners to use file-format and file-data checking for more reliable processing. |  |
| **Jackson Wilson** | Developed **code efficiency analysis** (time/space complexity grading). Added project-sorting to main and included missing dependencies in `requirements.txt`. |  |
| **Illina Islam** | Improved resume-bullet generation functions and built the new submenu for resume item generation, refining formatting and usability. | #22, #112, #166 |
| **Sana Shah** | Built the **AI media-project analyzer** for design/media files and integrated early logic for skill inference from visual artifacts. | #140 |




Burnup Chart:
<img width="764" height="398" alt="image" src="https://github.com/user-attachments/assets/abb42186-d341-4094-a3db-3b1406e6ff0f" />



In-Progress Tasks: 
<img width="825" height="144" alt="image" src="https://github.com/user-attachments/assets/12b73c94-5dc3-4e9e-9406-71e1751513dd" />


Completed Tasks:
<img width="831" height="665" alt="image" src="https://github.com/user-attachments/assets/d2cadccd-3015-4cc3-91e7-1d8273b8818c" />
<img width="838" height="590" alt="image" src="https://github.com/user-attachments/assets/4ee354a9-f490-4966-aac8-96e06a9e8478" />


#Test Report 

271 our of 274 test cases throughtout the project are functioning successfully. The 3 test cases with errors are currently undergoing refacroring and will continue to be worked on in the upcoming week. Other than those 3, everything else is being tested accurately and efficiently.

<img width="1214" height="624" alt="image" src="https://github.com/user-attachments/assets/d833433e-03ca-4b39-84e5-01ef51a95826" />



# Reflection Points
# What went well:

-New features such as the AI Project Ranking system, improved media analysis, resume-bullet generation updates, and the deletion safety module all integrated smoothly into the existing workflow.
-Unit tests and manual testing confirmed strong reliability across modules, and team communication during PR reviews helped maintain consistency.

# What didn’t go as planned:

-A few merge conflicts came up while integrating multiple new components, but they were resolved quickly.
-Some modules required extra manual testing time due to new AI-related setup steps, but everything was stabilized by the end of the week.











