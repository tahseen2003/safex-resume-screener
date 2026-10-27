# SafeX — AI Resume Screener

A simple web app that screens and ranks resumes against a job description automatically.

## What it does

Paste a job description, upload resumes (PDF or TXT), and SafeX extracts the required skills, scores each resume, and ranks candidates on a leaderboard. Results can be exported as a CSV.

## How to use

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**
   ```bash
   python app.py
   ```

3. **Open in browser** → `http://127.0.0.1:5000`

4. Paste your **job description**, upload **resumes**, click **Screen & Rank**.

5. Download the ranked results as a **CSV**.

## Tech

- **Flask** — web server  
- **PyPDF2** — PDF parsing  
- **Pandas** — ranking & CSV export  

## License

MIT
