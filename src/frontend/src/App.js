import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [faceData, setFaceData] = useState(null);
  const [speaking, setSpeaking] = useState(false);
  const [avatarFrame, setAvatarFrame] = useState(0);
  const [audioAvailable, setAudioAvailable] = useState(false);
  const [currentVolume, setCurrentVolume] = useState(0);
  const [threshold, setThreshold] = useState(0);

  const avatarImages = [
    'http://localhost:5000/assets/avatar/avatar_idle.png',
    'http://localhost:5000/assets/avatar/avatar_speaking_1.png',
    'http://localhost:5000/assets/avatar/avatar_speaking_2.png',
    'http://localhost:5000/assets/avatar/avatar_speaking_3.png'
  ];

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
        console.error('Error fetching face data:', err);
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
        console.error('Error fetching speaking status:', err);
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const handleManualToggle = async () => {
    try {
      await fetch('http://localhost:5000/toggle_speaking', { method: 'POST' });
    } catch (err) {
      console.error('Error toggling speaking:', err);
    }
  };

  useEffect(() => {
    let animInterval;
    if (speaking) {
      animInterval = setInterval(() => {
        setAvatarFrame((prev) => {
          if (prev === 0) return 1;
          if (prev >= avatarImages.length - 1) return 1;
          return prev + 1;
        });
      }, 150);
    } else {
      setAvatarFrame(0);
    }

    return () => clearInterval(animInterval);
  }, [speaking, avatarImages.length]);

  const avatarStyle = faceData
    ? {
        position: 'absolute',
        left: faceData.center_x + 50,
        top: faceData.center_y - 75,
        width: '150px',
        height: '150px',
        zIndex: 2,
        pointerEvents: 'none',
        transition: 'left 0.1s, top 0.1s',
        objectFit: 'cover',
        borderRadius: '50%',
        border: speaking ? '3px solid #ff4444' : '3px solid #4CAF50'
      }
    : {
        display: 'none'
      };

  // Volume bar percentage
  const volumePercent = Math.min((currentVolume / threshold) * 100, 100);

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#1a1a1a',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{
        color: '#fff',
        marginBottom: '20px',
        fontSize: '2.5rem',
        fontWeight: 'bold'
      }}>
        Camera Feed + Avatar
      </h1>

      <div style={{ 
        position: 'relative', 
        width: '640px', 
        height: '480px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        <img
          src="http://localhost:5000/video_feed"
          alt="Camera Feed"
          style={{
            width: '100%',
            height: '100%',
            display: 'block',
            zIndex: 1
          }}
        />
        <img
          src={avatarImages[avatarFrame]}
          alt="Avatar"
          style={avatarStyle}
        />
        
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'rgba(0,0,0,0.85)',
          color: 'white',
          padding: '15px',
          borderRadius: '8px',
          fontSize: '13px',
          zIndex: 3,
          fontFamily: 'monospace',
          minWidth: '250px'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <strong>🎤 User Speaking:</strong> {speaking ? '✅ YES' : '❌ NO'}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>🔊 Audio Device:</strong> {audioAvailable ? '✅ Working' : '❌ Not Available'}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>👤 Face Detected:</strong> {faceData ? '✅ YES' : '❌ NO'}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>🎭 Avatar Frame:</strong> {avatarFrame} {avatarFrame === 0 ? '(idle)' : '(talking)'}
          </div>
          
          {/* Volume Monitor */}
          <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #444' }}>
            <div style={{ marginBottom: '5px' }}>
              <strong>📊 Volume:</strong> {currentVolume.toFixed(1)} / {threshold}
            </div>
            <div style={{ 
              width: '100%', 
              height: '20px', 
              background: '#333', 
              borderRadius: '10px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${volumePercent}%`,
                height: '100%',
                background: speaking ? '#ff4444' : '#4CAF50',
                transition: 'width 0.1s, background 0.3s'
              }}></div>
            </div>
            <div style={{ fontSize: '11px', color: '#aaa', marginTop: '5px' }}>
              {currentVolume > threshold ? '🔴 Above threshold - SPEAKING!' : '⚪ Below threshold - silent'}
            </div>
          </div>
        </div>

        {!audioAvailable && (
          <button
            onClick={handleManualToggle}
            style={{
              position: 'absolute',
              bottom: 10,
              left: 10,
              padding: '10px 20px',
              background: speaking ? '#f44336' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontWeight: 'bold',
              zIndex: 3
            }}
          >
            {speaking ? '🔴 Stop Speaking' : '🟢 Start Speaking'}
          </button>
        )}

        <div style={{
          position: 'absolute',
          bottom: 10,
          left: audioAvailable ? 10 : 150,
          right: 10,
          background: 'rgba(255, 165, 0, 0.9)',
          color: 'black',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          zIndex: 3,
          textAlign: 'center'
        }}>
          {audioAvailable 
            ? '⚠️ Avatar mirrors YOUR speech (for testing). Speak louder if not detecting!'
            : '⚠️ Audio detection unavailable. Use manual button.'}
        </div>
      </div>
    </div>
  );
}

export default App;