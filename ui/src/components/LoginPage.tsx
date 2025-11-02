import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoggingIn(true);

    try {
      await login(username, password);
      // Login successful - redirect will be handled by AuthContext
    } catch (err) {
      setError('Login failed. Please try again.');
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>Enterprise Code Archaeologist</h2>
        <p>Sign in to access the system</p>
        
        <form onSubmit={handleSubmit} className="login-form-content">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoggingIn}
              placeholder="Enter your username"
              autoComplete="username"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoggingIn}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoggingIn || isLoading}
            className="login-button"
          >
            {isLoggingIn ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="login-help">
          <p>
            For prototype access, you can also <button 
              type="button" 
              onClick={() => login('anonymous', 'anonymous')}
              className="link-button"
            >
              continue as anonymous
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;