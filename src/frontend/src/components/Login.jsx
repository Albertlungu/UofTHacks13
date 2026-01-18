import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card } from './ui/card';

export default function Login({ onSwitchToSignup }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const { login, loading } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    
    if (!username.trim() || !password) {
      setLocalError('Please fill in all fields');
      return;
    }

    const result = await login(username, password);
    if (!result.success) {
      setLocalError(result.error);
    }
  };

  return (
    <Card className="w-full max-w-md p-10 backdrop-blur-sm bg-white/80 border-neutral-200/50 shadow-xl">
      <div className="space-y-8">
        <div className="space-y-3 text-center">
          <h1 className="text-3xl font-light tracking-tight text-neutral-900">Welcome back</h1>
          <p className="text-sm text-neutral-500">Enter your credentials to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-neutral-700 font-normal">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-neutral-700 font-normal">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
              className="h-12 text-base"
            />
          </div>

          {localError && (
            <div className="text-sm text-red-600 bg-red-50/80 px-4 py-3 rounded-lg border border-red-100">
              {localError}
            </div>
          )}

          <Button type="submit" className="w-full h-12 text-base font-normal" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-neutral-200"></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-neutral-500">or</span>
          </div>
        </div>

        <div className="text-center text-sm">
          <span className="text-neutral-500">Don't have an account?</span>{' '}
          <button
            onClick={onSwitchToSignup}
            className="text-neutral-900 font-medium hover:text-neutral-700 transition-colors"
            disabled={loading}
          >
            Sign up
          </button>
        </div>
      </div>
    </Card>
  );
}
