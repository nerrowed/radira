// RADIRA Web Chat - Client Application

class RadiraChat {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.config = {
            orchestrator_type: 'function_calling',
            enable_memory: false,
            confirmation_mode: 'auto'
        };

        this.initElements();
        this.attachEventListeners();
    }

    initElements() {
        // Screens
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.chatContainer = document.getElementById('chatContainer');
        this.inputArea = document.getElementById('inputArea');
        this.sessionInfo = document.getElementById('sessionInfo');

        // Buttons
        this.startChatBtn = document.getElementById('startChatBtn');
        this.newSessionBtn = document.getElementById('newSessionBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.sendBtn = document.getElementById('sendBtn');
        this.saveSettingsBtn = document.getElementById('saveSettingsBtn');

        // Input
        this.messageInput = document.getElementById('messageInput');

        // Chat
        this.chatMessages = document.getElementById('chatMessages');
        this.typingIndicator = document.getElementById('typingIndicator');

        // Session info
        this.currentSessionId = document.getElementById('currentSessionId');
        this.orchestratorType = document.getElementById('orchestratorType');
        this.statIterations = document.getElementById('statIterations');
        this.statTokens = document.getElementById('statTokens');
        this.statTools = document.getElementById('statTools');

        // Modal
        this.settingsModal = document.getElementById('settingsModal');
        this.orchestratorSelect = document.getElementById('orchestratorSelect');
        this.enableMemory = document.getElementById('enableMemory');
        this.confirmationMode = document.getElementById('confirmationMode');

        // Status
        this.connectionStatus = document.getElementById('connectionStatus');
    }

    attachEventListeners() {
        // Start chat
        this.startChatBtn.addEventListener('click', () => this.createSession());

        // New session
        this.newSessionBtn.addEventListener('click', () => this.showNewSessionConfirm());

        // Settings
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.settingsModal.classList.add('hidden');
        });

        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        // Input handling
        this.messageInput.addEventListener('input', (e) => {
            this.autoResize(e.target);
            this.sendBtn.disabled = !e.target.value.trim();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.messageInput.value.trim()) {
                    this.sendMessage();
                }
            }
        });

        // Hint buttons
        document.querySelectorAll('.hint-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const hint = btn.getAttribute('data-hint');
                this.messageInput.value = hint;
                this.autoResize(this.messageInput);
                this.sendBtn.disabled = false;
                this.messageInput.focus();
            });
        });
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    showSettings() {
        this.orchestratorSelect.value = this.config.orchestrator_type;
        this.enableMemory.checked = this.config.enable_memory;
        this.confirmationMode.value = this.config.confirmation_mode;
        this.settingsModal.classList.remove('hidden');
    }

    saveSettings() {
        this.config.orchestrator_type = this.orchestratorSelect.value;
        this.config.enable_memory = this.enableMemory.checked;
        this.config.confirmation_mode = this.confirmationMode.value;
        this.settingsModal.classList.add('hidden');

        // If already in a session, create a new one with new settings
        if (this.sessionId) {
            this.createSession();
        }
    }

    showNewSessionConfirm() {
        if (confirm('Start a new session? Current conversation will be lost.')) {
            this.createSession();
        }
    }

    async createSession() {
        try {
            this.showConnectionStatus('Creating session...', 'connecting');

            const response = await fetch('/api/session/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    config: this.config
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create session');
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            // Update UI
            this.welcomeScreen.classList.add('hidden');
            this.chatContainer.classList.remove('hidden');
            this.inputArea.classList.remove('hidden');
            this.sessionInfo.classList.remove('hidden');

            this.currentSessionId.textContent = this.sessionId.substring(0, 8);
            this.orchestratorType.textContent = this.getOrchestratorName(this.config.orchestrator_type);

            // Clear chat
            this.chatMessages.innerHTML = '';

            // Connect WebSocket
            this.connectWebSocket();

        } catch (error) {
            console.error('Error creating session:', error);
            this.showConnectionStatus('Failed to create session', 'error');
            alert('Failed to create session. Please try again.');
        }
    }

    getOrchestratorName(type) {
        const names = {
            'function_calling': 'Function Calling',
            'dual': 'Dual Orchestrator',
            'classic': 'Classic'
        };
        return names[type] || type;
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;

        this.showConnectionStatus('Connecting...', 'connecting');

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.showConnectionStatus('Connected', 'connected');
            setTimeout(() => {
                this.connectionStatus.classList.add('hidden');
            }, 2000);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showConnectionStatus('Connection error', 'error');
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.showConnectionStatus('Disconnected', 'error');
        };
    }

    handleMessage(data) {
        console.log('Received:', data);

        switch (data.type) {
            case 'system':
                this.addSystemMessage(data.message);
                break;

            case 'user_message':
                // Already displayed when sent
                break;

            case 'status':
                this.showTyping(data.message);
                break;

            case 'assistant_message':
                this.hideTyping();
                this.addAssistantMessage(data.content);
                break;

            case 'stats':
                this.updateStats(data.data);
                break;

            case 'error':
                this.hideTyping();
                this.addErrorMessage(data.message);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        // Add user message to UI
        this.addUserMessage(message);

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'message',
            content: message
        }));

        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.sendBtn.disabled = true;

        // Disable input while processing
        this.messageInput.disabled = true;
    }

    addUserMessage(content) {
        const messageDiv = this.createMessageElement('user', '👤', content);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addAssistantMessage(content) {
        const messageDiv = this.createMessageElement('assistant', '🤖', content);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        this.messageInput.disabled = false;
        this.messageInput.focus();
    }

    addSystemMessage(content) {
        const messageDiv = this.createMessageElement('system', 'ℹ️', content);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addErrorMessage(content) {
        const messageDiv = this.createMessageElement('error', '⚠️', content);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        this.messageInput.disabled = false;
    }

    createMessageElement(type, icon, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = icon;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());

        contentDiv.appendChild(bubbleDiv);
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        return messageDiv;
    }

    showTyping(message = 'Processing...') {
        this.typingIndicator.classList.remove('hidden');
        this.scrollToBottom();
    }

    hideTyping() {
        this.typingIndicator.classList.add('hidden');
    }

    updateStats(stats) {
        this.statIterations.textContent = stats.iteration || 0;
        this.statTokens.textContent = stats.tokens || 0;
        this.statTools.textContent = stats.tools_used || 0;
    }

    showConnectionStatus(message, status) {
        this.connectionStatus.classList.remove('hidden', 'connected', 'error');
        if (status) {
            this.connectionStatus.classList.add(status);
        }
        this.connectionStatus.querySelector('.status-text').textContent = message;
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 100);
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.radiraChat = new RadiraChat();
});
