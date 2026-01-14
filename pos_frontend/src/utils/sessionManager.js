// Create role-based timeout in sessionManager.js
export const getTimeoutForRole = (role) => {
  const timeouts = {
    'admin': 4 * 60 * 60 * 1000,    // 4 hours
    'manager': 6 * 60 * 60 * 1000,   // 6 hours
    'cashier': 12 * 60 * 60 * 1000   // 12 hours
  };
  return timeouts[role] || 30 * 60 * 1000; // Default 30 minutes
};

export const setupAutoLogout = (role, dispatch, logout) => {
  const timeout = getTimeoutForRole(role);
  
  // Warn 5 minutes before logout
  const warningTimeout = setTimeout(() => {
    const shouldContinue = window.confirm(
      'Your session will expire in 5 minutes. Click OK to stay logged in.'
    );
    
    if (shouldContinue) {
      // Refresh token logic here
      setupAutoLogout(role, dispatch, logout);
    }
  }, timeout - 5 * 60 * 1000);
  
  // Auto logout
  const logoutTimeout = setTimeout(() => {
    dispatch(logout());
    window.location.href = '/login';
  }, timeout);
  
  return () => {
    clearTimeout(warningTimeout);
    clearTimeout(logoutTimeout);
  };
};