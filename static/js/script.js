// DOM Elements
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const memoryInsights = document.getElementById('memory-insights');
const toggleInsightsButton = document.getElementById('toggle-insights');
const semanticContent = document.getElementById('semantic-content');
const temporalContent = document.getElementById('temporal-content');

// State variables
let sessionId = null;
let isWaitingForResponse = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Generate a random session ID
    sessionId = generateSessionId();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load all conversation history when page loads
    loadChatHistory();
    
    // Focus the input field on load
    chatInput.focus();
});

// Set up event listeners
function setupEventListeners() {
    // Submit form on Enter (but allow Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitChatForm();
        }
    });
    
    // Form submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitChatForm();
    });
    
    // Toggle memory insights
    toggleInsightsButton.addEventListener('click', toggleMemoryInsights);
}

// Load all conversation history
async function loadChatHistory() {
    try {
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message system';
        loadingDiv.innerHTML = '<div class="message-content"><p>Loading conversation history...</p></div>';
        chatMessages.appendChild(loadingDiv);

        const response = await fetch('/api/chat/history');
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();
        
        // Clear loading message and welcome message
        chatMessages.innerHTML = '';

        // Check if there are messages to display
        if (data.messages && data.messages.length > 0) {
            // Add all messages to the chat
            data.messages.forEach(message => {
                addMessageToChat(message.role, message.content);
            });
        } else {
            // If no messages, show the welcome message
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message system';
            welcomeDiv.innerHTML = '<div class="message-content"><p>Hello! I\'m your AI assistant with hybrid memory. I can remember our conversations over time and learn from our interactions. How can I help you today?</p></div>';
            chatMessages.appendChild(welcomeDiv);
        }
        
        // Scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Error loading chat history:', error);
        
        // Show error message
        chatMessages.innerHTML = '<div class="message system"><div class="message-content"><p>Error loading chat history. Please refresh the page to try again.</p></div></div>';
    }
}

// Submit the chat form
function submitChatForm() {
    const prompt = chatInput.value.trim();
    
    if (prompt && !isWaitingForResponse) {
        // Add user message to chat
        addMessageToChat('user', prompt);
        
        // Clear input field
        chatInput.value = '';
        
        // Show loading indicator
        showLoadingIndicator();
        
        // Send to API
        sendChatRequest(prompt);
    }
}

// Send chat request to the API
async function sendChatRequest(prompt) {
    isWaitingForResponse = true;
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoadingIndicator();
        
        // Display the assistant's response
        addMessageToChat('assistant', data.response_text);
        
        // Update memory insights if available
        updateMemoryInsights(data.temporal_context, data.semantic_context);
        
    } catch (error) {
        console.error('Error sending chat request:', error);
        
        // Remove loading indicator
        removeLoadingIndicator();
        
        // Show error message
        addMessageToChat('system', 'Sorry, there was an error processing your request. Please try again.');
    } finally {
        isWaitingForResponse = false;
    }
}

// Add a message to the chat display
function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Process content for markdown-like formatting (very simple version)
    const formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
        .replace(/`(.*?)`/g, '<code>$1</code>')            // Code
        .replace(/\n/g, '<br>');                          // Line breaks
    
    contentDiv.innerHTML = `<p>${formattedContent}</p>`;
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show loading indicator
function showLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.id = 'loading-indicator';
    
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove loading indicator
function removeLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Update memory insights display
function updateMemoryInsights(temporalContext, semanticContext) {
    // Only show the memory insights section if we have insights
    if ((temporalContext && temporalContext.length > 0) || 
        (semanticContext && semanticContext.length > 0)) {
        
        memoryInsights.classList.remove('hidden');
        
        // Update semantic memory display
        if (semanticContext && semanticContext.length > 0) {
            semanticContent.innerHTML = semanticContext.map(item => `
                <div class="memory-item">
                    <div>${item.text}</div>
                    ${item.metadata && item.metadata.timestamp ? 
                        `<div class="memory-item-time">Relevance: ${(1 - (item.distance || 0)).toFixed(2)}</div>` : ''}
                </div>
            `).join('');
        } else {
            semanticContent.innerHTML = '<p>No semantic memory context used.</p>';
        }
        
        // Update temporal memory display
        if (temporalContext && temporalContext.length > 0) {
            temporalContent.innerHTML = temporalContext.map(item => `
                <div class="memory-item">
                    <div>${truncateText(item.content, 100)}</div>
                    ${item.datetime ? 
                        `<div class="memory-item-time">From: ${formatDate(item.datetime)}</div>` : ''}
                </div>
            `).join('');
        } else {
            temporalContent.innerHTML = '<p>No temporal memory context used.</p>';
        }
    }
}

// Toggle memory insights visibility
function toggleMemoryInsights() {
    const insightsContent = document.querySelector('.insights-content');
    const isHidden = insightsContent.style.display === 'none';
    
    insightsContent.style.display = isHidden ? 'flex' : 'none';
    toggleInsightsButton.textContent = isHidden ? 'Hide Memory Insights' : 'Show Memory Insights';
}

// Helper function to format date
function formatDate(isoDate) {
    try {
        const date = new Date(isoDate);
        return date.toLocaleString();
    } catch (e) {
        return isoDate;
    }
}

// Helper function to truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Generate a random session ID
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}