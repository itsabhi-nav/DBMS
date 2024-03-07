import os
import pandas as pd
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect
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
    client = MongoClient("mongodb+srv://dubeyabhinav1001:dubey@cluster0.rjzqrrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", ssl=True)
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
            # Check if 'Birthday' is already a Timestamp object
            if isinstance(item['Birthday'], pd.Timestamp):
                item['Birthday'] = item['Birthday'].to_pydatetime()  # Convert Pandas Timestamp to Python datetime
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
        name = request.form['name']
        email = request.form['email']
        birthday = request.form['birthday']
        dialogue = request.form['dialogue']

        # Convert the date string to the correct format
        try:
            birthday = datetime.datetime.strptime(birthday, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            return "Invalid date format. Please enter the date in the format DD-MM-YYYY."

        # Connect to MongoDB
        client = MongoClient("mongodb+srv://dubeyabhinav1001:dubey@cluster0.rjzqrrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", ssl=True)
        db = client['dbms']  # Replace 'your_database_name' with your actual database name
        collection = db['bday']  # Replace 'your_collection_name' with your actual collection name

        # Check if the email already exists in the database
        existing_user = collection.find_one({'Email': email})
        if existing_user:
            return "User with this email already exists in the database."

        # Insert new user data into the database
        new_user = {
            'Name': name,
            'Email': email,
            'Birthday': birthday,
            'Dialogue': dialogue,
            'Year': []  # You can initialize this with an empty list
        }
        collection.insert_one(new_user)
        client.close()

        return redirect('/')
    else:
        return render_template('add_user.html')

if __name__ == "__main__":
    with app.app_context():
        insert_data()  # Insert data before starting the Flask app
    app.run(debug=True)
