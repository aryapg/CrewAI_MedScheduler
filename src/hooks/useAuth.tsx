import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { toast } from 'sonner';
import { authApi, setAuthToken, removeAuthToken, getUserData, setUserData, getAuthToken } from '@/lib/api-client';
import { useNavigate } from 'react-router-dom';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'patient' | 'doctor' | 'admin';
  phone?: string;
  specialty?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName: string, role?: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Load user from storage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = getAuthToken();
        const storedUser = getUserData();

        if (token && storedUser) {
          setUser(storedUser);
          
          // Verify token is still valid
          const result = await authApi.getCurrentUser();
          if (result.error) {
            // Token invalid, clear storage
            removeAuthToken();
            setUser(null);
          } else if (result.data) {
            // Update user data
            setUser(result.data);
            setUserData(result.data);
          }
        }
      } catch (error) {
        console.error('Error loading user:', error);
        removeAuthToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const signUp = async (email: string, password: string, fullName: string, role: string = 'patient') => {
    try {
      const result = await authApi.register(email, password, fullName, role);

      if (result.error) {
        throw new Error(result.error);
      }

      if (result.data) {
        // Store token and user data
        setAuthToken(result.data.access_token);
        setUser(result.data.user);
        setUserData(result.data.user);
        
      toast.success('Account created successfully!');
        
        // Navigate based on role
        setTimeout(() => {
          if (result.data!.user.role === 'patient') navigate('/patient');
          else if (result.data!.user.role === 'doctor') navigate('/doctor');
          else if (result.data!.user.role === 'admin') navigate('/admin');
          else navigate('/patient');
        }, 500);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to sign up');
      throw error;
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const result = await authApi.login(email, password);

      if (result.error) {
        throw new Error(result.error);
      }

      if (result.data) {
        // Store token and user data
        setAuthToken(result.data.access_token);
        setUser(result.data.user);
        setUserData(result.data.user);
        
      toast.success('Signed in successfully!');
        
        // Navigate based on role
        setTimeout(() => {
          if (result.data!.user.role === 'patient') navigate('/patient');
          else if (result.data!.user.role === 'doctor') navigate('/doctor');
          else if (result.data!.user.role === 'admin') navigate('/admin');
          else navigate('/patient');
        }, 500);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to sign in');
      throw error;
    }
  };

  const signOut = async () => {
    try {
      removeAuthToken();
      setUser(null);
      toast.success('Signed out successfully');
      navigate('/auth');
    } catch (error: any) {
      toast.error(error.message || 'Failed to sign out');
    }
  };

  const refreshUser = async () => {
    try {
      const result = await authApi.getCurrentUser();
      if (result.data) {
        setUser(result.data);
        setUserData(result.data);
      }
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
