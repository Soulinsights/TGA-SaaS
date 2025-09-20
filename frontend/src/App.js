import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Components
import Navigation from './components/Navigation';
import HomePage from './components/HomePage';
import SearchPage from './components/SearchPage';
import DocumentViewer from './components/DocumentViewer';
import QAChat from './components/QAChat';
import UploadConsole from './components/UploadConsole';
import ProjectProfiles from './components/ProjectProfiles';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentProject, setCurrentProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Initialize axios defaults
  useEffect(() => {
    axios.defaults.baseURL = API_BASE_URL;
    axios.defaults.headers.common['Content-Type'] = 'application/json';
  }, []);

  // Fetch documents
  const fetchDocuments = async (filters = {}) => {
    try {
      setLoading(true);
      const response = await axios.get('/api/documents', { params: filters });
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <Router>
      <div className="App">
        <Navigation currentProject={currentProject} />
        
        <main className="main-content">
          <Routes>
            <Route 
              path="/" 
              element={<HomePage documents={documents} loading={loading} />} 
            />
            <Route 
              path="/search" 
              element={
                <SearchPage 
                  currentProject={currentProject}
                  onProjectChange={setCurrentProject}
                />
              } 
            />
            <Route 
              path="/document/:id" 
              element={<DocumentViewer />} 
            />
            <Route 
              path="/qa" 
              element={
                <QAChat 
                  currentProject={currentProject}
                />
              } 
            />
            <Route 
              path="/upload" 
              element={
                <UploadConsole 
                  onUploadSuccess={() => fetchDocuments()}
                />
              } 
            />
            <Route 
              path="/projects" 
              element={
                <ProjectProfiles 
                  currentProject={currentProject}
                  onProjectChange={setCurrentProject}
                />
              } 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;