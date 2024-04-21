# Fundraising Platform with M-Pesa Integration

This project is a Flask-based web application designed to facilitate fundraising. The platform allows users to create and manage fundraising campaigns, and provides donors with the ability to contribute to these campaigns via M-Pesa, a mobile money service in Kenya. The project incorporates various functionalities, including user authentication, campaign management, and donation processing.

## Project Structure

- `app.py`: The main Flask application. It defines the web routes, connects to the SQLite database, and contains functions for M-Pesa integration, including STK push and transaction status checks.
- `database.py`: Contains database utility functions for creating and managing SQLite tables. It ensures the necessary tables for users, fundraisers, and donations are set up.
- `templates/`: A directory containing HTML templates for rendering different pages in the application, including the index, fundraiser details, registration, login, and donation pages.
- `static/`: A directory for storing static files such as images, CSS, and JavaScript.

## Key Features

- **User Authentication**: Allows users to register, log in, and manage their sessions.
- **Fundraiser Management**: Enables users to create and manage fundraising campaigns, providing details such as title, description, organizer information, and fundraising goals.
- **Donation Processing**: Integrates with M-Pesa to allow donors to contribute to fundraising campaigns via STK push. This process involves generating an authentication token, performing the STK push, and checking transaction status.
- **SQLite Database**: The application uses SQLite to store user information, fundraiser details, and donation records.

## Requirements

- Python 3.x
- Flask
- SQLite
- Requests (for HTTP requests)
- Werkzeug (for password hashing and security)

## Installation and Setup

1. Clone the repository to your local machine.
2. Install the required Python packages using `pip install -r requirements.txt`.
3. Set the `SECRET_KEY` in `app.py` to a secure value.
4. Configure the database path and ensure `sqlite3` is installed.
5. Run the Flask application with `python app.py`.

## Usage

- **Home Page**: Lists all available fundraising campaigns.
- **Fundraiser Detail**: Displays information about a specific fundraiser and allows users to donate.
- **Registration**: Allows new users to create an account.
- **Login**: Provides user authentication.
- **Donation**: Allows users to donate to a specific fundraiser using M-Pesa STK push.

## Important Notes

- **M-Pesa Integration**: Ensure you have the necessary credentials for M-Pesa integration, including `app_key` and `app_secret`.
- **Security**: Secure the `SECRET_KEY` and ensure proper error handling to avoid exposing sensitive information.
- **Compliance**: Ensure compliance with relevant regulations and M-Pesa's terms of service.

## License

Use it how you wanna :)

