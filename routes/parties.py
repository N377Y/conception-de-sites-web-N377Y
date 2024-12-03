from functools import wraps
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import random

# Create the Blueprint for game-related routes
parties_routes = Blueprint('parties', __name__)

# Initialize the database
if not os.path.exists("database.db"):  # Check if the database file exists
    open("database.db", "w").close()  # Create an empty database file if not
    db = SQL("sqlite:///database.db")  # Connect to the SQLite database
    # Create tables if they don't exist
    with open("database.sql", "r") as sql_file:
        sql_statements = sql_file.read().split(';')
        for statement in sql_statements:
            if statement.strip():  # Avoid empty statements
                db.execute(statement)
else:
    db = SQL("sqlite:///database.db")  # Connect to the existing SQLite database

@parties_routes.route('/start_game', methods=['POST'])
def start_game():
    """Start a new game by generating a game code."""
    # Generate a random 6-digit game code
    num = [random.randint(0, 9) for _ in range(6)]
    game_code = ''.join(map(str, num))
    user_id = session.get('user_id')  # Get the current user's ID from the session
    username = session.get('username')  # Get the current user's username from the session

    # Insert the game into the database with the initial state 'waiting'
    db.execute(
        "INSERT INTO games (gameCode, state, player1_id, player1_username) VALUES (?, ?, ?, ?)",
        game_code, "waiting", user_id, username
    )

    # Store the game code and role in the session
    session['game_code'] = game_code
    session['player_role'] = 'creator'

    return jsonify(num)  # Return the generated game code as JSON

@parties_routes.route('/join_game', methods=['POST'])
def join_game():
    """Allow a user to join an existing game."""
    data = request.get_json()  # Parse JSON request data
    game_code = data.get('game_code')  # Get the game code from the request
    user_id = session.get('user_id')  # Get the current user's ID from the session
    username = session.get('username')  # Get the current user's username from the session

    # Check if the game code exists
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Invalid game code.'}), 404

    # Check if the game is already full (maximum 2 players)
    if game[0]['player1_id'] and game[0]['player2_id']:
        return jsonify({'error': 'The game is already full.'}), 403

    # Check the game's state
    if game[0]['state'] == 'waiting':
        return jsonify({'error': 'The game is not ready yet. Wait for the creator to launch it.'}), 403

    # Add the user as the second player
    if not game[0]['player2_id']:
        db.execute("UPDATE games SET player2_id = ?, player2_username = ? WHERE gameCode = ?", user_id, username, game_code)
        session['game_code'] = game_code
        session['player_role'] = 'joiner'

        return jsonify({'redirect': url_for('parties.partie', game_code=game_code)})  # Redirect to the game page

    return jsonify({'error': 'Unable to join the game.'}), 400

@parties_routes.route('/launch_game', methods=['POST'])
def launch_game():
    """Launch the game and update its state."""
    game_code = session.get('game_code')  # Get the game code from the session
    if not game_code:
        return jsonify({'error': 'No ongoing game.'}), 403

    # Check if the user is the creator of the game
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game or session['player_role'] != 'creator':
        return jsonify({'error': 'You are not authorized to launch this game.'}), 403

    # Check if the game is already started
    if game[0]['state'] == 'started':
        return jsonify({'error': 'The game is already started.'}), 400

    # Update the game's state to 'started'
    db.execute("UPDATE games SET state = 'started' WHERE gameCode = ?", game_code)

    return jsonify({'message': 'The game has started. Player 2 can now join.'})

@parties_routes.route('/game/<game_code>', methods=['GET'])
def partie(game_code):
    """Render the game page for a specific game code."""
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to access the game.", "error")
        return redirect(url_for("log.login"))

    # Retrieve the game from the database
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    game = game[0]
    user_id = int(session['user_id'])
    player1_id = int(game['player1_id'])
    player2_id = int(game['player2_id']) if game['player2_id'] else None

    # Debugging information
    print(f"user_id (session): {user_id} (type: {type(user_id)})")
    print(f"player1_id (game): {player1_id} (type: {type(player1_id)})")
    print(f"player2_id (game): {player2_id} (type: {type(player2_id)})")

    # Check if the user is a participant in the game
    if user_id != player1_id and (player2_id is None or user_id != player2_id):
        flash("You are not a participant in this game.", "error")
        return redirect(url_for("home"))

    # Render the game page
    player1_username = game['player1_username']
    player2_username = game['player2_username'] if game['player2_username'] else "Waiting..."

    return render_template('partie.html', game_code=game_code, player1_username=player1_username, player2_username=player2_username, user_id=user_id)

@parties_routes.route('/get_scores', methods=['GET'])
def get_scores():
    """Get the current scores for a specific game."""
    game_code = request.args.get('game_code')  # Retrieve the game code from the request
    if not game_code:
        return jsonify({'error': 'Game code not provided.'}), 400

    # Retrieve game data from the database
    game = db.execute("SELECT score1, score2 FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    return jsonify({'score1': game[0]['score1'], 'score2': game[0]['score2']}), 200

@parties_routes.route('/update_score', methods=['POST'])
def update_score():
    """Update the score for a player in the game."""
    data = request.get_json()  # Parse JSON request data
    game_code = data.get('game_code')  # Get the game code
    user_id = session.get('user_id')  # Get the current user's ID from the session
    player = data.get('player')  # Player identifier (1 for player1, 2 for player2)
    action = data.get('action')  # Action ('increment' or 'decrement')

    if not game_code or not player or not action:
        return jsonify({'error': 'Invalid data.'}), 400

    # Retrieve the current game
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    game = game[0]
    score1, score2 = game['score1'], game['score2']

    # Verify update permissions
    if player == 1 and int(game['player1_id']) == user_id:
        if action == 'increment':
            score1 += 1
        elif action == 'decrement' and score1 > 0:
            score1 -= 1
    elif player == 2 and int(game['player2_id']) == user_id:
        if action == 'increment':
            score2 += 1
        elif action == 'decrement' and score2 > 0:
            score2 -= 1
    else:
        return jsonify({'error': 'Not authorized to update this score.'}), 403

    # Update the database
    db.execute(
        "UPDATE games SET score1 = ?, score2 = ? WHERE gameCode = ?",
        score1, score2, game_code
    )

    return jsonify({'message': 'Score updated successfully.'}), 200

@parties_routes.route('/game_state', methods=['GET'])
def game_state():
    """Retrieve the state of the current game."""
    game_code = session.get('game_code')  # Get the game code from the session
    if not game_code:
        return jsonify({'error': 'Game code not provided.'}), 400

    # Retrieve the game from the database
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    return jsonify({'game_code': game_code, 'state': game[0]['state']}), 200

@parties_routes.route('/end_game', methods=['POST'])
def end_game():
    """End the current game and update its state."""
    game_code = session.get('game_code')  # Get the game code from the session
    if not game_code:
        return jsonify({'error': 'No ongoing game.'}), 403

    # Retrieve the game from the database
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if game[0]['score1'] > game[0]['score2']:
        db.execute("UPDATE games SET winner = ? WHERE gameCode = ?", game[0]['player1_username'], game_code)
    elif game[0]['score2'] > game[0]['score1']:
        db.execute("UPDATE games SET winner = ? WHERE gameCode = ?", game[0]['player2_username'], game_code)
    else:
        db.execute("UPDATE games SET winner = 'Draw' WHERE gameCode = ?", game_code)

    # Update the game's state to 'ended'
    db.execute("UPDATE games SET state = 'ended' WHERE gameCode = ?", game_code)
    session.pop('game_code', None)  # Remove the game code from the session
    session.pop('player_role', None)  # Remove the player role from the session

    flash(f"Game {game_code} ended by {session.get('username')}", 'success')  # Flash a success message
    redirect_url = url_for('user.user_profile', user_id=session.get('user_id'))  # Redirect to the user's profile

    return jsonify({'message': 'Game ended successfully.', 'redirect': redirect_url}), 200
