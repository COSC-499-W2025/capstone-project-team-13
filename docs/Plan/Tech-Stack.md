# Tech Stack:

For the development of our system we will use the following the following tech stack and test frameworks:


### Frontend: 
Electron + React – Electron because it is a cross-platform desktop app shell that can access local files securely, and React because it has a huge library for interactive UI for our mined work artifacts and productivity insights.
### Backend: 
Node.js – Node.js because it is good for building fast APIs, and it integrates seamlessly with Electron while offering strong support for file system operations, process management, and connecting to databases for storing mined artifact metadata.
### Database: 
Postgresql - Because it can store metadata, project info, file paths, and metrics, supports flexible JSON fields, and integrates easily with an API and front-end.


## Testing, Requirement Verification
### Test frameworks:
Unit and Integration Testing: Jest (Compatible with Node.JS and front-end testing too e.g. HZTML. CSS), 

### End-to-End Testing: 
Playwright - Supports Electron apps directly, can handle multi-tab flows and cross-browser testing, good integration with React and Node.js testing environments, supports headless and GUI testing, (useful for automated CI/CD pipelines), can test file uploads, drag-and-drop, PDF generation, and dashboards reliably.


### API Testing: 
Jest + Supertest - Can version control API tests, can test all backend routes (artifact uploads, metadata extraction, scans, filtering, exports), works seamlessly with Node.js app and CI/CD (GitHub Actions). 


### CI/CD Integration:
GitHub Actions
