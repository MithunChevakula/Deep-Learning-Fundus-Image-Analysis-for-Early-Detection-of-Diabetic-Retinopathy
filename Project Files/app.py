import numpy as np
import os
import json
import tensorflow as tf
from tensorflow import keras
from keras.preprocessing import image
from keras.applications.inception_v3 import preprocess_input
from flask import Flask, request, flash, render_template, redirect, url_for

# Load model with legacy Keras format for compatibility
import tf_keras
model = tf_keras.models.load_model(r"Updated-Xception-diabetic-retinopathy.h5", compile=False)
app = Flask(__name__)
app.secret_key = "abc"
app.config['UPLOAD_FOLDER'] = "User_Images"

# Simple local JSON-based user database
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def find_user(mail):
    if not mail or not mail.strip():  # Don't match empty/None/whitespace emails
        return None
    mail = mail.strip()
    users = load_users()
    for user in users:
        if user.get('mail', '').strip() == mail:
            return user
    return None

def validate_password(password):
    """Password must have at least 8 chars, 1 uppercase, 1 lowercase, 1 digit"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, ""

def validate_phone(phone):
    """Phone must be exactly 10 digits"""
    if not phone.isdigit():
        return False, "Phone number must contain only digits"
    if len(phone) != 10:
        return False, "Phone number must be exactly 10 digits"
    return True, ""

# default home page or route
user = ""

@app.route('/')
def index():
    return render_template('index.html', pred="Login", vis ="visible")

@ app.route('/index')
def home():
    return render_template("index.html", pred="Login", vis ="visible")


# registration page
@ app.route('/register',methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mail = request.form.get("emailid", "").strip()
        mobile = request.form.get("num", "").strip()
        pswd = request.form.get("pass", "").strip()
        
        print(f"Registration attempt: name={name}, mail={mail}, mobile={mobile}, pswd={pswd}")
        
        # Validate required fields FIRST
        if not name or not mail or not mobile or not pswd:
            return render_template('register.html', pred="Please fill in all fields")
        
        # Validate phone number (10 digits)
        phone_valid, phone_error = validate_phone(mobile)
        if not phone_valid:
            return render_template('register.html', pred=phone_error)
        
        # Validate password (uppercase, lowercase, digit, min 8 chars)
        pwd_valid, pwd_error = validate_password(pswd)
        if not pwd_valid:
            return render_template('register.html', pred=pwd_error)
        
        # Only check for existing user AFTER all validation passes
        existing_user = find_user(mail)
        print(f"Existing user check: {existing_user}")
        
        if existing_user is not None:
            return render_template('register.html', pred="You are already a member, please login using your details")
        
        # Create new user
        data = {
            'name': name,
            'mail': mail,
            'mobile': mobile,
            'psw': pswd
        }
        print(f"Saving new user: {data}")
        users = load_users()
        users.append(data)
        save_users(users)
        return render_template("register.html", pred="Registration Successful! Please login using your details")
    else:
        return render_template('register.html', pred="")


@ app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        user = request.args.get('mail', '').strip()
        passw = request.args.get('pass', '').strip()
        
        # If no credentials provided (first visit or empty submission)
        if not user and not passw:
            # Check if this is a form submission (has query params) vs first visit
            if 'mail' in request.args or 'pass' in request.args:
                return render_template('login.html', pred="Enter your login details.")
            return render_template('login.html', pred="")
        
        # Validate required fields - one field missing
        if not user or not passw:
            return render_template('login.html', pred="Enter your login details.")
        
        print(f"Login attempt: {user}, {passw}")
        existing_user = find_user(user)
        print(f"Found user: {existing_user}")
        
        if existing_user is None:
            return render_template('login.html', pred="Wrong credentials. Please check your email and password.")
        else:
            if user == existing_user['mail'] and passw == existing_user['psw']:
                flash("Login Successful! Welcome " + str(existing_user['name']))
                return render_template('index.html', pred="Login Successful! Welcome " + str(existing_user['name']), vis ="hidden", vis2="visible")
            else:
                return render_template('login.html', pred="Wrong credentials. Please check your email and password.")
    else:
        return render_template('login.html')


@ app.route('/logout')
def logout():
    return render_template('logout.html')

@app.route("/predict",methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        f = request.files['file']
        # getting the current path 1.e where app.py is present
        basepath = os.path.dirname(__file__)
        #print ( " current path " , basepath )
        # from anywhere in the system we can give image but we want that
        filepath = os.path.join(str(basepath), 'User_Images', str(f.filename))
        #print ( " upload folder is " , filepath )
        f.save(filepath)
        img = tf.keras.utils.load_img(filepath, target_size=(299, 299))
        x = tf.keras.utils.img_to_array(img)  # ing to array
        x = np.expand_dims(x, axis=0)  # used for adding one more dimension
        #print ( x )
        img_data = preprocess_input(x)
        prediction = np.argmax(model.predict(img_data), axis=1)
        index = [' No Diabetic Retinopathy ', ' Mild NPDR ',
                 ' Moderate NPDR ', ' Severe NPDR ', ' Proliferative DR ']
        result = str(index[prediction[0]])
        print(result)
        return render_template('prediction.html', prediction=result, fname = filepath)
    else:
        return render_template("prediction.html")

if __name__ == "__main__":
    app.debug = False
    app.run()
