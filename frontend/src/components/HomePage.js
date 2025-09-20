import React from 'react';
import { Link } from 'react-router-dom';
import { Search, MessageCircle, Upload, Database, FileText, Building, Shield } from 'lucide-react';

const HomePage = ({ documents, loading }) => {
  const features = [
    {
      icon: Search,
      title: 'Hybrid-Suche',
      description: 'Volltext- und semantische Suche durch TGA-Dokumente mit intelligenten Filtern nach Gewerk, Bundesland und Gebäudetyp.',
      link: '/search'
    },
    {
      icon: MessageCircle,
      title: 'Q&A Chat',
      description: 'Stellen Sie Fragen zu TGA-Normen und erhalten Sie Antworten mit präzisen Quellenangaben durch RAG-Technologie.',
      link: '/qa'
    },
    {
      icon: Upload,
      title: 'Dokument-Upload',
      description: 'Laden Sie PDFs hoch - automatische OCR, Textextraktion, Kategorisierung und Embedding-Generierung.',
      link: '/upload'
    },
    {
      icon: Building,
      title: 'Projekt-Profile',
      description: 'Definieren Sie Projektkontext (Bundesland, Gebäudetyp) für maßgeschneiderte Suchergebnisse und Compliance.',
      link: '/projects'
    },
    {
      icon: Shield,
      title: 'Lizenz-Compliance',
      description: 'Automatische Erkennung lizenzierter DIN/VDI-Normen mit Metadaten-Anzeige und Deep-Links zu offiziellen Quellen.',
      link: '/search'
    },
    {
      icon: Database,
      title: 'Herstellerdaten',
      description: 'Umfassende Sammlung von TROX, Wolf, Wilo, Grundfos, Viega, Geberit, OBO, Hilti und Bosch Dokumenten.',
      link: '/search'
    }
  ];

  const stats = [
    { number: documents.length, label: 'Dokumente' },
    { number: '12', label: 'Gewerke' },
    { number: '16', label: 'Bundesländer' },
    { number: '8', label: 'Hersteller' }
  ];

  const recentCategories = [
    { name: 'Brandschutz', count: 24, icon: Shield },
    { name: 'HLK/RLT', count: 31, icon: Building },
    { name: 'Sanitär', count: 18, icon: FileText },
    { name: 'Elektro', count: 27, icon: Database }
  ];

  return (
    <div className="page-container">
      {/* Hero Section */}
      <div className="hero-section">
        <h1 className="hero-title">
          TGA Knowledge Platform
        </h1>
        <p className="hero-subtitle">
          Ihr zentraler Zugangspunkt zu technischen Gebäudeausrüstungs-Normen, 
          Herstellerdaten und Compliance-Informationen für Deutschland.
        </p>
        
        <div className="hero-stats">
          {stats.map((stat, index) => (
            <div key={index} className="stat-item">
              <span className="stat-number">{loading ? '...' : stat.number}</span>
              <span className="stat-label">{stat.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Features Grid */}
      <div className="features-grid">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <Link to={feature.link} key={index} className="feature-card">
              <div className="feature-icon">
                <Icon size={24} />
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </Link>
          );
        })}
      </div>

      {/* Recent Categories */}
      <div className="categories-section mt-8">
        <h2 className="page-title mb-6">Verfügbare Gewerke</h2>
        <div className="categories-grid">
          {recentCategories.map((category, index) => {
            const Icon = category.icon;
            return (
              <Link 
                to={`/search?trade=${encodeURIComponent(category.name)}`}
                key={index} 
                className="category-card"
              >
                <div className="category-icon">
                  <Icon size={20} />
                </div>
                <div className="category-info">
                  <h4 className="category-name">{category.name}</h4>
                  <span className="category-count">{category.count} Dokumente</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions mt-8">
        <h2 className="page-title mb-6">Schnellstart</h2>
        <div className="action-buttons">
          <Link to="/search" className="btn btn-primary">
            <Search size={16} />
            Dokumente durchsuchen
          </Link>
          <Link to="/qa" className="btn btn-secondary">
            <MessageCircle size={16} />
            Frage stellen
          </Link>
          <Link to="/upload" className="btn btn-outline">
            <Upload size={16} />
            Dokument hochladen
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;