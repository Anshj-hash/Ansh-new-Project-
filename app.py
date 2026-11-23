import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date, datetime
import hashlib

DB = Path(__file__).with_name("placement.db")
UPLOAD_DIR = Path(__file__).with_name("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Campus Placement Portal", page_icon="🎓", layout="wide")

def connect():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT NOT NULL,
            roll_no TEXT, department TEXT, phone TEXT
        );
        CREATE TABLE IF NOT EXISTS companies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, website TEXT, location TEXT,
            contact_email TEXT, description TEXT
        );
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER, title TEXT NOT NULL, description TEXT,
            eligibility TEXT, package TEXT, location TEXT,
            deadline TEXT, status TEXT DEFAULT 'Open',
            FOREIGN KEY(company_id) REFERENCES companies(id)
        );
        CREATE TABLE IF NOT EXISTS applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, job_id INTEGER,
            applied_on TEXT, status TEXT DEFAULT 'Applied',
            resume TEXT, UNIQUE(student_id, job_id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        """)
        admin = con.execute("SELECT id FROM users WHERE email='admin@campus.com'").fetchone()
        if not admin:
            con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                        ("Administrator","admin@campus.com",hash_password("admin123"),"Admin"))
        if con.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0:
            con.execute("INSERT INTO companies(name,website,location,contact_email,description) VALUES(?,?,?,?,?)",
                        ("TechNova Solutions","https://example.com","Gurugram","careers@example.com","Sample company profile"))
            cid = con.execute("SELECT id FROM companies LIMIT 1").fetchone()[0]
            con.execute("""INSERT INTO jobs(company_id,title,description,eligibility,package,location,deadline)
                           VALUES(?,?,?,?,?,?,?)""",
                        (cid,"Graduate Software Trainee","Entry-level software development role.",
                         "BCA / B.Tech; basic programming knowledge","₹4.5 LPA","Gurugram","2027-03-31"))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def query(sql, params=()):
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)

def execute(sql, params=()):
    with connect() as con:
        cur = con.execute(sql, params)
        con.commit()
        return cur.lastrowid

def login(email, password):
    rows = query("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password)))
    return rows.iloc[0].to_dict() if not rows.empty else None

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.rerun()

def login_page():
    st.title("🎓 Campus Placement Management System")
    st.caption("A centralized portal for students, recruiters and placement administrators.")
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Welcome to your career portal")
        st.write("Explore placement opportunities, apply for jobs, and track application progress.")
        st.info("Demo administrator: **admin@campus.com**  |  Password: **admin123**")
    with right:
        tab1, tab2 = st.tabs(["Login", "Student Registration"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    user = login(email.strip().lower(), password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
        with tab2:
            with st.form("register_form"):
                name = st.text_input("Full name")
                reg_email = st.text_input("Email address")
                roll = st.text_input("Roll number")
                dept = st.selectbox("Department", ["BCA","BBA","B.Tech","MCA","MBA","Other"])
                phone = st.text_input("Phone number")
                p1 = st.text_input("Create password", type="password")
                p2 = st.text_input("Confirm password", type="password")
                ok = st.form_submit_button("Create student account", use_container_width=True)
                if ok:
                    if not all([name, reg_email, roll, p1]):
                        st.error("Please fill all required fields.")
                    elif p1 != p2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            execute("INSERT INTO users(name,email,password,role,roll_no,department,phone) VALUES(?,?,?,?,?,?,?)",
                                    (name,reg_email.strip().lower(),hash_password(p1),"Student",roll,dept,phone))
                            st.success("Account created. Please login.")
                        except sqlite3.IntegrityError:
                            st.error("This email is already registered.")

def sidebar():
    u = st.session_state.user
    st.sidebar.title("🎓 Placement Portal")
    st.sidebar.write(f"**{u['name']}**")
    st.sidebar.caption(u["role"])
    st.sidebar.divider()
    if u["role"] == "Admin":
        pages = ["Dashboard","Manage Students","Manage Companies","Manage Jobs","Applications"]
    else:
        pages = ["Dashboard","Browse Jobs","My Applications","My Profile"]
    page = st.sidebar.radio("Navigation", pages)
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
    return page

def admin_dashboard():
    st.title("Admin Dashboard")
    students = query("SELECT COUNT(*) n FROM users WHERE role='Student'").iloc[0,0]
    companies = query("SELECT COUNT(*) n FROM companies").iloc[0,0]
    jobs = query("SELECT COUNT(*) n FROM jobs").iloc[0,0]
    apps = query("SELECT COUNT(*) n FROM applications").iloc[0,0]
    a,b,c,d = st.columns(4)
    for col, label, value in [(a,"Registered Students",students),(b,"Companies",companies),(c,"Job Listings",jobs),(d,"Applications",apps)]:
        col.metric(label, int(value))
    st.subheader("Recent applications")
    df = query("""SELECT a.id, u.name AS Student, j.title AS Job, c.name AS Company,
                         a.applied_on AS 'Applied On', a.status AS Status
                  FROM applications a JOIN users u ON a.student_id=u.id
                  JOIN jobs j ON a.job_id=j.id JOIN companies c ON j.company_id=c.id
                  ORDER BY a.id DESC LIMIT 10""")
    st.dataframe(df, use_container_width=True, hide_index=True)

def manage_students():
    st.title("Manage Students")
    with st.expander("Add student"):
        with st.form("add_student"):
            name=st.text_input("Name"); email=st.text_input("Email"); roll=st.text_input("Roll number")
            dept=st.selectbox("Department",["BCA","BBA","B.Tech","MCA","MBA","Other"])
            password=st.text_input("Temporary password",type="password")
            if st.form_submit_button("Add student"):
                try:
                    execute("INSERT INTO users(name,email,password,role,roll_no,department) VALUES(?,?,?,?,?,?)",
                            (name,email.lower(),hash_password(password),"Student",roll,dept))
                    st.success("Student added.")
                except Exception as e: st.error(f"Could not add student: {e}")
    df=query("SELECT id,name,email,roll_no,department,phone FROM users WHERE role='Student' ORDER BY id DESC")
    st.dataframe(df,use_container_width=True,hide_index=True)
    if not df.empty:
        sid=st.selectbox("Select student ID to delete",df["id"].tolist())
        if st.button("Delete selected student"):
            execute("DELETE FROM applications WHERE student_id=?",(int(sid),))
            execute("DELETE FROM users WHERE id=? AND role='Student'",(int(sid),))
            st.success("Student deleted."); st.rerun()

def manage_companies():
    st.title("Manage Companies")
    with st.form("company_form"):
        name=st.text_input("Company name"); website=st.text_input("Website"); location=st.text_input("Location")
        email=st.text_input("Contact email"); desc=st.text_area("Description")
        if st.form_submit_button("Add company"):
            if name:
                execute("INSERT INTO companies(name,website,location,contact_email,description) VALUES(?,?,?,?,?)",
                        (name,website,location,email,desc))
                st.success("Company added.")
            else: st.error("Company name is required.")
    df=query("SELECT * FROM companies ORDER BY id DESC")
    st.dataframe(df,use_container_width=True,hide_index=True)
    if not df.empty:
        cid=st.selectbox("Company ID to delete",df.id.tolist())
        if st.button("Delete company"):
            execute("DELETE FROM jobs WHERE company_id=?",(int(cid),))
            execute("DELETE FROM companies WHERE id=?",(int(cid),))
            st.success("Company and its job listings deleted."); st.rerun()

def manage_jobs():
    st.title("Manage Job Listings")
    companies=query("SELECT id,name FROM companies ORDER BY name")
    if companies.empty:
        st.warning("Add a company before creating a job.")
    else:
        with st.form("job_form"):
            company=st.selectbox("Company",companies.itertuples(index=False),format_func=lambda x:x.name)
            title=st.text_input("Job title"); desc=st.text_area("Description")
            eligibility=st.text_input("Eligibility criteria"); package=st.text_input("Package (e.g. ₹5 LPA)")
            location=st.text_input("Job location"); deadline=st.date_input("Application deadline",min_value=date.today())
            if st.form_submit_button("Publish job"):
                if title:
                    execute("""INSERT INTO jobs(company_id,title,description,eligibility,package,location,deadline)
                               VALUES(?,?,?,?,?,?,?)""",
                            (company.id,title,desc,eligibility,package,location,str(deadline)))
                    st.success("Job published.")
                else: st.error("Job title is required.")
    df=query("""SELECT j.id,c.name AS Company,j.title AS Job,j.package AS Package,j.location AS Location,
                       j.deadline AS Deadline,j.status AS Status
                FROM jobs j LEFT JOIN companies c ON j.company_id=c.id ORDER BY j.id DESC""")
    st.dataframe(df,use_container_width=True,hide_index=True)
    if not df.empty:
        jid=st.selectbox("Job ID to update",df.id.tolist())
        status=st.selectbox("Set job status",["Open","Closed"])
        x,y=st.columns(2)
        if x.button("Update status"):
            execute("UPDATE jobs SET status=? WHERE id=?",(status,int(jid))); st.success("Status updated."); st.rerun()
        if y.button("Delete job"):
            execute("DELETE FROM applications WHERE job_id=?",(int(jid),))
            execute("DELETE FROM jobs WHERE id=?",(int(jid),)); st.success("Job deleted."); st.rerun()

def applications_admin():
    st.title("Applications Management")
    df=query("""SELECT a.id,u.name AS Student,u.roll_no AS 'Roll No',j.title AS Job,c.name AS Company,
                       a.applied_on AS 'Applied On',a.status AS Status,a.resume AS Resume
                FROM applications a JOIN users u ON a.student_id=u.id
                JOIN jobs j ON a.job_id=j.id JOIN companies c ON j.company_id=c.id
                ORDER BY a.id DESC""")
    st.dataframe(df.drop(columns=["Resume"]) if not df.empty else df,use_container_width=True,hide_index=True)
    if not df.empty:
        aid=st.selectbox("Application ID",df.id.tolist())
        status=st.selectbox("Application status",["Applied","Under Review","Shortlisted","Selected","Rejected"])
        if st.button("Update application status"):
            execute("UPDATE applications SET status=? WHERE id=?",(status,int(aid)))
            st.success("Application status updated."); st.rerun()
        resume=df.loc[df.id==aid,"Resume"].iloc[0]
        if resume and Path(resume).exists():
            st.download_button("Download resume",Path(resume).read_bytes(),file_name=Path(resume).name)

def student_dashboard(user):
    st.title(f"Welcome, {user['name']} 👋")
    a=query("SELECT COUNT(*) n FROM jobs WHERE status='Open'").iloc[0,0]
    b=query("SELECT COUNT(*) n FROM applications WHERE student_id=?",(user["id"],)).iloc[0,0]
    c=query("SELECT COUNT(*) n FROM applications WHERE student_id=? AND status='Selected'",(user["id"],)).iloc[0,0]
    x,y,z=st.columns(3); x.metric("Open Opportunities",int(a)); y.metric("Applications Submitted",int(b)); z.metric("Selected",int(c))
    st.subheader("Latest opportunities")
    df=query("""SELECT j.id,j.title AS Job,c.name AS Company,j.package AS Package,j.location AS Location,
                       j.deadline AS Deadline
                FROM jobs j JOIN companies c ON j.company_id=c.id
                WHERE j.status='Open' ORDER BY j.id DESC LIMIT 5""")
    st.dataframe(df,use_container_width=True,hide_index=True)

def browse_jobs(user):
    st.title("Browse Placement Opportunities")
    search=st.text_input("Search by job title or company")
    df=query("""SELECT j.id,j.title AS Job,c.name AS Company,j.description AS Description,
                       j.eligibility AS Eligibility,j.package AS Package,j.location AS Location,
                       j.deadline AS Deadline,j.status AS Status
                FROM jobs j JOIN companies c ON j.company_id=c.id
                WHERE j.status='Open' ORDER BY j.id DESC""")
    if search:
        df=df[df["Job"].str.contains(search,case=False,na=False)|df["Company"].str.contains(search,case=False,na=False)]
    if df.empty: st.info("No open jobs found.")
    for _,r in df.iterrows():
        with st.container(border=True):
            st.subheader(r["Job"])
            st.write(f"**{r['Company']}** · {r['Location']} · **{r['Package']}**")
            st.write(r["Description"])
            st.caption(f"Eligibility: {r['Eligibility']} | Deadline: {r['Deadline']}")
            already=query("SELECT id FROM applications WHERE student_id=? AND job_id=?",(user["id"],int(r["id"])))
            with st.form(f"apply_{r['id']}"):
                resume=st.file_uploader("Upload resume (PDF/DOC/DOCX)",type=["pdf","doc","docx"],key=f"resume_{r['id']}")
                submitted=st.form_submit_button("Apply now",disabled=not already.empty)
                if not already.empty: st.success("You have already applied.")
                if submitted:
                    if resume:
                        safe_name=f"student_{user['id']}_job_{r['id']}_{Path(resume.name).name}"
                        path=UPLOAD_DIR/safe_name
                        path.write_bytes(resume.getvalue())
                        try:
                            execute("INSERT INTO applications(student_id,job_id,applied_on,status,resume) VALUES(?,?,?,?,?)",
                                    (user["id"],int(r["id"]),str(date.today()),"Applied",str(path)))
                            st.success("Application submitted successfully.")
                        except sqlite3.IntegrityError: st.warning("You have already applied.")
                    else: st.error("Please upload your resume first.")

def my_applications(user):
    st.title("My Applications")
    df=query("""SELECT a.id,j.title AS Job,c.name AS Company,j.package AS Package,
                       a.applied_on AS 'Applied On',a.status AS Status
                FROM applications a JOIN jobs j ON a.job_id=j.id
                JOIN companies c ON j.company_id=c.id
                WHERE a.student_id=? ORDER BY a.id DESC""",(user["id"],))
    if df.empty: st.info("You have not applied to any jobs yet.")
    else: st.dataframe(df,use_container_width=True,hide_index=True)

def my_profile(user):
    st.title("My Profile")
    with st.form("profile"):
        name=st.text_input("Full name",user.get("name",""))
        phone=st.text_input("Phone",user.get("phone") or "")
        dept=st.selectbox("Department",["BCA","BBA","B.Tech","MCA","MBA","Other"],
                          index=["BCA","BBA","B.Tech","MCA","MBA","Other"].index(user.get("department") or "BCA")
                          if user.get("department") in ["BCA","BBA","B.Tech","MCA","MBA","Other"] else 0)
        if st.form_submit_button("Save profile"):
            execute("UPDATE users SET name=?,phone=?,department=? WHERE id=?",(name,phone,dept,user["id"]))
            st.session_state.user=query("SELECT * FROM users WHERE id=?",(user["id"],)).iloc[0].to_dict()
            st.success("Profile updated.")

if st.session_state.user is None:
    login_page()
else:
    page=sidebar()
    user=st.session_state.user
    if user["role"]=="Admin":
        {"Dashboard":admin_dashboard,"Manage Students":manage_students,"Manage Companies":manage_companies,
         "Manage Jobs":manage_jobs,"Applications":applications_admin}[page]()
    else:
        {"Dashboard":lambda:student_dashboard(user),"Browse Jobs":lambda:browse_jobs(user),
         "My Applications":lambda:my_applications(user),"My Profile":lambda:my_profile(user)}[page]()
