from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from secret_key import secret_key
from init_db import initialize_database
import os
import re
import random
import time
import math

if not os.path.exists("data.db"):
    initialize_database()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key

db = SQLAlchemy(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(BASE_DIR, "datas")

# Main db class
class Human(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    age = db.Column(db.Integer, nullable=False) # Number (Age)
    gender = db.Column(db.String(10), nullable=False) # Male or Female
    photo_url = db.Column(db.String(255), nullable=False) # File URL

    def __repr__(self):
        return f'<Human {self.id} - Age: {self.age}, Gender: {self.gender}>'

def generate_options(correct, num_wrong, range_delta):
    lowest = correct - range_delta
    highest = correct + range_delta
    shift_value = correct - (int(correct - math.log2(correct)))

    '''
    -1 means options mostly gonna be lower than the correct answer
    0 means they gonna be distributed equally
    1 means they mostly gonna be lower than the correct answer
    '''
    possibility = random.randint(-1, 1)
    if possibility == -1:
        highest = highest - shift_value
        lowest = lowest - shift_value
    if possibility == 1:
        lowest = lowest + shift_value
        highest = highest + shift_value

    if lowest < 0:
        lowest = 0
    if highest > 110:
        highest = 110

    options = set()
    options.add(correct)
    while len(options) < (num_wrong + 1):
        wrong_option = random.randint(lowest, highest)
        options.add(wrong_option)

    options = list(options)
    random.shuffle(options)

    return options

def generate_question():
    """
    picks a random Human from db,
    generates 4 wrong choices in the range ±5 with reference to the correct Human age
    and randomly mixes 5 options with 1 correct choice.
    """
    human = Human.query.order_by(db.func.random()).first()
    correct_age = human.age
    options = generate_options(correct_age, 4, 6)

    return {
        'photo_path': human.photo_url,
        'correct_age': correct_age,
        'options': options
    }

@app.route('/')
def index():
    return render_template('index.html')

# Language setter (English or Turkish)
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang.lower() not in ['tr', 'en']:
        lang = 'tr'
    session['lang'] = lang.lower()
    # User returns to the page they came from (referrer) or redirects them to the home page
    return redirect(request.referrer or url_for('index'))

# Photo getter
@app.route('/photos/<path:filename>')
def photos(filename):
    return send_from_directory(PHOTOS_DIR, os.path.basename(filename))

# Main quiz page function
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    total_questions = 20  # Total number of questions
    if request.method == 'GET':
        # Initialize the session data at the first login to the quiz
        session['quiz'] = {'question_num': 1, 'score': 0}
        session['current_question'] = generate_question()
        return render_template('quiz.html',
                               question=session['current_question'],
                               question_num=session['quiz']['question_num'],
                               total_questions=total_questions,
                               message=None)
    else:
        # If it is not the first login, check the answer and move on to the next question
        try:
            user_answer = int(request.form.get('answer'))
        except (ValueError, TypeError):
            user_answer = None

        # Bring new question if there is no question or user answer
        current_question = session.get('current_question')
        if not current_question or user_answer is None:
            return redirect(url_for('quiz'))

        correct_answer = current_question['correct_age']
        lang = session.get("lang", "tr")

        # Check the answer and adjust the correct/wrong message
        if user_answer == correct_answer:
            if lang == "tr":
                message = "Doğru!"
            else:
                message = "Correct!"
            session['quiz']['score'] += 5
        else:
            if lang == "tr":
                message = f"Yanlış, yaşı {correct_answer} idi."
            else:
                message = f"Wrong, correct age was {correct_answer}."

        # Update the question number
        session['quiz']['question_num'] += 1

        # Redirect to the results page if the user has answered all questions
        if session['quiz']['question_num'] > total_questions:
            total_score = session['quiz']['score']
            accuracy = (total_score / (5 * total_questions)) * 100  # Each question is 5 points
            # Clear quiz data
            session.pop('current_question', None)
            return render_template('quiz_result.html', score=total_score, accuracy=accuracy)
        else:
            # Create a new question and render it with the correct/wrong message
            session['current_question'] = generate_question()
            return render_template('quiz.html',
                                   question=session['current_question'],
                                   question_num=session['quiz']['question_num'],
                                   total_questions=total_questions,
                                   message=message)
        
# Restart quiz function
@app.route('/quiz/restart')
def quiz_restart():
    # Clear quiz data
    session.pop('quiz', None)
    session.pop('current_question', None)
    return redirect(url_for('quiz'))

# Function for retrieve the quiz data from server so user cannot share manipulated data
@app.route('/get_quiz_result', methods=['GET'])
def get_quiz_result():
    quiz_data = session.get('quiz', {})
    score = quiz_data.get('score', 0)
    accuracy = (score / (5 * 20)) * 100
    return jsonify({'score': score, 'accuracy': accuracy})

# Marathon function
@app.route('/marathon', methods=['GET', 'POST'])
def marathon():
    if request.method == 'GET':
        # Initialize the session data at the first login to the marathon
        session['marathon'] = {
            'question_num': 1,
            'lives': 3,
            'correct_count': 0,
            'start_time': time.time()
        }
        session['current_question'] = generate_question()
        return render_template('marathon.html',
                               question=session['current_question'],
                               question_num=session['marathon']['question_num'],
                               lives=session['marathon']['lives'],
                               message=None)
    else:
        try:
            user_answer = int(request.form.get('answer'))
        except (ValueError, TypeError):
            user_answer = None

        current_question = session.get('current_question')
        if not current_question or user_answer is None:
            return redirect(url_for('marathon'))

        correct_answer = current_question['correct_age']
        lang = session.get("lang", "tr")
        if user_answer == correct_answer:
            if lang == "tr":
                message = "Doğru!"
            else:
                message = "Correct!"
            session['marathon']['correct_count'] += 1
        else:
            if lang == "tr":
                message = f"Yanlış, doğru yaş {correct_answer} idi."
            else:
                message = f"Wrong, correct age was {correct_answer}."
            # Decrease one life
            session['marathon']['lives'] -= 1

        # Update the current question number
        session['marathon']['question_num'] += 1

        # If all lives are used, redirect user to the results page
        if session['marathon']['lives'] <= 0:
            elapsed_time = int(time.time() - session['marathon']['start_time'])
            session['marathon']['final_elapsed_time'] = elapsed_time
            correct_count = session['marathon']['correct_count']
            question_num = session['marathon']['question_num'] - 1  # Answered questions
            session.pop('current_question', None)
            return render_template('marathon_result.html',
                                   correct_count=correct_count,
                                   question_num=question_num,
                                   elapsed_time=elapsed_time)
        else:
            session['current_question'] = generate_question()
            return render_template('marathon.html',
                                   question=session['current_question'],
                                   question_num=session['marathon']['question_num'],
                                   lives=session['marathon']['lives'],
                                   message=message)

# Marathon restart function
@app.route('/marathon/restart')
def marathon_restart():
    # Clean session data
    session.pop('marathon', None)
    session.pop('current_question', None)
    return redirect(url_for('marathon'))

# Function for retrieve the marathon data from server so user cannot share manipulated data
@app.route('/get_marathon_result', methods=['GET'])
def get_marathon_result():
    marathon_data = session.get('marathon', {})
    correct_count = marathon_data.get('correct_count', 0)
    question_num = marathon_data.get('question_num', 1) - 1
    elapsed_time = marathon_data.get('final_elapsed_time')

    return jsonify({
        'correct_count': correct_count,
        'question_num': question_num,
        'elapsed_time': elapsed_time
    })

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run()