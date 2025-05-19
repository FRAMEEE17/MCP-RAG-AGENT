(function() {
    const API_BASE = '/api/agent';
    
    class MCPIntegration {
        constructor() {
            this.sessionId = this._generateSessionId();
            this.connected = false;
            this.eventSource = null;
            this.messageCallbacks = [];
        }
        
        // Generate a random session ID
        _generateSessionId() {
            return 'session_' + Math.random().toString(36).substring(2, 15);
        }
        
        // Connect to the agent API
        async connect() {
            if (this.connected) return;
            
            try {
                // Test API connection with a health check
                const response = await fetch(`${API_BASE.replace('/chat', '')}/health`);
                if (!response.ok) {
                    console.error('Failed to connect to MCP Agent API');
                    return false;
                }
                
                this.connected = true;
                return true;
            } catch (error) {
                console.error('Error connecting to MCP Agent API:', error);
                return false;
            }
        }
        
        // Send a message to the agent
        async sendMessage(message) {
            if (!this.connected) {
                const connected = await this.connect();
                if (!connected) return;
            }
            
            try {
                // Close any existing event source
                if (this.eventSource) {
                    this.eventSource.close();
                }
                
                // Set up the event source for streaming
                const response = await fetch(`${API_BASE}/chat/${this.sessionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                let receivedText = '';
                let toolCalls = [];
                
                const processStream = async () => {
                    try {
                        while (true) {
                            const { done, value } = await reader.read();
                            
                            if (done) break;
                            
                            const text = decoder.decode(value, { stream: true });
                            receivedText += text;
                            
                            // Process each line in the received text
                            const lines = receivedText.split('\n');
                            receivedText = lines.pop() || '';  // Keep any incomplete line
                            
                            for (const line of lines) {
                                if (!line.trim()) continue;
                                
                                try {
                                    const event = JSON.parse(line);
                                    
                                    // Handle different event types
                                    switch (event.type) {
                                        case 'content':
                                            // Incremental content update
                                            this._notifyCallbacks({
                                                type: 'update',
                                                content: event.content
                                            });
                                            break;
                                            
                                        case 'tool_call':
                                            // Tool call notification
                                            toolCalls.push({
                                                tool: event.tool,
                                                arguments: event.arguments
                                            });
                                            this._notifyCallbacks({
                                                type: 'tool_call',
                                                tool: event.tool,
                                                arguments: event.arguments
                                            });
                                            break;
                                            
                                        case 'tool_result':
                                            // Tool result notification
                                            this._notifyCallbacks({
                                                type: 'tool_result',
                                                result: event.result
                                            });
                                            break;
                                            
                                        case 'final':
                                            // Final response
                                            this._notifyCallbacks({
                                                type: 'final',
                                                content: event.content,
                                                toolCalls: toolCalls
                                            });
                                            break;
                                            
                                        case 'error':
                                            // Error event
                                            this._notifyCallbacks({
                                                type: 'error',
                                                error: event.content
                                            });
                                            break;
                                    }
                                } catch (parseError) {
                                    console.error('Error parsing event:', parseError, line);
                                }
                            }
                        }
                    } catch (streamError) {
                        console.error('Error processing stream:', streamError);
                        this._notifyCallbacks({
                            type: 'error',
                            error: `Stream error: ${streamError.message}`
                        });
                    }
                };
                
                // Start processing the stream
                processStream();
                
                return true;
            } catch (error) {
                console.error('Error sending message:', error);
                this._notifyCallbacks({
                    type: 'error',
                    error: `Failed to send message: ${error.message}`
                });
                return false;
            }
        }
        
        // Register a callback for message events
        onMessage(callback) {
            if (typeof callback === 'function') {
                this.messageCallbacks.push(callback);
            }
        }
        
        // Notify all registered callbacks
        _notifyCallbacks(data) {
            for (const callback of this.messageCallbacks) {
                callback(data);
            }
        }
        
        // End the session
        async endSession() {
            if (!this.connected) return;
            
            try {
                // Close any existing event source
                if (this.eventSource) {
                    this.eventSource.close();
                    this.eventSource = null;
                }
                
                // Send request to end the session
                await fetch(`${API_BASE}/chat/${this.sessionId}`, {
                    method: 'DELETE'
                });
                
                // Reset session
                this.sessionId = this._generateSessionId();
                this.connected = false;
            } catch (error) {
                console.error('Error ending session:', error);
            }
        }
    }
    
    // Initialize and expose the integration to the window object
    window.mcpIntegration = new MCPIntegration();
    
    // Integrate with OpenWebUI if available
    if (window.OPENWEBUI_CONFIG) {
        // Add custom provider for MCP integration
        window.OPENWEBUI_PROVIDERS = window.OPENWEBUI_PROVIDERS || {};
        window.OPENWEBUI_PROVIDERS.mcp = {
            name: 'MCP Agent',
            
            // Initialize the provider
            init: async () => {
                return await window.mcpIntegration.connect();
            },
            
            // Send a message
            sendMessage: async (model, message, options) => {
                return await window.mcpIntegration.sendMessage(message);
            },
            
            // Clean up resources
            cleanup: async () => {
                return await window.mcpIntegration.endSession();
            }
        };
        
        console.log('MCP integration loaded successfully');
    } else {
        console.warn('OpenWebUI config not found');
    }
})();