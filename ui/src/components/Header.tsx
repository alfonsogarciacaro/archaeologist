import React, { useState } from 'react';
import { Search, Loader } from 'lucide-react';
import './Header.css';

interface HeaderProps {
  onInvestigate: (query: string) => void;
  isLoading: boolean;
}

const Header: React.FC<HeaderProps> = ({ onInvestigate, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onInvestigate(query.trim());
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="title">Enterprise Code Archaeologist</h1>
        <form onSubmit={handleSubmit} className="search-form">
          <div className="search-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter change request (e.g., 'Change term_sheet_id from string to UUID')"
              className="search-input"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="search-button"
              disabled={!query.trim() || isLoading}
            >
              {isLoading ? (
                <Loader className="loading-icon" size={20} />
              ) : (
                <Search size={20} />
              )}
            </button>
          </div>
        </form>
      </div>
    </header>
  );
};

export default Header;