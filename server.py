from flask import Flask,render_template,request,redirect,url_for
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from bson.objectid import ObjectId
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'anysecretkey'

client=pymongo.MongoClient('database:link')
db=client['HSManager']
collections=db['registrations']
ad_collections=db['admin_reg']
notice=db['notices']
student_room=db['student_rooms']
complaint = db['complaints']
outpass=db['outpasses']

admin_email='admin_mail_id@gmail.com'
admin_password='admin_password'

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/<name>")
def admin_home(name):
    get_notice=notice.find()
    return render_template("admin_dashboard.html",user_name=name,get_notice=get_notice)

@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        user={
            "email":request.form.get('email'),
            "password":request.form.get('password')
        }
        get_notice=notice.find()
        if user['email'][0]=='b':
            find_user=collections.find_one({"email":user['email']})
            if check_password_hash(find_user['password'],user['password']):
                return render_template("student_dashboard.html",get_notice=get_notice,user_name=find_user['name'])
            else:
                return '404'
        elif user['email'][0]=='m':
            find_user=ad_collections.find_one({"email":user['email']})
            if check_password_hash(find_user['password'],user['password']):
                return render_template("admin_dashboard.html",get_notice=get_notice,user_name=find_user['name'],user_email=find_user['email'])
            else:
                return '404'
    return render_template("login.html")

@app.route("/register",methods=['POST','GET'])
def register():
    if request.method=='POST':
        hash_and_salted_password=generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user={
            "name":request.form.get('name'),
            "student_id":request.form.get('studentId'),
            "email":request.form.get('email'),
            "password":hash_and_salted_password
        }
        if new_user['email'][0]=='b':
            collections.insert_one(new_user)
            return redirect(url_for('home',email=new_user['email']))
        elif new_user['email'][0]=='m':
            ad_collections.insert_one(new_user)
            return redirect(url_for('home',email=new_user['email']))
    return render_template("register.html")

@app.route("/post/<name>")
def post(name):
    return render_template("post.html",user_name=name)

@app.route("/post_notice/<name>",methods=['POST','GET'])
def post_notice(name):
    current_date = datetime.date.today().strftime('%d-%m-%Y')
    new_notice={
        "notice":request.form.get('post_notice'),
        "date":str(current_date)
    }
    print(new_notice)
    notice.insert_one(new_notice)
    return redirect(url_for('admin_home',name=name))


@app.route("/find_student",methods=['POST','GET'])
def find_student():
    if request.method=='POST':
        get_id=request.form.get('student_id')
        find_student=student_room.find_one({"student_id":get_id})
        return render_template("admin_stud_details.html",student=find_student)
    return render_template("find_student.html")

@app.route("/rmfinder",methods=['POST','GET'])
def rmfinder():
    if request.method=='POST':
        get_id=request.form.get('student_id')
        find_student=student_room.find_one({"student_id":get_id})
        return render_template("student_details.html",student=find_student)
    return render_template("rmfinder.html")

@app.route("/find_student/add_student",methods=['POST','GET'])
def add_student():
    if request.method=='POST':
        new_student={
            "name":request.form.get('name'),
            "student_id":request.form.get('student_id'),
            "branch":request.form.get('branch'),
            "email":request.form.get('email'),
            "room_no":request.form.get('room_no')
        }
        student_room.insert_one(new_student)
    return render_template("add_student.html")

@app.route("/student_complaints",methods=['POST','GET'])
def student_complaints():
    if request.method=='POST':
        new_complaint={
            "block":request.form.get('block'),
            "complaint":request.form.get('complaint'),
            "room_no":request.form.get('room_no'),
            "student_id":request.form.get('student_id')
        }
        complaint.insert_one(new_complaint)
    return render_template("student_complaints.html")

@app.route("/admin_complaints")
def admin_complaints():
    complaints=complaint.find()
    return render_template("admin_complaints.html",complaints=complaints)

@app.route("/admin_complaints/completed/<complaint_id>",methods=['GET'])
def admin_complaints_completed(complaint_id):
    find_complaint=complaint.find_one({"_id":ObjectId(complaint_id)})
    complaint.delete_one(find_complaint)
    return redirect(url_for('admin_complaints'))

@app.route("/student_outpass",methods=['POST','GET'])
def student_outpass():
    new_outpass={
        "student_id":request.form.get('student_id'),
        "name":request.form.get('name'),
        "branch":request.form.get('branch'),
        "reason":request.form.get('reason'),
        "ped_of_absence":request.form.get('ped_of_absence')
    }
    outpass.insert_one(new_outpass)
    return render_template("student_outpass.html")

@app.route("/admin_outpass")
def admin_outpass():
    outpasses=outpass.find()
    return render_template("admin_outpass.html",outpasses=outpasses)

@app.route("/admin_outpass/grant_outpass/<id>")
def grant_outpass(id):
    find_outpass=outpass.find_one({"_id":ObjectId(id)})
    get_mail=find_outpass['student_id']+'@iiit-bh.ac.in'
    msg=f"\nYou are granted outpass.\nName of the student: {find_outpass['name']}\nStudent ID: {find_outpass['student_id']}\nBranch of the student: {find_outpass['branch']} \nPeriod of absence:{find_outpass['ped_of_absence']} \nReason for absence: {find_outpass['reason']}"
    with smtplib.SMTP("smtp.gmail.com",port=587) as connection: #change the host and port according to the requirement.
        connection.starttls()
        connection.login(user=admin_email,password=admin_password)
        connection.sendmail(
            from_addr=admin_email,
            to_addrs=get_mail,
            msg=f"subject:Outpass granted \n\n {msg}"
        )
    outpass.delete_one(find_outpass)
    return redirect(url_for('admin_outpass'))

@app.route("/view_more/<id>")
def view_outpass_stud_details(id):
    find_outpass=outpass.find_one({"_id":ObjectId(id)})
    return render_template("outpass_stud_details.html",details=find_outpass)

if __name__=="__main__":
    app.run(debug=True)