# Logs

## Week 3 - Sept 15-21, 2025
<img width="1072" height="623" alt="Screenshot 2025-09-21 at 8 05 32 PM" src="https://github.com/user-attachments/assets/47e40adf-0d09-46cb-a923-c6f879e91522" />

* joined capstone repo
* contributed to functional and non-functional requirements in the document
* completed project requirement quiz
* only deliverables required for this week were regarding the requirement doc
* must complete project proposal and architecture diagram for next sprint 


## Week 4 - Sept 22-28, 2025
<img width="1091" height="633" alt="Screenshot 2025-09-28 at 11 11 21 AM" src="https://github.com/user-attachments/assets/aa3e9ba5-3113-42da-8da1-58a38bedd390" />

* worked on system architecture diagram
* contributed to functional requirements section of project proposal
* completed project proposal and system architecture diagram quiz
* created md files for project proposal
* team's work was well distributed
* so far no issues were faced
* must complete DFD diagram for next week


## Week 5 - Sept 29-Oct 5, 2025
<img width="1071" height="542" alt="Screenshot 2025-10-05 at 11 40 31 PM" src="https://github.com/user-attachments/assets/1d179afe-21a9-4c7d-bc18-7be53d4ce00c" />

* worked on dfd level 1 with Sana and Prina
* completed dfd survey
* there was not a lot of deliverables for this week, so everything went smooth
* no issues were faced this week
* must complete and finalize these for next week: system architecture diagram, dfds, wbs, README file, explainations for everything, set up of environment  


## Week 6 - Oct 6-Oct 12, 2025
<img width="1067" height="620" alt="Screenshot 2025-10-12 at 7 38 05 PM" src="https://github.com/user-attachments/assets/cdf70b96-d63b-4b2b-81ce-a470a6db5947" />

* worked on revising dfd with T'olu
* created code and pr for getting user's consent and storing user's answer
* worked on WBS
* team work was great this week, everything was distributed evenly
* no issues were faced this week
* for next week: continue project work, weekly logs, quiz 1


## Week 7 - Oct 13-Oct 19, 2025
<img width="1068" height="621" alt="Screenshot 2025-10-19 at 3 08 14 PM" src="https://github.com/user-attachments/assets/256a67cc-fa96-430c-a347-dfacc9d95af4" />

* completed quiz 1 in class
* had a team meeting on Wednesday
* researched on database implementation for our project
* worked on creating a rough database 1 according to our project proposal
  * Database 1 is for storing projects and raw project data
* updated the README file according to our current progress and plan
* no issures were faced this week
* for next: meet with team to discuss our project and contributions, plan out Database 2, upgrade Database 1 according to team's decisions, weekly logs
  * Database 2 should store project analyses


## Week 8 - Oct 20-Oct 26, 2025
<img width="1070" height="542" alt="Screenshot 2025-10-26 at 9 27 42 PM" src="https://github.com/user-attachments/assets/9d0621df-05ad-47b7-92f6-3cb4269cc7e4" />

* had our first check-in with the TA
* had a team meeting on Wednesday
* worked on codingProjectScanner.py + test_codingProjectScanner.py
  * this function deals with code projects specifically and extracts, analyzes, and stores data into the database
* added to testConsole for manually testing codingProjectScanner
* updated README.md as well
* no issues were faced this week
* for next week: meet with the team and discuss our contributions so far, create scanners for media projects and text projects


## Week 9 - Oct 27-Nov 2, 2025
<img width="1070" height="542" alt="Screenshot 2025-10-26 at 9 27 42 PM" src="https://github.com/user-attachments/assets/9d0621df-05ad-47b7-92f6-3cb4269cc7e4" />

* had our second check-in with the TA
* had a team meeting on Wednesday
  * As a team we established a pipline to follow, as we are almost at the part of connecting everything together (Special thanks to Maya for designing majority of the pipeline)
* worked on mediaProjectScanner.py + test_mediaProjectScanner.py
  * this fuction deals with visual/media projects specifically and extracts, analyzes, and stores data into the database
* updated visualMediaAnalyzer.py + test_visualMediaAnalyzer.py
  * this update allow visual Media Analyzer to handle more media types
  * this update also tests for more cases
* no issues were faced this week
* for next week: meet with team and disscuss our contributions so far, maybe update fileFormatCheck.py to check for more file types, start working the front-end portion (from the command line)


## Week 10 - Nov 3-Nov 9, 2025
<img width="1068" height="545" alt="Screenshot 2025-11-09 at 4 19 28 PM" src="https://github.com/user-attachments/assets/64d44e3a-9111-491e-9879-26178c988ff6" />

* had our third check-in with the TA
* had a team meeting on Wednesday
* updated config.py to allow more file formats
  * this lets fileFormatCheck.py allow more media file types
* no issues were face this week
* for week 12: meet with team and disscuss our contributions so far and decide on what to contribute to moving forward


## Week 12 - Nov 17-Nov 23, 2025
<img width="1069" height="534" alt="Screenshot 2025-11-23 at 12 54 57 PM" src="https://github.com/user-attachments/assets/6a856f92-8ae9-4956-b948-bc6e714d04c4" />

* missed our fourth check-in with the TA
* created resumeBulletGenerator.py + test_resumeBulletGenerator.py
  * resumeBulletGenerator.py generates resume components for all project types
  * resumeBulletGenerator.py creates a header containing the project title and skills
  * resumeBulletGenerator.py also produces 2/3 bullet point describing the project and the user's contributions
  * test_resumeBulletGenerator.py throughly tests resumeBulletGenerator.py
* no issues were faced this week
* for week 13: have a team meeting, create a pdf/html/md export function for resume bullets and project summaries, complete quiz 2


## Week 13 - Nov 24-Nov 30, 2025
<img width="1069" height="544" alt="Screenshot 2025-11-29 at 8 52 52 PM" src="https://github.com/user-attachments/assets/7a15460d-ea29-48a2-babd-678c8b567fb9" />

* there was no check-in this week
* had multiple team meetings this week
* worked on presentation slides
* completed quiz 2
* worked on multiple features this week
* worked on seperating resumeBulletGenerator.py + test_resumeBulletGenerator.py into 3 different files: codeBulletGenerator.py + tests, mediaBulletGenerator.py + tests, textBulletGenerator.py
  * seperating the universal resume bullets generator based on project types allows the code to be more modifiable as we deepen our analyses for the different project types
* worked on resumeAnalytics.py + test_resumeAnalytics.py and resumeMenu.py
  * resumeAnalytics.py offers ATS scoring on the bullets, general bullet improvements and comparison, and improvements based on the target role level
  * resumeMenu.py is a sub menu that will be added to main.py
  * the sub menu allows the user to generate new bullets, retrieve old bullets, improve bullets and delete existing bullets
* for week 14: present for milestone 1, complete team contract, complete milestone 1 self reflection + peer eval, submit demo video


## Week 14 - Dec 1-Dec 7, 2025
<img width="1066" height="546" alt="Screenshot 2025-12-06 at 8 33 16 PM" src="https://github.com/user-attachments/assets/ce7d9b42-5002-45ac-b722-ec9c3cb20fdb" />


* there was no check-in this week
* had multiple team meetings this week
* did our milestone 1 presentation
* updated main, fixed projectcollabtype.py and various other bug fixes in mediaProjectScanner.py and textDocumentScanner.py
* updated dfd
* everything went pretty well this week
* we'll see what's to come for next semester, I plan to do some work for our project over the break






