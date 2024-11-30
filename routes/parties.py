from functools import wraps
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import random

# Création du Blueprint
parties_routes = Blueprint('parties', __name__)

# Initialisation de la base de données
if not os.path.exists("database.db"):
    open("database.db", "w").close()
    db = SQL("sqlite:///database.db")
    # Créer la table si elle n'existe pas
    with open("database.sql", "r") as sql_file:
        sql_statements = sql_file.read().split(';')
        for statement in sql_statements:
            if statement.strip():
                db.execute(statement)
else:
    db = SQL("sqlite:///database.db")


@parties_routes.route('/start_game', methods=['POST'])
def start_game():
    # Generate a random game code
    num = [random.randint(0, 9) for _ in range(6)]
    game_code = ''.join(map(str, num))
    user_id = session.get('user_id')
    username = session.get('username')

    # Insert the game in the database with the initial state 'waiting'
    db.execute(
        "INSERT INTO games (gameCode, state, player1_id, player1_username) VALUES (?, ?, ?, ?)",
        game_code, "waiting", user_id, username
    )

    # Store game code in session
    session['game_code'] = game_code
    session['player_role'] = 'creator'

    return jsonify(num)



@parties_routes.route('/join_game', methods=['POST'])
def join_game():
    data = request.get_json()
    game_code = data.get('game_code')
    user_id = session.get('user_id')
    username = session.get('username')

    # Vérifier si le code de jeu existe et son état
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Code de partie invalide.'}), 404

    # Vérifier l'état du jeu - Player 2 ne peut rejoindre que si la partie est "ready" ou "started"
    if game[0]['state'] != 'started':
        return jsonify({'error': 'La partie n\'est pas encore prête. Attendez que le créateur de la partie la lance.'}), 403

    # Mettre à jour la partie avec le deuxième joueur
    db.execute("UPDATE games SET player2_id = ?, player2_username = ?  WHERE gameCode = ?", user_id, username, game_code)

    # Associer le joueur à la session
    session['game_code'] = game_code
    session['player_role'] = 'joiner'

    # Renvoyer l'URL à utiliser pour la redirection
    return jsonify({'redirect': url_for('parties.partie', game_code=game_code)})



@parties_routes.route('/launch_game', methods=['POST'])
def launch_game():
    game_code = session.get('game_code')
    if not game_code:
        return jsonify({'error': 'Aucune partie en cours.'}), 403

    # Vérifier si l'utilisateur est bien le créateur de la partie
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game or session['player_role'] != 'creator':
        return jsonify({'error': 'Vous n\'êtes pas autorisé à lancer cette partie.'}), 403

    # Mettre à jour l'état de la partie à 'started'
    db.execute("UPDATE games SET state = 'started' WHERE gameCode = ?", game_code)

    # Retourner une réponse pour informer que la partie est prête à commencer
    return jsonify({'message': 'La partie est prête, le joueur 2 peut maintenant rejoindre.'})




@parties_routes.route('/game/<game_code>', methods=['GET'])
def partie(game_code):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to access the game.", "error")
        return redirect(url_for("login"))

    # Get the game from the database
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    game = game[0]
    user_id = int(session['user_id'])
    player1_id = int(game['player1_id'])
    player2_id = int(game['player2_id']) if game['player2_id'] else None

    # Debugging prints
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
    game_code = request.args.get('game_code')
    if not game_code:
        return jsonify({'error': 'Game code not provided.'}), 400

    # Retrieve game data
    game = db.execute("SELECT score1, score2 FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    game = game[0]
    return jsonify({'score1': game['score1'], 'score2': game['score2']}), 200



@parties_routes.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    game_code = data.get('game_code')
    userId = session.get('user_id')
    player = data.get('player')
    action = data.get('action')  # 'increment' or 'decrement'

    if not game_code or not player or not action:
        return jsonify({'error': 'Invalid data provided.'}), 400

    # Retrieve current scores
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Game not found.'}), 404

    game = game[0]
    score1 = game['score1']
    score2 = game['score2']

        # Update the appropriate score
    if player == 1:
        if int(game['player1_id']) == userId:
            if action == 'increment':
                score1 += 1
            elif action == 'decrement' and score1 > 0:
                score1 -= 1
    elif player == 2:
        if int(game['player2_id']) == userId:
            if action == 'increment':
                score2 += 1
            elif action == 'decrement' and score2 > 0:
                score2 -= 1

        # Update the scores in the database
    db.execute(
            "UPDATE games SET score1 = ?, score2 = ? WHERE gameCode = ?",
            score1, score2, game_code
        )
    

    return jsonify({'message': 'Score updated successfully.'}), 200



@parties_routes.route('/game_state', methods=['GET'])
def game_state():
    """Récupérer l'état de la partie actuelle."""
    game_code = session.get('game_code')
    if not game_code:
        return jsonify({'error': 'Game code not provided.'}), 400

    # Récupérer les données de la partie
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Partie introuvable.'}), 404

    return jsonify({'game_code': game_code, 'state': game[0]['state']}), 200


@parties_routes.route('/end_game', methods=['POST'])
def end_game():
    """Terminer la partie actuelle."""
    game_code = session.get('game_code')
    if not game_code:
        return jsonify({'error': 'Aucune partie en cours.'}), 403

    # Chqnger le statut la partie de la base de données
    db.execute("UPDATE games SET state = 'ended' WHERE gameCode = ?", game_code)
    session.pop('game_code', None)
    session.pop('player_role', None)

    flash(f"Game {game_code} ended by {session.get('username')}", 'success')
    redirect_url = url_for('user_profile', user_id=session.get('user_id'))

    return jsonify({'message': 'Partie terminée avec succès.','redirect': redirect_url}), 200