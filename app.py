from flask import Flask, render_template, request, redirect, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'hackersecretkey123'
DATABASE = 'lab.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/stage/<int:stage>', methods=['GET', 'POST'])
def stage(stage):
    if stage < 1 or stage > 3:
        return "Stage not found", 404

    message = ''
    success = False
    user_input = ''

    if stage == 1:
        if request.method == 'POST':
            user_input = request.form.get('input', '')
            if "<script>alert(1)</script>" in user_input:
                success = True
                message = "Bravo, XSS basique réussi !"
            else:
                message = "Essaie d'injecter <script>alert(1)</script>."
        return render_template('stage.html', stage=stage, message=message, success=success, user_input=user_input)

    if stage == 2:
        if request.method == 'POST':
            username = request.form.get('username', '')
            query = f"SELECT * FROM users WHERE username = '{username}'"
            try:
                db = get_db()
                cur = db.execute(query)
                rows = cur.fetchall()
                if len(rows) > 0:
                    message = f"Welcome back, {username}! Now try to login as admin by bypassing the SQL."
                else:
                    message = "No user found."

                if username.lower().strip() == "admin'--":
                    success = True
                    message = "SQLi réussie ! Tu as contourné la requête."
            except Exception as e:
                message = f"Erreur SQL : {e}"

        return render_template('stage.html', stage=stage, message=message, success=success)

    if stage == 3:
        if request.method == 'POST':
            user_input = request.form.get('input', '')
            if 'svg/onload' in user_input and 'confirm(' in user_input and 'document.cookie' in user_input:
                success = True
                message = "Challenge XSS avancé validé !"
            else:
                message = "Essaie une injection XSS avancée avec confirm() + svg."

        return render_template('stage.html', stage=stage, message=message, success=success, user_input=user_input)

@app.route('/next/<int:current_stage>')
def next_stage(current_stage):
    next_stage = current_stage + 1
    if next_stage > 3:
        return redirect('/')
    return redirect(f'/stage/{next_stage}')

if __name__ == '__main__':
    with sqlite3.connect(DATABASE) as db:
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
        db.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'admin')")
        db.commit()
    app.run(debug=False, host="0.0.0.0")
