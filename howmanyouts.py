import os
import random

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import session
from flask import url_for
from werkzeug.contrib.cache import FileSystemCache

import game

app = Flask(__name__)
app.debug = False
app.testing = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

cache = FileSystemCache('cache')


@app.route('/')
def index():
    
    return render_template('index.html')


@app.route('/game/new')
def game_new():

    # start a brand new game
    game_id = random.randint(0, 50000000)
    a_game = game.Game(game_id)
    a_round = a_game.new_round()

    key = 'game_' + str(game_id)
    session["game_id"] = game_id
    cache.set(key, a_game)

    ret = get_game_info(a_game)
    return jsonify(game=ret)


@app.route('/game/guess/<int:guess>')
def game_guess(guess = None):

    ret = {'status' : 'error'}

    # retrieve game from session
    key = 'game_' + str(session["game_id"])
    a_game = cache.get(key)
    
    # process a guess if there was a game and a guess
    if (None != guess and None != a_game and None != a_game.get_cur_round()):
        
        a_round = a_game.get_cur_round()        
        a_game.end_round(guess)        
        
        # start new round
        a_game.new_round()
        cache.set(key, a_game)

        # new return
        ret = get_game_info(a_game)

        # give the player feedback to what happened last round
        ret["feedback"] = {"distance" : a_round.guess_distance
                         , "guess"    : a_round.guess
                         , "id"       : a_round.id
                         , "points"   : a_round.points
                         , "outs"     : []}

        for card in a_round.outs:
            ret["feedback"]["outs"].append(card.to_string())

 
    return jsonify(game=ret)

@app.errorhandler(500)
def page_not_found(error):
    return 'Damnit ' + repr(error)

def get_game_info(a_game):
    '''
    Helper for and putting the game info into an array
    '''
    ret = {'status' : 'ok'}
    a_round = a_game.get_cur_round()

    # add game status to response
    ret["id"] = a_game.id
    ret["score"] = a_game.score
    ret["remaining"] = a_game.rounds_remaining()
    ret["streak"] = a_game.streak
    ret["round"] = {"new" : "no"}

    if (None != a_round):

        ret["round"]["new"] = "yes" 
    
        # add hands to response
        ret["round"]["hands"] = []
        for hand in a_round.get_hands():
            ret["round"]["hands"].append([hand.hole[0].to_string()
                                        , hand.hole[1].to_string()])

        # add board to response
        ret["round"]["board"] = []
        for card in a_round.get_board():
            ret["round"]["board"].append(card.to_string())

        # add if the player is ahead at this point or not to response
        ret["round"]["ahead"] = a_round.ahead

        # time and points for the round
        ret["round"]["id"] = a_round.id
        ret["round"]["points"] = a_game.get_points_possible()
        ret["round"]["time"] = a_game.get_time_allowed()
    

    return ret;

if __name__ == '__main__':
    app.testing = True
    app.debug = True
    app.run()

