import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

const API_BASE = '';
const LS_KEY = 'optionChainContext';

const OptionChainContext = createContext();

export function useOptionChain() {
  return useContext(OptionChainContext);
}

export function OptionChainProvider({ user: externalUser, children }) {
  // State
  const [user, setUser] = useState(externalUser || null);
  const [expiry, setExpiry] = useState(() => localStorage.getItem('optionChain_expiry') || '');
  const [fetching, setFetching] = useState(() => localStorage.getItem('optionChain_fetching') === 'true');
  const [optionChain, setOptionChain] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('optionChain_data')) || [];
    } catch {
      return [];
    }
  });
  const [analytics, setAnalytics] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('optionChain_analytics')) || {};
    } catch {
      return {};
    }
  });
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);
  const lastOptionChainRef = useRef(null); // for change detection

  // Persist state
  useEffect(() => {
    localStorage.setItem('optionChain_expiry', expiry);
  }, [expiry]);
  useEffect(() => {
    localStorage.setItem('optionChain_fetching', fetching);
  }, [fetching]);
  useEffect(() => {
    localStorage.setItem('optionChain_data', JSON.stringify(optionChain));
  }, [optionChain]);
  useEffect(() => {
    localStorage.setItem('optionChain_analytics', JSON.stringify(analytics));
  }, [analytics]);

  // Fetch analytics (all modules) - define first
  const fetchAnalytics = useCallback(async () => {
    if (!user || !expiry) return;
    try {
      const [bias, style, reversal, trap, sr, entry] = await Promise.all([
        fetch(`${API_BASE}/bias-identifier?user=${user}&expiry=${expiry}`).then(r => r.json()),
        fetch(`${API_BASE}/market-style-identifier?user=${user}&expiry=${expiry}`).then(r => r.json()),
        fetch(`${API_BASE}/reversal-probability-finder?user=${user}&expiry=${expiry}`).then(r => r.json()),
        fetch(`${API_BASE}/trap-detector?user=${user}&expiry=${expiry}`).then(r => r.json()),
        fetch(`${API_BASE}/support-resistance-guard?user=${user}&expiry=${expiry}`).then(r => r.json()),
        fetch(`${API_BASE}/entry-logic-engine?user=${user}&expiry=${expiry}`).then(r => r.json()),
      ]);
      setAnalytics({ bias, style, reversal, trap, sr, entry });
    } catch (e) {
      // Partial analytics may be available
    }
  }, [user, expiry]);

  // Sync external user to context user
  useEffect(() => {
    if (externalUser && externalUser !== user) {
      setUser(externalUser);
    }
  }, [externalUser]);

  // Load from localStorage on mount (no need for 'user' in deps)
  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setUser(parsed.user || externalUser || null);
        setExpiry(parsed.expiry || '');
        setFetching(parsed.fetching || false);
        setOptionChain(parsed.optionChain || []);
        setAnalytics(parsed.analytics || {});
      } catch {}
    }
  }, [externalUser]);

  // Save to localStorage on state change
  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify({ user, expiry, fetching, optionChain, analytics }));
  }, [user, expiry, fetching, optionChain, analytics]);

  // Fetch option chain, only fetch analytics if data changed
  const fetchOptionChain = useCallback(async () => {
    if (!user || !expiry) return;
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/option-chain?user=${user}&expiry=${expiry}`);
      if (!res.ok) throw new Error('Failed to fetch option chain');
      const json = await res.json();
      const newStrikes = json.strikes || [];
      const newStrikesString = JSON.stringify(newStrikes);
      if (lastOptionChainRef.current !== newStrikesString) {
        setOptionChain(newStrikes);
        lastOptionChainRef.current = newStrikesString;
        fetchAnalytics(); // Only fetch analytics if option chain changed
      }
    } catch (e) {
      setError(e.message);
    }
  }, [user, expiry, fetchAnalytics]);

  // Polling logic
  useEffect(() => {
    if (!fetching || !user || !expiry) return;
    fetchOptionChain(); // Fetch immediately
    intervalRef.current = setInterval(fetchOptionChain, 5000);
    return () => clearInterval(intervalRef.current);
  }, [fetching, user, expiry, fetchOptionChain]);

  // Auto-resume fetching after reload if needed
  useEffect(() => {
    if (fetching && user && expiry) {
      startFetching(user, expiry);
    }
    // eslint-disable-next-line
  }, []);

  // Start/stop fetching
  const startFetching = (u, e) => {
    setUser(u);
    setExpiry(e);
    setFetching(true);
  };
  const stopFetching = () => {
    setFetching(false);
    clearInterval(intervalRef.current);
  };

  return (
    <OptionChainContext.Provider value={{
      user, setUser,
      expiry, setExpiry,
      fetching, startFetching, stopFetching,
      optionChain, analytics, error,
      fetchOptionChain, fetchAnalytics
    }}>
      {children}
    </OptionChainContext.Provider>
  );
} 