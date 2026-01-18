import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card } from './ui/card';

export default function Signup({ onSwitchToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const { signup, loading } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (!username.trim() || !password) {
      setLocalError('Username and password are required');
      return;
    }

    if (username.length < 3) {
      setLocalError('Username must be at least 3 characters');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    const result = await signup(username, password, email);
    if (!result.success) {
      setLocalError(result.error);
    }
  };

  return (
    <Card className="w-full max-w-md p-10 backdrop-blur-sm bg-white/80 border-neutral-200/50 shadow-xl">
      <div className="space-y-8">
        <div className="space-y-3 text-center">
          <h1 className="text-3xl font-light tracking-tight text-neutral-900">Create account</h1>
          <p className="text-sm text-neutral-500">Get started with a new account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-neutral-700 font-normal">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-neutral-700 font-normal">Email <span className="text-neutral-400">(optional)</span></Label>
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-neutral-700 font-normal">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="new-password"
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-neutral-700 font-normal">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              autoComplete="new-password"
              className="h-12 text-base"
            />
          </div>

          {localError && (
            <div className="text-sm text-red-600 bg-red-50/80 px-4 py-3 rounded-lg border border-red-100">
              {localError}
            </div>
          )}

          <Button type="submit" className="w-full h-12 text-base font-normal mt-6" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
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
          <span className="text-neutral-500">Already have an account?</span>{' '}
          <button
            onClick={onSwitchToLogin}
            className="text-neutral-900 font-medium hover:text-neutral-700 transition-colors"
            disabled={loading}
          >
            Login
          </button>
        </div>
      </div>
    </Card>
  );
}
