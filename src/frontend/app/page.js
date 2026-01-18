"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";

const AUTH_API_BASE =
  process.env.NEXT_PUBLIC_AUTH_API_BASE || "http://localhost:5001/api/auth";
const CORE_API_BASE =
  process.env.NEXT_PUBLIC_CORE_API_BASE || "http://localhost:5000";

export default function Page() {
  const [authView, setAuthView] = useState("login");
  const [authToken, setAuthToken] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [profilePassword, setProfilePassword] = useState("");
  const [profileText, setProfileText] = useState("{");
  const [profileStatus, setProfileStatus] = useState("");
  const [profileError, setProfileError] = useState("");

  const [faceData, setFaceData] = useState(null);
  const [speaking, setSpeaking] = useState(false);
  const [audioAvailable, setAudioAvailable] = useState(false);
  const [currentVolume, setCurrentVolume] = useState(0);
  const [threshold, setThreshold] = useState(0);
  const [cameraOnline, setCameraOnline] = useState(true);
  const [audioOnline, setAudioOnline] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedToken = window.localStorage.getItem("token");
    if (storedToken) {
      setAuthToken(storedToken);
    }
  }, []);

  useEffect(() => {
    if (!authToken) return;
    fetchCurrentUser();
  }, [authToken]);

  useEffect(() => {
    const faceInterval = setInterval(() => {
      fetchFaceData();
    }, 1000);

    const speakingInterval = setInterval(() => {
      fetchSpeakingStatus();
    }, 1000);

    return () => {
      clearInterval(faceInterval);
      clearInterval(speakingInterval);
    };
  }, []);

  const volumePercent = useMemo(() => {
    if (!threshold || threshold <= 0) return 0;
    return Math.min((currentVolume / threshold) * 100, 100);
  }, [currentVolume, threshold]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${AUTH_API_BASE}/me`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (!response.ok) {
        handleLogout();
        return;
      }
      const data = await response.json();
      setAuthUser(data);
    } catch (error) {
      setAuthError("Unable to reach the auth service.");
    }
  };

  const handleSignup = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError("");

    try {
      const response = await fetch(`${AUTH_API_BASE}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, email }),
      });
      const data = await response.json();

      if (!response.ok) {
        setAuthError(data.error || "Signup failed.");
        return;
      }

      if (typeof window !== "undefined") {
        window.localStorage.setItem("token", data.token);
      }
      setAuthToken(data.token);
      setAuthUser({ username: data.username });
      setUsername("");
      setEmail("");
      setPassword("");
    } catch (error) {
      setAuthError("Unable to reach the auth service.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError("");

    try {
      const response = await fetch(`${AUTH_API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();

      if (!response.ok) {
        setAuthError(data.error || "Login failed.");
        return;
      }

      if (typeof window !== "undefined") {
        window.localStorage.setItem("token", data.token);
      }
      setAuthToken(data.token);
      setAuthUser({ username: data.username, user_id: data.user_id });
      setUsername("");
      setPassword("");
    } catch (error) {
      setAuthError("Unable to reach the auth service.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("token");
    }
    setAuthToken(null);
    setAuthUser(null);
    setProfileStatus("");
    setProfileError("");
  };

  const handleGetProfile = async (event) => {
    event.preventDefault();
    setProfileStatus("");
    setProfileError("");

    try {
      const response = await fetch(`${AUTH_API_BASE}/profile`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password: profilePassword, action: "get" }),
      });
      const data = await response.json();

      if (!response.ok) {
        setProfileError(data.error || "Unable to fetch profile.");
        return;
      }

      setProfileText(JSON.stringify(data.profile, null, 2));
      setProfileStatus("Profile loaded.");
    } catch (error) {
      setProfileError("Unable to reach the auth service.");
    }
  };

  const handleUpdateProfile = async (event) => {
    event.preventDefault();
    setProfileStatus("");
    setProfileError("");

    let parsedProfile;
    try {
      parsedProfile = JSON.parse(profileText || "{}");
    } catch (error) {
      setProfileError("Profile JSON is not valid.");
      return;
    }

    try {
      const response = await fetch(`${AUTH_API_BASE}/profile`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password: profilePassword, profile: parsedProfile }),
      });
      const data = await response.json();

      if (!response.ok) {
        setProfileError(data.error || "Unable to update profile.");
        return;
      }

      setProfileStatus(data.message || "Profile updated.");
    } catch (error) {
      setProfileError("Unable to reach the auth service.");
    }
  };

  const fetchFaceData = async () => {
    try {
      const response = await fetch(`${CORE_API_BASE}/face_data`);
      if (!response.ok) {
        setCameraOnline(false);
        return;
      }
      const data = await response.json();
      setCameraOnline(true);
      if (data.faces && data.faces.length > 0) {
        setFaceData(data.faces[0]);
      } else {
        setFaceData(null);
      }
    } catch (error) {
      setCameraOnline(false);
    }
  };

  const fetchSpeakingStatus = async () => {
    try {
      const response = await fetch(`${CORE_API_BASE}/speaking_status`);
      if (!response.ok) {
        setAudioOnline(false);
        return;
      }
      const data = await response.json();
      setAudioOnline(true);
      setSpeaking(Boolean(data.is_speaking));
      setAudioAvailable(Boolean(data.audio_available));
      setCurrentVolume(data.current_volume || 0);
      setThreshold(data.threshold || 0);
    } catch (error) {
      setAudioOnline(false);
    }
  };

  const handleToggleSpeaking = async () => {
    try {
      await fetch(`${CORE_API_BASE}/toggle_speaking`, { method: "POST" });
    } catch (error) {
      setAudioOnline(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-12">
        <header className="space-y-2">
          <p className="text-sm text-muted-foreground">Identity and camera control</p>
          <h1 className="text-3xl font-semibold tracking-tight">Identity Console</h1>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Authentication</CardTitle>
                <CardDescription>Connect to the identity API.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {authUser ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Signed in</p>
                        <p className="text-base font-medium">
                          {authUser.username || authUser.email || "User"}
                        </p>
                      </div>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <Button variant="outline" onClick={handleLogout}>
                      Sign out
                    </Button>
                  </div>
                ) : (
                  <form
                    className="space-y-4"
                    onSubmit={authView === "login" ? handleLogin : handleSignup}
                  >
                    <div className="grid gap-2">
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={username}
                        onChange={(event) => setUsername(event.target.value)}
                        autoComplete="username"
                        required
                      />
                    </div>

                    {authView === "signup" ? (
                      <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={email}
                          onChange={(event) => setEmail(event.target.value)}
                          autoComplete="email"
                        />
                      </div>
                    ) : null}

                    <div className="grid gap-2">
                      <Label htmlFor="password">Password</Label>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        autoComplete={authView === "login" ? "current-password" : "new-password"}
                        required
                      />
                    </div>

                    {authError ? (
                      <p className="text-sm text-destructive">{authError}</p>
                    ) : null}

                    <div className="flex flex-wrap gap-3">
                      <Button type="submit" disabled={authLoading}>
                        {authView === "login" ? "Sign in" : "Create account"}
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() =>
                          setAuthView(authView === "login" ? "signup" : "login")
                        }
                      >
                        {authView === "login"
                          ? "Switch to sign up"
                          : "Switch to sign in"}
                      </Button>
                    </div>
                  </form>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Profile</CardTitle>
                <CardDescription>Read or update the profile payload.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="profile-password">Password</Label>
                  <Input
                    id="profile-password"
                    type="password"
                    value={profilePassword}
                    onChange={(event) => setProfilePassword(event.target.value)}
                    placeholder="Required for profile actions"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="profile-json">Profile JSON</Label>
                  <Textarea
                    id="profile-json"
                    value={profileText}
                    onChange={(event) => setProfileText(event.target.value)}
                  />
                </div>
                {profileError ? (
                  <p className="text-sm text-destructive">{profileError}</p>
                ) : null}
                {profileStatus ? (
                  <p className="text-sm text-muted-foreground">{profileStatus}</p>
                ) : null}
              </CardContent>
              <CardFooter className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  onClick={handleGetProfile}
                  disabled={!authUser || !profilePassword}
                >
                  Load profile
                </Button>
                <Button
                  onClick={handleUpdateProfile}
                  disabled={!authUser || !profilePassword}
                >
                  Update profile
                </Button>
              </CardFooter>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>System status</CardTitle>
                <CardDescription>Live data from camera and audio endpoints.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Camera</p>
                    <p className="text-sm text-muted-foreground">
                      {cameraOnline ? "Online" : "Unavailable"}
                    </p>
                  </div>
                  <Badge variant={cameraOnline ? "secondary" : "destructive"}>
                    {cameraOnline ? "Connected" : "Offline"}
                  </Badge>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Audio</p>
                    <p className="text-sm text-muted-foreground">
                      {audioOnline ? "Online" : "Unavailable"}
                    </p>
                  </div>
                  <Badge variant={audioOnline ? "secondary" : "destructive"}>
                    {audioOnline ? "Connected" : "Offline"}
                  </Badge>
                </div>

                <div className="rounded-md border border-border bg-muted/30 p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Speaking</p>
                    <Badge variant={speaking ? "destructive" : "outline"}>
                      {speaking ? "Active" : "Idle"}
                    </Badge>
                  </div>
                  <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                    <p>Audio available: {audioAvailable ? "Yes" : "No"}</p>
                    <p>Volume: {currentVolume.toFixed(2)}</p>
                    <p>Threshold: {threshold.toFixed(2)}</p>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-border">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${volumePercent}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-md border border-border bg-muted/30 p-4">
                  <p className="text-sm font-medium">Face tracking</p>
                  <div className="mt-2 text-sm text-muted-foreground">
                    {faceData ? (
                      <ul className="space-y-1">
                        <li>Center X: {faceData.center_x?.toFixed(2)}</li>
                        <li>Center Y: {faceData.center_y?.toFixed(2)}</li>
                        <li>Width: {faceData.width?.toFixed(2)}</li>
                        <li>Height: {faceData.height?.toFixed(2)}</li>
                      </ul>
                    ) : (
                      <p>No face detected.</p>
                    )}
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" onClick={handleToggleSpeaking}>
                  Toggle speaking state
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Camera feed</CardTitle>
                <CardDescription>Live stream from the backend.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-md border border-border bg-muted">
                  <img
                    src={`${CORE_API_BASE}/video_feed`}
                    alt="Camera feed"
                    className="h-auto w-full"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Avatar system</CardTitle>
                <CardDescription>
                  3D avatar synchronized with face tracking and speaking status.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                  Launch the avatar overlay view for the live camera feed.
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  type="button"
                  onClick={() => window.open("/avatar", "_blank", "noopener,noreferrer")}
                >
                  Open avatar view
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>3D hand tracking</CardTitle>
                <CardDescription>
                  Launch the immersive 3D workspace powered by the hand tracking feed.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                  This view uses your camera and the hand tracking websocket to drive a 3D grid.
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  type="button"
                  onClick={() => window.open("/three", "_blank", "noopener,noreferrer")}
                >
                  Open 3D view in new tab
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
