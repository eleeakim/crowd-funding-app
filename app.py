import datetime
import time
from flask import Flask, redirect, render_template, request, g, url_for
import sqlite3
import requests
from database import get_db, create_fundraisers_table, create_donation_table
import base64
import json
from flask import flash, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['DATABASE'] = 'fundraiser.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
            '''
        )
        g.db.commit()
    return g.db


def generate_auth_token(app_key, app_secret):
    # Encode app_key and app_secret using base64
    credentials = base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()
    
    # URL for OAuth endpoint
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    # Set headers for the request with basic authorization
    headers = {'Authorization': f'Basic {credentials}'}

    # Send GET request to OAuth endpoint
    response = requests.get(url, headers=headers)

    # Check if the API request was successful (status code 200)
    if response.status_code == 200:
        # Check if the response contains content
        if response.text:
            try:
                # Parse JSON data from response
                response_data = json.loads(response.text)
                
                # Check if 'access_token' is in response_data
                if 'access_token' in response_data:
                    # Return the access token
                    return response_data['access_token']
                else:
                    print("Error generating auth token:", response.text)
                    return None
            except json.JSONDecodeError as e:
                print("Error decoding JSON response:", e)
                return None
        else:
            print("Empty response received.")
            return None
    else:
        print("API request failed with status code:", response.status_code)
        return None




def generate_password(business_short_code):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Replace this with your actual passkey
    plaintext = "{}{}{}".format(business_short_code, passkey, timestamp)
    password = base64.b64encode(plaintext.encode()).decode()
    return password

def perform_stk_push(auth_token, business_short_code, callback_url, amount, phone_number):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + auth_token
    }

    password = generate_password(business_short_code)

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": 254708374149,
        "PartyB": business_short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "RAFIKI LIMITED 2023",
        "TransactionDesc": "Payment of X"
    }

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    max_retries = 3
    retry_delay = 5

    try:
        for retry_count in range(max_retries):
            response = requests.post(url, headers=headers, json=payload)
            print("STK Push Response Status Code:", response.status_code)
            print("STK Push Response Content:", response.text)

            if response.status_code == 200:
                response_data = response.json()
                return response_data
            elif response.status_code == 500:
                print("Server error. Retrying in {} seconds...".format(retry_delay))
                time.sleep(retry_delay)
            else:
                response.raise_for_status()

    except (requests.RequestException, json.JSONDecodeError, requests.exceptions.HTTPError) as ex:
        print("An error occurred while performing STK push:", ex)
    except Exception as ex:
        print("An unexpected error occurred while performing STK push:", ex)

    return None

def check_transaction_status(auth_token, business_short_code, checkout_request_id):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + auth_token
    }

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU5N2RkNzFhNDY3Y2QyZTBjODkzMDU5YjEwZjc4ZTZiNzJhZGExZWQyYzkxOTIwMjMwNzEzMjEzMzQ0",
        "Timestamp": "20230713213344",
        "CheckoutRequestID": checkout_request_id
    }

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        while "errorCode" in response_data and response_data["errorCode"] == "500.001.1001":
            print("Transaction still being processed. Retrying in 5 seconds...")
            time.sleep(5)
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
        return response_data
    except (requests.RequestException, json.JSONDecodeError) as ex:
        print("An error occurred while checking transaction status:", ex)
        return None

@app.route('/')
def index():
    db = get_db()
    fundraisers = db.execute('SELECT * FROM fundraisers').fetchall()
    return render_template('index.html', fundraisers=fundraisers)

@app.route('/about/<int:fundraiser_id>')
def fundraiser_detail(fundraiser_id):
    db = get_db()
    fundraiser = db.execute('SELECT * FROM fundraisers WHERE id = ?', (fundraiser_id,)).fetchone()
    return render_template('about.html', fundraiser=fundraiser)

def get_fundraiser_by_id(fundraiser_id):
    db = get_db()
    fundraiser = db.execute('SELECT * FROM fundraisers WHERE id = ?', (fundraiser_id,)).fetchone()
    return fundraiser

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/save_fundraiser', methods=['POST'])
def save_fundraiser():
    create_fundraisers_table()
    title = request.form['title']
    description = request.form['description']
    organizer_name = request.form['organizer_name']
    organizer_email = request.form['organizer_email']
    fundraising_goal = float(request.form['fundraising_goal'])
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    db = get_db()
    db.execute(
        'INSERT INTO fundraisers (title, description, organizer_name, organizer_email, fundraising_goal, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (title, description, organizer_name, organizer_email, fundraising_goal, start_date, end_date)
    )
    db.commit()

    # Redirect to the homepage after successful fundraiser creation
    return redirect(url_for('index'))

@app.route('/donate/<int:fundraiser_id>', methods=['GET', 'POST'])
def donate(fundraiser_id):
    db = get_db()
    fundraiser_details = get_fundraiser_by_id(fundraiser_id)

    if fundraiser_details is None:
        return redirect(url_for('index'))
    
    donations = db.execute('SELECT * FROM donation WHERE fundraiser_id = ?', (fundraiser_id,)).fetchall()
    total_donated = sum(donation['amount'] for donation in donations)

    if request.method == 'POST':
        app_key = "W834dhXOUuwdtFdCaFIJHGnbxXrNmjWAB3P5TNoEydUiqKHg"
        app_secret = "OhrNfrLUrvQ1d6lrrHO6bMk7L8SZarZdnlLaYKk9H9FfCbzgnjHNwAGIwHQAmA7A"
        auth_token = generate_auth_token(app_key, app_secret)

        if auth_token:
            business_short_code = 174379
            callback_url = "https://7624-154-159-252-48.ngrok-free.app"
        
            amount = float(request.form['amount'])  # Get amount from the form
            phone_number = request.form['phone_number']  # Get phone number from the form
            
            result = perform_stk_push(auth_token, business_short_code, callback_url, amount, phone_number)
            
            if result:
                if "errorCode" in result:
                    print("STK Push Error:", result["errorMessage"])
                else:
                    checkout_request_id = result.get("CheckoutRequestID")
                    if checkout_request_id:
                        response_data = check_transaction_status(auth_token, business_short_code, checkout_request_id)
                        if response_data:
                            # Save the payment details to the database
                            name = request.form['name']
                            message = request.form['message']
                            db.execute(
                                'INSERT INTO donation (fundraiser_id, name, phone_number, amount, message) VALUES (?, ?, ?, ?, ?)',
                                (fundraiser_id, name, phone_number, amount, message)
                            )
                            db.commit()

                            return render_template('result.html', response_data=response_data)
            else:
                print("Empty response received or STK push failed.")

    return render_template('donate.html', fundraiser=fundraiser_details, donations=donations, total_donated=total_donated)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username or email already exists in the database
        db = get_db()
        existing_user = db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?', (username, email)
        ).fetchone()

        if existing_user:
            flash('Username or email already exists.', 'danger')
        else:
            # Hash the password and store the user in the database
            hashed_password = generate_password_hash(password, method='sha256')
            db.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user and check_password_hash(user['password'], password):
            # Successful login
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            # Invalid login
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')



@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    with app.app_context():
        create_fundraisers_table()
        create_donation_table()
    app.run(debug=True, host='0.0.0.0')
