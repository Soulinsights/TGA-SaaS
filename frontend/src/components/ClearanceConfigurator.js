import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calculator, CheckCircle, AlertCircle, XCircle, Download, Settings, ExternalLink, FileText } from 'lucide-react';

const ClearanceConfigurator = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    product_id: '',
    material: '',
    DN: '',
    insulation: {
      class: '',
      thickness_mm: '',
      wrap: []
    },
    layout: '',
    bundle_count: 1,
    mount: {
      clamp_spacing_m: ''
    },
    context: {
      location: '',
      jurisdiction: '',
      building_class: ''
    }
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState(false);
  const [options, setOptions] = useState({
    products: [],
    materials: [],
    insulationClasses: [],
    wrappingTypes: [],
    jurisdictions: []
  });

  // Load form options on component mount
  useEffect(() => {
    loadFormOptions();
  }, []);

  const loadFormOptions = async () => {
    try {
      const [products, materials, insulationClasses, wrappingTypes, jurisdictions] = await Promise.all([
        axios.get('/api/fire/products'),
        axios.get('/api/fire/materials'),
        axios.get('/api/fire/insulation-classes'),
        axios.get('/api/fire/wrapping-types'),
        axios.get('/api/fire/jurisdictions')
      ]);

      setOptions({
        products: products.data,
        materials: materials.data,
        insulationClasses: insulationClasses.data,
        wrappingTypes: wrappingTypes.data,
        jurisdictions: jurisdictions.data
      });
    } catch (error) {
      console.error('Error loading form options:', error);
    }
  };

  const handleInputChange = (path, value) => {
    setFormData(prev => {
      const newData = { ...prev };
      const pathArray = path.split('.');
      let current = newData;
      
      for (let i = 0; i < pathArray.length - 1; i++) {
        current = current[pathArray[i]];
      }
      
      current[pathArray[pathArray.length - 1]] = value;
      return newData;
    });
  };

  const handleWrapChange = (wrapType, checked) => {
    setFormData(prev => ({
      ...prev,
      insulation: {
        ...prev.insulation,
        wrap: checked 
          ? [...prev.insulation.wrap, wrapType]
          : prev.insulation.wrap.filter(w => w !== wrapType)
      }
    }));
  };

  const validateStep = (stepNum) => {
    switch (stepNum) {
      case 1:
        return formData.product_id && formData.material && formData.DN && 
               formData.insulation.class && formData.insulation.thickness_mm && 
               formData.layout && formData.mount.clamp_spacing_m;
      case 2:
        return formData.context.location && formData.context.jurisdiction && 
               formData.context.building_class;
      default:
        return true;
    }
  };

  const computeClearance = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/fire/clearance/compute', {
        ...formData,
        DN: parseInt(formData.DN),
        insulation: {
          ...formData.insulation,
          class: formData.insulation.class,
          thickness_mm: parseInt(formData.insulation.thickness_mm)
        },
        bundle_count: parseInt(formData.bundle_count),
        mount: {
          clamp_spacing_m: parseFloat(formData.mount.clamp_spacing_m)
        }
      }, {
        params: { debug }
      });
      
      setResult(response.data);
      setStep(3);
    } catch (error) {
      console.error('Error computing clearance:', error);
      alert('Fehler bei der Berechnung: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'zulässig':
        return <CheckCircle className="text-green-600" size={24} />;
      case 'bedingt zulässig':
        return <AlertCircle className="text-yellow-600" size={24} />;
      case 'nicht zulässig':
        return <XCircle className="text-red-600" size={24} />;
      default:
        return <AlertCircle className="text-gray-600" size={24} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'zulässig':
        return 'text-green-700 bg-green-100 border-green-300';
      case 'bedingt zulässig':
        return 'text-yellow-700 bg-yellow-100 border-yellow-300';
      case 'nicht zulässig':
        return 'text-red-700 bg-red-100 border-red-300';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-300';
    }
  };

  const resetForm = () => {
    setFormData({
      product_id: '',
      material: '',
      DN: '',
      insulation: { class: '', thickness_mm: '', wrap: [] },
      layout: '',
      bundle_count: 1,
      mount: { clamp_spacing_m: '' },
      context: { location: '', jurisdiction: '', building_class: '' }
    });
    setResult(null);
    setStep(1);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Brandschutz-Abstandsrechner</h1>
          <p className="page-subtitle">
            Berechnung von Mindestabständen für TGA-Leitungen nach deutschen Brandschutzbestimmungen
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={debug}
              onChange={(e) => setDebug(e.target.checked)}
            />
            <Settings size={16} />
            Debug
          </label>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="progress-indicator mb-6">
        <div className="flex items-center justify-center gap-4">
          {[1, 2, 3].map((num) => (
            <div key={num} className="flex items-center gap-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold
                ${step >= num ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                {num}
              </div>
              <span className={`text-sm ${step >= num ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                {num === 1 && 'Konfiguration'}
                {num === 2 && 'Kontext'}
                {num === 3 && 'Ergebnis'}
              </span>
              {num < 3 && <div className="w-8 h-px bg-gray-300 mx-2" />}
            </div>
          ))}
        </div>
      </div>

      {/* Step 1: Configuration */}
      {step === 1 && (
        <div className="configurator-step">
          <h2 className="step-title">Schritt 1: System-Konfiguration</h2>
          
          <div className="form-grid">
            {/* Product Selection */}
            <div className="form-group">
              <label className="form-label">Produkt/System *</label>
              <select
                className="form-select"
                value={formData.product_id}
                onChange={(e) => handleInputChange('product_id', e.target.value)}
              >
                <option value="">Produkt auswählen</option>
                {options.products.map(product => (
                  <option key={product.id} value={product.id}>
                    {product.manufacturer_name} - {product.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Material */}
            <div className="form-group">
              <label className="form-label">Material *</label>
              <select
                className="form-select"
                value={formData.material}
                onChange={(e) => handleInputChange('material', e.target.value)}
              >
                <option value="">Material auswählen</option>
                {options.materials.map(material => (
                  <option key={material.value} value={material.value}>
                    {material.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Nominal Diameter */}
            <div className="form-group">
              <label className="form-label">Nennweite DN *</label>
              <input
                type="number"
                className="form-input"
                placeholder="z.B. 200"
                value={formData.DN}
                onChange={(e) => handleInputChange('DN', e.target.value)}
                min="10"
                max="1000"
              />
            </div>

            {/* Insulation Class */}
            <div className="form-group">
              <label className="form-label">Dämmklasse *</label>
              <select
                className="form-select"
                value={formData.insulation.class}
                onChange={(e) => handleInputChange('insulation.class', e.target.value)}
              >
                <option value="">Dämmklasse auswählen</option>
                {options.insulationClasses.map(insClass => (
                  <option key={insClass.value} value={insClass.value}>
                    {insClass.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Insulation Thickness */}
            <div className="form-group">
              <label className="form-label">Dämmdicke (mm) *</label>
              <input
                type="number"
                className="form-input"
                placeholder="z.B. 30"
                value={formData.insulation.thickness_mm}
                onChange={(e) => handleInputChange('insulation.thickness_mm', e.target.value)}
                min="5"
                max="200"
              />
            </div>

            {/* Layout */}
            <div className="form-group">
              <label className="form-label">Verlegeart *</label>
              <select
                className="form-select"
                value={formData.layout}
                onChange={(e) => handleInputChange('layout', e.target.value)}
              >
                <option value="">Verlegeart auswählen</option>
                <option value="parallel">Parallel</option>
                <option value="bundled">Gebündelt</option>
                <option value="single">Einzeln</option>
              </select>
            </div>

            {/* Bundle Count */}
            <div className="form-group">
              <label className="form-label">Anzahl Leitungen</label>
              <input
                type="number"
                className="form-input"
                value={formData.bundle_count}
                onChange={(e) => handleInputChange('bundle_count', e.target.value)}
                min="1"
                max="10"
              />
            </div>

            {/* Clamp Spacing */}
            <div className="form-group">
              <label className="form-label">Befestigungsabstand (m) *</label>
              <input
                type="number"
                step="0.1"
                className="form-input"
                placeholder="z.B. 1.5"
                value={formData.mount.clamp_spacing_m}
                onChange={(e) => handleInputChange('mount.clamp_spacing_m', e.target.value)}
                min="0.1"
                max="5.0"
              />
            </div>
          </div>

          {/* Wrapping Types */}
          <div className="form-group form-group-full">
            <label className="form-label">Ummantelung</label>
            <div className="wrapping-grid">
              {options.wrappingTypes.map(wrap => (
                <label key={wrap.value} className="wrapping-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.insulation.wrap.includes(wrap.value)}
                    onChange={(e) => handleWrapChange(wrap.value, e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  {wrap.label}
                </label>
              ))}
            </div>
          </div>

          <div className="step-actions">
            <button
              className="btn btn-primary"
              onClick={() => setStep(2)}
              disabled={!validateStep(1)}
            >
              Weiter zu Kontext
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Context */}
      {step === 2 && (
        <div className="configurator-step">
          <h2 className="step-title">Schritt 2: Projekt-Kontext</h2>
          
          <div className="form-grid">
            {/* Location */}
            <div className="form-group">
              <label className="form-label">Einbauort *</label>
              <select
                className="form-select"
                value={formData.context.location}
                onChange={(e) => handleInputChange('context.location', e.target.value)}
              >
                <option value="">Einbauort auswählen</option>
                <option value="shaft">Schacht</option>
                <option value="wall">Wand</option>
                <option value="ceiling">Decke</option>
                <option value="floor">Fußboden</option>
                <option value="open">Frei verlegt</option>
              </select>
            </div>

            {/* Jurisdiction */}
            <div className="form-group">
              <label className="form-label">Bundesland *</label>
              <select
                className="form-select"
                value={formData.context.jurisdiction}
                onChange={(e) => handleInputChange('context.jurisdiction', e.target.value)}
              >
                <option value="">Bundesland auswählen</option>
                {options.jurisdictions.map(jurisdiction => (
                  <option key={jurisdiction.value} value={jurisdiction.value}>
                    {jurisdiction.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Building Class */}
            <div className="form-group">
              <label className="form-label">Gebäudeklasse *</label>
              <select
                className="form-select"
                value={formData.context.building_class}
                onChange={(e) => handleInputChange('context.building_class', e.target.value)}
              >
                <option value="">Gebäudeklasse auswählen</option>
                <option value="Hochhaus">Hochhaus</option>
                <option value="Gewerbebau">Gewerbebau</option>
                <option value="Wohnbau">Wohnbau</option>
                <option value="Industriebau">Industriebau</option>
                <option value="Krankenhaus">Krankenhaus</option>
                <option value="Schule">Schule</option>
                <option value="Bürogebäude">Bürogebäude</option>
                <option value="Hotel">Hotel</option>
              </select>
            </div>
          </div>

          <div className="step-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setStep(1)}
            >
              Zurück
            </button>
            <button
              className="btn btn-primary"
              onClick={computeClearance}
              disabled={!validateStep(2) || loading}
            >
              {loading ? (
                <>
                  <div className="loading-spinner" />
                  Berechnung läuft...
                </>
              ) : (
                <>
                  <Calculator size={16} />
                  Abstand berechnen
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Results */}
      {step === 3 && result && (
        <div className="configurator-step">
          <h2 className="step-title">Ergebnis der Abstandsberechnung</h2>
          
          {/* Main Result */}
          <div className="result-panel">
            <div className="result-header">
              <div className="result-clearance">
                <span className="clearance-label">Mindestabstand</span>
                <span className="clearance-value">{result.min_clearance_mm} mm</span>
              </div>
              <div className={`result-status ${getStatusColor(result.status)}`}>
                {getStatusIcon(result.status)}
                <span className="status-text">{result.status}</span>
              </div>
            </div>

            {result.notes && (
              <div className="result-notes">
                <p>{result.notes}</p>
              </div>
            )}

            {/* Conditions */}
            {result.conditions_unmet && result.conditions_unmet.length > 0 && (
              <div className="conditions-panel">
                <h4 className="conditions-title">Nicht erfüllte Bedingungen:</h4>
                <ul className="conditions-list">
                  {result.conditions_unmet.map((condition, index) => (
                    <li key={index} className="condition-item unmet">
                      <XCircle size={16} />
                      {condition}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Sources */}
            <div className="sources-panel">
              <h4 className="sources-title">Quellen und Zulassungen:</h4>
              <div className="sources-list">
                {result.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      <span className={`source-type ${source.type.toLowerCase()}`}>
                        {source.type}
                      </span>
                      {source.number && (
                        <span className="source-number">{source.number}</span>
                      )}
                    </div>
                    <div className="source-details">
                      <span className="source-anchor">{source.anchor}</span>
                      {source.ref && (
                        <span className="source-ref">{source.ref}</span>
                      )}
                    </div>
                    <a 
                      href={source.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      <ExternalLink size={14} />
                      Zur Quelle
                    </a>
                  </div>
                ))}
              </div>
            </div>

            {/* Debug Information */}
            {debug && result.debug_info && (
              <div className="debug-panel">
                <h4 className="debug-title">Debug-Informationen:</h4>
                <pre className="debug-content">
                  {JSON.stringify(result.debug_info, null, 2)}
                </pre>
              </div>
            )}
          </div>

          <div className="result-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setStep(2)}
            >
              Zurück bearbeiten
            </button>
            <button
              className="btn btn-primary"
              onClick={() => alert('PDF-Export wird implementiert')}
            >
              <Download size={16} />
              Als PDF exportieren
            </button>
            <button
              className="btn btn-outline"
              onClick={resetForm}
            >
              <FileText size={16} />
              Neue Berechnung
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClearanceConfigurator;