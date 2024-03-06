import os
import pandas as pd
import datetime
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from pymongo import MongoClient
import insert_data  # Import insert_data.py module

# Load environment variables from .env file
load_dotenv()

# Enter your authentication details
GMAIL_ID = os.getenv('GMAIL_ID')
GMAIL_PSWD = os.getenv('GMAIL_PSWD')

def sendEmail(to, sub, msg):
    print(f"Email to {to} sent with subject: {sub} and message: {msg}")
    em = EmailMessage()
    em['From'] = GMAIL_ID
    em['To'] = to
    em['Subject'] = sub
    em.set_content(msg)

    context = smtplib.SMTP('smtp.gmail.com', 587)
    context.starttls()
    context.login(GMAIL_ID, GMAIL_PSWD)
    context.sendmail(GMAIL_ID, to, em.as_string())
    context.quit()

if __name__ == "__main__":
    # Run insert_data.py to insert data into MongoDB
    insert_data.insert_data()

    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['dbms']  # Replace 'your_database_name' with your actual database name
    collection = db['bday']  # Replace 'your_collection_name' with your actual collection name

    # Fetch data from MongoDB
    df = pd.DataFrame(list(collection.find()))

    if not df.empty:  # Check if DataFrame is not empty
        today = datetime.datetime.now().strftime("%d-%m")
        yearNow = datetime.datetime.now().strftime("%Y")

        writeInd = []
        for index, item in df.iterrows():
            if isinstance(item['Birthday'], str):  # Check if 'Birthday' is a string
                item['Birthday'] = datetime.datetime.strptime(item['Birthday'], "%Y-%m-%d")  # Convert string to datetime

            bday = item['Birthday'].strftime("%d-%m")  # Convert datetime to string
            if today == bday and yearNow not in str(item['Year']):
                sendEmail(item['Email'], "Happy Birthday", item['Dialogue'])
                writeInd.append(index)

        print(writeInd)

        for i in writeInd:
            yr = df.at[i, 'Year']
            df.loc[i, 'Year'] = str(yr) + ',' + str(yearNow)

        # Save the updated DataFrame back to MongoDB
        collection.delete_many({})  # Clear existing data in the collection
        collection.insert_many(df.to_dict('records'))

    client.close()  # Close the MongoDB connection
