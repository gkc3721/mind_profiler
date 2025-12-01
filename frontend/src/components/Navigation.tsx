import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-teal-50">
      <Navigation />
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Routes will be rendered here */}
      </main>
    </div>
  );
};

const Navigation: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Run Pipeline' },
    { path: '/profiles', label: 'Profile Sets' },
    { path: '/runs', label: 'History' },
    { path: '/config', label: 'Config' }
  ];
  
  return (
    <nav className="bg-white/70 backdrop-blur-lg border-b border-slate-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-teal-400 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-sky-600 to-teal-500 bg-clip-text text-transparent">
              Zenin EEG
            </span>
          </div>
          
          <div className="flex gap-2">
            {navItems.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-full font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-sky-500 to-teal-400 text-white shadow-md'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};
