from contextlib import closing
import os
import pickle
import random
import sqlite3
from time import time
import zlib

from flask import Flask
from flask import g
from flask import jsonify
from flask import make_response
from flask import request
from flask import render_template
from flask import session
from flask import url_for

import game

# Version of html game to force Css/Js refresh
VERSION = 7


# Location of database
DATABASE = '/srv/www/howmanyouts.com/howmanyouts/database/data.db'
SCHEMA = '/srv/www/howmanyouts.com/howmanyouts/database/schema.sql'    

if __name__ == '__main__':
    DATABASE = 'database/data.db'
    SCHEMA = 'database/schema.sql'
   

# Timestamp for when leaderboards started
LEADERBOARD_START = 1327168800

# Interval in seconds between leaderboard resets
LEADERBOARD_INTERVAL = 604800

# FLASK
app = Flask(__name__)
app.debug = False
app.testing = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route('/', methods = ['GET'])
def index():
    
    session["name"] = request.cookies.get('name', 'Ralphie')
    session["game_id"] = None
    return render_template('index.html'
                         , testing = app.testing
                         , version = VERSION)


@app.route('/game/new', methods = ['GET', 'POST'])
def game_new():

    ret = {'status' : 'error'}

    # start a brand new game by first hitting up the db
    game_id = write_db("INSERT INTO game (name, time_start) VALUES (?, ?)",  [session["name"], time()])

    if game_id is not None:
   
        # create the new game and first round
        a_game = game.Game(game_id)
        a_round = a_game.new_round()

        # save the game to the database and session
        session["game_id"] = game_id
        write_db("UPDATE game SET data = ? WHERE ROWID = ?", [buffer(zlib.compress(pickle.dumps(a_game))), game_id])

        # return info about the current game and round
        ret = get_game_info(a_game)
        ret["round"] = get_round_info(a_game)



    return jsonify(game=ret)


@app.route('/game/guess/<int:guess>', methods = ['POST'])
def game_guess(guess = None):

    ret = {'status' : 'error'}

    # retrieve game from session and database
    game_id = session["game_id"]    
    results = query_db("SELECT data FROM game WHERE ROWID = ?", [game_id], True)

    a_game = pickle.loads(zlib.decompress(results['data']).encode('utf-8'))
    
    # process a guess if there was a game and a guess
    if (None != guess and None != a_game and None != a_game.get_cur_round()):
        
        #  end round
        a_round = a_game.get_cur_round()        
        a_game.end_round(guess)        

        # save to db
        write_db("UPDATE game SET data = ?, score = ?, completed = ? WHERE ROWID = ?", [buffer(zlib.compress(pickle.dumps(a_game))), a_game.score, a_round.id, game_id])

        # new return givin the player feedback to what happened last round
        ret = get_game_info(a_game)
        ret["feedback"] = {"distance" : a_round.guess_distance
                         , "draws"    : a_round.draws
                         , "guess"    : a_round.guess
                         , "id"       : a_round.id
                         , "points"   : a_round.points
                         , "score"    : a_game.score
                         , "outs"     : []}

        for card in a_round.outs:
            ret["feedback"]["outs"].append(card.to_string())

        # if the game is over, mark the game as completed and find out where this player's score ranks!
        if (None == a_game.get_cur_round()):

            # mark completed
            write_db("UPDATE game SET time_completed = ? WHERE ROWID = ?", [time(), game_id])

            # grab rank all time
            results = query_db("SELECT COUNT(*) as rank FROM game WHERE completed = ? AND time_completed IS NOT NULL AND score > ?", [game.Game.ROUND_COUNT, a_game.score], True)            
            rank = int(results['rank']) + 1

            ret["feedback"]["rank"] = rank

            # update all time rank
            if (1 == rank):
                write_db("DELETE FROM hiscores WHERE period = 0", commit = False)
                write_db("INSERT INTO hiscores (game_id, period) VALUES (?, ?)", [game_id, 0])                

            # grab rank last interval
            now = time()
            last = int(now - ((now - LEADERBOARD_START) % LEADERBOARD_INTERVAL))
            
            results = query_db("SELECT COUNT(*) as rank FROM game WHERE completed = ? AND time_completed IS NOT NULL AND time_completed >= ? AND score > ?", [game.Game.ROUND_COUNT, last,  a_game.score], True)            
            rank = int(results['rank']) + 1

            # update last interval
            if (1 == rank):
                write_db("DELETE FROM hiscores WHERE period = ?", [last], commit=False)
                write_db("INSERT INTO hiscores (game_id, period) VALUES (?, ?)", [game_id, last])                


            ret["feedback"]["rank_interval"] = rank

 
    return jsonify(game=ret)


@app.route('/game/round', methods = ['GET', 'POST'])
def game_round():

    ret = {'status' : 'error'}

    # retrieve game from session and database
    game_id = session["game_id"]    
    results = query_db("SELECT data FROM game WHERE ROWID = ?", [game_id], True)

    a_game = pickle.loads(zlib.decompress(results['data']).encode('utf-8'))    

    # create a new round  if there is a game and a new round
    if (None != a_game and None != a_game.get_cur_round()):

        # start new round
        a_game.new_round()

        # save to db
        write_db("UPDATE game SET data = ? WHERE ROWID = ?", [buffer(zlib.compress(pickle.dumps(a_game))), game_id])

        # new return
        ret = get_game_info(a_game)
        ret["round"] = get_round_info(a_game)                
        

    return jsonify(game=ret)

@app.route('/game/name/<string:name>', methods = ['POST'])
def game_name(name):
    ''' 
    Change the name of the player in the session, cookie,  and for their current game
    '''

    name = name.strip()
    name = name[0:32]

    ret = {'status' : 'ok'}    
    resp = make_response(jsonify(game=ret))
    
    session['name'] = name
    resp.set_cookie('name', value=name, expires=(time() + 4492800))


    if (None != session["game_id"]):
        write_db("UPDATE game SET name = ? WHERE ROWID = ?", [session["name"], session["game_id"]])        


    return resp

@app.route('/scores/<string:interval>', methods =['GET'])
def scores(interval):
    '''
    Grab the top 10 scores for all time or an interval
    '''
   
    ret = {'status' : 'error'}

    # either grab all time or the last interval
    start = 0
    now = time()
    last = int(now - ((now - LEADERBOARD_START) % LEADERBOARD_INTERVAL))

    if ("interval" == interval):
        start = last

    # query the db for last 10 scores    
    results = query_db("SELECT name, score FROM game WHERE completed = ? AND time_completed IS NOT NULL AND time_completed >= ? ORDER BY score DESC LIMIT 5", [game.Game.ROUND_COUNT, start])

    if (None != results):        
        
        # put the scores into the response    
        rank = 1
        scores = []
        for score in results:
            scores.append([rank, score["name"], score["score"]])
            rank += 1
    

        ret["status"] = "ok"            
        ret["scores"] = scores
        ret["interval"] = interval

    return jsonify(game=ret)



@app.errorhandler(500)
def page_not_found(error):
    return 'Damnit ' + repr(error)


def get_game_info(a_game):
    '''
    Helper for putting the game info into an array
    '''

    ret = {'status' : 'ok'}

    # add game status to response
    ret["id"] = a_game.id
    ret["time"] =  a_game.get_time_allowed()
    ret["name"] = session["name"]
    ret["more"] = "no"

    if None != a_game.get_cur_round():
        ret["more"] = "yes"

    # add hi scores
    ret["alltime_name"] = "Nobody Yet!"
    ret["alltime_score"] = "0"
    ret["interval_name"] = "Nobody Yet!"
    ret["interval_score"] = "0"

    results = query_db("SELECT g.score, g.name FROM game AS g, hiscores AS h WHERE g.ROWID = h.game_id AND h.period = 0", [], True)
    if (None != results):
        ret["alltime_name"] = results["name"]
        ret["alltime_score"] = results["score"]

    now = time()
    last_period = int(now - ((now - LEADERBOARD_START) % LEADERBOARD_INTERVAL))    
    results = query_db("SELECT g.score, g.name FROM game AS g, hiscores AS h WHERE g.ROWID = h.game_id AND h.period = ?", [last_period], True)
    if (None != results):
        ret["interval_name"] = results["name"]
        ret["interval_score"] = results["score"]    

    return ret


def get_round_info(a_game):
    '''
    Helper for putting round info into an array
    '''

    ret = {'status' : 'ok'}
    a_round = a_game.get_cur_round()

    if (None != a_round):
    
        # add hands to response
        ret["hands"] = []
        for hand in a_round.get_hands():
            ret["hands"].append([hand.hole[0].to_string()
                                        , hand.hole[1].to_string()])

        # add board to response
        ret["board"] = []
        for card in a_round.get_board():
            ret["board"].append(card.to_string())

        # add if the player is ahead at this point or not to response
        ret["ahead"] = a_round.ahead

        # time and points for the round
        ret["id"] = a_round.id
        ret["points"] = a_game.get_points_possible()

    return ret;


'''
******************
    DATABASE 
******************
'''

def connect_db():
    return sqlite3.connect(DATABASE)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def query_db(query, args = (), one = False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def write_db(query, args = (), commit = True):
    
    cur = g.db.execute(query, args)
    
    if commit:
        g.db.commit()

    return cur.lastrowid


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource(SCHEMA) as f:
            db.cursor().executescript(f.read())
        db.commit()

'''
********************
    MAIN
********************
'''
if __name__ == '__main__':

    app.testing = True
    app.debug = True
    app.run()



