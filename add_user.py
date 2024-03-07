from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['birthday_db']
collection = db['people']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_person', methods=['POST'])
def add_person():
    name = request.form['name']
    email = request.form['email']
    dob = request.form['dob']

    # Insert data into MongoDB
    collection.insert_one({'name': name, 'email': email, 'dob': dob})

    return 'Person added successfully!'

if __name__ == '__main__':
    app.run(debug=True)
