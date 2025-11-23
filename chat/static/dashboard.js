// Connexion WebSocket
const socket = io();

// Elements DOM
const messagesBox = document.getElementById('messagesBox');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const navBtns = document.querySelectorAll('.nav-btn');
const tabContents = document.querySelectorAll('.tab-content');
const pageTitle = document.getElementById('pageTitle');
const unreadAlertsSpan = document.getElementById('unreadAlerts');
const clearAlertsBtn = document.getElementById('clearAlertsBtn');

let currentTab = 'chat';
let allAlerts = [];
let allMessages = [];
let allDiagnostics = [];

// ==================== NAVIGATION ====================

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Mettre à jour le bouton actif
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Afficher le bon onglet
        tabContents.forEach(tab => tab.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
        currentTab = tabName;
        
        // Mettre à jour le titre
        const titles = {
            'chat': '💬 Chat avec le Système',
            'alerts': '🚨 Alertes Système',
            'diagnostics': '📋 Historique des Diagnostics',
            'stats': '📊 Statistiques'
        };
        pageTitle.textContent = titles[tabName] || 'Dashboard';
        
        // Charger les données si nécessaire
        if (tabName === 'alerts') loadAlerts();
        else if (tabName === 'diagnostics') loadDiagnostics();
        else if (tabName === 'stats') loadStats();
    });
});

// ==================== CHAT ====================

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Ajouter le message utilisateur
    addMessage(message, 'user');
    messageInput.value = '';
    
    // Émettre via WebSocket
    socket.emit('send_message', { content: message });
    
    // Demander une réponse du système
    socket.emit('request_system_response', { query: message });
});

function addMessage(content, sender = 'user') {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender === 'user' ? 'user-message' : 'system-message'}`;
    
    const nameSpan = document.createElement('strong');
    nameSpan.textContent = sender === 'user' ? 'Vous' : 'Système';
    
    const pTag = document.createElement('p');
    pTag.textContent = content;
    
    msgDiv.appendChild(nameSpan);
    msgDiv.appendChild(pTag);
    
    messagesBox.appendChild(msgDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

// ==================== WEBSOCKET EVENTS ====================

socket.on('connect', () => {
    console.log('✅ Connecté au serveur');
    loadMessages();
    loadAlerts();
    loadStats();
});

socket.on('new_message', (data) => {
    addMessage(data.content, data.is_from_system ? 'system' : 'user');
});

socket.on('system_response', (data) => {
    addMessage(data.content, 'system');
});

socket.on('system_error', (data) => {
    addMessage(`Erreur: ${data.error}`, 'system');
});

socket.on('new_alert', (data) => {
    console.log('🚨 Nouvelle alerte:', data);
    allAlerts.unshift(data);
    updateUnreadAlerts();
    if (currentTab === 'alerts') renderAlerts();
    // Notification
    showNotification(`Alerte: ${data.title}`, data.message, 'warning');
});

socket.on('alert_read', (data) => {
    updateUnreadAlerts();
});

socket.on('new_diagnostic', (data) => {
    console.log('📋 Nouveau diagnostic:', data);
    allDiagnostics.unshift(data);
    if (currentTab === 'diagnostics') renderDiagnostics();
    // Notification
    showNotification(`Diagnostic: ${data.diagnostic_id}`, data.description, 'info');
});

// ==================== CHARGEMENT DES DONNÉES ====================

async function loadMessages() {
    try {
        const response = await fetch('/api/messages');
        if (response.ok) {
            allMessages = await response.json();
            allMessages.forEach(msg => {
                addMessage(msg.content, msg.is_from_system ? 'system' : 'user');
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement messages:', error);
    }
}

async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts?limit=100');
        if (response.ok) {
            allAlerts = await response.json();
            updateUnreadAlerts();
            renderAlerts();
        }
    } catch (error) {
        console.error('❌ Erreur chargement alertes:', error);
    }
}

async function loadDiagnostics() {
    try {
        const response = await fetch('/api/diagnostics?limit=50');
        if (response.ok) {
            allDiagnostics = await response.json();
            renderDiagnostics();
        }
    } catch (error) {
        console.error('❌ Erreur chargement diagnostics:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('totalAlerts').textContent = stats.total_alerts;
            document.getElementById('criticalAlerts').textContent = stats.critical_alerts;
            document.getElementById('totalMessages').textContent = stats.total_messages;
            document.getElementById('totalDiagnostics').textContent = stats.total_diagnostics;
        }
    } catch (error) {
        console.error('❌ Erreur chargement stats:', error);
    }
}

// ==================== RENDU ALERTES ====================

function renderAlerts() {
    const alertsList = document.getElementById('alertsList');
    
    if (allAlerts.length === 0) {
        alertsList.innerHTML = '<p class="empty-message">Aucune alerte</p>';
        return;
    }
    
    alertsList.innerHTML = allAlerts.map(alert => `
        <div class="alert-item ${alert.is_read ? '' : 'unread'} ${alert.severity === 'critical' ? 'critical' : ''}">
            <div class="alert-content">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${new Date(alert.created_at).toLocaleString()}</div>
            </div>
            <span class="alert-severity ${alert.severity}">${alert.severity.toUpperCase()}</span>
            ${!alert.is_read ? `
                <button class="btn btn-small btn-primary" onclick="markAlertRead(${alert.id})">Marquer lu</button>
            ` : ''}
        </div>
    `).join('');
}

async function markAlertRead(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/read`, { method: 'PUT' });
        if (response.ok) {
            const alert = allAlerts.find(a => a.id === alertId);
            if (alert) alert.is_read = true;
            renderAlerts();
            updateUnreadAlerts();
        }
    } catch (error) {
        console.error('❌ Erreur marquer alerte:', error);
    }
}

function updateUnreadAlerts() {
    const unreadCount = allAlerts.filter(a => !a.is_read).length;
    unreadAlertsSpan.textContent = `${unreadCount} ⚠️`;
}

// ==================== RENDU DIAGNOSTICS ====================

function renderDiagnostics() {
    const diagnosticsList = document.getElementById('diagnosticsList');
    
    if (allDiagnostics.length === 0) {
        diagnosticsList.innerHTML = '<p class="empty-message">Aucun diagnostic</p>';
        return;
    }
    
    diagnosticsList.innerHTML = allDiagnostics.map(diag => `
        <div class="diagnostic-card">
            <div class="diagnostic-id">ID: ${diag.diagnostic_id}</div>
            <div class="diagnostic-description">${diag.description || 'Pas de description'}</div>
            <span class="diagnostic-status ${diag.status}">${diag.status.toUpperCase()}</span>
            <div class="diagnostic-time">${new Date(diag.created_at).toLocaleString()}</div>
            ${diag.result ? `
                <details style="margin-top: 10px; font-size: 12px;">
                    <summary>Voir le résultat</summary>
                    <pre style="background: #f1f5f9; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 5px;">${JSON.stringify(diag.result, null, 2)}</pre>
                </details>
            ` : ''}
        </div>
    `).join('');
}

// ==================== NOTIFICATIONS ====================

function showNotification(title, message, type = 'info') {
    // Utiliser la notification du navigateur si disponible
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/icon.png'
        });
    }
    
    // Fallback: afficher dans la console
    console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
}

// Demander la permission pour les notifications
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// ==================== INITIALISATION ====================

// Charger les données au chargement
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
    loadAlerts();
    loadStats();
});

// Rafraîchir les stats toutes les 30 secondes
setInterval(() => {
    if (currentTab === 'stats') loadStats();
}, 30000);

// Bouton "Marquer tout comme lu"
clearAlertsBtn.addEventListener('click', async () => {
    for (const alert of allAlerts.filter(a => !a.is_read)) {
        await markAlertRead(alert.id);
    }
});
