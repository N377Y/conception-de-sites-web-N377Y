// Ensure all buttons are enabled on page refresh
    toggleButtonsForAction('enable'); // Explicitly enable all buttons on page load


function toggleButtonsForAction(action) {
    const buttons = document.querySelectorAll('button'); // Select all buttons
    buttons.forEach(button => {
        switch (action) {
            case 'join_game':
                button.disabled = !button.id.includes('validate'); // Only enable the validate button
                break;
            case 'start_game':
                button.disabled = !button.id.includes('startGameButton'); // Only enable the launch button
                break;
            case 'profile':
                button.disabled = button.id !== 'change' && button.id !== 'save' && button.id !== 'update-status-btn'; // Enable profile-related buttons
                break;
            case 'see_stats':
                button.disabled = true; // Disable all buttons
                break;
            case 'enable':
                button.disabled = false; // Enable all buttons
        }
    });
}





document.getElementById('start').onclick = async function (e) {
        e.preventDefault();

        // Get the element to display the result
        const codebox = document.getElementById('ball');
        const launcher = document.getElementById('launcher');
        launcher.removeAttribute('hidden');
        const principal = document.getElementById('acceuil');
        principal.style.filter = 'blur(5px)';;

        try {
            // Send the POST request to the server
            const response = await fetch('/start_game', {
                method: 'POST'
            });

            // Check if the response is OK
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            // Parse the JSON response
            const code = await response.json();

            // Create a new paragraph element to display the result

            const bigBox = document.createElement('div');
            bigBox.id = "code";
            code.forEach((num) => {
                // Create a new div element for each number
                const boxElement = document.createElement('div');
                boxElement.textContent = num; // Set the number as the content
                boxElement.style.color = 'darkgreen';
                boxElement.style.backgroundColor = 'white';
                boxElement.style.border = '1px solid darkgreen';
                boxElement.style.padding = '10px';
                boxElement.style.margin = '5px';
                boxElement.style.display = 'inline-block'; // Display elements side-by-side
                boxElement.style.borderRadius = '5px';
                boxElement.style.fontSize = '16px';
                bigBox.append(boxElement);
        });

        // Append the box to the codebox container
        codebox.appendChild(bigBox);

        // Generate the QR code
        const qrData = "https://footelly.onrender.com/game/"+code.join(''); // Combine all numbers into a string
        const qrCodeURL = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrData)}&size=200x200`;
        const qrImage = document.getElementById('qrcode');

        if (qrImage) {
            qrImage.src = qrCodeURL;
        } else {
            // If QR code container is missing, create it
            const newQrImage = document.createElement('img');
            newQrImage.id = 'qrcode';
            newQrImage.src = qrCodeURL;
            codebox.appendChild(newQrImage);
        }
        toggleButtonsForAction('start_game'); // Disable all except launch game

        } catch (error) {
            console.error('Error:', error);

            // Create and append an error message
            const errorMessage = document.createElement('p');
            errorMessage.style.color = "red";
            errorMessage.innerHTML = `<strong>Error:</strong> ${error.message}`;
            codebox.appendChild(errorMessage);
        }


    };

    // Close button logic
    document.getElementById('closeButton1').onclick = function () {
            const codebox = document.getElementById('ball');
            const launcher = document.getElementById('launcher');
            const principal = document.getElementById('acceuil');
            const code = document.getElementById('code')
            // Reset the codebox to its initial state
            launcher.setAttribute('hidden', 'true'); 
            // Hide the codebox by removing it from the DOM
            code.remove();
            principal.style.filter = 'blur(0px)';
            toggleButtonsForAction('enable'); // Re-enable all buttons


        };

        document.getElementById('view_profile').onclick = function () {
            const user = document.getElementById('user_info');
            user.removeAttribute('hidden');
            const principal = document.getElementById('acceuil');
            principal.style.filter = 'blur(5px)';
            toggleButtonsForAction('profile'); // Disable all except launch game
        };

        document.getElementById('change').onclick = function (e) {
            e.preventDefault();
            const change = document.getElementById('pro_pic');
            change.removeAttribute('hidden');
        };

        document.getElementById('choose_user').addEventListener('change', function () {
            const username = this.value; // Récupère l'utilisateur sélectionné

            if (username) {
                // Appelle l'API Flask pour récupérer les statistiques
                fetch(`/stats?username=${username}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error("Erreur lors de la récupération des données.");
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Affiche les données dans la page
                        displayStats(data);
                    })
                    .catch(error => {
                        console.error(error);
                        document.getElementById('stats_container').innerHTML = `
                            <p style="color: red;">Cannot Show stats. Try again later.</p>
                        `;
                    });
            }
        });


        document.getElementById('save').onclick = function () {
            const change = document.getElementById('pro_pic');
            change.setAttribute('hidden');
        };

        console.log(document.getElementById('join'));
        document.addEventListener('DOMContentLoaded', function () {
            const joinButton = document.getElementById('join');
            console.log(joinButton); // Debugging log
            if (joinButton) {
                joinButton.addEventListener('click', function () {
                console.log('Join button clicked'); // Debugging log
                toggleButtonsForAction('join_game'); // Disable all except launch game

                // Show the modal
                const codebox = document.getElementById('door');
                codebox.removeAttribute('hidden');
                const principal = document.getElementById('acceuil');
                principal.style.filter = 'blur(5px)';
                    });
            }
        });

        document.getElementById('stats').onclick = async function (e) {
            e.preventDefault();
            toggleButtonsForAction('see_stats'); // Disable all except launch game
            // Get the element to display the result
            const choice = document.getElementById('view_stats');
            choice.removeAttribute('hidden');
        };
        const inputs = document.querySelectorAll(".code-container input");

        // Permet de passer automatiquement au champ suivant
        inputs.forEach((input, index) => {
            input.addEventListener("input", (event) => {
                const value = event.target.value;
                if (value.length === 1 && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            });

            // Permet de revenir au champ précédent si on efface
            input.addEventListener("keydown", (event) => {
                if (event.key === "Backspace" && index > 0 && !input.value) {
                    inputs[index - 1].focus();
                }
            });
        });

        // Gestion du formulaire
        document.getElementById('validate').onclick = async function (e) {
            e.preventDefault();

            // Récupérer les valeurs des cases
            const code = Array.from(inputs).map(input => input.value).join("");

            if (code.length === 6) {
                console.log("Code soumis :", code);
                // Envoyer au backend (Exemple avec fetch)

                        // Appel AJAX pour rejoindre une partie
                        fetch('/join_game', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ game_code: code })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.redirect) {
                                // Rediriger vers l'URL reçue
                                window.location.href = data.redirect;
                            } else if (data.error) {
                                // Gérer l'erreur (ex: code de partie invalide)
                                alert(data.error);
                            }
                        })
                        .catch(error => console.error('Erreur:', error));
                    }

                
            };

        document.getElementById('closeButton2').onclick = function () {
            const codebox = document.getElementById('door');
            const principal = document.getElementById('acceuil');
            // Reset the codebox to its initial state
            codebox.setAttribute('hidden', 'true'); 
            principal.style.filter = 'blur(0px)';
            toggleButtonsForAction('enable'); // Re-enable all buttons

        };

        document.getElementById('closeButton3').onclick = function () {
            const user = document.getElementById('user_info');
            // Reset the codebox to its initial state
            user.setAttribute('hidden', 'true'); 
            const principal = document.getElementById('acceuil');
            principal.style.filter = 'blur(0px)';
            toggleButtonsForAction('enable'); // Re-enable all buttons
        };

        document.getElementById('closeButton4').onclick = function () {
            const container = document.getElementById('stats_container');
            container.innerHTML = ''; // Clear the stats content
            const choice = document.getElementById('view_stats');
            // Reset the codebox to its initial state
            choice.setAttribute('hidden', 'true');
            const selectElement = document.getElementById('choose_user');
            selectElement.value = ''; // Reset the select element to its default value 
            toggleButtonsForAction('enable'); // Re-enable all buttons
        };


        function launchGame() {
            fetch('/launch_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect) {
                    // Rediriger vers l'URL reçue
                    window.location.href = data.redirect;
                } else if (data.error) {
                    // Gérer l'erreur (ex: code de partie invalide)
                    alert(data.error);
                }
                })
            .catch(error => console.error('Erreur:', error));
        }
        function checkGameStatus(gameCode) {
            fetch(`/game_state?game_code=${gameCode}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.state === 'ready' || data.state === 'started') {
                    // Rediriger vers la page de la partie
                    window.location.href = `/game/${data.game_code}`;
                } else {
                    console.log('En attente du lancement de la partie...');
                }
            })
            .catch(error => console.error('Erreur:', error));
        }
        // Fonction pour afficher les statistiques
        function displayStats(stats) {
            const container = document.getElementById('stats_container');

            // Si aucune donnée n'est trouvée
            if (stats.length === 0) {
                container.innerHTML = `<p>No game found for this user or profile might be private</p>`;
                return;
            }

            // Génère le HTML des statistiques
            let statsHTML = `<h2>Stats of User</h2>`;
            statsHTML += `
                <table border="1" style="border-collapse: collapse;" id="stats_table">
                    <thead>
                        <tr>
                            <th>Player 1</th>
                            <th>Player 2</th>
                            <th>Score Player 1</th>
                            <th>Score Player 2</th>
                            <th>Winner</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            stats.forEach(game => {
                statsHTML += `
                    <tr>
                        <td>${game.player1_username}</td>
                        <td>${game.player2_username}</td>
                        <td>${game.score1}</td>
                        <td>${game.score2}</td>
                        <td>${game.winner}</td>
                    </tr>
                `;
            });


            statsHTML += `</tbody></table>`;
            container.innerHTML = statsHTML;
        }


        const statusSelect = document.getElementById("status-select");
        const updateBtn = document.getElementById("update-status-btn");
        const statusMessage = document.getElementById("status-message");
        const currentStatus = document.getElementById("current-status");

        updateBtn.addEventListener("click", async () => {
            const newStatus = statusSelect.value;

            try {
                const response = await fetch("/profile/update_status", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: newStatus })
                });

                if (response.ok) {
                    const data = await response.json();
                    currentStatus.textContent = data.status; // Update the displayed status
                } else {
                    throw new Error("Failed to update status.");
                }
            } catch (error) {
                console.error(error);
                statusMessage.style.color = "red";
                statusMessage.textContent = "An error occurred while updating your status.";
            }
        });


// Appeler la fonction checkGameStatus toutes les 3 secondes tant que le jeu n'est pas lancé
        setInterval(() => {
            const gameCode = "{{ game_code }}";  // Assurez-vous que cette variable est définie dans votre modèle
            checkGameStatus(gameCode);
        }, 3000);

