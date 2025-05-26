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

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

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

    # Stage 1: XSS challenge - input is reflected unsanitized
    if stage == 1:
        if request.method == 'POST':
            user_input = request.form.get('input', '')
            # Check if user triggered alert (simulate by presence of <script>alert(1)</script>)
            if "<script>alert(1)</script>" in user_input:
                success = True
            else:
                message = 'Try to inject <script>alert(1)</script> to pass.'

        return render_template('stage.html', stage=stage, message=message, success=success)

    # Stage 2: SQLi challenge - basic vulnerable query
    if stage == 2:
        if request.method == 'POST':
            username = request.form.get('username', '')
            # WARNING: This is intentionally vulnerable!
            db = get_db()
            query = f"SELECT * FROM users WHERE username = '{username}'"
            try:
                cur = db.execute(query)
                rows = cur.fetchall()
                if len(rows) > 0:
                    message = f"Welcome back, {username}! Now try to login as admin by bypassing the SQL."
                else:
                    message = "No user found."
                if username.lower() == "admin'--":
                    success = True
            except Exception as e:
                message = "SQL error or injection attempt detected."

        return render_template('stage.html', stage=stage, message=message, success=success)

    # Stage 3: Final success page
    if stage == 3:
        return render_template('stage.html', stage=stage, message="Congrats! You passed all stages.", success=True)

@app.route('/next/<int:current_stage>')
def next_stage(current_stage):
    next_stage = current_stage + 1
    if next_stage > 3:
        return redirect('/')
    return redirect(f'/stage/{next_stage}')

if __name__ == '__main__':
    # Initial DB setup
    with sqlite3.connect(DATABASE) as db:
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
        db.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'admin')")
        db.commit()
    app.run(debug=False, host="0.0.0.0")
