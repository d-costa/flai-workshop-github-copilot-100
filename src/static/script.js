const activitiesContainer = document.getElementById('activities-container');
const emailInput = document.getElementById('email-input');

// Fetch and display activities
async function loadActivities() {
    try {
        const response = await fetch('/activities');
        const activities = await response.json();
        displayActivities(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
        activitiesContainer.innerHTML = '<p>Error loading activities. Please try again later.</p>';
    }
}

// Display activities in the UI
function displayActivities(activities) {
    activitiesContainer.innerHTML = '';
    
    for (const [name, details] of Object.entries(activities)) {
        const card = document.createElement('div');
        card.className = 'activity-card';
        
        const participantsList = details.participants && details.participants.length > 0
            ? `<ul class="participants-list">
                ${details.participants.map(email => `<li>${email}</li>`).join('')}
               </ul>`
            : '<p class="no-participants">No participants yet</p>';
        
        card.innerHTML = `
            <h2>${name}</h2>
            <p class="description">${details.description}</p>
            <p class="schedule"><strong>Schedule:</strong> ${details.schedule}</p>
            <p class="capacity"><strong>Capacity:</strong> ${details.current_participants || details.participants.length}/${details.max_participants}</p>
            <div class="participants-section">
                <h3>Participants:</h3>
                ${participantsList}
            </div>
            <button onclick="signUp('${name}')">Sign Up</button>
        `;
        
        activitiesContainer.appendChild(card);
    }
}

// Sign up for an activity
async function signUp(activityName) {
    const email = emailInput.value.trim();
    
    if (!email) {
        alert('Please enter your email address');
        return;
    }
    
    if (!email.includes('@')) {
        alert('Please enter a valid email address');
        return;
    }
    
    try {
        const response = await fetch(`/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(email)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(result.message);
            loadActivities(); // Reload to show updated participant list
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error signing up:', error);
        alert('Error signing up. Please try again later.');
    }
}

// Load activities when page loads
loadActivities();