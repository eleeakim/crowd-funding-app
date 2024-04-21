import sqlite3
from flask import g, current_app

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def create_donation_table():
    db = get_db()
    with current_app.open_resource('schema_donation.sql') as f:
        db.executescript(f.read().decode('utf8'))

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def get_fundraiser_by_id(fundraiser_id):
    db = get_db()
    fundraiser = db.execute(
        'SELECT * FROM fundraisers WHERE id = ?', (fundraiser_id,)
    ).fetchone()
    return fundraiser



def create_fundraisers_table():
    db = get_db()
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS fundraisers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            organizer_name TEXT NOT NULL,
            organizer_email TEXT NOT NULL,
            fundraising_goal REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL
        )
        '''
    )
    db.commit()
