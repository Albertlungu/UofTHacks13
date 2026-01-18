import React, { useEffect, useState, useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

// Avatar States: IDLE, LISTENING, THINKING, SPEAKING
function Avatar3D({ state, position, scale = 0.6 }) {
  const group = useRef();
  const { scene, animations } = useGLTF('http://localhost:5000/assets/models/droid.glb');
  const { actions } = useAnimations(animations, group);
  
  const stateRef = useRef(state);
  const positionRef = useRef(position);
  const timeOffsetRef = useRef(Math.random() * 1000); // Random start for variation

  // Update refs
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    positionRef.current = position;
  }, [position]);

    // Procedural animations and head rotation based on state
  useFrame((frameState) => {
    if (!group.current) return;

    const time = frameState.clock.elapsedTime + timeOffsetRef.current;
    const currentState = stateRef.current;
    const currentPosition = positionRef.current;

    // Smooth position tracking - Three.js does ALL the smoothing now
    if (currentPosition) {
      const targetX = currentPosition.x * 2.0;  // INCREASED from 0.5 to 2.0
      const targetY = currentPosition.y * 2.0;  // INCREASED from 0.5 to 2.0
      
      // Smooth lerp for stable movement
      group.current.position.x = THREE.MathUtils.lerp(
        group.current.position.x,
        targetX,
        0.12  // INCREASED from 0.08 for more responsive
      );
      group.current.position.y = THREE.MathUtils.lerp(  
        group.current.position.y,
        targetY,
        0.12  // INCREASED from 0.08 for more responsive
      );
    } else {
      // Return to center when no face
      group.current.position.x = THREE.MathUtils.lerp(group.current.position.x, 0, 0.05);
      group.current.position.y = THREE.MathUtils.lerp(group.current.position.y, 0, 0.05);
    }

    // Calculate head rotation based on face position (looking at user)
    let headRotationY = 0;
    let headRotationX = 0;

    if (currentPosition) {
      headRotationY = currentPosition.x * 0.9;  // More responsive
      headRotationX = -currentPosition.y * 0.5;
    }

    if (currentState === 'IDLE') {
      // IDLE: Gentle hovering motion for drone robot
      const hover = Math.sin(time * 1.2) * 0.15;
      group.current.position.y = hover;
      
      const sway = Math.sin(time * 0.5) * 0.05;
      group.current.position.z = sway;
      
      const lookAround = Math.sin(time * 0.3) * 0.15;
      group.current.rotation.y = headRotationY * 0.5 + lookAround;
      group.current.rotation.x = headRotationX * 0.5;
      
      const lean = Math.cos(time * 0.4) * 0.05;
      group.current.rotation.z = lean;
      
    } else if (currentState === 'LISTENING') {
      // LISTENING: Attentive, engaged posture
      group.current.position.z = 0.1 + Math.sin(time * 2) * 0.02;
      
      const attentiveNod = Math.sin(time * 1.8) * 0.12;
      group.current.rotation.y = headRotationY * 0.85 + attentiveNod * 0.3;
      group.current.rotation.x = headRotationX + attentiveNod;
      
      const engageTilt = Math.sin(time * 1.2) * 0.06;
      group.current.rotation.z = engageTilt;
      
    } else if (currentState === 'THINKING') {
      // THINKING: Contemplative, introspective motion
      const contemplation = Math.sin(time * 0.6) * 0.12;
      group.current.position.z = contemplation - 0.1;
      
      const thoughtfulTurn = Math.sin(time * 0.5) * 0.2;
      group.current.rotation.y = headRotationY * 0.4 + thoughtfulTurn;
      group.current.rotation.x = -0.25 + Math.sin(time * 0.4) * 0.1;
      
      const ponderTilt = Math.cos(time * 0.7) * 0.12;
      group.current.rotation.z = ponderTilt;
      
    } else if (currentState === 'SPEAKING') {
      // SPEAKING: Animated, engaging, expressive
      const bounce = Math.sin(time * 3.2) * 0.08;
      group.current.position.z = bounce + 0.05;
      
      const speechBob = Math.sin(time * 2.4) * 0.15;
      const gestureRotation = Math.sin(time * 1.8 + Math.PI/4) * 0.12;
      
      group.current.rotation.y = headRotationY * 0.9 + gestureRotation;
      group.current.rotation.x = headRotationX * 0.8 + speechBob * 0.15;
      
      const expressiveSway = Math.cos(time * 2.2) * 0.15;
      group.current.rotation.z = expressiveSway;
    }
  });

    // MUCH BRIGHTER lighting and material setup
  useEffect(() => {
    if (scene) {
      scene.traverse((child) => {
        if (child.isMesh) {
          // Make materials much brighter
          child.material.transparent = true;
          child.material.opacity = 1.0;  // Full opacity
          
          // AGGRESSIVE brightness boost
          if (child.material.emissive) {
            child.material.emissive.setHex(0x444444);  // Self-emission glow
            child.material.emissiveIntensity = 0.5;    // Strong self-emission
          }
          
          // Boost metallic/roughness for better light reflection
          if (child.material.metalness !== undefined) {
            child.material.metalness = 0.3;
          }
          if (child.material.roughness !== undefined) {
            child.material.roughness = 0.4;
          }
        }
      });
    }
  }, [scene]);

  return (
    <group ref={group} position={[0, -0.8, 0]} scale={scale}>
      <primitive object={scene} />
      
      {/* VERY BRIGHT LIGHTS - multiple sources */}
      <pointLight position={[5, 4, 4]} intensity={3.5} color="#ffffff" />
      <pointLight position={[-5, 4, 3]} intensity={3.0} color="#ffffff" />
      <pointLight position={[0, 0, 4]} intensity={2.8} color="#ffffff" />
      <pointLight position={[3, -1, 2]} intensity={2.5} color="#ffffff" />
      <pointLight position={[-3, -1, 2]} intensity={2.5} color="#ffffff" />
      
      {/* State-specific accent lighting */}
      {state === 'LISTENING' && (
        <pointLight 
          position={[0, 1.5, 2]} 
          intensity={2.0} 
          color="#4ecdc4" 
          distance={8}
        />
      )}
      
      {state === 'THINKING' && (
        <pointLight 
          position={[0, 2, 2]} 
          intensity={2.5} 
          color="#9b59b6" 
          distance={8}
        />
      )}
      
      {state === 'SPEAKING' && (
        <pointLight 
          position={[1, 0.5, 2]} 
          intensity={3.0} 
          color="#ff4444" 
          distance={8}
        />
      )}
    </group>
  );
}

function FallbackAvatar({ state, position }) {
  const meshRef = useRef();
  
  useFrame((state) => {
    if (meshRef.current && position) {
      meshRef.current.position.x = THREE.MathUtils.lerp(
        meshRef.current.position.x,
        position.x * 1.2 + 0.3,
        0.12
      );
      meshRef.current.position.y = THREE.MathUtils.lerp(
        meshRef.current.position.y,
        position.y * 0.8,
        0.12
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
          opacity={0.95}
          emissive={stateColors[state] || "#4ecdc4"}
          emissiveIntensity={0.5}
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
      
      <mesh position={[0, -0.08, 0.35]}>
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
        <Avatar3D state={state} position={position} scale={0.6} />
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
      const normX = -((faceData.center_x - 640) / 640);  // Add negative sign to mirror
      const normY = -(faceData.center_y - 360) / 360;
      
      // Pass normalized position for avatar to follow
      setAvatarPosition({ 
        x: normX,
        y: normY,
        z: 0 
      });
    } else {
      // Return to center when no face detected
      setAvatarPosition({ x: 0, y: 0, z: 0 });
    }
  }, [faceData]);

    return (
      <>
        {/* MAXIMUM AMBIENT for full visibility */}
        <ambientLight intensity={1.2} />
        <directionalLight position={[8, 10, 6]} intensity={1.8} castShadow />
        <directionalLight position={[-8, 8, 5]} intensity={1.2} castShadow />
        <hemisphereLight args={['#ffffff', '#888888', 1.0]} />
        
        {/* Additional fill lights for dark corners */}
        <pointLight position={[0, 5, 0]} intensity={2.0} color="#ffffff" />
        
        <AvatarWithErrorBoundary state={avatarState} position={avatarPosition} />
        
        {/* FIXED camera position - NO ZOOM */}
        <PerspectiveCamera makeDefault position={[0, 0, 5.5]} fov={50} />
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
        {/* Camera Feed - NO stretch */}
        <img
          src="http://localhost:5000/video_feed"
          alt="Camera Feed"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: 'block',
            position: 'absolute',
            top: 0,
            left: 0,
            zIndex: 1,
            transform: 'scale(1.0)'
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
            <Canvas 
                gl={{ 
                  alpha: true, 
                  antialias: true,
                  preserveDrawingBuffer: false 
                }}
                style={{ background: 'transparent' }}
              >
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

export default App;