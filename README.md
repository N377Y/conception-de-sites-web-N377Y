[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/D1k672bR)
# Flask Boilerplate

Un projet Flask simple avec une structure de base.

## Installation

1. Créer un environnement virtuel :

```bash
python -m venv venv
```

2. Activer l'environnement virtuel :

- Windows :
```cmd
. venv\Scripts\activate
```
- Linux/Mac :
```bash
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement

Pour lancer l'application :
```bash
python app.py
```

L'application sera accessible à l'adresse : http://127.0.0.1:5000


La structure finale du projet sera :
```
.
├── models/
│   └── user.py
├── static/
│   └── styles.css
├── templates/
│   ├── layout.html
│   └── index.html
├── .gitignore
├── app.py
├── README.md
├── database.sql
└── requirements.txt
```