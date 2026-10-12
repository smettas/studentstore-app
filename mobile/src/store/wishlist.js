import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { wishlistApi } from '../services/wishlistApi';
import { useAuth } from './auth';
const Context = createContext(null);
export function WishlistProvider({ children }) {
  const { isAuthenticated, sessionVersion } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const refresh = useCallback(async () => {
    if (!isAuthenticated) { setData(null); return null; }
    setLoading(true);
    try { const result = await wishlistApi.get(); setData(result); return result; }
    finally { setLoading(false); }
  }, [isAuthenticated]);
  useEffect(() => { setData(null); }, [sessionVersion]);
  const value = useMemo(() => ({ data, loading, refresh }), [data, loading, refresh]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useWishlist() {
  const context = useContext(Context);
  if (!context) throw new Error('useWishlist must be used inside WishlistProvider');
  return context;
}
