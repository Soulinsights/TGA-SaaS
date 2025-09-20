import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Upload, MessageCircle, Settings, Database, Building, Calculator } from 'lucide-react';

const Navigation = ({ currentProject }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Startseite', icon: Database },
    { path: '/search', label: 'Suche', icon: Search },
    { path: '/qa', label: 'Q&A Chat', icon: MessageCircle },
    { path: '/clearance', label: 'Brandschutz', icon: Calculator },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/projects', label: 'Projekte', icon: Building }
  ];

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          <div className="nav-brand-icon">
            TGA
          </div>
          <span>Knowledge Platform</span>
        </Link>

        <ul className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        {currentProject && (
          <div className="project-indicator">
            <Building size={16} />
            <span>{currentProject.name}</span>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;