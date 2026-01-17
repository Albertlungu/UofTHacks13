import React, { useEffect, useState, useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

// Avatar States: IDLE, LISTENING, THINKING, SPEAKING
function Avatar3D({ state, position, scale = 2.0 }) {
  const group = useRef();
  const { scene, animations } = useGLTF('http://localhost:5000/assets/models/chibi.glb');
  const { actions } = useAnimations(animations, group);

  const currentAnimationIndex = useRef(0);
  const animationChangeInterval = useRef(null);
  const stateRef = useRef(state);

  // Update state ref
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // Animation management based on state
  useEffect(() => {
    if (!actions) return;

    const actionKeys = Object.keys(actions);
    if (actionKeys.length === 0) return;

    // Stop all animations
    actionKeys.forEach(key => {
      if (actions[key]) actions[key].stop();
    });

    // Clear any existing intervals
    if (animationChangeInterval.current) {
      clearInterval(animationChangeInterval.current);
      animationChangeInterval.current = null;
    }

    if (state === 'SPEAKING') {
      // SPEAKING: Active mouth animations, cycling
      const firstAction = actions[actionKeys[0]];
      if (firstAction) {
        firstAction.reset();
        firstAction.setLoop(THREE.LoopRepeat);
        firstAction.timeScale = 1.2; // Slightly faster
        firstAction.play();
      }

      // Cycle through animations
      currentAnimationIndex.current = 0;
      animationChangeInterval.current = setInterval(() => {
        if (stateRef.current !== 'SPEAKING') return;

        currentAnimationIndex.current = (currentAnimationIndex.current + 1) % actionKeys.length;
        const nextKey = actionKeys[currentAnimationIndex.current];
        const nextAction = actions[nextKey];

        if (nextAction) {
          actionKeys.forEach(key => {
            if (key !== nextKey && actions[key]) {
              actions[key].fadeOut(0.3);
            }
          });

          nextAction.reset();
          nextAction.fadeIn(0.3);
          nextAction.setLoop(THREE.LoopRepeat);
          nextAction.timeScale = 1.2;
          nextAction.play();
        }
      }, 2500);

    } else if (state === 'THINKING') {
      // THINKING: Slow looping animation, intentional silence
      const firstAction = actions[actionKeys[0]];
      if (firstAction) {
        firstAction.reset();
        firstAction.setLoop(THREE.LoopRepeat);
        firstAction.timeScale = 0.4; // Much slower
        firstAction.play();
      }

    } else if (state === 'LISTENING') {
      // LISTENING: Subtle animation, attentive
      const firstAction = actions[actionKeys[0]];
      if (firstAction) {
        firstAction.reset();
        firstAction.setLoop(THREE.LoopRepeat);
        firstAction.timeScale = 0.6;
        firstAction.play();
      }

    } else {
      // IDLE: Minimal movement, observing
      // No animations playing, just procedural motion
    }

    return () => {
      if (animationChangeInterval.current) {
        clearInterval(animationChangeInterval.current);
      }
    };
  }, [state, actions]);

  // Procedural animations based on state
  useFrame((state) => {
    if (!group.current) return;

    const time = state.clock.elapsedTime;
    const currentState = stateRef.current;

    // VERY SMOOTH position tracking - slower lerp for natural motion
    if (position) {
      group.current.position.x = THREE.MathUtils.lerp(
        group.current.position.x,
        position.x,
        0.08  // Slower = smoother following
      );
      group.current.position.y = THREE.MathUtils.lerp(
        group.current.position.y,
        position.y,
        0.08
      );
    }

    if (currentState === 'IDLE') {
      // IDLE: Subtle breathing, occasional eye movement
      const breathe = Math.sin(time * 1.2) * 0.01;
      group.current.position.z = -0.2 + breathe;

      const subtleRotation = Math.sin(time * 0.2) * 0.02;
      group.current.rotation.y = subtleRotation;

    } else if (currentState === 'LISTENING') {
      // LISTENING: Head tilt, attentive posture
      const breathe = Math.sin(time * 1.5) * 0.008;
      group.current.position.z = -0.1 + breathe;

      const headTilt = Math.sin(time * 0.3) * 0.06;
      group.current.rotation.z = headTilt;
      group.current.rotation.y = 0.1;  // Slight lean toward user

    } else if (currentState === 'THINKING') {
      // THINKING: Slow, contemplative motion
      const slowFloat = Math.sin(time * 0.4) * 0.01;
      group.current.position.z = -0.15 + slowFloat;

      const slowRotation = Math.sin(time * 0.25) * 0.04;
      group.current.rotation.y = slowRotation;

    } else if (currentState === 'SPEAKING') {
      // SPEAKING: Energetic but controlled
      const bounce = Math.sin(time * 4) * 0.01;
      group.current.position.z = -0.1 + bounce;

      const activeRotation = Math.sin(time * 0.3) * 0.03;
      group.current.rotation.y = activeRotation;
    }
  });

  // Semi-transparent rendering
  useEffect(() => {
    if (scene) {
      scene.traverse((child) => {
        if (child.isMesh) {
          child.material.transparent = true;
          child.material.opacity = 0.85;
        }
      });
    }
  }, [scene]);

  return (
    <group ref={group} position={[0, -1, 0]} scale={scale}>
      <primitive object={scene} />

      {/* State-specific lighting */}
      <pointLight position={[3, 3, 3]} intensity={1.0} color="#ffffff" />
      <pointLight position={[-3, 2, 2]} intensity={0.6} color="#ffffff" />

      {state === 'LISTENING' && (
        <pointLight
          position={[0, 1, 2]}
          intensity={0.8}
          color="#4ecdc4"
          distance={4}
        />
      )}

      {state === 'THINKING' && (
        <pointLight
          position={[0, 2, 2]}
          intensity={1.0}
          color="#9b59b6"
          distance={4}
        />
      )}

      {state === 'SPEAKING' && (
        <pointLight
          position={[0, 0, 2]}
          intensity={1.5}
          color="#ff4444"
          distance={4}
        />
      )}
    </group>
  );
}

function FallbackAvatar({ state, position }) {
  const meshRef = useRef();
  const mouthRef = useRef();

  useFrame((state) => {
    if (meshRef.current && position) {
      meshRef.current.position.x = THREE.MathUtils.lerp(
        meshRef.current.position.x,
        position.x,
        0.02
      );
      meshRef.current.position.y = THREE.MathUtils.lerp(
        meshRef.current.position.y,
        position.y,
        0.02
      );
    }
  });

  const stateColors = {
    IDLE: "#4ecdc4",
    LISTENING: "#4ecdc4",
    THINKING: "#9b59b6",
    SPEAKING: "#ff4444"
  };

  return (
    <group>
      <mesh ref={meshRef} position={[0, 0, 0]}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshStandardMaterial
          color={stateColors[state] || "#4ecdc4"}
          transparent
          opacity={0.85}
          emissive={stateColors[state] || "#4ecdc4"}
          emissiveIntensity={0.4}
        />
      </mesh>

      <mesh position={[-0.12, 0.1, 0.35]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="black" />
      </mesh>

      <mesh position={[0.12, 0.1, 0.35]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="black" />
      </mesh>

      <mesh ref={mouthRef} position={[0, -0.08, 0.35]}>
        <boxGeometry args={[0.2, 0.06, 0.05]} />
        <meshStandardMaterial color="black" />
      </mesh>
    </group>
  );
}

function LoadingAvatar() {
  return (
    <mesh>
      <sphereGeometry args={[0.3, 16, 16]} />
      <meshStandardMaterial color="#4CAF50" wireframe />
    </mesh>
  );
}

function AvatarWithErrorBoundary({ state, position }) {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return <FallbackAvatar state={state} position={position} />;
  }

  return (
    <Suspense fallback={<LoadingAvatar />}>
      <ErrorBoundary onError={() => setHasError(true)}>
        <Avatar3D state={state} position={position} scale={2.0} />
      </ErrorBoundary>
    </Suspense>
  );
}

class ErrorBoundary extends React.Component {
  componentDidCatch(error) {
    console.error('Avatar error:', error.message);
    this.props.onError();
  }

  render() {
    return this.props.children;
  }
}

function Scene({ avatarState, faceData }) {
  const [avatarPosition, setAvatarPosition] = useState({ x: 0, y: 0, z: 0 });

  useEffect(() => {
    if (faceData) {
      // Normalize face position to -1 to 1 range
      const normX = (faceData.center_x - 640) / 640;
      const normY = -(faceData.center_y - 360) / 360;

      // Avatar follows face position smoothly (stays near face, slightly offset)
      setAvatarPosition({
        x: normX * 1.5,    // Direct follow, no extra offset
        y: normY * 1.2,    // Vertical follow
        z: 0
      });
    }
  }, [faceData]);

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1.0} castShadow />
      <hemisphereLight args={['#87CEEB', '#1a1a1a', 0.7]} />

      <AvatarWithErrorBoundary state={avatarState} position={avatarPosition} />

      <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={45} />
    </>
  );
}

function App() {
  const [faceData, setFaceData] = useState(null);
  const [speaking, setSpeaking] = useState(false);
  const [audioAvailable, setAudioAvailable] = useState(false);
  const [currentVolume, setCurrentVolume] = useState(0);
  const [threshold, setThreshold] = useState(0);
  const [show3D, setShow3D] = useState(true);
  const [avatarState, setAvatarState] = useState('IDLE');

  // Determine avatar state based on conditions
  useEffect(() => {
    if (speaking) {
      setAvatarState('SPEAKING');
    } else if (faceData) {
      // If face detected but not speaking = LISTENING
      setAvatarState('LISTENING');
    } else {
      setAvatarState('IDLE');
    }
  }, [speaking, faceData]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:5000/face_data');
        const data = await res.json();
        if (data.faces && data.faces.length > 0) {
          setFaceData(data.faces[0]);
        } else {
          setFaceData(null);
        }
      } catch (err) {
        // Silent fail
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:5000/speaking_status');
        const data = await res.json();

        setSpeaking(data.is_speaking);
        setAudioAvailable(data.audio_available);
        setCurrentVolume(data.current_volume || 0);
        setThreshold(data.threshold || 5);
      } catch (err) {
        // Silent fail
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const handleManualToggle = async () => {
    try {
      await fetch('http://localhost:5000/toggle_speaking', { method: 'POST' });
    } catch (err) {
      console.error('Error toggling:', err);
    }
  };

  const volumePercent = Math.min((currentVolume / threshold) * 100, 100);

  const stateColors = {
    IDLE: '#666',
    LISTENING: '#4ecdc4',
    THINKING: '#9b59b6',
    SPEAKING: '#ff4444'
  };

  const stateLabels = {
    IDLE: 'IDLE',
    LISTENING: 'LISTENING',
    THINKING: 'THINKING',
    SPEAKING: 'SPEAKING'
  };

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#000000',
      fontFamily: '"Segoe UI", Arial, sans-serif',
      overflow: 'hidden'
    }}>
      <h1 style={{
        color: '#ffffff',
        marginBottom: '20px',
        fontSize: '2.5rem',
        fontWeight: '600',
        letterSpacing: '1px',
        textTransform: 'uppercase'
      }}>
        AI Companion
      </h1>

      <div style={{
        position: 'relative',
        width: '1280px',
        height: '720px',
        backgroundColor: '#000',
        overflow: 'hidden',
        border: '1px solid #333'
      }}>
        {/* HIGH QUALITY Camera Feed */}
        <img
          src="http://localhost:5000/video_feed"
          alt="Camera Feed"
          style={{
            width: '1280px',
            height: '720px',
            objectFit: 'cover',
            display: 'block',
            position: 'absolute',
            top: 0,
            left: 0,
            zIndex: 1,
            opacity: 1.0,  // Changed from 0.7 to full opacity
            imageRendering: 'crisp-edges',  // Use crisp rendering
            filter: 'brightness(1.0) contrast(1.1)',  // Slight contrast boost
            WebkitImageRendering: 'crisp-edges'  // For Safari
          }}
        />

        {show3D && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 2,
            pointerEvents: 'none'
          }}>
            <Canvas shadows>
              <Scene avatarState={avatarState} faceData={faceData} />
            </Canvas>
          </div>
        )}

        {/* Minimal Status Bar */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          background: 'rgba(0,0,0,0.9)',
          color: '#ffffff',
          padding: '12px 20px',
          zIndex: 3,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #333',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          <div style={{ display: 'flex', gap: '25px' }}>
            <span>
              AUDIO: <span style={{ color: audioAvailable ? '#4CAF50' : '#666' }}>
                {audioAvailable ? 'ON' : 'OFF'}
              </span>
            </span>
            <span>
              FACE: <span style={{ color: faceData ? '#4CAF50' : '#666' }}>
                {faceData ? 'DETECTED' : 'NONE'}
              </span>
            </span>
            <span>
              STATE: <span style={{ color: stateColors[avatarState] }}>
                {stateLabels[avatarState]}
              </span>
            </span>
          </div>

          <button
            onClick={() => setShow3D(!show3D)}
            style={{
              padding: '5px 14px',
              background: show3D ? '#4CAF50' : '#444',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '11px',
              textTransform: 'uppercase'
            }}
          >
            3D {show3D ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Volume Indicator */}
        <div style={{
          position: 'absolute',
          top: '50px',
          left: '20px',
          width: '200px',
          zIndex: 3
        }}>
          <div style={{
            fontSize: '10px',
            color: '#aaa',
            marginBottom: '4px',
            fontFamily: 'monospace'
          }}>
            VOL: {currentVolume.toFixed(0)} / {threshold}
          </div>
          <div style={{
            width: '100%',
            height: '3px',
            background: '#222',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${volumePercent}%`,
              height: '100%',
              background: speaking ? '#ff4444' : '#4CAF50',
              transition: 'width 0.1s'
            }}></div>
          </div>
        </div>

        {!audioAvailable && (
          <button
            onClick={handleManualToggle}
            style={{
              position: 'absolute',
              bottom: '70px',
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '10px 25px',
              background: speaking ? '#ff4444' : '#4CAF50',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              zIndex: 3,
              fontSize: '13px',
              textTransform: 'uppercase'
            }}
          >
            {speaking ? 'STOP' : 'START'}
          </button>
        )}

        {/* Status Message */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: `rgba(${avatarState === 'SPEAKING' ? '255,68,68' : avatarState === 'LISTENING' ? '78,205,196' : '102,102,102'}, 0.95)`,
          color: '#ffffff',
          padding: '10px',
          zIndex: 3,
          textAlign: 'center',
          fontWeight: '600',
          fontSize: '12px',
          borderTop: '1px solid',
          borderColor: stateColors[avatarState],
          textTransform: 'uppercase',
          letterSpacing: '1px'
        }}>
          {stateLabels[avatarState]}
        </div>
      </div>
    </div>
  );
}

import React from "react";
import BlockBuilder3D from "./BlockBuilder3D";

function App() {
    return (
        <div className="App">
            <BlockBuilder3D />
        </div>
    );
}

export default App;
