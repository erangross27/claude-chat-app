import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

const CLAUDE_MODELS = {
  "claude-sonnet-4-20250514": "Claude 4 Sonnet",
  "claude-opus-4-20250514": "Claude 4 Opus"
};

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>The application encountered an error. Please refresh the page.</p>
          <button onClick={() => window.location.reload()}>Refresh Page</button>
          <details style={{ marginTop: '1rem' }}>
            <summary>Error Details</summary>
            <pre>{this.state.error?.toString()}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

// Copy button component for code blocks
const CodeBlock = ({ className, children, ...props }) => {
  const [isCopied, setIsCopied] = useState(false);
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = children;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  return (
    <div className="code-block-container">
      <button 
        className={`copy-button ${isCopied ? 'copied' : ''}`}
        onClick={copyToClipboard}
        title="Copy code"
      >
        {isCopied ? '✓ Copied!' : '📋 Copy'}
      </button>
      <pre className={className} {...props}>
        <code>{children}</code>
      </pre>
    </div>
  );
};

// Sidebar Component
const Sidebar = ({ 
  conversations = [], // Default to empty array
  currentConversationId, 
  onConversationSelect, 
  onNewConversation, 
  onDeleteConversation,
  isLoading 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Ensure conversations is always an array
  const safeConversations = Array.isArray(conversations) ? conversations : [];
  
  // Debounced search function
  const searchConversations = async (query) => {
    if (!query || query.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await axios.get(`/conversations/search?q=${encodeURIComponent(query.trim())}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };
  
  // Debounce search calls
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchConversations(searchTerm);
    }, 300); // 300ms debounce
    
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);
  
  // Use search results if searching, otherwise show all conversations
  const displayConversations = searchTerm.trim().length >= 2 ? searchResults : safeConversations;
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button 
          className="new-chat-button" 
          onClick={onNewConversation}
          disabled={isLoading}
        >
          + New Chat
        </button>
        <div className="search-container">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          {searchTerm && (
            <button 
              className="clear-search"
              onClick={() => setSearchTerm('')}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      <div className="conversations-list">
        {isSearching ? (
          <div className="search-loading">
            🔄 Searching...
          </div>
        ) : displayConversations.length === 0 && searchTerm.trim().length >= 2 ? (
          <div className="no-results">
            No conversations found matching "{searchTerm}"
          </div>
        ) : (
          displayConversations.map(conversation => (
            <div 
              key={conversation.id}
              className={`conversation-item ${currentConversationId === conversation.id ? 'active' : ''}`}
              onClick={() => onConversationSelect(conversation.id)}
            >
              <div className="conversation-title">
                {conversation.title}
              </div>
              <div className="conversation-date">
                {new Date(conversation.updated_at).toLocaleDateString()}
              </div>
              <button 
                className="delete-conversation"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation(conversation.id);
                }}
                title="Delete conversation"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

function App() {
  // Global error handling
  useEffect(() => {
    const handleError = (error) => {
      console.error('Global error caught:', error);
      // Prevent default behavior that might cause page reload
      if (error.preventDefault) {
        error.preventDefault();
      }
      // Don't let the error bubble up and crash the app
      return true;
    };

    const handleUnhandledRejection = (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      // Prevent default behavior that might cause page reload
      if (event.preventDefault) {
        event.preventDefault();
      }
      // Don't let the error bubble up and crash the app
      return true;
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  // Detect RTL language
  const [isRTL, setIsRTL] = useState(false);
  
  useEffect(() => {
    // Check if the document or html element has RTL direction
    const htmlDir = document.documentElement.dir;
    const bodyDir = document.body.dir;
    const computedDir = window.getComputedStyle(document.documentElement).direction;
    
    // Check browser language for RTL languages
    const rtlLanguages = ['ar', 'he', 'fa', 'ur', 'yi', 'ji', 'iw', 'ku', 'ps', 'sd'];
    const browserLang = navigator.language.substring(0, 2);
    const fullLang = navigator.language.toLowerCase();
    
    console.log('Browser language:', navigator.language, 'Short:', browserLang);
    console.log('HTML dir:', htmlDir, 'Body dir:', bodyDir, 'Computed dir:', computedDir);
    
    const isRightToLeft = 
      htmlDir === 'rtl' || 
      bodyDir === 'rtl' || 
      computedDir === 'rtl' || 
      rtlLanguages.includes(browserLang) ||
      fullLang.includes('he') || // Hebrew detection
      fullLang.includes('ar'); // Arabic detection
    
    console.log('Final RTL decision:', isRightToLeft);
    setIsRTL(isRightToLeft);
    
    // Set document direction if RTL detected
    if (isRightToLeft) {
      document.documentElement.dir = 'rtl';
      document.body.dir = 'rtl';
      document.documentElement.classList.add('rtl');
      document.body.classList.add('rtl');
    }
  }, []);

  const [conversations, setConversations] = useState([]); // Initialize as empty array
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-20250514');
  const [temperature, setTemperature] = useState(0.1);
  const [useStreaming, setUseStreaming] = useState(false); // TEMPORARILY DISABLED
  const [enableThinking, setEnableThinking] = useState(false);
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [ws, setWs] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on component mount
  useEffect(() => {
    if (!initialized) {
      console.log('Initializing app...');
      loadConversations();
      setInitialized(true);
    }
  }, [initialized]);

  // Auto-select first conversation when conversations are loaded
  useEffect(() => {
    if (!currentConversationId && Array.isArray(conversations) && conversations.length > 0) {
      console.log('Auto-selecting first conversation:', conversations[0].id);
      setCurrentConversationId(conversations[0].id);
      loadConversation(conversations[0].id);
    }
  }, [conversations]); // Removed currentConversationId from dependencies

  // WebSocket setup
  useEffect(() => {
    // If streaming is disabled, close any existing WebSocket and don't create new ones
    if (!useStreaming) {
      if (ws) {
        console.log('Streaming disabled, closing WebSocket...');
        ws.close(1000, 'Streaming disabled');
        setWs(null);
      }
      return;
    }

    // Only create WebSocket if streaming is enabled and no WebSocket exists
    if (useStreaming && !ws) {
      console.log('Setting up WebSocket connection...');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected successfully');
        setWs(websocket);
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'chunk') {
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              
              if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
                lastMessage.content = data.full_message;
              } else {
                newMessages.push({
                  role: 'assistant',
                  content: data.full_message,
                  isStreaming: true,
                  timestamp: new Date().toISOString()
                });
              }
              
              return newMessages;
            });
          } else if (data.type === 'complete') {
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.isStreaming = false;
                lastMessage.content = data.message;
              }
              
              // Check if we should generate a title after conversation has 2+ messages
              if (newMessages.length >= 2 && currentConversationId) {
                // Generate title after assistant responds (async, don't wait)
                generateConversationTitle(currentConversationId);
              }
              
              // Refresh conversations list to update timestamps
              loadConversations();
              
              return newMessages;
            });
            setIsLoading(false);
          } else if (data.type === 'error') {
            console.error('WebSocket error:', data.message);
            setIsLoading(false);
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `Error: ${data.message}`,
              timestamp: new Date().toISOString(),
              isError: true
            }]);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      websocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        // Only set ws to null if it wasn't a manual close (code 1000)
        if (event.code !== 1000) {
          console.log('WebSocket closed unexpectedly, will attempt to reconnect...');
        }
        setWs(null);
      };

      // Store websocket reference to prevent cleanup during render cycles
      const currentWebSocket = websocket;
      
      return () => {
        console.log('Cleaning up WebSocket...');
        // Only close if the websocket is the current one and in a closeable state
        if (currentWebSocket && currentWebSocket.readyState === WebSocket.OPEN) {
          currentWebSocket.close(1000, 'Component cleanup');
        } else if (currentWebSocket && currentWebSocket.readyState === WebSocket.CONNECTING) {
          // If still connecting, wait a bit then close
          currentWebSocket.addEventListener('open', () => {
            currentWebSocket.close(1000, 'Component cleanup');
          });
        }
      };
    }

    // Cleanup function that runs on every dependency change
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('Effect cleanup: closing WebSocket...');
        ws.close(1000, 'Effect cleanup');
      }
    };
  }, [useStreaming, ws]);

  // API Functions
  const loadConversations = async () => {
    try {
      const response = await axios.get('/conversations');
      // Ensure we always set an array
      const data = response.data;
      if (Array.isArray(data)) {
        setConversations(data);
      } else {
        console.error('API returned non-array data:', data);
        setConversations([]);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      // Ensure conversations remains an array even on error
      setConversations([]);
    }
  };

  const loadConversation = async (conversationId) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    
    try {
      console.log('Loading conversation:', conversationId);
      const response = await axios.get(`/conversations/${conversationId}`);
      console.log('Conversation data:', response.data);
      
      if (response.data && Array.isArray(response.data.messages)) {
        const loadedMessages = response.data.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.created_at,
          model: msg.model
        }));
        console.log('Loaded messages:', loadedMessages);
        setMessages(loadedMessages);
      } else {
        console.log('No messages found in conversation or invalid data structure');
        setMessages([]);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      if (error.response) {
        console.error('Response error:', error.response.status, error.response.data);
        // If conversation not found, clear messages but keep it selected
        if (error.response.status === 404) {
          setMessages([]);
        }
      }
      // Don't clear messages on network errors to avoid losing the conversation view
    }
  };

  const createNewConversation = async () => {
    try {
      const title = `Chat ${new Date().toLocaleString()}`;
      const response = await axios.post('/conversations', { title });
      const newConversation = response.data;
      
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversationId(newConversation.id);
      setMessages([]);
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const deleteConversation = async (conversationId) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await axios.delete(`/conversations/${conversationId}`);
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      // If we deleted the current conversation, select another one or create new
      if (currentConversationId === conversationId) {
        const remainingConversations = conversations.filter(conv => conv.id !== conversationId);
        if (remainingConversations.length > 0) {
          setCurrentConversationId(remainingConversations[0].id);
          loadConversation(remainingConversations[0].id);
        } else {
          setCurrentConversationId(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const selectConversation = async (conversationId) => {
    console.log('Selecting conversation:', conversationId);
    setCurrentConversationId(conversationId);
    await loadConversation(conversationId);
  };

  const generateConversationTitle = async (conversationId) => {
    if (!conversationId) {
      return "New Chat";
    }
    
    try {
      const response = await fetch(`/conversations/${conversationId}/generate-title`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Update the conversation in the list
        setConversations(prevConversations =>
          prevConversations.map(conv =>
            conv.id === conversationId
              ? { ...conv, title: data.title }
              : conv
          )
        );
        return data.title;
      }
    } catch (error) {
      console.error('Error generating conversation title:', error);
      // Fallback to simple title generation
      return "New Chat";
    }
  };

  const updateConversationTitle = async (conversationId, title) => {
    try {
      await axios.put(`/conversations/${conversationId}/title`, { title });
      setConversations(prev => prev.map(conv => 
        conv.id === conversationId ? { ...conv, title } : conv
      ));
    } catch (error) {
      console.error('Error updating conversation title:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // Create new conversation if none exists
    let conversationId = currentConversationId;
    if (!conversationId) {
      try {
        const title = await generateConversationTitle(null) || "New Chat";
        const response = await axios.post('/conversations', { title });
        conversationId = response.data.id;
        setCurrentConversationId(conversationId);
        setConversations(prev => [response.data, ...prev]);
      } catch (error) {
        console.error('Error creating conversation:', error);
        return;
      }
    }

    const message = inputMessage;
    setInputMessage('');
    setIsLoading(true);
    
    // Add user message to chat
    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // Update conversation title if it's the first message or after 3 messages
    if (messages.length === 0) {
      // For first message, use placeholder title initially
      updateConversationTitle(conversationId, "New Chat");
    } else if (messages.length === 2) {
      // After bot responds to first user message, generate a smart title
      generateConversationTitle(conversationId);
    }

    if (useStreaming && ws) {
      // Send via WebSocket
      const wsMessage = {
        message,
        conversation_history: messages,
        model: selectedModel,
        temperature,
        enable_thinking: enableThinking,
        enable_web_search: enableWebSearch,
        conversation_id: conversationId
      };
      
      ws.send(JSON.stringify(wsMessage));
    } else {
      // Fallback to REST API
      try {
        const response = await axios.post('/chat', {
          message,
          conversation_history: messages,
          model: selectedModel,
          temperature,
          enable_thinking: enableThinking,
          enable_web_search: enableWebSearch,
          conversation_id: conversationId
        });

        const assistantMessage = {
          role: 'assistant',
          content: response.data.message,
          timestamp: response.data.timestamp,
          model: selectedModel
        };
        setMessages(prev => {
          const newMessages = [...prev, assistantMessage];
          
          // Check if we should generate a title after conversation has 2+ messages
          if (newMessages.length >= 2 && conversationId) {
            // Generate title after assistant responds (async, don't wait)
            generateConversationTitle(conversationId);
          }
          
          // Refresh conversations list to update timestamps
          loadConversations();
          
          return newMessages;
        });
        setIsLoading(false);
      } catch (error) {
        console.error('Error sending message:', error);
        setIsLoading(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${error.response?.data?.detail || 'Failed to send message'}`,
          timestamp: new Date().toISOString(),
          isError: true
        }]);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`app ${isRTL ? 'rtl' : 'ltr'}`}>
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onConversationSelect={selectConversation}
        onNewConversation={createNewConversation}
        onDeleteConversation={deleteConversation}
        isLoading={isLoading}
      />
      
      <div className="main-content">
        <header className="header">
          <h1>Claude Chat</h1>
          <div className="header-controls">
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-select"
              disabled={isLoading}
            >
              {Object.entries(CLAUDE_MODELS).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>
            
            <label className="temperature-control">
              Temperature: {temperature}
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="temperature-slider"
                disabled={isLoading}
              />
            </label>
            
            <label className="thinking-toggle">
              <input
                type="checkbox"
                checked={enableThinking}
                onChange={(e) => setEnableThinking(e.target.checked)}
                disabled={isLoading}
              />
              Extended Thinking
            </label>
            
            <label className="web-search-toggle">
              <input
                type="checkbox"
                checked={enableWebSearch}
                onChange={(e) => setEnableWebSearch(e.target.checked)}
                disabled={isLoading}
              />
              🌐 Web Search
            </label>
          </div>
        </header>

        <div className="chat-container">
          <div className="messages">
            {messages.map((message, index) => {
              // RTL-aware message alignment
              let messageClass;
              if (isRTL) {
                // In RTL: user messages on right, assistant on left
                messageClass = message.role === 'user' ? 'user-rtl' : 'assistant-rtl';
              } else {
                // In LTR: user on right, assistant on left (standard)
                messageClass = message.role === 'user' ? 'user' : 'assistant';
              }
              
              // Debug logging
              if (index === messages.length - 1) { // Only log the last message to avoid spam
                console.log('Message rendering debug:', {
                  isRTL,
                  role: message.role,
                  messageClass,
                  finalClassName: `message ${messageClass} ${message.isError ? 'error' : ''}`
                });
              }
                
              return (
                <div key={index} className={`message ${messageClass} ${message.isError ? 'error' : ''}`}>
                  <div className="message-role">
                    {message.role === 'user' ? '👤 You' : '🤖 Claude'}
                    {message.model && ` (${CLAUDE_MODELS[message.model] || message.model})`}
                    {message.isStreaming && ' ⏳'}
                  </div>
                  <div className="message-content">
                    <ReactMarkdown
                      components={{
                        code: ({ node, inline, className, children, ...props }) => {
                          if (inline) {
                            return <code className={className} {...props}>{children}</code>;
                          }
                          return <CodeBlock className={className} {...props}>{children}</CodeBlock>;
                        }
                      }}
                      style={isRTL ? { direction: 'rtl', textAlign: 'right' } : {}}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                  <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              );
            })}
            {isLoading && !messages.some(m => m.isStreaming) && (
              <div className="message assistant">
                <div className="message-role">🤖 Claude {selectedModel && `(${CLAUDE_MODELS[selectedModel]})`}</div>
                <div className="message-content typing">Thinking...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              className="message-input"
              disabled={isLoading}
              rows={3}
              style={isRTL ? { direction: 'rtl', textAlign: 'right' } : {}}
            />
            <button 
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="send-button"
            >
              {isLoading ? '⏳ Sending...' : '📤 Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Wrap App with ErrorBoundary
function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}

export default AppWithErrorBoundary;
