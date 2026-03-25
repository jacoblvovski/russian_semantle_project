from flask import Flask, render_template, request, redirect, url_for, session
from backend import *
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rating.db'
db = SQLAlchemy(app)
app_start_date = datetime(2026, 3, 25)
current_date = datetime.now()
random_seed = (current_date - app_start_date).days
random.seed(random_seed)
with open('500_words.txt', encoding='utf-8') as f:
    words = f.readlines()
words = [word.strip() for word in words]
answer = words[random.randint(0, 49)]


class Rating(db.Model):
    __tablename__ = 'Rating'
    game_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number_of_attempts = db.Column(db.Integer)
    average_similarity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))


class Users(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, unique=True)


with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def game():
    guess = ''
    if 'guesses' not in session:
        session['guesses'] = dict()
    session['guesses'] = {key: float(value) for key, value in session['guesses'].items() if key}
    if request.method == 'POST':
        guess = request.form.get('guess').strip()
        if len(guess) != 0:
            similarity = float(cosine(vectorize(guess), vectorize('яблоко')))
            session['guesses'][guess] = similarity
    similarity_dict = session['guesses']
    sorted_guesses = dict(sorted(similarity_dict.items(), key=lambda item: item[1], reverse=True))
    if guess == answer:
        session['guesses_for_rating'] = session.pop('guesses')
        return redirect(url_for('victory'))
    return render_template('game.html',
                           status='Не отгадано',
                           similarity_dict=sorted_guesses)


@app.route('/victory', methods=['POST', 'GET'])
def victory():
    name = False
    if request.method == 'POST':
        name = request.form.get('name_submission', '').strip()
    if name:
        user_guesses = session['guesses_for_rating']
        user = Users(
            name=name
        )
        number_of_attempts = len(user_guesses.keys())
        average_similarity = sum(user_guesses.values()) / number_of_attempts
        names = [user.name for user in Users.query.all()]
        if name not in names:
            db.session.add(user)
            user_id = Users.query.filter(Users.name == name).all()[0].user_id
            player_rating = Rating(
                number_of_attempts=number_of_attempts,
                average_similarity=average_similarity,
                user_id=user_id
            )
            db.session.add(player_rating)
            db.session.commit()
            db.session.refresh(user)
            db.session.refresh(player_rating)
            return redirect(url_for('rating'))
        else:
            return render_template('victory_page.html',
                                       status='Это имя занято, выберите другое.')
        user_id = Users.query.filter(User.name == name).all()[0].user_id
        player_rating = Rating(
            number_of_attempts=number_of_attempts,
            average_similarity=average_similarity,
            user_id=user_id
        )
        db.session.add(player_rating)
        db.session.commit()
    return render_template('victory_page.html',
                               status='')


@app.route('/rating')
def rating():
    rated_users = db.session.query(Users.name, Rating.number_of_attempts, Rating.average_similarity).join(Rating, Users.user_id == Rating.user_id).order_by(Rating.number_of_attempts.asc(), Rating.average_similarity.desc()).all()
    rated_users_table = '''
    <table style="margin-left: auto; margin-right: auto;">
  <tr>
    <th>Игрок</th>
    <th>Число попыток</th>
    <th>Среднее сходство слов</th>
  </tr>
    '''
    for user in rated_users:
        row = f'''
        <tr>
        <td>{user[0]}</td>
        <td>{user[1]}</td>
        <td>{user[2]}</td>
        </tr>
         '''
        rated_users_table += row
    rated_users_table += '</table>'
    return render_template('rating.html',
                           rating=rated_users_table)


if __name__ == '__main__':
    app.run()
