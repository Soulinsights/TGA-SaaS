import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';

const UploadConsole = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    trade: '',
    category: '',
    jurisdiction: '',
    building_type: '',
    year: '',
    license_type: 'open'
  });

  const fileInputRef = useRef(null);

  const trades = [
    'HLK/RLT', 'Sanitär', 'Elektro', 'Brandschutz', 'Aufzugstechnik', 
    'Sicherheitstechnik', 'Gebäudeautomation', 'Beleuchtung', 'Medizintechnik',
    'Fördertechnik', 'Kältetechnik', 'Mess-, Steuer- und Regeltechnik'
  ];

  const categories = [
    'Standard', 'Produktdaten', 'Technische Anleitung', 'Zulassung', 
    'Montagehinweise', 'Wartungsanleitung', 'Planungshilfe', 'Prüfbericht',
    'Herstellerdokumentation', 'Compliance-Dokument'
  ];

  const jurisdictions = [
    'Bundesweit', 'Bayern', 'Baden-Württemberg', 'Nordrhein-Westfalen',
    'Hessen', 'Niedersachsen', 'Sachsen', 'Berlin', 'Hamburg', 'Bremen',
    'Rheinland-Pfalz', 'Saarland', 'Schleswig-Holstein', 'Thüringen',
    'Sachsen-Anhalt', 'Brandenburg', 'Mecklenburg-Vorpommern', 'EU-Richtlinie'
  ];

  const buildingTypes = [
    'Hochhaus', 'Gewerbebau', 'Wohnbau', 'Industriebau', 'Krankenhaus',
    'Schule', 'Bürogebäude', 'Hotel', 'Einkaufszentrum', 'Logistikzentrum',
    'Sportstätte', 'Kulturgebäude', 'Verkehrsbau'
  ];

  const licenseTypes = [
    { value: 'open', label: 'Frei verfügbar' },
    { value: 'DIN', label: 'DIN-Norm (lizenziert)' },
    { value: 'VDI', label: 'VDI-Richtlinie (lizenziert)' },
    { value: 'proprietary', label: 'Herstellereigen' }
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (file) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    
    if (!allowedTypes.includes(file.type)) {
      alert('Nur PDF, DOC, DOCX und TXT Dateien sind erlaubt.');
      return;
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      alert('Datei ist zu groß. Maximum: 50MB');
      return;
    }

    setSelectedFile(file);
    
    // Auto-fill title if empty
    if (!formData.title) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
      setFormData(prev => ({ ...prev, title: nameWithoutExt }));
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      alert('Bitte wählen Sie eine Datei aus.');
      return;
    }

    if (!formData.title || !formData.trade || !formData.category) {
      alert('Bitte füllen Sie alle Pflichtfelder aus.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadResult(null);

    try {
      const uploadFormData = new FormData();
      uploadFormData.append('file', selectedFile);
      
      // Add all form fields
      Object.keys(formData).forEach(key => {
        if (formData[key]) {
          uploadFormData.append(key, formData[key]);
        }
      });

      const response = await axios.post('/api/documents/upload', uploadFormData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setUploadResult({
        success: true,
        message: response.data.message,
        documentId: response.data.document_id
      });

      // Reset form
      setSelectedFile(null);
      setFormData({
        title: '',
        description: '',
        trade: '',
        category: '',
        jurisdiction: '',
        building_type: '',
        year: '',
        license_type: 'open'
      });
      
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      if (onUploadSuccess) {
        onUploadSuccess();
      }

    } catch (error) {
      console.error('Upload error:', error);
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || 'Upload fehlgeschlagen'
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dokument Upload</h1>
        <p className="page-subtitle">
          Laden Sie TGA-Dokumente hoch für automatische Verarbeitung und Indizierung
        </p>
      </div>

      {/* Upload Area */}
      <div className="upload-section">
        <div
          className={`upload-area ${dragActive ? 'dragover' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
          
          {selectedFile ? (
            <div className="selected-file">
              <FileText size={48} className="file-icon" />
              <div className="file-info">
                <h3 className="file-name">{selectedFile.name}</h3>
                <p className="file-size">{formatFileSize(selectedFile.size)}</p>
                <p className="file-type">{selectedFile.type}</p>
              </div>
              <button
                type="button"
                className="clear-file-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
              >
                <X size={20} />
              </button>
            </div>
          ) : (
            <div className="upload-prompt">
              <Upload size={64} className="upload-icon" />
              <h3 className="upload-text">
                Datei hier ablegen oder klicken zum Auswählen
              </h3>
              <p className="upload-hint">
                PDF, DOC, DOCX oder TXT • Maximal 50MB
              </p>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="progress-text">Upload läuft... {uploadProgress}%</p>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div className={`upload-result ${uploadResult.success ? 'success' : 'error'}`}>
            {uploadResult.success ? (
              <CheckCircle size={20} />
            ) : (
              <AlertCircle size={20} />
            )}
            <span>{uploadResult.message}</span>
            {uploadResult.documentId && (
              <p className="document-id">Dokument-ID: {uploadResult.documentId}</p>
            )}
          </div>
        )}
      </div>

      {/* Metadata Form */}
      <form onSubmit={handleUpload} className="upload-form">
        <div className="form-section">
          <h2 className="form-section-title">Dokument-Metadaten</h2>
          
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Titel *</label>
              <input
                type="text"
                className="form-input"
                placeholder="Dokumenttitel eingeben"
                value={formData.title}
                onChange={(e) => handleFormChange('title', e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Gewerk *</label>
              <select
                className="form-select"
                value={formData.trade}
                onChange={(e) => handleFormChange('trade', e.target.value)}
                required
              >
                <option value="">Gewerk auswählen</option>
                {trades.map(trade => (
                  <option key={trade} value={trade}>{trade}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Kategorie *</label>
              <select
                className="form-select"
                value={formData.category}
                onChange={(e) => handleFormChange('category', e.target.value)}
                required
              >
                <option value="">Kategorie auswählen</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Lizenztyp</label>
              <select
                className="form-select"
                value={formData.license_type}
                onChange={(e) => handleFormChange('license_type', e.target.value)}
              >
                {licenseTypes.map(license => (
                  <option key={license.value} value={license.value}>{license.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Jurisdiktion</label>
              <select
                className="form-select"
                value={formData.jurisdiction}
                onChange={(e) => handleFormChange('jurisdiction', e.target.value)}
              >
                <option value="">Jurisdiktion auswählen</option>
                {jurisdictions.map(jurisdiction => (
                  <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Gebäudetyp</label>
              <select
                className="form-select"
                value={formData.building_type}
                onChange={(e) => handleFormChange('building_type', e.target.value)}
              >
                <option value="">Gebäudetyp auswählen</option>
                {buildingTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Jahr</label>
              <input
                type="number"
                className="form-input"
                placeholder="z.B. 2024"
                min="1990"
                max="2030"
                value={formData.year}
                onChange={(e) => handleFormChange('year', e.target.value)}
              />
            </div>

            <div className="form-group form-group-full">
              <label className="form-label">Beschreibung</label>
              <textarea
                className="form-textarea"
                placeholder="Beschreibung des Dokuments..."
                value={formData.description}
                onChange={(e) => handleFormChange('description', e.target.value)}
                rows={3}
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary btn-large"
            disabled={!selectedFile || uploading}
          >
            {uploading ? (
              <>
                <div className="loading-spinner" />
                Wird hochgeladen...
              </>
            ) : (
              <>
                <Upload size={16} />
                Dokument hochladen
              </>
            )}
          </button>
        </div>
      </form>

      {/* Processing Info */}
      <div className="processing-info">
        <h3>Was passiert nach dem Upload?</h3>
        <ol className="processing-steps">
          <li>Datei wird validiert und gespeichert</li>
          <li>Text wird extrahiert (OCR bei PDFs)</li>
          <li>Dokument wird in Abschnitte unterteilt</li>
          <li>Embeddings werden generiert</li>
          <li>Dokument ist durchsuchbar und für Q&A verfügbar</li>
        </ol>
      </div>
    </div>
  );
};

export default UploadConsole;