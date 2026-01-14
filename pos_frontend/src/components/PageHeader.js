// import React from 'react';
// import { Link } from 'react-router-dom';
// import './PageHeader.css';

// const PageHeader = ({ title, subtitle, showDashboardButton = true, children }) => {
//   return (
//     <div className="page-header">
//       <div className="page-header-content">
//         <div className="page-header-text">
//           <h2>{title}</h2>
//           {subtitle && <p className="page-subtitle">{subtitle}</p>}
//         </div>
//         <div className="page-header-actions">
//           {children}
//           {showDashboardButton && (
//             <Link to="/dashboard" className="btn-dashboard">
//               Dashboard
//             </Link>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default PageHeader;

// pos_frontend/src/components/PageHeader.js
import React from 'react';
import { Link } from 'react-router-dom';
import './PageHeader.css';

const PageHeader = ({ 
  title, 
  showDashboardButton = true, 
  dashboardPath = '/dashboard',
  children 
}) => {
  return (
    <div className="page-header">
      <div className="page-header-title">
        <h2>{title}</h2>
      </div>
      <div className="page-header-actions">
        {showDashboardButton && (
          <Link to={dashboardPath} className="btn-back">
            ← Dashboard
          </Link>
        )}
        {children}
      </div>
    </div>
  );
};

export default PageHeader;