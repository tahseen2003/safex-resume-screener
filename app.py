import os
import re
import mimetypes
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from PyPDF2 import PdfReader

# Fix MIME types on Windows (ensures .css is served as text/css)
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app = Flask(__name__)


def extract_text_from_pdf(file_storage):
    reader = PdfReader(file_storage)
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def extract_text_from_txt(file_storage):
    raw = file_storage.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def extract_keywords_from_jd(jd_text):
    keywords = set()
    for line in jd_text.strip().splitlines():
        s = line.strip()
        if not s or s.endswith(":"):
            continue
        bm = re.match(r"^[\-\*\u2022]\s*(.+)", s)
        if bm:
            for p in re.split(r"[,;/]", bm.group(1)):
                c = p.strip().rstrip(".")
                if c and len(c) < 60:
                    keywords.add(c.lower())
            continue
        if s.count(",") >= 2:
            for p in re.split(r"[,;/]", s):
                c = p.strip().rstrip(".")
                if c and len(c) < 60:
                    keywords.add(c.lower())
    if not keywords:
        tech = [
            "python","java","javascript","typescript","c++","c#","go","rust",
            "ruby","php","swift","kotlin","django","flask","fastapi","react",
            "angular","vue","node.js","express","spring","sql","mysql",
            "postgresql","mongodb","redis","docker","kubernetes","aws","azure",
            "gcp","terraform","git","linux","ci/cd","jenkins","rest api",
            "graphql","microservices","pandas","numpy","scikit-learn",
            "tensorflow","pytorch","machine learning","deep learning","nlp",
            "html","css","agile","scrum","oop","data structures","algorithms",
            "excel","power bi","tableau","communication","teamwork",
        ]
        jd_lower = jd_text.lower()
        for t in tech:
            if t in jd_lower:
                keywords.add(t)
    return sorted(keywords)


def guess_name(text):
    for line in text.strip().splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("name:"):
            return s.split(":", 1)[1].strip().title()
        if len(s) < 60 and not s.startswith("http") and not s.endswith(":"):
            return s.title()
    return "Unknown"


def score_resume(text, keywords):
    low = text.lower()
    matched = [kw for kw in keywords if kw in low]
    return len(matched), matched


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/screen", methods=["POST"])
def screen():
    jd_text = request.form.get("jd_text", "").strip()
    files = request.files.getlist("resumes")
    if not jd_text:
        return jsonify({"error": "Please provide a job description."}), 400
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Please upload at least one resume."}), 400

    keywords = extract_keywords_from_jd(jd_text)
    if not keywords:
        return jsonify({"error": "Could not extract keywords from JD."}), 400

    results = []
    for f in files:
        if f.filename == "":
            continue
        fn = f.filename.lower()
        try:
            if fn.endswith(".pdf"):
                text = extract_text_from_pdf(f)
            elif fn.endswith(".txt"):
                text = extract_text_from_txt(f)
            else:
                continue
        except Exception as e:
            results.append({"Rank":0,"Name":f.filename,"Score":"0/"+str(len(keywords)),
                "Matched_Skills":f"Error: {e}","File":f.filename,"score_num":0,"total":len(keywords)})
            continue

        if not text.strip():
            results.append({"Rank":0,"Name":f.filename,"Score":"0/"+str(len(keywords)),
                "Matched_Skills":"No text extracted","File":f.filename,"score_num":0,"total":len(keywords)})
            continue

        name = guess_name(text)
        sc, matched = score_resume(text, keywords)
        results.append({"Rank":0,"Name":name,"Score":f"{sc}/{len(keywords)}",
            "Matched_Skills":", ".join(matched),"File":f.filename,"score_num":sc,"total":len(keywords)})

    if not results:
        return jsonify({"error": "No valid .pdf or .txt files found."}), 400

    results.sort(key=lambda x: x["score_num"], reverse=True)
    for i, r in enumerate(results, 1):
        r["Rank"] = i

    csv_data = [{k: v for k, v in r.items() if k not in ("score_num","total")} for r in results]
    df = pd.DataFrame(csv_data)
    df.to_csv(os.path.join(os.path.dirname(__file__), "ranked_candidates.csv"), index=False)

    return jsonify({"keywords": keywords, "results": results, "csv_ready": True})


@app.route("/download-csv")
def download_csv():
    p = os.path.join(os.path.dirname(__file__), "ranked_candidates.csv")
    if not os.path.exists(p):
        return "No results yet.", 404
    return send_file(p, as_attachment=True, download_name="ranked_candidates.csv")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
