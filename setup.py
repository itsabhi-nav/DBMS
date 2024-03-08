import os
import pandas as pd
import datetime
import re
from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect, url_for
from pymongo import MongoClient
from email_utils import sendEmail
import pymongo

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
    db = client['dbms']  
    collection = db['bday']  

    # Fetch data from MongoDB
    df = pd.DataFrame(list(collection.find()))

    sent_emails = session.get('sent_emails', [])

    if not df.empty:  
        today = datetime.datetime.now().strftime("%d-%m")
        yearNow = datetime.datetime.now().strftime("%Y")

        writeInd = []
        for index, item in df.iterrows():
            if isinstance(item['Birthday'], datetime.datetime):
                pass
            else:
                try:
                    item['Birthday'] = datetime.datetime.strptime(item['Birthday'], "%Y-%m-%d")  
                except ValueError:
                    item['Birthday'] = datetime.datetime.strptime(item['Birthday'], "%d-%m-%Y")  

            bday = item['Birthday'].strftime("%d-%m")  
            if today == bday and yearNow not in str(item['Year']):
                try:
                    sendEmail(item['Email'], "Happy Birthday", item['Dialogue'], GMAIL_ID, GMAIL_PSWD)
                    sent_emails.append({'name': item['Name'], 'status': 'success'})  
                    print(f"Wished Happy Birthday to {item['Name']}.")
                except Exception as e:
                    sent_emails.append({'name': item['Name'], 'status': 'failed'})  
                    print(f"Error sending email to {item['Email']}: {str(e)}")  
                writeInd.append(index)

        print("Sent Emails:", sent_emails)  

        for i in writeInd:
            yr = df.at[i, 'Year']
            df.loc[i, 'Year'] = str(yr) + ',' + str(yearNow)

        try:
            # Update the records in MongoDB with the modified DataFrame
            for record in df.to_dict('records'):
                collection.update_one({'_id': record['_id']}, {'$set': record}, upsert=False)
        except pymongo.errors.BulkWriteError as e:
            for error in e.details.get('writeErrors', []):
                if error.get('code') == 11000:  
                    print(f"Duplicate key error: {error.get('errmsg')}")
                    # Handle duplicate key error
                else:
                    print(f"Other write error: {error}")
        except Exception as e:
            print(f"Error updating data in MongoDB: {str(e)}")

    client.close()  

    session['sent_emails'] = sent_emails  

    return render_template('index.html', sent_emails=sent_emails)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        birthday_str = request.form['birthday']
        dialogue = request.form['dialogue']
        
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', birthday_str):
            return "Invalid date format. Please use YYYY-MM-DD format for birthday."

        try:
            birthday = datetime.datetime.strptime(birthday_str, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date. Please provide a valid date in YYYY-MM-DD format."
        
        birthday_datetime = datetime.datetime.combine(birthday, datetime.datetime.min.time())

        client = MongoClient("mongodb+srv://dubeyabhinav1001:dubey@cluster0.rjzqrrm.mongodb.net/?retryWrites=true&w=majority")
        db = client['dbms']  
        collection = db['bday']  

        existing_data = collection.find_one({"Name": name, "Email": email})
        if existing_data:
            return "Data already exists in the database. Cannot add duplicate entries."
        
        new_user = {
            "Name": name,
            "Birthday": birthday_datetime,  
            "Year": str(birthday.year),
            "Email": email,
            "Dialogue": dialogue
        }
        collection.insert_one(new_user)
        client.close()

        return redirect(url_for('index'))
    else:
        return render_template('add_user.html')

if __name__ == "__main__":
    app.run(debug=True)
