# CrediRate: A Relational Trust Engine

**CrediRate** is a full-stack Flask and MySQL application designed to showcase programmatic credibility scoring. By moving beyond traditional "dumb" averages, CrediRate utilizes complex backend SQL Views to evaluate the metadata of every single reviewer (recency, history, reliability, and verification status) to generate a robust, tamper-resistant **Weighted Trust Score**.

---
## Demo Link: 
https://youtu.be/9iT_ev2he1A

## Key Features
- **Algorithmic Trust Scores**: Calculates a dynamic `final_weight` for every single review using multiple mathematical factors directly inside a mathematical MySQL View.
- **Interactive User Profiles**: Click dynamically on reviewers to see their personalized dashboards showing their Reputation Score, join date, and complete audit trail.
- **Verified "Web3" style Badges**: Visually identifies historically trusted users with native verification styling (`✔ Verified`).
- **Transparency Dashboard**: Displays side-by-side comparisons of the "Opaque Average" versus the newly calculated "Structured Trust Score" for entities!
- **Live Filtering**: Sort the audit trail dynamically to immediately hide unverified reviewers.

---

## 🛠 Tech Stack
- **Backend**: Python 3 (Flask)
- **Database**: MySQL (Hosted locally via XAMPP)
- **Frontend**: Vanilla HTML5, native CSS (with glassmorphism UI), Context API Vanilla JavaScript.

---

## Quickstart: Local Setup

This project uses XAMPP out of the box because it was specifically migrated from SQLite to properly utilize advanced SQL View integrations.

**1. Database Initialization**
Make sure XAMPP is installed and start the **MySQL module** on Port 3306.

**2. Automatic Build**
Open a terminal inside this folder and run the build script. This will automatically set up your python virtual environment, install requirements, link to your local XAMPP MySQL server, construct the required table views, and seed the demo data.
```bash
build.bat
```

**3. Run the Local Server**
With the database seeded, launch the Python server:
```bash
run.bat
```
*(You can now visit your live app at `http://127.0.0.1:5000`)*

---

## Database Schema Architecture

The core magic of CrediRate is handled on the database layer. Instead of looping math in Python arrays, the logic is defined inside the relational structure. Here is how Trust is quantified inside `vw_credibility_weights`:

* **Recency Factor (`w_r`)**: Evaluates how old a review is. Recent reviews are weighted significantly heavier.
* **History Factor (`w_s`)**: Gives a multiplier bonus if the user has historically reviewed the same entity before.
* **Reliability (`w_l`)**: A global rating tracking how many total reviews a user has contributed to the platform altogether.
* **Verification Bonus**: A flat structural jump (+5) simply for achieving Verified status.

**How to test the schema:**
You can actually drop into your XAMPP PhpMyAdmin local database (`credirate`) while running the app. You'll see new reviewers and weights actively being recalculated and persisted. 

---

##  Recommended Demo Flow 

If you are demoing this for a presentation or viva, here is the intended flow:
1. Load up the Dashboard on Localhost and describe the glass-morphic UI.
2. Click **Asteria Bistro** to view the breakdown between the standard `Opaque Average` and the newly calculated `Weighted Trust Score`. 
3. Scroll down into the **Audit Trail** and show the specific algorithmic modifiers attached to each review card. 
4. Click the **"Verified Reviewers Only"** toggle slider to showcase dynamic dataset manipulation.
5. Emphasize the new **User Profile Structure** by actively clicking on the name of a Verified Reviewer (e.g., *Priya Menon*) to slide over to their distinct history context.
6. Submit a brand new review on the side panel using a new name, to demonstrate how the MySQL API handles the instant creation and weighted integration of zero-day accounts!

---

*Authored and developed natively for python execution environments.*
