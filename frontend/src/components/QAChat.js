import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Bot, ExternalLink, AlertCircle } from 'lucide-react';

const QAChat = ({ currentProject }) => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      type: 'bot',
      content: 'Hallo! Ich bin Ihr TGA-Experte. Stellen Sie mir Fragen zu Normen, Herstellerdaten oder technischen Richtlinien.',
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    trade_filter: '',
    jurisdiction_filter: '',
    building_type_filter: ''
  });
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const trades = [
    'HLK/RLT', 'Sanitär', 'Elektro', 'Brandschutz', 'Aufzugstechnik', 
    'Sicherheitstechnik', 'Gebäudeautomation', 'Beleuchtung'
  ];

  const jurisdictions = [
    'Bundesweit', 'Bayern', 'Baden-Württemberg', 'Nordrhein-Westfalen',
    'Hessen', 'Niedersachsen', 'Berlin', 'Hamburg'
  ];

  const buildingTypes = [
    'Hochhaus', 'Gewerbebau', 'Wohnbau', 'Industriebau', 
    'Krankenhaus', 'Schule', 'Bürogebäude', 'Hotel'
  ];

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Set project context filters when project changes
  useEffect(() => {
    if (currentProject) {
      setFilters(prev => ({
        ...prev,
        jurisdiction_filter: currentProject.jurisdiction,
        building_type_filter: currentProject.building_type
      }));
    }
  }, [currentProject]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',  
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const qaQuery = {
        question: inputMessage,
        project_context: currentProject || null,
        ...filters
      };

      const response = await axios.post('/api/qa', qaQuery);
      
      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.data.answer,
        citations: response.data.citations,
        confidence: response.data.confidence,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('QA error:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Entschuldigung, ich konnte Ihre Frage nicht beantworten. Bitte versuchen Sie es erneut.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const exampleQuestions = [
    'Welche Brandschutzklappen sind für Hochhäuser in Bayern vorgeschrieben?',
    'Was sagt DIN 4102 zur Brandklassifizierung von Bauteilen?',
    'Welche TROX Luftbehandlungsgeräte eignen sich für Bürogebäude?',
    'Wie sind Pumpen nach den aktuellen Energierichtlinien zu dimensionieren?'
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">TGA Q&A Chat</h1>
        <p className="page-subtitle">
          Stellen Sie Fragen zu Normen und erhalten Sie Antworten mit Quellenangaben
        </p>
      </div>

      {/* Project Context Banner */}
      {currentProject && (
        <div className="project-banner mb-4">
          <div className="project-banner-content">
            <h3>Projektkontext: {currentProject.name}</h3>
            <p>Antworten werden automatisch nach {currentProject.jurisdiction}, {currentProject.building_type} gefiltert</p>
          </div>
        </div>
      )}

      {/* Chat Filters */}
      <div className="chat-filters mb-4">
        <div className="filter-row">
          <select
            className="filter-select"
            value={filters.trade_filter}
            onChange={(e) => setFilters(prev => ({ ...prev, trade_filter: e.target.value }))}
          >
            <option value="">Alle Gewerke</option>
            {trades.map(trade => (
              <option key={trade} value={trade}>{trade}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.jurisdiction_filter}
            onChange={(e) => setFilters(prev => ({ ...prev, jurisdiction_filter: e.target.value }))}
          >
            <option value="">Alle Jurisdiktionen</option>
            {jurisdictions.map(jurisdiction => (
              <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.building_type_filter}
            onChange={(e) => setFilters(prev => ({ ...prev, building_type_filter: e.target.value }))}
          >
            <option value="">Alle Gebäudetypen</option>
            {buildingTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Example Questions */}
      {messages.length <= 1 && (
        <div className="example-questions mb-6">
          <h3 className="mb-3">Beispielfragen:</h3>
          <div className="example-grid">
            {exampleQuestions.map((question, index) => (
              <button
                key={index}
                className="example-question"
                onClick={() => setInputMessage(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Container */}
      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`chat-message ${message.type}`}>
              <div className={`chat-avatar ${message.type}`}>
                {message.type === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="chat-bubble-container">
                <div className={`chat-bubble ${message.type} ${message.error ? 'error' : ''}`}>
                  <div className="message-content">
                    {message.content}
                  </div>
                  {message.confidence && (
                    <div className="confidence-indicator">
                      Vertrauen: {(message.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
                
                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                  <div className="citations">
                    <div className="citation-title">
                      Quellen ({message.citations.length}):
                    </div>
                    <div className="citation-list">
                      {message.citations.map((citation, index) => (
                        <div key={index} className="citation-item">
                          <div className="citation-header">
                            <strong>{citation.document_title}</strong>
                            <span className="citation-relevance">
                              {(citation.relevance_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="citation-details">
                            {citation.title} - Seite {citation.page_number}
                          </div>
                          <div className="citation-anchor">
                            <code>{citation.anchor_id}</code>
                            <button className="citation-link">
                              <ExternalLink size={12} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="message-timestamp">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="chat-message bot">
              <div className="chat-avatar bot">
                <Bot size={16} />
              </div>
              <div className="chat-bubble bot">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <form onSubmit={handleSendMessage} className="chat-input-container">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Stellen Sie Ihre TGA-Frage hier..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            rows={1}
          />
          <button 
            type="submit" 
            className="chat-send-btn"
            disabled={loading || !inputMessage.trim()}
          >
            {loading ? (
              <div className="loading-spinner" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default QAChat;