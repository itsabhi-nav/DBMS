import os
import pandas as pd
import datetime
import re
from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect, url_for
from pymongo import MongoClient
from email_utils import sendEmail
from insert_data import insert_data

app = Flask(__name__)
app.secret_key = 'abcdefghijklmnopqrstuvwxyz'

# Load environment variables from .env file
load_dotenv()

# Enter your authentication details
GMAIL_ID = os.getenv('GMAIL_ID')
GMAIL_PSWD = os.getenv('GMAIL_PSWD')

@app.route('/')
def index():
    # Connect to MongoDB
    client = MongoClient("mongodb+srv://dubeyabhinav1001:dubey@cluster0.rjzqrrm.mongodb.net/?retryWrites=true&w=majority", ssl=True)
    db = client['dbms']  # Replace 'your_database_name' with your actual database name
    collection = db['bday']  # Replace 'your_collection_name' with your actual collection name

    # Fetch data from MongoDB
    df = pd.DataFrame(list(collection.find()))

    sent_emails = session.get('sent_emails', [])

    if not df.empty:  # Check if DataFrame is not empty
        today = datetime.datetime.now().strftime("%d-%m")
        yearNow = datetime.datetime.now().strftime("%Y")

        writeInd = []
        for index, item in df.iterrows():
            # Check if 'Birthday' is already a datetime object
            if isinstance(item['Birthday'], datetime.datetime):
                # Skip parsing if it's already a datetime object
                pass
            else:
                # Handle date format mismatch
                try:
                    item['Birthday'] = datetime.datetime.strptime(item['Birthday'], "%Y-%m-%d")  # Convert string to datetime
                except ValueError:
                    item['Birthday'] = datetime.datetime.strptime(item['Birthday'], "%d-%m-%Y")  # Convert string to datetime

            bday = item['Birthday'].strftime("%d-%m")  # Convert datetime to string
            if today == bday and yearNow not in str(item['Year']):
                try:
                    sendEmail(item['Email'], "Happy Birthday", item['Dialogue'], GMAIL_ID, GMAIL_PSWD)
                    sent_emails.append({'name': item['Name'], 'status': 'success'})  # Add name to the list of sent emails with status
                    print(f"Wished Happy Birthday to {item['Name']}.")
                except Exception as e:
                    sent_emails.append({'name': item['Name'], 'status': 'failed'})  # Add name to the list of sent emails with status
                    print(f"Error sending email to {item['Email']}: {str(e)}")  # Print error if email sending fails
                writeInd.append(index)

        print("Sent Emails:", sent_emails)  # Print sent emails for debugging

        for i in writeInd:
            yr = df.at[i, 'Year']
            df.loc[i, 'Year'] = str(yr) + ',' + str(yearNow)

        # Save the updated DataFrame back to MongoDB
        collection.delete_many({})  # Clear existing data in the collection
        collection.insert_many(df.to_dict('records'))

    client.close()  # Close the MongoDB connection

    session['sent_emails'] = sent_emails  # Storing sent_emails in session

    return render_template('index.html', sent_emails=sent_emails)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Process the form data submitted via POST method
        name = request.form['name']
        email = request.form['email']
        birthday_str = request.form['birthday']
        dialogue = request.form['dialogue']
        
        # Validate the date format (YYYY-MM-DD)
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', birthday_str):
            return "Invalid date format. Please use YYYY-MM-DD format for birthday."

        # Convert birthday string to a datetime object
        try:
            birthday = datetime.datetime.strptime(birthday_str, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date. Please provide a valid date in YYYY-MM-DD format."
        
        # Convert birthday date to datetime object
        birthday_datetime = datetime.datetime.combine(birthday, datetime.datetime.min.time())

        # Connect to MongoDB
        client = MongoClient("mongodb+srv://dubeyabhinav1001:dubey@cluster0.rjzqrrm.mongodb.net/?retryWrites=true&w=majority")
        db = client['dbms']  
        collection = db['bday']  

        # Check if data already exists
        existing_data = collection.find_one({"Name": name, "Email": email})
        if existing_data:
            return "Data already exists in the database. Cannot add duplicate entries."
        
        # Insert new user data into the database
        new_user = {
            "Name": name,
            "Birthday": birthday_datetime,  # Use the converted datetime object
            "Year": str(birthday.year),
            "Email": email,
            "Dialogue": dialogue
        }
        collection.insert_one(new_user)
        client.close()

        # Redirect to the index page after adding the user
        return redirect(url_for('index'))
    else:
        # Render the form for adding a new user
        return render_template('add_user.html')

if __name__ == "__main__":
    with app.app_context():
        insert_data()  # Insert data before starting the Flask app
    app.run(debug=True)
