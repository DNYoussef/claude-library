/**
 * React Auth Context
 * @module react-auth/AuthContext
 */
import { createContext } from 'react';
import type { AuthContextValue } from './types';

export const AuthContext = createContext<AuthContextValue | null>(null);
export default AuthContext;
