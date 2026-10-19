'use client';

import { usePathname, useRouter } from 'next/navigation';
import React from 'react';

export type AuthContextType = {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string;
  role_codes: string[];
  status: string;
};

const AuthContext = React.createContext<{
  user: AuthContextType | null;
  changeUser: (user: AuthContextType | null) => void;
    } | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthContextType | null>({
    id: '1',
    email: 'e',
    full_name: 'Admin',
    avatar_url: '',
    role_codes: ['ADMIN', 'USER'],
    status: 'ACTIVE',
  });
  const pathname = usePathname();
  const router = useRouter();

  const changeUser = (user: AuthContextType | null) => {
    setUser(user);
  };

  React.useEffect(() => {
    // Simulate fetching user data from an API or local storage
    if (pathname.startsWith('/auth')) {
      return;
    }
    const fetchUser = async () => {
      setTimeout(() => {
        setUser({
          id: '1',
          email: 'e',
          full_name: 'Admin',
          avatar_url: '',
          role_codes: ['ADMIN', 'USER'],
          status: 'ACTIVE',
        });
      }, 1000);
    };
    fetchUser();
  }, [pathname]);

  return (
    <AuthContext.Provider
      value={{
        user,
        changeUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
