import React, { useEffect, useState, useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF, useAnimations, PerspectiveCamera } from "@react-three/drei";
import * as THREE from "three";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Eye, EyeOff, Activity } from "lucide-react";

// Avatar States: IDLE, LISTENING, THINKING, SPEAKING
function Avatar3D({ state, position, scale = 2.0 }) {
    const group = useRef();
    const { scene, animations } = useGLTF(
        "http://localhost:5000/assets/models/chibi.glb",
    );
    const { actions } = useAnimations(animations, group);

    const currentAnimationIndex = useRef(0);
    const animationChangeInterval = useRef(null);
    const stateRef = useRef(state);

    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    useEffect(() => {
        if (!actions) return;

        const actionKeys = Object.keys(actions);
        if (actionKeys.length === 0) return;

        actionKeys.forEach((key) => {
            if (actions[key]) actions[key].stop();
        });

        if (animationChangeInterval.current) {
            clearInterval(animationChangeInterval.current);
            animationChangeInterval.current = null;
        }

        if (state === "SPEAKING") {
            const firstAction = actions[actionKeys[0]];
            if (firstAction) {
                firstAction.reset();
                firstAction.setLoop(THREE.LoopRepeat);
                firstAction.timeScale = 1.2;
                firstAction.play();
            }

            currentAnimationIndex.current = 0;
            animationChangeInterval.current = setInterval(() => {
                if (stateRef.current !== "SPEAKING") return;

                currentAnimationIndex.current =
                    (currentAnimationIndex.current + 1) % actionKeys.length;
                const nextKey = actionKeys[currentAnimationIndex.current];
                const nextAction = actions[nextKey];

                if (nextAction) {
                    actionKeys.forEach((key) => {
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
        } else if (state === "THINKING") {
            const firstAction = actions[actionKeys[0]];
            if (firstAction) {
                firstAction.reset();
                firstAction.setLoop(THREE.LoopRepeat);
                firstAction.timeScale = 0.4;
                firstAction.play();
            }
        } else if (state === "LISTENING") {
            const firstAction = actions[actionKeys[0]];
            if (firstAction) {
                firstAction.reset();
                firstAction.setLoop(THREE.LoopRepeat);
                firstAction.timeScale = 0.6;
                firstAction.play();
            }
        }

        return () => {
            if (animationChangeInterval.current) {
                clearInterval(animationChangeInterval.current);
            }
        };
    }, [state, actions]);

    useFrame((state) => {
        if (!group.current) return;

        const time = state.clock.elapsedTime;
        const currentState = stateRef.current;

        if (position) {
            group.current.position.x = THREE.MathUtils.lerp(
                group.current.position.x,
                position.x,
                0.08,
            );
            group.current.position.y = THREE.MathUtils.lerp(
                group.current.position.y,
                position.y,
                0.08,
            );
        }

        if (currentState === "IDLE") {
            const breathe = Math.sin(time * 1.2) * 0.01;
            group.current.position.z = -0.2 + breathe;

            const subtleRotation = Math.sin(time * 0.2) * 0.02;
            group.current.rotation.y = subtleRotation;
        } else if (currentState === "LISTENING") {
            const breathe = Math.sin(time * 1.5) * 0.008;
            group.current.position.z = -0.1 + breathe;

            const headTilt = Math.sin(time * 0.3) * 0.06;
            group.current.rotation.z = headTilt;
            group.current.rotation.y = 0.1;
        } else if (currentState === "THINKING") {
            const slowFloat = Math.sin(time * 0.4) * 0.01;
            group.current.position.z = -0.15 + slowFloat;

            const slowRotation = Math.sin(time * 0.25) * 0.04;
            group.current.rotation.y = slowRotation;
        } else if (currentState === "SPEAKING") {
            const bounce = Math.sin(time * 4) * 0.01;
            group.current.position.z = -0.1 + bounce;

            const activeRotation = Math.sin(time * 0.3) * 0.03;
            group.current.rotation.y = activeRotation;
        }
    });

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

            <pointLight position={[3, 3, 3]} intensity={1.0} color="#ffffff" />
            <pointLight position={[-3, 2, 2]} intensity={0.6} color="#ffffff" />

            {state === "LISTENING" && (
                <pointLight
                    position={[0, 1, 2]}
                    intensity={0.8}
                    color="#4ecdc4"
                    distance={4}
                />
            )}

            {state === "THINKING" && (
                <pointLight
                    position={[0, 2, 2]}
                    intensity={1.0}
                    color="#9b59b6"
                    distance={4}
                />
            )}

            {state === "SPEAKING" && (
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

    useFrame((state) => {
        if (meshRef.current && position) {
            meshRef.current.position.x = THREE.MathUtils.lerp(
                meshRef.current.position.x,
                position.x,
                0.02,
            );
            meshRef.current.position.y = THREE.MathUtils.lerp(
                meshRef.current.position.y,
                position.y,
                0.02,
            );
        }
    });

    const stateColors = {
        IDLE: "#666666",
        LISTENING: "#4ecdc4",
        THINKING: "#9b59b6",
        SPEAKING: "#ef4444",
    };

    return (
        <group>
            <mesh ref={meshRef} position={[0, 0, 0]}>
                <sphereGeometry args={[0.4, 32, 32]} />
                <meshStandardMaterial
                    color={stateColors[state] || "#666666"}
                    transparent
                    opacity={0.85}
                    emissive={stateColors[state] || "#666666"}
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
            <meshStandardMaterial color="#a1a1aa" wireframe />
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
        console.error("Avatar error:", error.message);
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
            const normX = (faceData.center_x - 640) / 640;
            const normY = -(faceData.center_y - 360) / 360;

            setAvatarPosition({
                x: normX * 1.5,
                y: normY * 1.2,
                z: 0,
            });
        }
    }, [faceData]);

    return (
        <>
            <ambientLight intensity={0.5} />
            <directionalLight
                position={[10, 10, 5]}
                intensity={1.0}
                castShadow
            />
            <hemisphereLight args={["#87CEEB", "#1a1a1a", 0.7]} />

            <AvatarWithErrorBoundary
                state={avatarState}
                position={avatarPosition}
            />

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
    const [avatarState, setAvatarState] = useState("IDLE");

    useEffect(() => {
        if (speaking) {
            setAvatarState("SPEAKING");
        } else if (faceData) {
            setAvatarState("LISTENING");
        } else {
            setAvatarState("IDLE");
        }
    }, [speaking, faceData]);

    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch("http://localhost:5000/face_data");
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
                const res = await fetch(
                    "http://localhost:5000/speaking_status",
                );
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
            await fetch("http://localhost:5000/toggle_speaking", {
                method: "POST",
            });
        } catch (err) {
            console.error("Error toggling:", err);
        }
    };

    const volumePercent = Math.min((currentVolume / threshold) * 100, 100);

    const getStateBadgeVariant = (state) => {
        switch (state) {
            case "LISTENING":
                return "default";
            case "SPEAKING":
                return "destructive";
            case "THINKING":
                return "secondary";
            default:
                return "idle";
        }
    };

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center p-8">
            <div className="w-full max-w-7xl space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold tracking-tight text-white">
                        AI Companion
                    </h1>
                    <div className="flex items-center gap-3">
                        <Badge variant={audioAvailable ? "success" : "outline"}>
                            {audioAvailable ? "Audio Active" : "Audio Inactive"}
                        </Badge>
                        <Badge variant={faceData ? "success" : "outline"}>
                            {faceData ? "Face Detected" : "No Face"}
                        </Badge>
                        <Badge variant={getStateBadgeVariant(avatarState)}>
                            {avatarState}
                        </Badge>
                    </div>
                </div>

                {/* Main Video Container */}
                <div className="relative w-full aspect-video bg-zinc-950 rounded-lg overflow-hidden border border-zinc-800">
                    {/* Camera Feed */}
                    <img
                        src="http://localhost:5000/video_feed"
                        alt="Camera Feed"
                        className="absolute inset-0 w-full h-full object-cover"
                        style={{
                            imageRendering: "crisp-edges",
                            WebkitImageRendering: "crisp-edges",
                        }}
                    />

                    {/* 3D Avatar Overlay */}
                    {show3D && (
                        <div className="absolute inset-0 pointer-events-none z-10">
                            <Canvas shadows>
                                <Scene
                                    avatarState={avatarState}
                                    faceData={faceData}
                                />
                            </Canvas>
                        </div>
                    )}

                    {/* Controls Overlay - Top Right */}
                    <div className="absolute top-4 right-4 z-20">
                        <Button
                            onClick={() => setShow3D(!show3D)}
                            variant={show3D ? "default" : "outline"}
                            size="sm"
                            className="gap-2"
                        >
                            {show3D ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                            3D Avatar
                        </Button>
                    </div>

                    {/* Volume Indicator - Bottom Left */}
                    <div className="absolute bottom-4 left-4 z-20 space-y-2">
                        <div className="flex items-center gap-2 text-xs text-zinc-400 font-mono">
                            <Activity className="h-3 w-3" />
                            <span>Volume: {currentVolume.toFixed(0)} / {threshold}</span>
                        </div>
                        <div className="w-48 h-1 bg-zinc-800 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-100 ${
                                    speaking ? "bg-red-500" : "bg-green-500"
                                }`}
                                style={{ width: `${volumePercent}%` }}
                            />
                        </div>
                    </div>

                    {/* Manual Control - Bottom Center */}
                    {!audioAvailable && (
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
                            <Button
                                onClick={handleManualToggle}
                                variant={speaking ? "destructive" : "default"}
                                size="lg"
                            >
                                {speaking ? "Stop" : "Start"}
                            </Button>
                        </div>
                    )}

                    {/* State Indicator - Bottom */}
                    <div className={`absolute bottom-0 left-0 right-0 h-1 transition-colors z-20 ${
                        avatarState === "SPEAKING" ? "bg-red-500" :
                        avatarState === "LISTENING" ? "bg-cyan-500" :
                        avatarState === "THINKING" ? "bg-purple-500" :
                        "bg-zinc-600"
                    }`} />
                </div>
            </div>
        </div>
    );
}

export default App;

