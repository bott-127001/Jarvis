import React from 'react';
import './App.css';
import Login from './Login';
import OptionChain from './OptionChain';
import BiasIdentifier from './BiasIdentifier';
import MarketStyleIdentifier from './MarketStyleIdentifier';
import ReversalProbabilityFinder from './ReversalProbabilityFinder';
import TrapDetectorIdentifier from './TrapDetectorIdentifier';
import EntryLogicEngine from './EntryLogicEngine';
import MomentumIdentifier from './MomentumIdentifier';
import { OptionChainProvider } from './OptionChainContext';

const sections = [
  { key: 'login', label: 'Login' },
  { key: 'optionChain', label: 'Option Chain' },
  { key: 'biasIdentifier', label: 'Bias Identifier' },
  { key: 'momentumIdentifier', label: 'Momentum Identifier' },
  { key: 'reversalProbability', label: 'Reversal Probability' },
  { key: 'trapIdentifier', label: 'Trap Identifier' },
  { key: 'entryIdentifier', label: 'Entry Identifier' },
];

function App() {
  const [selected, setSelected] = React.useState(() => localStorage.getItem('selectedModule') || 'login');
  const [authenticated, setAuthenticated] = React.useState(() => localStorage.getItem('authenticated') === 'true');
  const [checking, setChecking] = React.useState(false);
  const [user, setUser] = React.useState(() => localStorage.getItem('user'));
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // Persist selected module
  React.useEffect(() => {
    localStorage.setItem('selectedModule', selected);
  }, [selected]);

  // Persist authentication and user
  React.useEffect(() => {
    localStorage.setItem('authenticated', authenticated);
    if (user) {
      localStorage.setItem('user', user);
    } else {
      localStorage.removeItem('user');
    }
  }, [authenticated, user]);

  // Auth logic remains, but user/expiry state is now only for login
  React.useEffect(() => {
    if (!user) return;
    const checkToken = async () => {
      setChecking(true);
      try {
        const res = await fetch(`http://localhost:8000/check-token?user=${user}`);
        const data = await res.json();
        setAuthenticated(data.valid);
        if (!data.valid) setSelected('login');
      } catch {
        setAuthenticated(false);
        setSelected('login');
      } finally {
        setChecking(false);
      }
    };
    checkToken();
  }, [user]);

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    setAuthenticated(true);
    setSelected('optionChain');
    localStorage.setItem('authenticated', 'true');
    localStorage.setItem('user', loggedInUser);
    localStorage.setItem('selectedModule', 'optionChain');
  };

  const handleLogout = () => {
    setAuthenticated(false);
    setUser(null);
    setSelected('login');
    localStorage.removeItem('authenticated');
    localStorage.removeItem('user');
    localStorage.setItem('selectedModule', 'login');
  };

  const sectionContent = {
    login: <Login onLoginSuccess={handleLoginSuccess} />, // pass callback
    optionChain: <OptionChain />, // now uses context
    biasIdentifier: <BiasIdentifier />, // uses context
    momentumIdentifier: <MomentumIdentifier />, // uses context
    reversalProbability: <ReversalProbabilityFinder />, // uses context
    trapIdentifier: <TrapDetectorIdentifier />, // uses context
    entryIdentifier: <EntryLogicEngine />, // now uses context
  };

  const visibleSections = authenticated
    ? sections
    : sections.filter(s => s.key === 'login');

  // Detect mobile
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 700;

  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 700 && sidebarOpen) setSidebarOpen(false);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen]);

  return (
    <OptionChainProvider user={user}>
      <div className="dashboard-root">
        <aside className="sidebar">
          <div className="sidebar-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Trading Engine
            <span className="sidebar-hamburger" onClick={() => setSidebarOpen(true)}>
              <span className="hamburger-icon">&#9776;</span>
            </span>
          </div>
          {authenticated && user && (
            <div style={{ padding: '16px 0', textAlign: 'center', color: '#bbb', fontWeight: 500 }}>
              User: <span style={{ color: '#fff', fontWeight: 600 }}>{user.charAt(0).toUpperCase() + user.slice(1)}</span>
              <button
                onClick={handleLogout}
                style={{ marginLeft: 16, padding: '4px 12px', borderRadius: 8, border: 'none', background: '#e53935', color: '#fff', fontWeight: 600, cursor: 'pointer' }}
              >
                Logout
              </button>
            </div>
          )}
          <nav className="sidebar-nav-desktop">
            {visibleSections.map((section) => (
              <button
                key={section.key}
                className={`sidebar-btn${selected === section.key ? ' active' : ''}`}
                onClick={() => setSelected(section.key)}
                disabled={checking}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </aside>
        {/* Mobile Sidebar Overlay */}
        <div className={`sidebar-overlay${sidebarOpen ? ' open' : ''}`} onClick={() => setSidebarOpen(false)}></div>
        <div className={`sidebar-mobile${sidebarOpen ? ' open' : ''}`}>
          <div className="sidebar-mobile-header">
            <span style={{ fontWeight: 700, fontSize: 20 }}>Menu</span>
            <span className="sidebar-mobile-close" onClick={() => setSidebarOpen(false)}>&times;</span>
          </div>
          <nav className="sidebar-mobile-nav">
            {visibleSections.map((section) => (
              <button
                key={section.key}
                className={`sidebar-btn${selected === section.key ? ' active' : ''}`}
                onClick={() => { setSelected(section.key); setSidebarOpen(false); }}
                disabled={checking}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </div>
        <main className="main-content">
          <div className="section-content">
            {checking ? <div style={{ color: '#bbb' }}>Checking authentication...</div> : sectionContent[selected]}
          </div>
        </main>
      </div>
    </OptionChainProvider>
  );
}

export default App;
