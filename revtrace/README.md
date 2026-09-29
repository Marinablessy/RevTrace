# RevTrace — How to Run

RevTrace is made up of multiple services. Each service must be started in a separate terminal.

---

 1. Expected Folder Structure

After extracting the ZIP, the project should look approximately like this:

```text
revtrace/
│
├── README.md
├── requirements.txt
│
├── revtrace-core/
├── revtrace-prospecting/
├── deal-desk/
├── proposal-rfp/
└── dashboard/

2. Software Required
Install the following before running RevTrace:
- Python 3.10 or later
- Node.js 18 or later
- npm
Check Python:
python --version

Check Node.js:
node --version

Check npm:
npm --version

3. Configure API Keys
The project contains placeholder API keys.
Before running RevTrace, open the relevant .env or .env.local files and replace placeholder values such as:
GROQ_API_KEY=YOUR_API_KEY
HINDSIGHT_API_KEY=YOUR_API_KEY

with valid API keys.
Do not publish real API keys in a public repository.
4. First-Time Setup
Open the main revtrace folder in VS Code.
Then open:
Terminal → New Terminal

Make sure the terminal is inside the main revtrace folder.
Example:
cd "C:\Users\YourName\Desktop\revtrace"

Install Python dependencies:
pip install -r requirements.txt

Install Deal Desk dependencies:
cd ".\deal-desk"
npm.cmd install
cd ..

Install Dashboard dependencies:
cd ".\dashboard"
npm.cmd install
cd ..

These installation commands are required only once on a new machine.
5. Run RevTrace
From the main revtrace folder, run:
powershell -ExecutionPolicy Bypass -File .\START_REVTRACE.ps1

This single command starts all RevTrace services automatically:
RevTrace Core          → http://localhost:8100
Prospecting Backend    → http://localhost:8000
Prospecting UI         → http://localhost:8501
Deal Desk              → http://localhost:3000
Proposal / RFP         → http://localhost:8502
RevTrace Dashboard     → http://localhost:5173

Wait a few seconds for all services to start.
Then open:
http://localhost:5173

This is the main RevTrace Dashboard.
6. Normal Run After First-Time Setup
After dependencies are installed once, every future run only requires:
cd "C:\Users\YourName\Desktop\revtrace"
powershell -ExecutionPolicy Bypass -File .\START_REVTRACE.ps1

That is all.
7. RevTrace Workflow
Once all services are running:
Prospecting Agent
        ↓
Qualified Opportunity
        ↓
Deal Desk
        ↓
Commercial Approval
        ↓
Proposal / RFP Agent
        ↓
Proposal Submitted
        ↓
WON / LOST
        ↓
RevTrace Dashboard

Customer journey stages:
NEW_PROSPECT
→ OUTREACH_SENT
→ ENGAGED_PROSPECT
→ MEETING_SCHEDULED
→ QUALIFIED_OPPORTUNITY
→ DEAL_DESK
→ COMMERCIAL_APPROVED
→ PROPOSAL_DRAFT
→ PROPOSAL_SUBMITTED
→ WON / LOST

8. Service URLs
Component	URL
RevTrace Core	http://localhost:8100
Prospecting Backend	http://localhost:8000
Prospecting Agent	http://localhost:8501
Deal Desk	http://localhost:3000
Proposal / RFP Agent	http://localhost:8502
RevTrace Dashboard	http://localhost:5173


Recommended entry point:
http://localhost:5173

9. If PowerShell Blocks the Script
Run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Then run:
.\START_REVTRACE.ps1

Or use the direct command:
powershell -ExecutionPolicy Bypass -File .\START_REVTRACE.ps1

10. If a Port Is Already in Use
If you see:
Address already in use

or:
Port already in use

the service may already be running.
Check the corresponding URL first.
Ports used by RevTrace:
8100 = RevTrace Core
8000 = Prospecting Backend
8501 = Prospecting UI
3000 = Deal Desk
8502 = Proposal / RFP
5173 = Dashboard

11. Manual Startup — Fallback
If the one-command launcher does not work, start the services manually in separate terminals.
Terminal 1 — RevTrace Core
cd "C:\Users\YourName\Desktop\revtrace\revtrace-core"
python -m uvicorn main:app --reload --port 8100

Terminal 2 — Prospecting Backend
cd "C:\Users\YourName\Desktop\revtrace\revtrace-prospecting"
python -m uvicorn backend.main:app --reload --port 8000

Terminal 3 — Prospecting UI
cd "C:\Users\YourName\Desktop\revtrace\revtrace-prospecting"
python -m streamlit run frontend.py --server.port 8501

Terminal 4 — Deal Desk
cd "C:\Users\YourName\Desktop\revtrace\deal-desk"
npm.cmd run dev

Terminal 5 — Proposal / RFP
cd "C:\Users\YourName\Desktop\revtrace\proposal-rfp"
python -m streamlit run app.py --server.port 8502

Terminal 6 — Dashboard
cd "C:\Users\YourName\Desktop\revtrace\dashboard"
npm.cmd run dev

Start them in this order:
1. RevTrace Core
2. Prospecting Backend
3. Prospecting UI
4. Deal Desk
5. Proposal / RFP
6. Dashboard

12. Stopping RevTrace
If services were started manually, go to each terminal and press:
Ctrl + C

If RevTrace was started using START_REVTRACE.ps1, stop the running RevTrace processes before restarting the project.