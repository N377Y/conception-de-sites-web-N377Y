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
    # Generate a list of 6 random numbers between 0 and 9
    num = [random.randint(0, 9) for _ in range(6)]

    # Convert the list to a string
    game_code = ''.join(map(str, num))

    # Insérer la partie dans la base de données
    db.execute(
        "INSERT INTO games (gameCode, state) VALUES (?, ?)",
        game_code, "waiting"
    )

    # Enregistrer la partie dans la session
    session['game_code'] = game_code

    return jsonify(num)


@parties_routes.route('/join_game', methods=['POST'])
def join_game():
    """Permet à un joueur de rejoindre une partie."""
    data = request.get_json()
    game_code = data.get('game_code')

    # Vérifier si le code existe dans la base de données
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Code de partie invalide.'}), 404

    # Associer le joueur à la session
    session['game_code'] = game_code

    # Rediriger vers la page de la partie
    return redirect(url_for('parties.partie', game_code=game_code))

@parties_routes.route('/game/<game_code>', methods=['GET'])
def partie(game_code):
    """Affiche la page de la partie."""
    # Vérifier si le jeu existe
    game = db.execute("SELECT * FROM games WHERE gameCode = ?", game_code)
    if not game:
        return jsonify({'error': 'Partie introuvable.'}), 404

    return render_template('partie.html', game_code=game_code)



@parties_routes.route('/game_state', methods=['GET'])
def game_state():
    """Récupérer l'état de la partie actuelle."""
    game_code = session.get('game_code')
    if not game_code:
        return jsonify({'error': 'Aucune partie en cours.'}), 403

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

    # Supprimer la partie de la base de données
    db.execute("DELETE FROM games WHERE gameCode = ?", game_code)
    session.pop('game_code', None)

    return jsonify({'message': 'Partie terminée avec succès.'}), 200
