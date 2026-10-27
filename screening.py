import os
import pandas as pd
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def load_keywords_with_weights():
    # Higher weight = more important skill
    keywords_weights = {
        'python': 3,
        'django': 2,
        'flask': 2,
        'rest api': 2,
        'sql': 2,
        'git': 1,
        'pandas': 1,
        'oop': 1,
        'linux': 1,
        'docker': 1
    }
    return keywords_weights

def semantic_match(resume_text, keyword):
    """Check exact match OR semantic similarity using spaCy"""
    resume_doc = nlp(resume_text)
    keyword_doc = nlp(keyword)
    
    # 1. Exact match first
    if keyword in resume_text:
        return True
    
    # 2. Semantic match: check similarity > 0.7
    for token in resume_doc:
        if token.similarity(keyword_doc) > 0.7:
            # Example: "web framework" in resume will match "django"
            if keyword in ['django', 'flask'] and token.text in ['framework', 'web', 'backend']:
                return True
            if keyword == 'sql' and token.text in ['database', 'db', 'mysql', 'postgres']:
                return True
            if keyword == 'git' and token.text in ['github', 'gitlab', 'version control']:
                return True
    return False

def score_resume(resume_path, keywords_weights):
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_text = f.read().lower()
    
    score = 0
    matched = []
    for kw, weight in keywords_weights.items():
        if semantic_match(resume_text, kw):
            score += weight
            matched.append(f"{kw}({weight})")
    
    with open(resume_path, 'r', encoding='utf-8') as f:
        name_line = f.readline()
    name = name_line.replace('name:', '').strip().title()
    return name, score, matched

def main():
    resume_folder = 'resume'
    
    if not os.path.exists(resume_folder):
        print(f"ERROR: Folder '{resume_folder}' not found!")
        return
    
    keywords_weights = load_keywords_with_weights()
    max_score = sum(keywords_weights.values()) # total possible = 17
    results = []
    
    for filename in os.listdir(resume_folder):
        if filename.endswith('.txt'):
            path = os.path.join(resume_folder, filename)
            name, score, matched = score_resume(path, keywords_weights)
            results.append({
                'Rank': 0,
                'Name': name, 
                'Score': f"{score}/{max_score}", 
                'Percentage': round(score/max_score*100, 1),
                'Matched_Skills': ', '.join(matched),
                'File': filename
            })
    
    if not results:
        print("ERROR: No resume.txt files found")
        return
    
    results.sort(key=lambda x: x['Percentage'], reverse=True)
    
    for i, r in enumerate(results, 1):
        r['Rank'] = i
    
    # Print results
    print("=== AI RECRUITMENT SCREENING - spaCy SMART MATCH ===\n")
    
    for r in results:
        print(f"Rank {r['Rank']}: {r['Name']}")
        print(f" Score: {r['Score']} = {r['Percentage']}%")
        print(f" Matched: {r['Matched_Skills']}\n")
    
    # Save report.txt
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("TOP 3 CANDIDATES - SMART MATCHING WITH spaCy\n=============================================\n")
        for r in results[:3]:
            f.write(f"{r['Name']} - Score: {r['Score']} = {r['Percentage']}%\n")
            f.write(f"Matched Skills: {r['Matched_Skills']}\n\n")
        f.write("\nBIAS NOTE:\nUses semantic matching. 'database' = 'SQL'. No demographic data used.")
    
    print("Report saved to report.txt")

    # CSV EXPORT
    df = pd.DataFrame(results)
    df.to_csv('ranked_candidates.csv', index=False)
    print("CSV saved to ranked_candidates.csv")

if __name__ == "__main__":
    main()
 