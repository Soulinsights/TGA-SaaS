import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Filter, FileText, ExternalLink, AlertCircle } from 'lucide-react';

const SearchPage = ({ currentProject, onProjectChange }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    trade_filter: '',
    category_filter: '',
    jurisdiction_filter: '',
    building_type_filter: '',
    license_filter: ''
  });

  const trades = [
    'HLK/RLT', 'Sanitär', 'Elektro', 'Brandschutz', 'Aufzugstechnik', 
    'Sicherheitstechnik', 'Gebäudeautomation', 'Beleuchtung'
  ];

  const categories = [
    'Standard', 'Produktdaten', 'Technische Anleitung', 'Zulassung', 
    'Montagehinweise', 'Wartungsanleitung', 'Planungshilfe'
  ];

  const jurisdictions = [
    'Bundesweit', 'Bayern', 'Baden-Württemberg', 'Nordrhein-Westfalen',
    'Hessen', 'Niedersachsen', 'Berlin', 'Hamburg', 'EU-Richtlinie'
  ];

  const buildingTypes = [
    'Hochhaus', 'Gewerbebau', 'Wohnbau', 'Industriebau', 
    'Krankenhaus', 'Schule', 'Bürogebäude', 'Hotel'
  ];

  const licenseTypes = [
    { value: '', label: 'Alle Lizenzen' },
    { value: 'open', label: 'Frei verfügbar' },
    { value: 'DIN', label: 'DIN-Norm (lizenziert)' },
    { value: 'VDI', label: 'VDI-Richtlinie (lizenziert)' },
    { value: 'proprietary', label: 'Herstellereigen' }
  ];

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const searchParams = {
        query: searchQuery,
        ...filters,
        limit: 20,
        offset: 0
      };

      // Add project context if available
      if (currentProject) {
        searchParams.jurisdiction_filter = currentProject.jurisdiction;
        searchParams.building_type_filter = currentProject.building_type;
      }

      const response = await axios.post('/api/search', searchParams);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterKey, value) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
  };

  const getLicenseIndicator = (licenseType) => {
    const indicators = {
      'open': { class: 'open', label: 'Frei' },
      'DIN': { class: 'din', label: 'DIN' },
      'VDI': { class: 'vdi', label: 'VDI' },
      'proprietary': { class: 'proprietary', label: 'Proprietär' }
    };
    return indicators[licenseType] || { class: 'open', label: 'Unbekannt' };
  };

  const truncateContent = (content, maxLength = 300) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">TGA-Dokumenten Suche</h1>
        <p className="page-subtitle">
          Durchsuchen Sie Normen, Herstellerdaten und technische Richtlinien
        </p>
      </div>

      {/* Project Context Banner */}
      {currentProject && (
        <div className="project-banner mb-6">
          <div className="project-banner-content">
            <h3>Aktives Projekt: {currentProject.name}</h3>
            <p>Filter automatisch angewendet: {currentProject.jurisdiction}, {currentProject.building_type}</p>
          </div>
        </div>
      )}

      {/* Search Form */}
      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              className="search-input"
              placeholder="Suchbegriff eingeben (z.B. 'Brandschutzklappen', 'DIN 4102', 'Trox AHU')"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <div className="loading-spinner" />
              ) : (
                <Search size={16} />
              )}
              Suchen
            </button>
          </div>
        </form>

        {/* Filters */}
        <div className="search-filters">
          <select
            className="filter-select"
            value={filters.trade_filter}
            onChange={(e) => handleFilterChange('trade_filter', e.target.value)}
          >
            <option value="">Alle Gewerke</option>
            {trades.map(trade => (
              <option key={trade} value={trade}>{trade}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.category_filter}
            onChange={(e) => handleFilterChange('category_filter', e.target.value)}
          >
            <option value="">Alle Kategorien</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.jurisdiction_filter}
            onChange={(e) => handleFilterChange('jurisdiction_filter', e.target.value)}
          >
            <option value="">Alle Jurisdiktionen</option>
            {jurisdictions.map(jurisdiction => (
              <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.building_type_filter}
            onChange={(e) => handleFilterChange('building_type_filter', e.target.value)}
          >
            <option value="">Alle Gebäudetypen</option>
            {buildingTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.license_filter}
            onChange={(e) => handleFilterChange('license_filter', e.target.value)}
          >
            {licenseTypes.map(license => (
              <option key={license.value} value={license.value}>{license.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Search Results */}
      <div className="search-results">
        {loading && (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p>Suche läuft...</p>
          </div>
        )}

        {!loading && searchResults.length > 0 && (
          <div className="results-header mb-4">
            <p className="results-count">{searchResults.length} Ergebnisse gefunden</p>
          </div>
        )}

        {!loading && searchQuery && searchResults.length === 0 && (
          <div className="no-results">
            <AlertCircle size={48} className="no-results-icon" />
            <h3>Keine Ergebnisse gefunden</h3>
            <p>Versuchen Sie andere Suchbegriffe oder weniger spezifische Filter.</p>
          </div>
        )}

        {searchResults.map((result) => {
          const licenseInfo = getLicenseIndicator(result.license_type);
          return (
            <div key={result.id} className="result-card">
              <div className="result-header">
                <div>
                  <h3 className="result-title">{result.document_title}</h3>
                  <h4 className="result-section-title">{result.title}</h4>
                  <div className="result-meta">
                    <span className="result-badge">{result.trade}</span>
                    <span className="result-badge">{result.category}</span>
                    <span className={`license-indicator ${licenseInfo.class}`}>
                      {licenseInfo.label}
                    </span>
                    <span className="result-badge">Seite {result.page_number}</span>
                  </div>
                </div>
                <div className="result-score">
                  Relevanz: {(result.relevance_score * 100).toFixed(0)}%
                </div>
              </div>

              <div className="result-content">
                {result.license_type === 'DIN' || result.license_type === 'VDI' ? (
                  <div className="license-notice">
                    <AlertCircle size={16} />
                    <span>Lizenzierter Inhalt - nur Metadaten verfügbar.</span>
                    <a href="#" className="license-link">
                      <ExternalLink size={14} />
                      Zur offiziellen Quelle
                    </a>
                  </div>
                ) : (
                  <p>{truncateContent(result.content)}</p>
                )}
              </div>

              <div className="result-footer">
                <span className="result-anchor">Anker: {result.anchor_id}</span>
                <button className="btn btn-secondary btn-sm">
                  <FileText size={14} />
                  Dokument öffnen
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SearchPage;