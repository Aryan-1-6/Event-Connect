from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_moment import Moment
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room
from flask_login import current_user, login_required, LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from multiprocessing import Process
import mysql.connector
import json
import pandas as pd
import nltk
import os
from thefuzz import fuzz
from werkzeug.utils import secure_filename
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime

sid = SentimentIntensityAnalyzer()

with open("config.json", "r") as f:
    config = json.load(f)


# Create a database connection
cnx = mysql.connector.connect(
    host="localhost",  # Update with your host
    user=config["username"],
    password=config["password"],
    database="se_project"
)
# Create a cursor object to execute SQL queries
cursor = cnx.cursor()
app = Flask(__name__)
bcrypt = Bcrypt(app)
moment = Moment(app)
app.secret_key = '1234567890'
socketio = SocketIO(app)


# login_manager = LoginManager()
# login_manager.init_app(app)
# csrf = CSRFProtect(app)


# @login_manager.user_loader
# def load_user(user_id):
#     query = "SELECT * FROM User WHERE UserID = %s"
#     cursor.execute(query, (user_id,))
#     user_data = cursor.fetchone()
#     if user_data:
#         # Create a User object using UserMixin
#         user = User()
#         user.id = user_data['UserID']
#         return user
#     else:
#         return None


#----
def get_user_by_email(email):
    query = f"SELECT * FROM User WHERE Email = '{email}'"
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def get_org_id(name):
    query=f"SELECT OrganizationID FROM Organization where Name='{name}'"
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def create_new_user(form_data):
    email = form_data.get("email")
    password = form_data.get("password")
    role = form_data.get("role")  # Assuming "role" is the name of the checkbox
    organization = form_data.get("organization")

    # Extract the user's name from the email
    name = email.split("@")[0]
    # Get the organization ID (if it exists)
    organization_id = get_org_id(organization)
    if organization_id:
        organization_id = organization_id[0][0]
    else:
        organization_id = None  # Use None, not 'NULL'

    # Hash the user's password before saving it to the database
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Check if a profile picture file was uploaded
    if "profileImage" in request.files:
        profile_image = request.files["profileImage"]
        if profile_image.filename != "":
            # Save the profile picture to a folder and store the path in the database
            upload_folder = "static/profile_images"
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Create a unique filename for the profile picture
            filename = os.path.join(upload_folder, secure_filename(profile_image.filename))
            profile_image.save(filename)

    # Use parameterized query to prevent SQL injection
    insert_query = "INSERT INTO User (Name, Email, Role, Password, OrganizationID, profile_pic) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (name, email, role, hashed_password, organization_id, filename if "filename" in locals() else None)
    cursor.execute(insert_query, values)
    cnx.commit()


#------
#create event
def create_new_event(form_data, user_id):
    title = form_data.get("title")
    description = form_data.get("description")
    event_date = form_data.get("event_date")  # Assuming event date is part of form data
    created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Assuming you want to record the current date/time
    topic = form_data.get("topic")
    organizer_id = user_id  # Event organizer is the user creating the event
    event_type = form_data.get("event_type")    
    location = form_data.get("location")
    footfall = form_data.get("footfall")
    popularity_factor = form_data.get("popularity_factor")

    # Check if the user is an event organizer
    query = f"SELECT Role FROM User WHERE UserID={user_id} AND Role='Organiser'"
    cursor.execute(query)
    result = cursor.fetchone()
    if not result:
        return "Only event organizers can create events."

    values = (title, description, event_date, created_date, topic, organizer_id, event_type, location, footfall, popularity_factor)
    insert_query = "INSERT INTO Event (Title, Description, EventDate, CreatedAtDate, Topic, OrganizerID, EventType, Location, footfall, popularity_factor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_query, values)
    cnx.commit()

    event_id = cursor.lastrowid
    return event_id


@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST" and "user_id" in session:
        form_data = request.form.to_dict()
        user_id = session["user_id"]
        event_id = create_new_event(form_data,user_id)
        return redirect(url_for("create_package", event_id=event_id))
    elif "user_id" not in session:
        flash("Please Login to add posts", "danger")
    return render_template("create_post.html")


def create_new_package(form_data, user_id, event_id):
    name = form_data.get("name")
    description = form_data.get("description")
    organizer_id = user_id  # Event organizer is the user creating the event
    price_from = form_data.get("price_from")
    price_to = form_data.get("price_to")

    query = f"SELECT Role FROM User WHERE UserID={user_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    role = "Organiser"
    role = (role,)
    if result != role:
        return "Only event organizers can create events."
    values = (event_id, organizer_id, name, description, price_from, price_to)
    insert_query = "INSERT INTO Package (EventID, OrganizerID, Name, Description, Price, Price_limit) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_query, values)
    cnx.commit()

    return "Package created successfully."

@app.route("/create_packages/<int:event_id>", methods=["GET", "POST"])
def create_package(event_id):
    if request.method == "POST" and "user_id" in session:
        form_data = request.form.to_dict()
        user_id = session["user_id"]
        create_new_package(form_data,user_id,event_id)
        return redirect(url_for("create_package", event_id=event_id))
    elif "user_id" not in session:
        flash("Please Login to add posts", "danger")
    return render_template("create_package.html",event_id=event_id)


#-----
#searching mech
def get_best_matching_titles(search_query):
    query="SELECT Title,EventID FROM Event;"
    cursor.execute(query)
    result=cursor.fetchall()
    titles=[]
    for title in result:
        titles.append([title[0],title[1]])
    string_match_dict={}
    for title in titles:
        string_match_dict[title[1]]=fuzz.ratio(title[0], search_query)
    string_match_dict=sorted(string_match_dict.items(), key=lambda x:x[1], reverse=True)
    string_match_dict = dict(string_match_dict)
    return list(string_match_dict.keys())

#----
def fetch_post_from_database(post_id):
    query = "SELECT Event.EventID, Event.Title, Event.Location, Event.footfall, Event.popularity_factor, Event.Description, Event.EventDate ,Event.CreatedAtDate, Event.Topic, Event.EventType, User.Name FROM Event INNER JOIN User ON Event.OrganizerID = User.UserID WHERE Event.EventID = %s;"
    cursor.execute(query, (post_id,))
    post_data = cursor.fetchone()

    if post_data:
        post = {
            'EventID': post_data[0],
            'Title': post_data[1],
            'Location': post_data[2],
            'footfall': post_data[3],
            'popularity_factor': post_data[4],
            'Description': post_data[5],
            'EventDate': post_data[6],
            'CreatedAtDate': post_data[7],
            'Topic': post_data[8],
            'Type': post_data[9],
            'Name': post_data[10],
        }

        return post

    return None

def fetch_packages_from_database(event_id):
    query = "SELECT Package.PackageID, Package.Name, Package.Price, Package.Price_limit, Package.Description FROM Package WHERE Package.EventID = %s;"
    cursor.execute(query, (event_id,))
    rows = cursor.fetchall()

    packages = []
    for row in rows:
        package = {
            'PackageID': row[0],
            'Name': row[1],
            'Price_from': row[2],
            'Price_to': row[3],
            'Description': row[4],
        }
        packages.append(package)
    return packages


#display selected event
@app.route("/view_post/<int:event_id>", methods=["GET","POST"])
def view_post(event_id):
    # Fetch the specific post from the database
    session['previous_route'] = request.url
    post = fetch_post_from_database(event_id)
    packages = fetch_packages_from_database(event_id)
    if post is None:
        flash("Post not found", "danger")
        return redirect(url_for("home"))
    if "user_id" in session:
        user_id = session["user_id"]
        print(user_id, " jeivjv")
    # Fetch comments for the post
    # comments = fetch_comments_for_post(post_id)
    # df=get_sentiment_analytics(post_id)
    # data = {
        # 'labels': list(df['SentimentLabel'].value_counts().index),
        # 'data': list(df['SentimentLabel'].value_counts().values),
        # 'colors': ['green', 'red', 'gray'],
    # }
    # data['data'] = [int(x) for x in data['data']]

    # grouped = df.groupby(['CreatedAtDate', 'SentimentLabel']).size().unstack().fillna(0)

    # Check if 'positive', 'negative', and 'neutral' are present in the grouped DataFrame
    # if 'positive' not in grouped:
        # grouped['positive'] = [0] * len(grouped)
    # if 'negative' not in grouped:
        # grouped['negative'] = [0] * len(grouped)
    # if 'neutral' not in grouped:
        # grouped['neutral'] = [0] * len(grouped)

    # data2 = {
        # "labels": list(grouped.index),
        # "positive": list(grouped['positive']),
        # "negative": list(grouped['negative']),
        # "neutral": list(grouped['neutral']),
    # }
# 
    # data2['positive'] = [int(x) for x in data2['positive']]
    # data2['negative'] = [int(x) for x in data2['negative']]
    # data2['neutral'] = [int(x) for x in data2['neutral']]
    csrf_token=generate_csrf()

    # Render a template to view the post with comments
    return render_template("view_post.html", post=post, packages=packages, csrf_token=csrf_token, user_id=user_id)



@app.route("/view_package", methods=["GET"])
def view_package():
    # Fetch package details from the database based on the package_id
    # package = fetch_package(package_id)
    package = request.args.get("package", None)
    package_str = package.strip('{}')

    # Split the string into key-value pairs
    pairs = package_str.split(', ')

    # Initialize an empty dictionary to store the key-value pairs
    package_dict = {}

    # Iterate through the key-value pairs
    for pair in pairs:
        # Split each pair into key and value
        key, value = pair.split(': ')
        # Remove single quotes from keys and values
        key = key.strip("'")
        # Check if the value is numeric and convert it accordingly
        if value.startswith("'") and value.endswith("'"):
            value = value.strip("'")
        if value.isdigit():
            value = int(value)
        elif value.startswith("Decimal('") and value.endswith("')"):
            value = float(value.strip("Decimal('").rstrip("')"))
        # Add key-value pair to the dictionary
        package_dict[key] = value


    package = package_dict
    # for key, value in package.items():
        # pack_dict[key] = value
    # print(pack_dict)
    if package is None:
        flash("Package not found.", "danger")
        return redirect(url_for("home"))  # Redirect to home page or any other appropriate page
    return render_template("view_package.html", package=package)  

#------
# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch user from the database based on the provided email
        user = get_user_by_email(email)  # Replace with your database logic

        if len(user)>0:
            user=user[0]
            # Check if the provided password matches the hashed password in the database
            if bcrypt.check_password_hash(user[4], password):
                # Set a session variable to track the user's session
                session["user_id"] = user[0]
                flash("Login successful", "success")
                return redirect(url_for("home"))  # Redirect to the home page upon successful login
            else:
                flash("User with the entered Credentials was not found. Please try again.", "danger")
        else:
            flash("User with the entered Credentials was not found. Please try again.", "danger")

    return render_template("login.html")  # Display the login form

def get_organizations():
    organizations = []
    cursor.execute("SELECT name FROM organization")

    # Fetch all rows from the result set
    rows = cursor.fetchall()

    # Iterate over the rows and append organization names to the list
    for row in rows:
        organizations.append(row[0])

    return organizations

# Signup route
@app.route("/", methods=["GET", "POST"])
def signup():
    organizations = get_organizations()
    if request.method == "POST":
        # Capture all form inputs as a dictionary
        form_data = request.form.to_dict()
        email = form_data.get("email")
        if len(get_user_by_email(email)) > 0:
            flash("A user with this Email already exists", "danger")
        else:
            create_new_user(form_data)
            flash("Signup successful", "success")
            return redirect(url_for("login"))  # Redirect to the home page upon successful signup
    return render_template("signup.html", organizations=organizations)  # Display the signup form

@app.route("/logout", methods=["POST"])
def logout():
    if  request.method == "POST":
        session.clear()
        return redirect(url_for("login"))

#--------
def get_ranked_posts(ranked_ids):
    dfs=[]
    for event_id in ranked_ids:
        query = f"SELECT Event.*,Name FROM Event join User ON Event.OrganizerID=User.UserID WHERE EventID={event_id};"
        cursor.execute(query)
        result = cursor.fetchall()
        posts_df=pd.DataFrame(result,columns=["EventID","Title", "Location", "footfall", "popularity_factor","Description","EventDate","CreatedAtDate","Status","Topic","OrganizerID","EventType","PostedBy"])
        dfs.append(posts_df.head(10))    
    result_df=pd.concat(dfs,axis=0)
    return result_df

def get_stats_for_post(post_id):
    query1 = f"SELECT Upvotes+Downvotes FROM Post WHERE PostID={post_id};"
    cursor.execute(query1)
    total_votes= cursor.fetchall()
    total_votes=total_votes[0][0]
    query2=f"SELECT COUNT(*) FROM Comment WHERE PostID={post_id}"
    cursor.execute(query2)
    total_comments= cursor.fetchall()
    total_comments=total_comments[0][0]
    query3=f"SELECT Content FROM Comment WHERE PostID={post_id}"
    cursor.execute(query3)
    comments= cursor.fetchall()
    neg=0
    pos=0
    neut=0
    for comment in comments:
        comment=comment[0]
        sentiment_scores = sid.polarity_scores(comment)
        compound_score = sentiment_scores['compound']
        if compound_score<-0.05:
            neg+=1
        elif compound_score>0.05:
            pos+=1
        else:
            neut+=1

    query4=f"SELECT Downvotes FROM Post WHERE PostID={post_id};"
    cursor.execute(query4)
    downvotes=cursor.fetchall()
    downvotes=downvotes[0][0]
    return [total_votes,total_comments,neg,pos,neut,downvotes]


# app.config['MAX_POSTS'] = 100
# max_posts = app.config['MAX_POSTS']
def rank_posts():
    query0="SELECT DISTINCT EventID from Event;"
    cursor.execute(query0)
    all_posts= cursor.fetchall()
    post_to_score={}
    for post_id in all_posts:
        post_id=post_id[0]
        # stats=get_stats_for_post(post_id)
        # score=stats[0]+stats[1]-stats[2]+stats[3]-0.5*stats[5]
        score = 100
        # max_posts -= 1
        post_to_score[post_id]=score
    res= post_to_score.copy()
    sorted_res = sorted(res.items(), key=lambda x:x[1], reverse=True)
    sorted_res = dict(sorted_res)
    return list(sorted_res.keys())

@app.route("/home", methods=["GET", "POST"])
def home():
    # posts_df=get_posts()
    ranked_ids=rank_posts()
    session['previous_route'] = request.url
    checkloggedin=("user_id" in session)
    search_query=""
    search_query = request.form.get('search_query')
    if search_query is not None:
        ranked_ids=get_best_matching_titles(search_query)
    if ranked_ids != []:
        posts_df=get_ranked_posts(ranked_ids)
    else:
        posts_df = None


    user_id = session.get("user_id")

    query = f"SELECT role FROM User WHERE UserID = {user_id};"
    cursor.execute(query)
    role = cursor.fetchone()[0]

    if role == "Sponsor":
        response_list = get_responses(user_id)
        return render_template("sponsor_home.html", posts_df=posts_df, response_list=response_list, checkloggedin=checkloggedin)
    else:
        interest_list = pd.DataFrame(get_interests(user_id))
        return render_template("home.html", posts_df=posts_df, interest_list=interest_list, checkloggedin=checkloggedin)


def get_responses(user_id):
    query = "SELECT User.Name, Interest.PackageID, Interest.interaction_date, Interest.accepted, Package.EventID, Interest.SponsorID FROM Interest INNER JOIN User ON Interest.OrganizerID = User.UserID INNER JOIN Package ON Package.PackageID = Interest.PackageID WHERE Interest.SponsorID=%s;"
    cursor.execute(query, (user_id,))

    response_list = []
    for response in cursor.fetchall():
        if(response[3] == 0):
            continue
        if(response[3] == -1):
            val="Rejected"
        else:
            val="Accepted"
        response_dict = {
            "sponsor_name": response[0],
            "package_id": response[1],
            "interaction_date": pd.to_datetime(response[2]),
            "accepted": val,
            "event_id": response[4],
            "sponsor_id": response[5]
        }
        response_list.append(response_dict)
    print(response_list)
    return response_list

def get_interests(user_id):
    query = "SELECT User.Name, Interest.PackageID, Interest.interaction_date, Interest.accepted, Package.EventID, Interest.SponsorID FROM Interest INNER JOIN User ON Interest.SponsorID = User.UserID INNER JOIN Package ON Package.PackageID = Interest.PackageID WHERE Interest.OrganizerID=%s;"
    cursor.execute(query, (user_id,))

    interest_list = []
    for interest in cursor.fetchall():
        if(interest[3]):
            continue
        interest_dict = {
            "sponsor_name": interest[0],
            "package_id": interest[1],
            "interaction_date": pd.to_datetime(interest[2]),
            "accepted": bool(interest[3]),
            "event_id": interest[4],
            "sponsor_id": interest[5]
        }
        interest_list.append(interest_dict)
    print(interest_list)
    return interest_list

@app.route("/accept_request", methods=["POST"])
def accept_interest():
    print("mdmdls")
    package_id = request.form.get("package_id")
    if package_id != "":
        query = "UPDATE Interest SET accepted=1 WHERE PackageID=%s;"
        cursor.execute(query, (package_id,))
        cnx.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/reject_request", methods=["POST"])
def reject_interest():
    package_id = request.form.get("package_id")
    if package_id != "":
        query = "UPDATE Interest SET accepted=-1 WHERE PackageID=%s;"
        cursor.execute(query, (package_id,))
        cnx.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/user_profile/<int:user_di>", methods=["GET", "POST"])
def user_profile(user_di):
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        # Fetch posts created by the logged-in user
        query = f"SELECT * FROM User WHERE UserID = {user_di}"
        query2 = f"SELECT * FROM Event WHERE OrganizerID = {user_di}"

        cursor.execute(query)
        user_id = cursor.fetchall()
        posts_df = pd.DataFrame(user_id, columns=["UserID","Name","Email","Role","Password","OrganizationID","profile_pic"])
        cursor.execute(query2)
        user_post = cursor.fetchall()
        user_post_df = pd.DataFrame(user_post, columns=["EventID", "Title", "Location","footfall","popularity_factor","Description", "EventDate", "CreatedAtDate", "Status", "Topic", "OrganizerID", "EventType"])
        temp = posts_df["OrganizationID"][0]
        # print(temp)
        if(temp is not None):
            query2 = f"select Name from organization where OrganizationID = {temp};"
            cursor.execute(query2)
            user_org = cursor.fetchall()
            user_org = user_org[0][0]

        else:
            user_org = None


        checkloggedin = True
        return render_template("user_profile.html", posts_df=posts_df, user_org=user_org,temp=temp, user_post_df=user_post_df, checkloggedin=checkloggedin)
    else:
        flash("Please log in to view your posts", "danger")
        return redirect(url_for("login"))

@app.route("/my_post", methods=["GET", "POST"])
def my_posts():
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        # Fetch posts created by the logged-in user
        query = f"SELECT * FROM Event WHERE OrganizerID = {user_id}"
        cursor.execute(query)
        user_posts = cursor.fetchall()
        posts_df = pd.DataFrame(user_posts, columns=["EventID", "Title", "Location","footfall","popularity_factor","Description","EventDate", "CreatedAtDate", "Status", "Topic", "OrganizationID", "PackageID", "EventType"])
        post_id = 1
        checkloggedin = True
        return render_template("my_post.html", posts_df=posts_df, post_id = post_id, checkloggedin=checkloggedin)
    else:
        flash("Please log in to view your posts", "danger")
        return redirect(url_for("login"))


@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if "user_id" in session:
        user_id = session["user_id"]

        # Check if the post with the given ID exists and belongs to the logged-in user
        query = "SELECT OrganizerID FROM Event WHERE EventID = %s"
        cursor.execute(query, (post_id,))
        result = cursor.fetchone()

        if result and result[0] == user_id:
            # If the post exists and belongs to the user, delete it
            delete_query = "DELETE FROM Event WHERE EventID = %s"
            cursor.execute(delete_query, (post_id,))
            cnx.commit()
            flash("Event deleted successfully", "success")
        else:
            flash("You don't have permission to delete this event", "danger")
    else:
        flash("Please log in to delete events", "danger")

    # Redirect back to the "My Posts" page
    return redirect(url_for("my_posts"))


def fetch_filtered_posts(location, eventType, eventTopic, footfall_to, footfall_from, budget_from, budget_to):
    # Start building the SQL query
    if budget_from == "" or budget_to == "":
        query = "SELECT DISTINCT Event.EventID, Event.Title, Event.Location, Event.footfall, Event.popularity_factor, Event.Description, Event.EventDate, Event.CreatedAtDate, Event.Status, Event.Topic, Event.EventType, Event.OrganizerID,User.Name "\
        "FROM Event INNER JOIN User ON Event.OrganizerID = User.UserID"
    else:
        query = """
            SELECT DISTINCT 
                Event.EventID, 
                Event.Title, 
                Event.Location, 
                Event.footfall, 
                Event.popularity_factor, 
                Event.Description, 
                Event.EventDate, 
                Event.CreatedAtDate, 
                Event.Status, 
                Event.Topic, 
                Event.EventType, 
                Event.OrganizerID,
                User.Name,
                Package.Price,
                Package.Price_limit 
            FROM 
                Event 
            INNER JOIN 
                User 
            ON 
                Event.OrganizerID = User.UserID
            INNER JOIN
                Package 
            ON 
                Package.EventId = Event.EventID
            """

    
    a,b,c,d,e = 0,0,0,0,0
    if location != "":
        location = (location,)
        a=1
    if eventType != "":
        eventType = (eventType,)
        b=1
    if eventTopic != "":
        eventTopic = (eventTopic,)
        c=1   
    if footfall_to != "" and footfall_from != "":
        footfall_to = (footfall_to,)
        footfall_from = (footfall_from,) 
        d=1   
    if budget_from != "" and budget_to != "":
        budget_from = (budget_from,)
        budget_to = (budget_to,)
        e=1

    params = []
    if a:
        query += " AND Event.Location = %s"
        params.append(location)
    if b:
        if a:
            query += " AND Event.EventType = %s"
        else:
            query += " WHERE Event.EventType = %s"
        params.append(eventType)
    if c:
        if a or b:
            query += " AND Event.Topic = %s"
        else:
            query += " WHERE Event.Topic = %s"
        params.append(eventTopic)
    if d:
        if a or b or c:
            query += " AND Event.footfall >= %s AND Event.footfall <= %s"
        else:
            query += " WHERE Event.footfall >= %s AND Event.footfall <= %s"
        params.append(footfall_from)
        params.append(footfall_to)  
    if e:
        if a or b or c or d:
            query += " AND Package.Price >= %s AND Package.Price_limit <= %s"
        else:
            query += " WHERE Package.Price >= %s AND Package.Price_limit <= %s"
        params.append(budget_from)
        params.append(budget_to)  
 
    params_flat = tuple(item[0] for item in params)
    cursor.execute(query, params_flat)

    filtered_posts = []

    for post_data in cursor.fetchall():
        post = {
            'EventID': post_data[0],
            'Title': post_data[1],
            'Location': post_data[2],
            'footfall': post_data[3],
            'popularity_factor': post_data[4],
            'Description': post_data[5],
            'EventDate': post_data[6],
            'CreatedAtDate': post_data[7],
            'Status': post_data[8],
            'Topic': post_data[9],
            'EventType': post_data[10],
            'OrganizerID': post_data[11],
            'Name': post_data[12]
        }
        filtered_posts.append(post)

    return filtered_posts



@app.route('/apply_filters', methods=['POST'])
def apply_filters():
    # Retrieve filter parameters from the form data
    location = request.form.get('location')
    eventType = request.form.get('eventType')
    eventTopic = request.form.get('eventTopic')
    budgetFrom = request.form.get('budgetFrom')
    budgetTo = request.form.get('budgetTo')
    attendeesFrom = request.form.get('attendeesFrom')
    attendeesTo = request.form.get('attendeesTo')


    posts_df = pd.DataFrame(fetch_filtered_posts(location, eventType, eventTopic,attendeesTo, attendeesFrom, budgetFrom, budgetTo))

    return render_template('sponsor_home.html', posts_df=posts_df)

def get_organizer_info(package_id):
    # Your logic to fetch the organizer's information based on the package ID goes here
    # For example, you might join the Packages table with the Users table to get the organizer's information
    # Assuming you have a Packages table with an organizer_id column that references the Users table
    query = "SELECT Package.OrganizerID FROM Package WHERE Package.PackageId = %s"
    print(package_id," ccmmc")
    package_id = tuple(package_id)
    cursor.execute(query, (package_id))
    post_data = cursor.fetchall()
    if post_data != []:
        return post_data[0]
    else:
        return None


@app.route('/show_interest', methods=['POST'])
def show_interest():
    print('evwevedv')
    package_id = request.json.get('packageId')
    sponsor_id = request.json.get('sponsorId')
    print(sponsor_id)
    # Get the organizer's identifier associated with the package
    organizer_identifier = get_organizer_info(package_id)

    if organizer_identifier:
        # Emit a WebSocket event to notify the organizer

        # Fetch package details
        organizer_id = str(organizer_identifier[0])
        socketio.emit('interest_shown', {'packageId': package_id}, room=organizer_id)
        interaction_type = "sponsor_approach"
        accepted= 0
        
        query = "INSERT into Interest (SponsorID, OrganizerID, PackageID, interaction_type, accepted) VALUES (%s,%s,%s,%s,%s)"
        values =  (sponsor_id, organizer_id, package_id, interaction_type, accepted)
        print(values)
        cursor.execute(query, values)
        cnx.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Organizer identifier not found.'}), 405





@app.route("/organization_info/<int:org_id>", methods=["GET", "POST"])
def organization_info(org_id):
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        checkloggedin = True

        query = f"SELECT * FROM Organization;"
        cursor.execute(query)
        other_organizations = cursor.fetchall()
        # Convert the list of dictionaries to a Pandas DataFrame
        other_organizations = pd.DataFrame(other_organizations, columns=["OrganizationID","Name","ContactInformation","Description","Location"])
        org_id = str(org_id)
        # Pass the organization ID to the template
        return render_template("organization_info.html", other_organizations=other_organizations, org_id=org_id, checkloggedin=checkloggedin)
    else:
        flash("Please log in to view organization information", "danger")
        return redirect(url_for("login"))

def run_flask_app(host, port):
    app.run(host=host, port=port)

if __name__ == "__main__":
    
    # app.run(host='192.168.56.1') 
    app.run(debug=True) 
    
    # IP and port for the first instance
    # host1 = '127.0.0.1'  # Replace with your desired IP address
    # port1 = 5000  # Replace with your desired port number

    # # IP and port for the second instance
    # host2 = '192.168.56.1'  # Replace with your desired IP address
    # port2 = 5000  # Replace with your desired port number

    # # Create two separate processes for running each instance
    # process1 = Process(target=run_flask_app, args=(host1, port1))
    # process2 = Process(target=run_flask_app, args=(host2, port2))

    # # Start both processes
    # process1.start()
    # process2.start()
    # # app.run(host=host2)
    # # Wait for both processes to finish
    # process1.join()
    # process2.join()
# if __name__ == '__main__':
#     app.run(debug=True)


