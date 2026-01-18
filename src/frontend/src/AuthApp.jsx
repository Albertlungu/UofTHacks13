import { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Signup from './components/Signup';
import Profile from './components/Profile';

function AuthApp() {
  const [view, setView] = useState('login');
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 flex items-center justify-center p-6">
        <Profile />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 flex flex-col items-center justify-center p-6">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">Identity</h1>
        <p className="text-sm text-neutral-500">Secure authentication system</p>
      </div>
      {view === 'login' ? (
        <Login onSwitchToSignup={() => setView('signup')} />
      ) : (
        <Signup onSwitchToLogin={() => setView('login')} />
      )}
    </div>
  );
}

export default function AuthAppWrapper() {
  return (
    <AuthProvider>
      <AuthApp />
    </AuthProvider>
  );
}
