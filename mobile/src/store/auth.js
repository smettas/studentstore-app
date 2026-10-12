import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../services/authApi';
import { clearTokens, getAccessToken, saveTokens } from '../utils/tokenStorage';

const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionVersion, setSessionVersion] = useState(0);
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (await getAccessToken()) {
          const profile = await authApi.profile();
          if (active) setUser(profile);
        }
      } catch (error) {
        // Keep tokens on transient network failures; only clear rejected sessions.
        if (error.status === 401 || error.status === 400 || error.message.startsWith('Session expired')) await clearTokens();
      } finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, []);
  const signIn = useCallback(async (mobile, otp) => {
    const result = await authApi.verifyOtp(mobile, otp);
    await saveTokens(result);
    setUser(result.user);
    setSessionVersion(v => v + 1);
    return result.user;
  }, []);
  const signOut = useCallback(async () => {
    await clearTokens(); setUser(null); setSessionVersion(v => v + 1);
  }, []);
  const value = useMemo(() => ({ user, loading, isAuthenticated: Boolean(user), sessionVersion, signIn, signOut }), [user, loading, sessionVersion, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
