import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { FileText, ExternalLink, AlertCircle, Download, Share } from 'lucide-react';

const DocumentViewer = () => {
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDocument();
  }, [id]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/documents/${id}`);
      setDocument(response.data);
      if (response.data.sections && response.data.sections.length > 0) {
        setActiveSection(response.data.sections[0].id);
      }
    } catch (error) {
      console.error('Error fetching document:', error);
      setError('Dokument konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const getLicenseIndicator = (licenseType) => {
    const indicators = {
      'open': { class: 'open', label: 'Frei verfügbar', icon: '🟢' },
      'DIN': { class: 'din', label: 'DIN-Norm (lizenziert)', icon: '🟡' },
      'VDI': { class: 'vdi', label: 'VDI-Richtlinie (lizenziert)', icon: '🟡' },
      'proprietary': { class: 'proprietary', label: 'Herstellereigen', icon: '🔒' }
    };
    return indicators[licenseType] || { class: 'open', label: 'Unbekannt', icon: '❓' };
  };

  const handleSectionClick = (sectionId) => {
    setActiveSection(sectionId);
    // Scroll to section in content area
    const element = document.getElementById(`section-${sectionId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const copyAnchorId = (anchorId) => {
    navigator.clipboard.writeText(anchorId);
    // Could add toast notification here
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Dokument wird geladen...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">
          <AlertCircle size={48} />
          <h2>Fehler</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="page-container">
        <div className="not-found-state">
          <FileText size={48} />
          <h2>Dokument nicht gefunden</h2>
          <p>Das angeforderte Dokument existiert nicht oder ist nicht verfügbar.</p>
        </div>
      </div>
    );
  }

  const licenseInfo = getLicenseIndicator(document.license_type);
  const isLicensed = document.license_type === 'DIN' || document.license_type === 'VDI';

  return (
    <div className="page-container">
      {/* Document Header */}
      <div className="document-header">
        <div className="document-title-section">
          <h1 className="document-title">{document.title}</h1>
          {document.description && (
            <p className="document-description">{document.description}</p>
          )}
        </div>

        <div className="document-meta">
          <div className="meta-row">
            <span className="meta-label">Gewerk:</span>
            <span className="meta-badge">{document.trade}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Kategorie:</span>
            <span className="meta-badge">{document.category}</span>
          </div>
          {document.jurisdiction && (
            <div className="meta-row">
              <span className="meta-label">Jurisdiktion:</span>
              <span className="meta-value">{document.jurisdiction}</span>
            </div>
          )}
          {document.building_type && (
            <div className="meta-row">
              <span className="meta-label">Gebäudetyp:</span>
              <span className="meta-value">{document.building_type}</span>
            </div>
          )}
          {document.year && (
            <div className="meta-row">
              <span className="meta-label">Jahr:</span>
              <span className="meta-value">{document.year}</span>
            </div>
          )}
          <div className="meta-row">
            <span className="meta-label">Lizenz:</span>
            <span className={`license-indicator ${licenseInfo.class}`}>
              {licenseInfo.icon} {licenseInfo.label}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Seiten:</span>
            <span className="meta-value">{document.page_count || 'N/A'}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Erstellt:</span>
            <span className="meta-value">{formatDate(document.created_at)}</span>
          </div>
        </div>

        <div className="document-actions">
          <button className="btn btn-secondary">
            <Download size={16} />
            Download
          </button>
          <button className="btn btn-secondary">
            <Share size={16} />
            Teilen
          </button>
          {isLicensed && (
            <button className="btn btn-outline">
              <ExternalLink size={16} />
              Zur Quelle
            </button>
          )}
        </div>
      </div>

      {/* License Warning */}
      {isLicensed && (
        <div className="license-warning">
          <AlertCircle size={20} />
          <div>
            <strong>Lizenzierter Inhalt</strong>
            <p>
              Dieses Dokument unterliegt dem {document.license_type}-Urheberrecht. 
              Nur Metadaten und Zusammenfassungen werden angezeigt. 
              Für den Volltext ist eine entsprechende Lizenz erforderlich.
            </p>
          </div>
        </div>
      )}

      {/* Document Layout */}
      <div className="document-viewer">
        {/* Table of Contents */}
        <div className="document-outline">
          <h3 className="outline-title">Inhaltsverzeichnis</h3>
          <div className="outline-sections">
            {document.sections?.map((section) => (
              <div
                key={section.id}
                className={`outline-item ${activeSection === section.id ? 'active' : ''}`}
                onClick={() => handleSectionClick(section.id)}
              >
                <div className="outline-item-title">{section.title}</div>
                <div className="outline-item-page">Seite {section.page_number}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Document Content */}
        <div className="document-content">
          {document.sections?.map((section) => (
            <div
              key={section.id}
              id={`section-${section.id}`}
              className={`document-section ${activeSection === section.id ? 'active' : ''}`}
            >
              <div className="section-header">
                <h2 className="section-title">{section.title}</h2>
                <div className="section-meta">
                  <span className="section-page">Seite {section.page_number}</span>
                  {section.section_hierarchy && (
                    <span className="section-hierarchy">{section.section_hierarchy}</span>
                  )}
                </div>
              </div>

              <div className="section-content">
                {isLicensed ? (
                  <div className="license-placeholder">
                    <AlertCircle size={24} />
                    <h4>Lizenzierter Inhalt</h4>
                    <p>
                      Der Volltext dieses Abschnitts ist aufgrund von Lizenzbestimmungen 
                      nicht verfügbar. Bitte konsultieren Sie die offizielle {document.license_type}-Quelle.
                    </p>
                    <button className="btn btn-primary btn-sm">
                      <ExternalLink size={14} />
                      Zur offiziellen Quelle
                    </button>
                  </div>
                ) : (
                  <div className="section-text">
                    {section.content.split('\n').map((paragraph, index) => (
                      <p key={index} className="content-paragraph">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                )}
              </div>

              <div className="section-footer">
                <div className="anchor-info">
                  <span className="anchor-label">Anker-ID:</span>
                  <code 
                    className="anchor-id"
                    onClick={() => copyAnchorId(section.anchor_id)}
                    title="Klicken zum Kopieren"
                  >
                    {section.anchor_id}
                  </code>
                </div>
                <div className="section-hash">
                  Hash: {section.content_hash?.substring(0, 8)}
                </div>
              </div>
            </div>
          ))}

          {(!document.sections || document.sections.length === 0) && (
            <div className="no-sections">
              <FileText size={48} />
              <h3>Keine Abschnitte verfügbar</h3>
              <p>
                Dieses Dokument wurde noch nicht verarbeitet oder enthält keine 
                extrahierbaren Textabschnitte.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;