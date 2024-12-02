document.addEventListener("DOMContentLoaded", () => {
    // Section toggling
    const viewUsersBtn = document.getElementById("view-users-btn");
    const viewGamesBtn = document.getElementById("view-games-btn");
    const adminPanelBtn = document.getElementById("admin-panel-btn");

    const usersSection = document.getElementById("users-section");
    const gamesSection = document.getElementById("games-section");
    const adminPanelSection = document.getElementById("admin-panel-section");

    // Helper function to toggle sections
    const toggleSection = (sectionToShow) => {
        [usersSection, gamesSection, adminPanelSection].forEach(section => {
            if (section === sectionToShow) {
                section.classList.add("active");
            } else {
                section.classList.remove("active");
            }
        });
    };

    // Toggle Users Section
    viewUsersBtn.addEventListener("click", () => toggleSection(usersSection));

    // Toggle Games Section
    viewGamesBtn.addEventListener("click", () => toggleSection(gamesSection));

    // Toggle Admin Panel Section
    adminPanelBtn.addEventListener("click", () => toggleSection(adminPanelSection));

    // Handle Add User Form
    document.getElementById("add-user-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        fetch("/admin/add_user", {
            method: "POST",
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message);
                location.reload();
            })
            .catch((error) => console.error("Error:", error));
    });

    // Handle Delete User Form
    document.getElementById("delete-user-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        fetch("/admin/delete_user", {
            method: "POST",
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message);
                location.reload();
            })
            .catch((error) => console.error("Error:", error));
    });

    // Handle Clear Database
    document.getElementById("clear-database-btn").addEventListener("click", () => {
        if (confirm("Are you sure you want to clear the database?")) {
            fetch("/admin/clear_database", { method: "POST" })
                .then((response) => response.json())
                .then((data) => alert(data.message))
                .catch((error) => console.error("Error:", error));
        }
    });

    // Modal for User Stats
    const statsModal = document.getElementById("stats-modal");
    const statsContainer = document.getElementById("stats-container");
    const statsUsername = document.getElementById("stats-username");
    const closeStatsModal = document.getElementById("close-stats-modal");

    // Add event listeners to username links
    document.querySelectorAll(".view-stats").forEach(link => {
        link.addEventListener("click", async (e) => {
            e.preventDefault();
            const username = e.target.dataset.username;

            // Fetch user stats from the server
            try {
                const response = await fetch(`/stats?username=${username}`);
                const data = await response.json();

                if (response.ok) {
                    // Populate the modal with stats
                    statsUsername.textContent = username;
                    if (data.length > 0) {
                        statsContainer.innerHTML = `
                            <table>
                                <thead>
                                    <tr>
                                        <th>Player 1</th>
                                        <th>Player 2</th>
                                        <th>Score 1</th>
                                        <th>Score 2</th>
                                        <th>Winner</th>
                                    </tr>
                                </thead>
                                <tbody style=" margin-bottom: 10mm;">
                                    ${data.map(game => `
                                        <tr>
                                            <td>${game.player1_username}</td>
                                            <td>${game.player2_username}</td>
                                            <td>${game.score1}</td>
                                            <td>${game.score2}</td>
                                            <td>${game.winner}</td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        `;
                    } else {
                        statsContainer.innerHTML = `<p>No stats available for this user.</p>`;
                    }
                } else {
                    statsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
                }

                // Show the modal
                statsModal.classList.add("show");
            } catch (error) {
                console.error("Error fetching stats:", error);
                statsContainer.innerHTML = `<p>Failed to load stats. Please try again later.</p>`;
                statsModal.classList.add("show");
            }
        });
    });

    // Close Modal
    closeStatsModal.addEventListener("click", () => {
        statsModal.classList.remove("show");
        statsContainer.innerHTML = ""; // Clear the modal content
    });

    // Optional: Close modal when clicking outside of the modal content
    statsModal.addEventListener("click", (event) => {
        if (event.target === statsModal) {
            statsModal.classList.remove("show");
            statsContainer.innerHTML = ""; // Clear the modal content
        }
    });
});
