from flask import Flask,render_template,request,redirect,url_for
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aaec0770c47c1563dfb147b3bdb14072'

client=pymongo.MongoClient('mongodb://localhost:27017')
db=client['HSManager']
collections=db['registrations']
ad_collections=db['admin_reg']

@app.route("/<email>")
def home(email):
    if email[0]=='b':
        return render_template("student.html")
    elif email[0]=='m':
        return render_template("admin.html")

@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        user={
            "email":request.form.get('email'),
            "password":request.form.get('password')
        }
        if user['email'][0]=='b':
            find_user=collections.find_one({"email":user['email']})
        elif user['email'][0]=='m':
            find_user=ad_collections.find_one({"email":user['email']})
        print(find_user)
        if check_password_hash(find_user['password'],user['password']):
            return redirect(url_for('home',email=user['email']))
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

if __name__=="__main__":
    app.run(debug=True)