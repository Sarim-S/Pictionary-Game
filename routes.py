from flask import Blueprint, render_template
from .shared_data import users, ordered_scores

main = Blueprint("main", __name__)

@main.route('/')
def join():
    return render_template('connect_page.html')

@main.route('/test')
def handle_test():
    usernames = [name for name in users.values()]
    return render_template('join_test.html', usernames=usernames)

@main.route("/game")
def handle_game():
    usernames = [name for name in users.values()]
    return render_template('game_page.html', usernames=usernames)

@main.route("/end")
def handle_end():
    scores = ordered_scores[0]
    print(scores)
    return render_template('scoreboard.html', scores=scores)