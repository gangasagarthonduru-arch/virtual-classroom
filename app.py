from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE INIT (RUN ONCE) ----------------
def init_db():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            branch TEXT,
            year TEXT
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT,
            branch TEXT,
            year TEXT
        )
        ''')
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS videos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT,
          filename TEXT,
          branch TEXT,
          year TEXT
)
''')

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = cur.fetchone()

        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            session['branch'] = user[5]
            session['year'] = user[6]

            return redirect('/dashboard')

        return "Invalid login ❌"

    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        branch = request.form['branch']
        year = request.form['year']

        try:
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (name,email,password,role,branch,year) VALUES (?,?,?,?,?,?)",
                    (name,email,password,role,branch,year)
                )

            return redirect('/login')

        except sqlite3.IntegrityError:
            return "Email already exists ❌"

    return render_template("signup.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template(
    "dashboard.html",
    name=session.get("name"),
    role=session.get("role")
)
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE id=?",
            (session['user_id'],)
        )

        user = cur.fetchone()

    return render_template("profile.html", user=user)
# ---------------- UPLOAD NOTES ----------------
@app.route('/upload_notes', methods=['GET','POST'])
def upload_notes():

    if request.method == 'POST':
        title = request.form['title']
        branch = request.form['branch']
        year = request.form['year']

        file = request.files['file']
        filename = file.filename

        os.makedirs("uploads", exist_ok=True)
        file.save(os.path.join("uploads", filename))

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notes (title, filename, branch, year) VALUES (?,?,?,?)",
                (title, filename, branch, year)
            )

        return "Upload successful ✔"

    return render_template("upload_notes.html")
@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'Teacher':
        return "Access Denied"

    if request.method == 'POST':

        title = request.form['title']
        branch = request.form['branch']
        year = request.form['year']

        video = request.files['video']
        filename = video.filename

        os.makedirs("uploads/videos", exist_ok=True)

        video.save(os.path.join("uploads/videos", filename))

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO videos (title, filename, branch, year) VALUES (?, ?, ?, ?)",
                (title, filename, branch, year)
            )

        return "Video uploaded successfully ✔"

    return render_template("upload_video.html")
@app.route('/view_videos')
def view_videos():

    if 'user_id' not in session:
        return redirect('/login')

    branch = session['branch']
    year = session['year']

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM videos WHERE branch=? AND year=?",
            (branch, year)
        )

        videos = cur.fetchall()

    return render_template("view_videos.html", videos=videos)

# ---------------- VIEW NOTES ----------------
@app.route('/view_notes')
def view_notes():
    branch = session.get('branch')
    year = session.get('year')

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        search = request.args.get('search', '')

        if search:
           cur.execute(
                "SELECT * FROM notes WHERE branch=? AND year=? AND title LIKE ?",
                 (session['branch'], session['year'], '%' + search + '%')
    )
        else:
           cur.execute(
               "SELECT * FROM notes WHERE branch=? AND year=?",
               (session['branch'], session['year'])
    )
        notes = cur.fetchall()

    return render_template("view_notes.html", notes=notes)
@app.route('/delete_note/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'Teacher':
        return "Access Denied"

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id=?", (id,))
        conn.commit()

    return redirect('/view_notes')

# ---------------- DOWNLOAD FILE ----------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)
@app.route('/uploads/videos/<filename>')
def uploaded_video(filename):
    return send_from_directory(
        'uploads/videos',
        filename
    )
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True)