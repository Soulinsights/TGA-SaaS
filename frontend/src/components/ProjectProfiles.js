import React, { useState, useEffect } from 'react';
import { Building, Plus, Edit, Trash2, Check, X } from 'lucide-react';

const ProjectProfiles = ({ currentProject, onProjectChange }) => {
  const [profiles, setProfiles] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    jurisdiction: '',
    building_type: '',
    usage_class: '',
    special_requirements: []
  });

  const jurisdictions = [
    'Bundesweit', 'Bayern', 'Baden-Württemberg', 'Nordrhein-Westfalen',
    'Hessen', 'Niedersachsen', 'Sachsen', 'Berlin', 'Hamburg', 'Bremen',
    'Rheinland-Pfalz', 'Saarland', 'Schleswig-Holstein', 'Thüringen',
    'Sachsen-Anhalt', 'Brandenburg', 'Mecklenburg-Vorpommern'
  ];

  const buildingTypes = [
    'Hochhaus', 'Gewerbebau', 'Wohnbau', 'Industriebau', 'Krankenhaus',
    'Schule', 'Bürogebäude', 'Hotel', 'Einkaufszentrum', 'Logistikzentrum',
    'Sportstätte', 'Kulturgebäude', 'Verkehrsbau'
  ];

  const usageClasses = [
    'Nutzungsklasse 1', 'Nutzungsklasse 2', 'Nutzungsklasse 3',
    'Nutzungsklasse 4', 'Nutzungsklasse 5', 'Sonderbau'
  ];

  const specialRequirements = [
    'Barrierefreiheit', 'Erhöhter Brandschutz', 'Explosionsschutz',
    'Hygieneanforderungen', 'Denkmalschutz', 'Energieeffizienz',
    'Lärmschutz', 'Strahlenschutz', 'Reinraumtechnik'
  ];

  // Mock data - in real app this would come from API
  useEffect(() => {
    const mockProfiles = [
      {
        id: '1',
        name: 'Krankenhaus München',
        description: 'Neubau Klinikum mit 200 Betten',
        jurisdiction: 'Bayern',
        building_type: 'Krankenhaus',
        usage_class: 'Sonderbau',
        special_requirements: ['Hygieneanforderungen', 'Erhöhter Brandschutz'],
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z'
      },
      {
        id: '2',
        name: 'Bürokomplex Berlin',
        description: 'Bürogebäude mit 15 Etagen',
        jurisdiction: 'Berlin',
        building_type: 'Bürogebäude',
        usage_class: 'Nutzungsklasse 2',
        special_requirements: ['Energieeffizienz', 'Barrierefreiheit'],
        created_at: '2024-01-10T14:30:00Z',
        updated_at: '2024-01-20T09:15:00Z'
      }
    ];
    setProfiles(mockProfiles);
  }, []);

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      jurisdiction: '',
      building_type: '',
      usage_class: '',
      special_requirements: []
    });
    setShowCreateForm(false);
    setEditingProfile(null);
  };

  const handleCreate = () => {
    setShowCreateForm(true);
    setEditingProfile(null);
    resetForm();
  };

  const handleEdit = (profile) => {
    setEditingProfile(profile.id);
    setFormData({
      name: profile.name,
      description: profile.description || '',
      jurisdiction: profile.jurisdiction,
      building_type: profile.building_type,
      usage_class: profile.usage_class || '',
      special_requirements: profile.special_requirements || []
    });
    setShowCreateForm(true);
  };

  const handleSave = async () => {
    if (!formData.name || !formData.jurisdiction || !formData.building_type) {
      alert('Bitte füllen Sie alle Pflichtfelder aus.');
      return;
    }

    const profileData = {
      ...formData,
      id: editingProfile || Date.now().toString(),
      created_at: editingProfile ? 
        profiles.find(p => p.id === editingProfile)?.created_at : 
        new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    if (editingProfile) {
      // Update existing profile
      setProfiles(prev => prev.map(p => p.id === editingProfile ? profileData : p));
    } else {
      // Create new profile
      setProfiles(prev => [...prev, profileData]);
    }

    resetForm();
  };

  const handleDelete = (profileId) => {
    if (window.confirm('Möchten Sie dieses Projektprofil wirklich löschen?')) {
      setProfiles(prev => prev.filter(p => p.id !== profileId));
      if (currentProject?.id === profileId) {
        onProjectChange(null);
      }
    }
  };

  const handleActivateProject = (profile) => {
    onProjectChange(profile);
  };

  const handleRequirementToggle = (requirement) => {
    setFormData(prev => ({
      ...prev,
      special_requirements: prev.special_requirements.includes(requirement)
        ? prev.special_requirements.filter(r => r !== requirement)
        : [...prev.special_requirements, requirement]
    }));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Projekt-Profile</h1>
          <p className="page-subtitle">
            Definieren Sie Projektkontext für maßgeschneiderte Suchergebnisse
          </p>
        </div>
        <button className="btn btn-primary" onClick={handleCreate}>
          <Plus size={16} />
          Neues Profil
        </button>
      </div>

      {/* Current Project Banner */}
      {currentProject && (
        <div className="current-project-banner">
          <div className="banner-content">
            <Building size={24} />
            <div>
              <h3>Aktives Projekt: {currentProject.name}</h3>
              <p>{currentProject.jurisdiction} • {currentProject.building_type}</p>
            </div>
          </div>
          <button 
            className="btn btn-secondary"
            onClick={() => onProjectChange(null)}
          >
            Deaktivieren
          </button>
        </div>
      )}

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="profile-form">
          <div className="form-header">
            <h2>{editingProfile ? 'Profil bearbeiten' : 'Neues Profil erstellen'}</h2>
            <button className="btn btn-secondary btn-sm" onClick={resetForm}>
              <X size={16} />
            </button>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Projektname *</label>
              <input
                type="text"
                className="form-input"
                placeholder="z.B. Krankenhaus München"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Jurisdiktion *</label>
              <select
                className="form-select"
                value={formData.jurisdiction}
                onChange={(e) => setFormData(prev => ({ ...prev, jurisdiction: e.target.value }))}
              >
                <option value="">Jurisdiktion auswählen</option>
                {jurisdictions.map(jurisdiction => (
                  <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Gebäudetyp *</label>
              <select
                className="form-select"
                value={formData.building_type}
                onChange={(e) => setFormData(prev => ({ ...prev, building_type: e.target.value }))}
              >
                <option value="">Gebäudetyp auswählen</option>
                {buildingTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Nutzungsklasse</label>
              <select
                className="form-select"
                value={formData.usage_class}
                onChange={(e) => setFormData(prev => ({ ...prev, usage_class: e.target.value }))}
              >
                <option value="">Nutzungsklasse auswählen</option>
                {usageClasses.map(uClass => (
                  <option key={uClass} value={uClass}>{uClass}</option>
                ))}
              </select>
            </div>

            <div className="form-group form-group-full">
              <label className="form-label">Beschreibung</label>
              <textarea
                className="form-textarea"
                placeholder="Projektbeschreibung..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            <div className="form-group form-group-full">
              <label className="form-label">Besondere Anforderungen</label>
              <div className="requirements-grid">
                {specialRequirements.map(requirement => (
                  <label key={requirement} className="requirement-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.special_requirements.includes(requirement)}
                      onChange={() => handleRequirementToggle(requirement)}
                    />
                    <span className="checkmark"></span>
                    {requirement}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button className="btn btn-secondary" onClick={resetForm}>
              Abbrechen
            </button>
            <button className="btn btn-primary" onClick={handleSave}>
              <Check size={16} />
              {editingProfile ? 'Aktualisieren' : 'Erstellen'}
            </button>
          </div>
        </div>
      )}

      {/* Profiles List */}
      <div className="profiles-list">
        {profiles.length === 0 ? (
          <div className="empty-state">
            <Building size={48} />
            <h3>Keine Projektprofile vorhanden</h3>
            <p>Erstellen Sie Ihr erstes Projektprofil für kontextuelle Suche.</p>
            <button className="btn btn-primary" onClick={handleCreate}>
              <Plus size={16} />
              Profil erstellen
            </button>
          </div>
        ) : (
          <div className="profiles-grid">
            {profiles.map(profile => (
              <div 
                key={profile.id} 
                className={`profile-card ${currentProject?.id === profile.id ? 'active' : ''}`}
              >
                <div className="profile-header">
                  <div className="profile-title">
                    <h3>{profile.name}</h3>
                    {currentProject?.id === profile.id && (
                      <span className="active-badge">Aktiv</span>
                    )}
                  </div>
                  <div className="profile-actions">
                    <button 
                      className="btn-icon"
                      onClick={() => handleEdit(profile)}
                      title="Bearbeiten"
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn-icon btn-danger"
                      onClick={() => handleDelete(profile.id)}
                      title="Löschen"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                {profile.description && (
                  <p className="profile-description">{profile.description}</p>
                )}

                <div className="profile-meta">
                  <div className="meta-item">
                    <span className="meta-label">Jurisdiktion:</span>
                    <span className="meta-value">{profile.jurisdiction}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Gebäudetyp:</span>
                    <span className="meta-value">{profile.building_type}</span>
                  </div>
                  {profile.usage_class && (
                    <div className="meta-item">
                      <span className="meta-label">Nutzungsklasse:</span>
                      <span className="meta-value">{profile.usage_class}</span>
                    </div>
                  )}
                </div>

                {profile.special_requirements && profile.special_requirements.length > 0 && (
                  <div className="requirements-tags">
                    {profile.special_requirements.map(req => (
                      <span key={req} className="requirement-tag">{req}</span>
                    ))}
                  </div>
                )}

                <div className="profile-footer">
                  <span className="profile-date">
                    Erstellt: {formatDate(profile.created_at)}
                  </span>
                  <button
                    className={`btn btn-sm ${currentProject?.id === profile.id ? 'btn-secondary' : 'btn-primary'}`}
                    onClick={() => handleActivateProject(profile)}
                    disabled={currentProject?.id === profile.id}
                  >
                    {currentProject?.id === profile.id ? 'Aktiv' : 'Aktivieren'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectProfiles;