import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card } from './ui/card';

export default function Profile() {
  const { user, logout, getProfile, updateProfile } = useAuth();
  const [password, setPassword] = useState('');
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLoadProfile = async () => {
    setError('');
    setSuccess('');
    
    if (!password) {
      setError('Password is required to decrypt profile');
      return;
    }

    setLoading(true);
    const result = await getProfile(password);
    setLoading(false);

    if (result.success) {
      setProfile(result.profile);
      setEditedProfile(JSON.stringify(result.profile, null, 2));
      setSuccess('Profile loaded successfully');
    } else {
      setError(result.error);
    }
  };

  const handleSaveProfile = async () => {
    setError('');
    setSuccess('');

    try {
      const parsedProfile = JSON.parse(editedProfile);
      setLoading(true);
      const result = await updateProfile(password, parsedProfile);
      setLoading(false);

      if (result.success) {
        setProfile(parsedProfile);
        setIsEditing(false);
        setSuccess('Profile updated successfully');
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Invalid JSON format');
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl space-y-6">
      <Card className="p-10 backdrop-blur-sm bg-white/80 border-neutral-200/50 shadow-xl">
        <div className="space-y-8">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-6">
            <div>
              <h1 className="text-3xl font-light tracking-tight text-neutral-900">Profile</h1>
              <p className="text-sm text-neutral-500 mt-2">
                {user?.username}
              </p>
            </div>
            <Button variant="outline" onClick={logout} className="h-10 px-6">
              Logout
            </Button>
          </div>

          <div className="space-y-5">
            <div className="space-y-3">
              <Label htmlFor="password" className="text-neutral-700 font-normal">Password <span className="text-neutral-400 text-xs">(required for decryption)</span></Label>
              <div className="flex gap-3">
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  autoComplete="current-password"
                  className="h-11 text-base"
                />
                <Button 
                  onClick={handleLoadProfile} 
                  disabled={loading || !password}
                  className="h-11 px-6 whitespace-nowrap"
                >
                  {loading ? 'Loading...' : 'Load Profile'}
                </Button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50/80 px-4 py-3 rounded-lg border border-red-100">
                {error}
              </div>
            )}

            {success && (
              <div className="text-sm text-green-700 bg-green-50/80 px-4 py-3 rounded-lg border border-green-100">
                {success}
              </div>
            )}
          </div>
        </div>
      </Card>

      {profile && (
        <Card className="p-10 backdrop-blur-sm bg-white/80 border-neutral-200/50 shadow-xl">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-neutral-100 pb-5">
              <h2 className="text-2xl font-light text-neutral-900">Profile Data</h2>
              <div className="flex gap-3">
                {isEditing ? (
                  <>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setIsEditing(false);
                        setEditedProfile(JSON.stringify(profile, null, 2));
                      }}
                      disabled={loading}
                      className="h-10 px-5"
                    >
                      Cancel
                    </Button>
                    <Button 
                      onClick={handleSaveProfile}
                      disabled={loading}
                      className="h-10 px-5"
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </>
                ) : (
                  <Button onClick={() => setIsEditing(true)} className="h-10 px-5">
                    Edit Profile
                  </Button>
                )}
              </div>
            </div>

            {isEditing ? (
              <textarea
                className="w-full h-96 font-mono text-sm p-5 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-950 focus:border-transparent bg-neutral-50/50 resize-none"
                value={editedProfile}
                onChange={(e) => setEditedProfile(e.target.value)}
                disabled={loading}
              />
            ) : (
              <pre className="w-full p-5 bg-neutral-50/70 border border-neutral-200 rounded-lg overflow-auto text-sm font-mono">
                {JSON.stringify(profile, null, 2)}
              </pre>
            )}

            <div className="bg-neutral-50/50 border border-neutral-200 rounded-lg p-5">
              <p className="text-xs font-medium text-neutral-700 mb-2">Profile Structure</p>
              <div className="text-xs text-neutral-500 space-y-1.5">
                <p><span className="font-mono text-neutral-700">voice_profile</span> — Speech characteristics and patterns</p>
                <p><span className="font-mono text-neutral-700">mannerisms</span> — Communication style and preferences</p>
                <p><span className="font-mono text-neutral-700">preferences</span> — User settings and customizations</p>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
