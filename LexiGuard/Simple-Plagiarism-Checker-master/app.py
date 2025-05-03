from flask import Flask, request, render_template, session, redirect, url_for
from auth import auth_bp
from models import create_tables
from db_config import get_db_connection
import re, math, os, requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.register_blueprint(auth_bp)

create_tables()

# --- Tokenize text ---
def tokenize(text):
    return re.sub(r"[^\w]", " ", text.lower()).split()

# --- Calculate similarity and highlight both texts ---
def calculate_similarity(query, db_text):
    query_words = tokenize(query)
    db_words = tokenize(db_text)
    unique_words = list(set(query_words + db_words))

    query_tf = [query_words.count(word) for word in unique_words]
    db_tf = [db_words.count(word) for word in unique_words]

    dot_product = sum(q * d for q, d in zip(query_tf, db_tf))
    query_mag = math.sqrt(sum(q ** 2 for q in query_tf))
    db_mag = math.sqrt(sum(d ** 2 for d in db_tf))

    if query_mag == 0 or db_mag == 0:
        return 0, "⚠️ Not enough content to compare.", query, db_text

    match_percent = (dot_product / (query_mag * db_mag)) * 100

    # Highlight common words
    common_words = set(query_words) & set(db_words)

    def highlight(text, common):
        for word in common:
            text = re.sub(rf'\b({re.escape(word)})\b', r'<mark>\1</mark>', text, flags=re.IGNORECASE)
        return text

    highlighted_query = highlight(query, common_words)
    highlighted_db = highlight(db_text, common_words)

    return match_percent, f"✅ Text match: {match_percent:.2f}%", highlighted_query, highlighted_db

# --- Main page (/check) ---
@app.route("/check", methods=["GET", "POST"])
def main_page():
    if 'user_id' not in session:
        return redirect('/login')

    query, text2, output = "", "", ""
    match_percent, file1_text, file2_text = None, "", ""
    highlighted_text1, highlighted_text2 = "", ""

    if request.method == "POST":
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")

        if file1 and file2:
            file1_text = file1.read().decode("utf-8")
            file2_text = file2.read().decode("utf-8")
            match_percent, output, highlighted_text1, highlighted_text2 = calculate_similarity(file1_text, file2_text)
        else:
            query = request.form.get("query", "")
            text2 = request.form.get("text2", "")
            if not text2.strip():
                try:
                    with open("database1.txt", "r") as f:
                        text2 = f.read()
                except:
                    output = "❌ database1.txt not found."
                    return render_template("index.html", query=query, text2=text2, output=output)
            match_percent, output, highlighted_text1, highlighted_text2 = calculate_similarity(query, text2)

        # Save to history
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO History (user_id, input_text, plagiarism_percent) VALUES (?, ?, ?)",
                       (session['user_id'], query or file1_text, match_percent))
        conn.commit()
        conn.close()

        return render_template("index.html",
                               query=query, text2=text2, output=output,
                               match_percent=round(match_percent, 2) if match_percent else None,
                               highlighted_text1=highlighted_text1,
                               highlighted_text2=highlighted_text2,
                               file1_text=file1_text, file2_text=file2_text)

    return render_template("index.html")

# --- Alternate page ---
@app.route("/alt", methods=["GET", "POST"])
def alternate_page():
    if 'user_id' not in session:
        return redirect('/login')

    query = request.form.get("query", "")
    text2 = request.form.get("text2", "")
    output, highlighted_text1, highlighted_text2 = "", "", ""
    match_percent = None

    if request.method == "POST":
        if not text2.strip():
            try:
                with open("database1.txt", "r") as f:
                    text2 = f.read()
            except:
                output = "❌ database1.txt not found."
                return render_template("index2.html", query=query, text2=text2, output=output)

        match_percent, output, highlighted_text1, highlighted_text2 = calculate_similarity(query, text2)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO History (user_id, input_text, plagiarism_percent) VALUES (?, ?, ?)",
                       (session['user_id'], query, match_percent))
        conn.commit()
        conn.close()

    return render_template(
        'index2.html',
        query=query,
        text2=text2,
        output=output,
        highlighted_text1=highlighted_text1,
        highlighted_text2=highlighted_text2
    )
# --- Web plagiarism check page ---
@app.route("/web-check", methods=["GET", "POST"])
def web_check():
    if 'user_id' not in session:
        return redirect('/login')

    query = ""
    results = []
    match_percent = 0

    if request.method == "POST":
        file = request.files.get("file")
        if file:
            query = file.read().decode("utf-8")
        else:
            query = request.form.get("query", "")

        if query.strip():
            api_key = "your api_key"
            search_engine_id = "search_engine_id"
            endpoint = "your endpoint link"
            params = {"key": api_key, "cx": search_engine_id, "q": query[:256]}
            response = requests.get(endpoint, params=params)

            if response.status_code == 200:
                data = response.json()
                results = data.get("items", [])

                total_score, count = 0, 0
                for item in results:
                    snippet = item.get("snippet", "")
                    if snippet:
                        sim, _, _, _ = calculate_similarity(query, snippet)
                        total_score += sim
                        count += 1

                if count > 0:
                    match_percent = total_score / count

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO History (user_id, input_text, plagiarism_percent) VALUES (?, ?, ?)",
                           (session['user_id'], query, match_percent))
            conn.commit()
            conn.close()

    return render_template("index3.html", query=query, results=results, match_percent=round(match_percent, 2))

# --- History page ---
@app.route("/history")
def history():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT input_text, plagiarism_percent, timestamp FROM History WHERE user_id = ? ORDER BY timestamp DESC",
                   (session['user_id'],))
    records = cursor.fetchall()
    conn.close()
    return render_template("history.html", history=records)

@app.route("/")
def home():
    return redirect("/check")

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# --- Run the app ---
if __name__ == "__main__":
    app.run(debug=True)
