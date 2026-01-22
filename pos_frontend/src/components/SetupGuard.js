// pos_frontend/src/components/SetupGuard.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import api from '../services/api';

const SetupGuard = ({ children }) => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [setupRequired, setSetupRequired] = useState(false);

  useEffect(() => {
    const checkSetup = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.get('/setup/status/');
        
        const needsSetup = response.data.setup_required && 
                          response.data.is_admin && 
                          !response.data.user_completed_setup;
        
        if (needsSetup) {
          setSetupRequired(true);
          navigate('/setup');
        }
      } catch (error) {
        console.error('Error checking setup status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkSetup();
  }, [isAuthenticated, navigate]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#F5F1E8'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#1B5E4C' }}>Loading...</h2>
          <p>Checking setup status...</p>
        </div>
      </div>
    );
  }

  if (setupRequired) {
    return null; // Will redirect to setup
  }

  return children;
};

export default SetupGuard;