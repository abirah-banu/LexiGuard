from flask import Flask, request, render_template
import re
import math
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def plagiarism_checker():
    query = ""
    text2 = ""
    output = ""
    match_percentage = 0
    database_content = ""
    show_db = False
    compare_two = False

    if request.method == "POST":
        # Clear
        if 'clear' in request.form:
            return render_template("index.html", query="", text2="", output="")

        # Upload File
        elif 'file' in request.files and request.files['file'].filename:
            uploaded_file = request.files['file']
            query = uploaded_file.read().decode("utf-8")

        # View DB
        elif 'view_db' in request.form:
            show_db = True
            try:
                with open("database1.txt", "r") as f:
                    database_content = f.read()
            except:
                database_content = "❌ Could not open database1.txt"

        # Compare Two Texts
        elif 'compare_two' in request.form:
            compare_two = True
            query = request.form.get("query", "")
            text2 = request.form.get("text2", "")

        # Export Report
        elif 'export' in request.form:
            try:
                with open("report.txt", "w") as f:
                    f.write(f"Input:\n{request.form.get('query','')}\n\n")
                    f.write(f"Comparison:\n{request.form.get('text2','')}\n\n")
                    f.write(f"Result:\n{request.form.get('output','')}")
                output = "✅ Report exported as report.txt"
            except Exception as e:
                output = f"❌ Could not export report: {e}"

        # Check plagiarism
        else:
            query = request.form.get("query", "")
            text2 = request.form.get("text2", "")
            if text2.strip():
                db_text = text2
            else:
                try:
                    with open("database1.txt", "r") as f:
                        db_text = f.read()
                except:
                    output = "❌ database1.txt not found."
                    return render_template("index.html", query=query, text2=text2, output=output)

            def tokenize(text):
                return re.sub(r"[^\w]", " ", text.lower()).split()

            query_words = tokenize(query)
            db_words = tokenize(db_text)

            unique_words = list(set(query_words + db_words))
            query_tf = [query_words.count(word) for word in unique_words]
            db_tf = [db_words.count(word) for word in unique_words]

            dot_product = sum(q * d for q, d in zip(query_tf, db_tf))
            query_mag = math.sqrt(sum(q ** 2 for q in query_tf))
            db_mag = math.sqrt(sum(d ** 2 for d in db_tf))

            if query_mag == 0 or db_mag == 0:
                match_percentage = 0
                output = "⚠️ Not enough content to compare."
            else:
                match_percentage = (dot_product / (query_mag * db_mag)) * 100
                output = f"✅ Input query text matches {match_percentage:.2f}% with the database."

    return render_template("index.html",
                           query=query,
                           text2=text2,
                           output=output,
                           match_percent=round(match_percentage, 2),
                           show_db=show_db,
                           database=database_content,
                           compare_two=compare_two)


if __name__ == "__main__":
    app.run(debug=True)
