from flask import request, session
from flask_socketio import emit
from .extensions import socketio
from .shared_data import users, user_tokens, draw_cycle, correct_guesses, scores, words, ordered_scores
from random import choice
import uuid
import time

is_round_active = False
deleted_words = []

def get_items(dictionary):
    items = [item for item in dictionary.values()]
    return items

def make_word(word_list):
    word = choice(word_list)
    display = ""
    for letter in word:
        display += "_ "
    display.strip()
    return [word, display]

@socketio.on('connect')
def handle_connect():
    user_token = request.cookies.get('user_token')
    print(f"connect token: {user_token}")
    # if user_token and user_token in user_tokens:
    #     id_to_override = None
    #     username = user_tokens[user_token]
    #     for id, user in users.items():
    #         if user == username:
    #             id_to_override = id
    #     users.pop(id_to_override)
    #     users[request.sid] = username
    # else:
    #     print("new connection")
    print(f"connection : {users}")

@socketio.on('join')
def handle_join(username):
    user_token = str(uuid.uuid4())
    user_tokens[user_token] = username
    users.update({user_token: username})
    print(f"join test after {users}")

    usernames = get_items(users)
    first_user = usernames[0]


    emit('set-cookie', {'token': user_token}, to=request.sid)
    emit('displayed', broadcast=True)
    emit('redirect', {'url': "/test", "name": username}, broadcast=True)
    emit('update_list', {'items': usernames, "length": len(usernames), "first": first_user}, broadcast=True)
    print(f"Cookies: {request.cookies}")

    
@socketio.on('leave')
def handle_leave(data):
    # token = request.cookies.get('user_token')
    
    
    # if not token or token not in users or token not in user_tokens:
    #     print("old token used AHHHHHHH")

    # print(f"printing users for disconnect: {users}")
    # print(f"token requesting to leave : {token}")
    # username = users[token]
    # users.pop(token, None)
    # user_tokens.pop(token, None)

    username = data['user']
    token_to_delete = None
    if username:
        for user in users.keys():
            print(f"current user: {user}")
            if users[user] == data['user']:
                token_to_delete = user
                print(f"token deleting: {token_to_delete}")
                username = users[user]
    users.pop(token_to_delete)
    user_tokens.pop(token_to_delete)

    usernames = get_items(users)
    first_user = usernames[0]
    
    print(f"after leave: {users}")

    emit('clear-cookie', to=request.sid)
    emit('to-home', {'url': "/", 'username': username}, to=request.sid)
    emit('update_list', {'items': usernames, "length": len(usernames), "first": first_user}, broadcast=True, include_self=False)

@socketio.on("start-game")
def handle_start():
    emit('to-game', {'url': "/game"}, broadcast=True)

@socketio.on('start')
def handle_game_start():
    usernames = get_items(users)
    for user in usernames:
        draw_cycle[user] = {'times': 0, 'drawing': False}
    
    first_drawer = next(iter(draw_cycle))
    draw_cycle[first_drawer]["times"] += 1
    draw_cycle[first_drawer]["drawing"] = True

    items = make_word(words)
    word, display = items[0], items[1]
    deleted_words.append(word)
    words.remove(word)

    emit('set_drawer', {'drawer': first_drawer, "display": display, "word": word}, broadcast=True)

    # def countdown():
    #     for t in range(duration, -1, -1):
    #         emit('timer_update', {'time': t}, broadcast=True)
    #         time.sleep(1)
    #     emit('round-end', broadcast=True)

    # Thread(target=countdown).start()

@socketio.on('round-end')
def handle_round_end():
    emit('round-end', broadcast=True)

@socketio.on('drawing')
def handle_draw(data):
    emit('drawing', data, broadcast=True, include_self=False)

@socketio.on("clear-canvas")
def handle_clear():
    emit("clear-canvas", broadcast=True)

@socketio.on('correct-guess')
def handle_correct(data):
    number_of_guesses = data['guess_num'] - 1
    current_drawer = None
    for player in draw_cycle.keys():
        if draw_cycle[player]['drawing'] == True:
            current_drawer = player

    print(f"scores before adding: {scores}")
    if current_drawer not in scores.keys():
        scores[current_drawer] = 0

    if current_drawer in correct_guesses:
        correct_guesses.remove(current_drawer)
    
    usernames = get_items(users)
    total_users = len(usernames)
    max_points = total_users*10
    least_points = 10
    points_earned = max_points - (number_of_guesses*2)
    if points_earned < least_points:
        points_earned = least_points

    usernames.remove(current_drawer)
    guessed_user = data['username']

    if guessed_user in correct_guesses:
        pass
    else:
        correct_guesses.append(guessed_user)
        if guessed_user in scores.keys():
            scores[guessed_user] += points_earned
        else:
            scores[guessed_user] = points_earned
    print(correct_guesses, scores)
    
    if set(usernames) == set(correct_guesses):
        scores[current_drawer] += len(correct_guesses)*10
        draw_cycle[current_drawer]['drawing'] = False

        emit("update_scores", scores, broadcast=True)
        emit("all_guessed", broadcast=True)

@socketio.on('next_drawer')
def handle_next_drawer(data):
    global is_round_active

    if is_round_active:
        return
    
    is_round_active = True

    current_round = data['round']
    drawer = None
    for user in draw_cycle.keys():
        if draw_cycle[user]['times'] < current_round:
            drawer= user
            draw_cycle[user]['times'] += 1
            draw_cycle[user]['drawing'] = True
            break
    if drawer is None:
        if current_round == 2:
            print(scores)
            ordered_scores.append(dict(sorted(scores.items(), key=lambda item: item[1], reverse=True)))
            emit('game_over', {"url": '/end'}, broadcast=True)
            return
        current_round += 1
        emit('next_round', {'round': current_round})
        is_round_active = False
        return
    
    items = make_word(words)
    word, display = items[0], items[1]
    deleted_words.append(word)
    words.remove(word)

    emit('set_drawer', {'drawer': drawer, "display": display, "word": word}, broadcast=True)
    
    socketio.sleep(5)
    is_round_active = False

@socketio.on("play_again")
def handle_play_again():
    global is_round_active

    scores.clear()
    users.clear()
    user_tokens.clear()
    draw_cycle.clear()
    correct_guesses.clear()
    ordered_scores.clear()
    is_round_active = False
    for word in deleted_words:
        words.append(word)
    deleted_words.clear()

    emit('start_again', {"url": "/"}, broadcast=True)
    
@socketio.on('run_timer')
def handle_timer():
    duration = 60

    for i in range(duration):
        emit('update_time', {"duration": duration})
        duration -= 1
        time.sleep(1) 



# @socketio.on('disconnect')
# def handle_disconnect():
#     print(users)
#     token = request.cookies.get('user_token')
#     print(f"token disconnected: {token}")
#     users.pop(token)
#     print(users)
#     emit('refresh', broadcast=True)