from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from gd_operations import list_drive_photos, FOLDER_ID
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Main db class
class Human(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    age = db.Column(db.Integer, nullable=False) # Number (Age)
    gender = db.Column(db.String(10), nullable=False) # Male or Female
    photo_url = db.Column(db.String(255), nullable=False) # File URL

    def __repr__(self):
        return f'<Human {self.id} - Age: {self.age}, Gender: {self.gender}>'

# Veritabanını oluştur
def initialize_database():
    with app.app_context():
        db.create_all()  # Create database

        # If database already filled, don't fill it again
        if Human.query.first():
            print("Database is already filled.")
            return

        # Regex pattern for age_genderValue_raceValue_date.jpg files
        pattern = re.compile(r'^(?P<age>\d+)_(?P<gender>\w+)_.*\.jpg$', re.IGNORECASE)

        for name, url in list_drive_photos(FOLDER_ID):
            match = pattern.match(name)
            if match:
                age = int(match.group('age'))
                gender = "male" if match.group('gender') == "0" else "female"

                new_human = Human(age=age, gender=gender, photo_url=url)
                db.session.add(new_human)

        # Complete database filling
        db.session.commit()