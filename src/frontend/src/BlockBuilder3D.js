import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Grid configuration
const GRID_SIZE = 5; // 5x5x5 grid
const BLOCK_SIZE = 4.0; // 4 units per block
const TOTAL_SIZE = GRID_SIZE * BLOCK_SIZE; // 20x20x20 total

// Interaction plane for hand projection
const INTERACTION_PLANE_Z = 10; // Distance from camera

const BlockBuilder3D = () => {
    const mountRef = useRef(null);
    const videoRef = useRef(null);
    const overlayCanvasRef = useRef(null);

    // Three.js refs
    const sceneRef = useRef(null);
    const cameraRef = useRef(null);
    const projectionCameraRef = useRef(null); // Screen-aligned camera for hand projection
    const rendererRef = useRef(null);
    const gridGroupRef = useRef(null);
    const blocksRef = useRef(new Map()); // Map of "x,y,z" -> block mesh
    const hoverBlockRef = useRef(null);
    const raycasterRef = useRef(new THREE.Raycaster());
    const recenterButtonRef = useRef(null);

    // Gesture state
    const prevLeftPinchRef = useRef(false);
    const prevRightPinchRef = useRef(false);
    const prevFistPosRef = useRef(null);
    const twoFistsPanRef = useRef(null);
    const twoHandsZoomRef = useRef(null);
    const buttonPinchCooldownRef = useRef(false);

    // Hover hold timers
    const rightPinchHoldStartRef = useRef(null);
    const leftPinchHoldStartRef = useRef(null);
    const hoverProgressRef = useRef(0);

    const [blockCount, setBlockCount] = useState(0);

    useEffect(() => {
        console.log("BlockBuilder3D: Initializing...");

        // Create Three.js scene
        const scene = new THREE.Scene();
        sceneRef.current = scene;

        // Main camera (for viewing the scene at an angle)
        const camera = new THREE.PerspectiveCamera(
            60, // Adjusted to match typical webcam FOV (55-60 degrees)
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        camera.position.set(25, 25, 25);
        camera.lookAt(0, 0, 0);
        cameraRef.current = camera;

        // Projection camera (screen-aligned for hand tracking)
        // This camera looks straight at the scene from the front, matching the user's view
        const projectionCamera = new THREE.PerspectiveCamera(
            60, // Match main camera FOV
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        projectionCamera.position.set(0, 0, 50); // Positioned in front, looking at origin
        projectionCamera.lookAt(0, 0, 0);
        projectionCameraRef.current = projectionCamera;

        // Renderer
        const renderer = new THREE.WebGLRenderer({
            alpha: true,
            antialias: true,
        });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setClearColor(0x000000, 0);
        rendererRef.current = renderer;

        if (mountRef.current) {
            mountRef.current.appendChild(renderer.domElement);
        }

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 15, 10);
        scene.add(directionalLight);

        // Create grid group (this will be rotated)
        const gridGroup = new THREE.Group();
        gridGroupRef.current = gridGroup;
        scene.add(gridGroup);

        // Create white Minecraft-style 3D grid
        createGrid(gridGroup);

        // OrbitControls for manual camera control
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Animation loop
        const animate = () => {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        // Set up camera feed
        navigator.mediaDevices
            .getUserMedia({ video: { facingMode: "user" } })
            .then((stream) => {
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            })
            .catch((err) => {
                console.error("Error accessing camera:", err);
            });

        // Set up overlay canvas
        const canvas = overlayCanvasRef.current;
        if (canvas) {
            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(window.innerWidth * dpr);
            canvas.height = Math.floor(window.innerHeight * dpr);
            canvas.style.width = `${window.innerWidth}px`;
            canvas.style.height = `${window.innerHeight}px`;
            const ctx = canvas.getContext("2d");
            if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        // WebSocket connection
        console.log("Attempting to connect to WebSocket server...");
        const ws = new WebSocket("ws://localhost:8765");

        ws.onopen = () => {
            console.log("✓ WebSocket connected to hand tracking server");
        };

        ws.onmessage = (event) => {
            try {
                const handData = JSON.parse(event.data);
                console.log("Received hand data:", handData.hands?.length || 0, "hands");
                handleHandData(handData);
            } catch (err) {
                console.error("Error parsing hand data:", err, event.data);
            }
        };

        ws.onerror = (error) => {
            console.error("✗ WebSocket error:", error);
            console.error("Make sure the Python backend is running: python run_hand_tracker.py");
        };

        ws.onclose = () => {
            console.log("✗ WebSocket disconnected");
        };

        // Handle window resize
        const handleResize = () => {
            const aspect = window.innerWidth / window.innerHeight;
            camera.aspect = aspect;
            camera.updateProjectionMatrix();

            projectionCamera.aspect = aspect;
            projectionCamera.updateProjectionMatrix();

            renderer.setSize(window.innerWidth, window.innerHeight);

            const canvas = overlayCanvasRef.current;
            if (canvas) {
                const dpr = window.devicePixelRatio || 1;
                canvas.width = Math.floor(window.innerWidth * dpr);
                canvas.height = Math.floor(window.innerHeight * dpr);
                canvas.style.width = `${window.innerWidth}px`;
                canvas.style.height = `${window.innerHeight}px`;
                const ctx = canvas.getContext("2d");
                if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            }
        };
        window.addEventListener("resize", handleResize);

        // Cleanup
        return () => {
            window.removeEventListener("resize", handleResize);
            if (ws) ws.close();
            if (renderer) renderer.dispose();
            if (mountRef.current && renderer.domElement) {
                mountRef.current.removeChild(renderer.domElement);
            }
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject;
                stream.getTracks().forEach((track) => track.stop());
            }
        };
    }, []);

    const createGrid = (parent) => {
        const halfSize = TOTAL_SIZE / 2;

        // Create white 3D grid lines
        const gridMaterial = new THREE.LineBasicMaterial({
            color: 0xffffff,
            linewidth: 1,
            opacity: 0.6,
            transparent: true,
        });

        // Create grid lines on all three axes
        for (let i = -halfSize; i <= halfSize; i += BLOCK_SIZE) {
            // XY planes at different Z
            const xyGeometry = new THREE.BufferGeometry();
            const xyVertices = [];
            // Horizontal lines
            for (let j = -halfSize; j <= halfSize; j += BLOCK_SIZE) {
                xyVertices.push(-halfSize, j, i, halfSize, j, i);
            }
            // Vertical lines
            for (let j = -halfSize; j <= halfSize; j += BLOCK_SIZE) {
                xyVertices.push(j, -halfSize, i, j, halfSize, i);
            }
            xyGeometry.setAttribute(
                "position",
                new THREE.Float32BufferAttribute(xyVertices, 3)
            );
            parent.add(new THREE.LineSegments(xyGeometry, gridMaterial));

            // XZ planes at different Y
            const xzGeometry = new THREE.BufferGeometry();
            const xzVertices = [];
            for (let j = -halfSize; j <= halfSize; j += BLOCK_SIZE) {
                xzVertices.push(-halfSize, i, j, halfSize, i, j);
                xzVertices.push(j, i, -halfSize, j, i, halfSize);
            }
            xzGeometry.setAttribute(
                "position",
                new THREE.Float32BufferAttribute(xzVertices, 3)
            );
            parent.add(new THREE.LineSegments(xzGeometry, gridMaterial));

            // YZ planes at different X
            const yzGeometry = new THREE.BufferGeometry();
            const yzVertices = [];
            for (let j = -halfSize; j <= halfSize; j += BLOCK_SIZE) {
                yzVertices.push(i, -halfSize, j, i, halfSize, j);
                yzVertices.push(i, j, -halfSize, i, j, halfSize);
            }
            yzGeometry.setAttribute(
                "position",
                new THREE.Float32BufferAttribute(yzVertices, 3)
            );
            parent.add(new THREE.LineSegments(yzGeometry, gridMaterial));
        }

        // Create bounding box edges (bright white)
        const boxGeometry = new THREE.BoxGeometry(
            TOTAL_SIZE,
            TOTAL_SIZE,
            TOTAL_SIZE
        );
        const boxEdges = new THREE.EdgesGeometry(boxGeometry);
        const boxLines = new THREE.LineSegments(
            boxEdges,
            new THREE.LineBasicMaterial({
                color: 0xffffff,
                linewidth: 3,
                opacity: 1.0,
                transparent: false,
            })
        );
        parent.add(boxLines);

        console.log(
            `Grid created: ${GRID_SIZE}x${GRID_SIZE}x${GRID_SIZE} (${TOTAL_SIZE}x${TOTAL_SIZE}x${TOTAL_SIZE} units)`
        );
    };

    const handleHandData = (handData) => {
        // Draw hand overlay
        const canvas = overlayCanvasRef.current;
        if (canvas) {
            const ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (handData.hands && handData.hands.length > 0) {
                handData.hands.forEach((hand) => {
                    drawHand(ctx, hand, canvas.width, canvas.height);
                });
            }
        }

        if (!handData.hands || handData.hands.length === 0) {
            // Reset gesture state
            prevLeftPinchRef.current = false;
            prevRightPinchRef.current = false;
            prevFistPosRef.current = null;
            twoFistsPanRef.current = null;
            twoHandsZoomRef.current = null;
            removeHoverBlock();
            return;
        }

        // Separate hands by handedness (MediaPipe returns camera view)
        // "Left" in camera view = user's right hand
        // "Right" in camera view = user's left hand
        let leftHand = null; // User's left hand
        let rightHand = null; // User's right hand

        handData.hands.forEach((hand) => {
            if (hand.handedness === "Right") {
                leftHand = hand; // User's left
            } else if (hand.handedness === "Left") {
                rightHand = hand; // User's right
            }
        });

        // Process gestures
        processGestures(leftHand, rightHand);
    };

    const drawHand = (ctx, hand, width, height) => {
        // Draw landmarks with better visibility
        hand.landmarks.forEach((lm, idx) => {
            const x = lm.x * width;
            const y = lm.y * height;
            const size = 12;

            // Draw circle for each landmark
            ctx.beginPath();
            ctx.arc(x, y, size / 2, 0, 2 * Math.PI);

            // Highlight pinch points
            if (idx === 4 || idx === 8) {
                ctx.fillStyle = hand.is_pinching ? "#ff0000" : "#ffff00";
                ctx.fill();
            } else {
                ctx.fillStyle = "#00ff00";
                ctx.fill();
            }

            // Add white border for visibility
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 2;
            ctx.stroke();
        });

        // Draw connections with better visibility
        const connections = [
            [0, 1],
            [1, 2],
            [2, 3],
            [3, 4], // Thumb
            [0, 5],
            [5, 6],
            [6, 7],
            [7, 8], // Index
            [0, 9],
            [9, 10],
            [10, 11],
            [11, 12], // Middle
            [0, 13],
            [13, 14],
            [14, 15],
            [15, 16], // Ring
            [0, 17],
            [17, 18],
            [18, 19],
            [19, 20], // Pinky
            [5, 9],
            [9, 13],
            [13, 17], // Palm
        ];

        ctx.lineWidth = 3;
        ctx.strokeStyle = hand.is_fist ? "#ffff00" : hand.is_pinching ? "#ff0000" : "#00ff00";
        connections.forEach(([start, end]) => {
            const startLm = hand.landmarks[start];
            const endLm = hand.landmarks[end];
            ctx.beginPath();
            ctx.moveTo(startLm.x * width, startLm.y * height);
            ctx.lineTo(endLm.x * width, endLm.y * height);
            ctx.stroke();
        });

        // Draw gesture labels for debugging
        ctx.fillStyle = "#ffffff";
        ctx.font = "16px monospace";
        ctx.fillText(
            `${hand.handedness} - Pinch: ${hand.is_pinching} | Fist: ${hand.is_fist}`,
            10,
            hand.handedness === "Left" ? 30 : 60
        );
    };

    const processGestures = (leftHand, rightHand) => {
        // Priority order: Two-hand gestures > Single hand gestures

        // Debug logging
        if (leftHand || rightHand) {
            console.log("Gestures detected:", {
                leftHand: leftHand ? { pinch: leftHand.is_pinching, fist: leftHand.is_fist } : null,
                rightHand: rightHand ? { pinch: rightHand.is_pinching, fist: rightHand.is_fist } : null,
            });
        }

        // TWO HANDS PINCHING: Zoom
        if (
            leftHand &&
            rightHand &&
            leftHand.is_pinching &&
            rightHand.is_pinching
        ) {
            console.log("Two-hand zoom gesture detected");
            handleTwoHandZoom(leftHand, rightHand);
            return;
        }

        // TWO FISTS: Pan camera
        if (leftHand && rightHand && leftHand.is_fist && rightHand.is_fist) {
            console.log("Two-fist pan gesture detected");
            handleTwoFistPan(leftHand, rightHand);
            return;
        }

        // Reset two-hand gesture states if not active
        twoHandsZoomRef.current = null;
        twoFistsPanRef.current = null;

        // SINGLE FIST: Rotate grid
        if ((leftHand && leftHand.is_fist) || (rightHand && rightHand.is_fist)) {
            const fistHand = leftHand?.is_fist ? leftHand : rightHand;
            console.log("Single fist rotate gesture detected");
            handleSingleFistRotate(fistHand);
        } else {
            prevFistPosRef.current = null;
        }

        // Check if pinching near re-center button
        const isNearButton =
            rightHand &&
            rightHand.is_pinching &&
            checkButtonHover(rightHand.landmarks[8].x, rightHand.landmarks[8].y);

        if (isNearButton) {
            console.log("Hand near re-center button!");
            if (!buttonPinchCooldownRef.current) {
                console.log("Activating re-center");
                recenterCamera();
                buttonPinchCooldownRef.current = true;
                setTimeout(() => {
                    buttonPinchCooldownRef.current = false;
                }, 1000);
            }
            highlightButton(true);
            removeHoverBlock();
        } else {
            highlightButton(false);

            // RIGHT HAND PINCH: Add block (3 second hold)
            if (rightHand && rightHand.is_pinching) {
                const indexTip = rightHand.landmarks[8];
                const worldPos = screenToWorld(
                    indexTip.x,
                    indexTip.y,
                    rightHand
                );

                // Start timer if just started pinching
                if (!rightPinchHoldStartRef.current) {
                    rightPinchHoldStartRef.current = Date.now();
                    console.log("Right hand pinch started - hold for 3s to place");
                }

                // Calculate hold progress
                const holdTime = (Date.now() - rightPinchHoldStartRef.current) / 1000;
                hoverProgressRef.current = Math.min(holdTime / 3.0, 1.0);

                // Show green hover with progress
                showHoverBlock(worldPos, 'green', hoverProgressRef.current);

                // Place block after 3 seconds
                if (holdTime >= 3.0 && !prevRightPinchRef.current) {
                    console.log("Right hand pinch - placing block");
                    placeBlock(worldPos);
                    prevRightPinchRef.current = true;
                    rightPinchHoldStartRef.current = null;
                    hoverProgressRef.current = 0;
                }
            } else {
                prevRightPinchRef.current = false;
                rightPinchHoldStartRef.current = null;
                hoverProgressRef.current = 0;
            }
        }

        // LEFT HAND PINCH: Remove block (3 second hold)
        if (leftHand && leftHand.is_pinching) {
            const indexTip = leftHand.landmarks[8];
            const worldPos = screenToWorld(
                indexTip.x,
                indexTip.y,
                leftHand
            );

            // Start timer if just started pinching
            if (!leftPinchHoldStartRef.current) {
                leftPinchHoldStartRef.current = Date.now();
                console.log("Left hand pinch started - hold for 3s to remove");
            }

            // Calculate hold progress
            const holdTime = (Date.now() - leftPinchHoldStartRef.current) / 1000;
            const progress = Math.min(holdTime / 3.0, 1.0);

            // Show red hover with progress
            showHoverBlock(worldPos, 'red', progress);

            // Delete block after 3 seconds
            if (holdTime >= 3.0 && !prevLeftPinchRef.current) {
                console.log("Left hand pinch - deleting block");
                deleteBlock(worldPos);
                prevLeftPinchRef.current = true;
                leftPinchHoldStartRef.current = null;
            }
        } else {
            prevLeftPinchRef.current = false;
            leftPinchHoldStartRef.current = null;
        }

        // Remove hover if no pinching happening
        if ((!rightHand || !rightHand.is_pinching) && (!leftHand || !leftHand.is_pinching)) {
            removeHoverBlock();
        }
    };

    const calculateHandSize = (landmarks) => {
        // Calculate hand size using wrist (0) to middle finger tip (12) distance in screen space
        const wrist = landmarks[0];
        const middleTip = landmarks[12];

        const dx = middleTip.x - wrist.x;
        const dy = middleTip.y - wrist.y;

        // Return distance in normalized coordinates (0-1 range)
        return Math.sqrt(dx * dx + dy * dy);
    };

    // Function to remap MediaPipe coordinates to Visible Screen NDC
    const getVisibleNDC = (mpX, mpY) => {
        const video = videoRef.current;
        if (!video || !video.videoWidth || !video.videoHeight) {
            return { x: 0, y: 0 };
        }

        const videoAspect = video.videoWidth / video.videoHeight;
        const screenAspect = window.innerWidth / window.innerHeight;

        let scaleX = 1, scaleY = 1;
        let offsetX = 0, offsetY = 0;

        // Logic for 'object-fit: cover'
        if (screenAspect > videoAspect) {
            // Screen is wider: Top/Bottom of video are cropped
            // We need to "stretch" the Y coordinate to match the visible area
            const scale = screenAspect / videoAspect;
            scaleY = scale;
            offsetY = (1 - 1 / scale) / 2;
        } else {
            // Screen is taller: Sides of video are cropped
            const scale = videoAspect / screenAspect;
            scaleX = scale;
            offsetX = (1 - 1 / scale) / 2;
        }

        // 1. Remap Raw MediaPipe coords to Visible 0..1 range
        // We subtract the hidden offset and scale up the remaining visible part
        const visibleX = (mpX - offsetX) * scaleX;
        const visibleY = (mpY - offsetY) * scaleY;

        // 2. Flip X for Mirror Effect (video CSS has scaleX(-1))
        const mirroredX = 1 - visibleX;

        // 3. Convert to Three.js NDC (-1 to +1)
        const ndcX = (mirroredX * 2) - 1;
        const ndcY = -(visibleY * 2) + 1; // Note the negative sign for Y!

        return { x: ndcX, y: ndcY };
    };

    const screenToWorld = (normalizedX, normalizedY, hand = null) => {
        // Convert normalized screen coords (0-1) to 3D world position
        // Uses "ghost zone" removal and plane raycasting for solid alignment

        // 1. Get visible NDC coordinates (handles object-fit: cover cropping)
        const ndc = getVisibleNDC(normalizedX, normalizedY);

        // 2. Create raycaster from the ACTUAL camera users look through
        const raycaster = raycasterRef.current;
        const camera = cameraRef.current;
        raycaster.setFromCamera(new THREE.Vector2(ndc.x, ndc.y), camera);

        // 3. Raycast to an interaction plane at Y=0 (grid center height)
        // This creates a mathematically solid tracking surface
        const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
        const target = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, target);

        if (target) {
            return target;
        }

        // Fallback if ray doesn't hit plane (shouldn't happen with proper camera setup)
        return new THREE.Vector3(0, 0, 0);
    };

    const snapToGrid = (position) => {
        const halfSize = TOTAL_SIZE / 2;

        let x = Math.round(position.x / BLOCK_SIZE) * BLOCK_SIZE;
        let y = Math.round(position.y / BLOCK_SIZE) * BLOCK_SIZE;
        let z = Math.round(position.z / BLOCK_SIZE) * BLOCK_SIZE;

        // Clamp to grid bounds
        x = Math.max(-halfSize + BLOCK_SIZE / 2, Math.min(halfSize - BLOCK_SIZE / 2, x));
        y = Math.max(-halfSize + BLOCK_SIZE / 2, Math.min(halfSize - BLOCK_SIZE / 2, y));
        z = Math.max(-halfSize + BLOCK_SIZE / 2, Math.min(halfSize - BLOCK_SIZE / 2, z));

        return new THREE.Vector3(x, y, z);
    };

    const getBlockKey = (position) => {
        return `${position.x},${position.y},${position.z}`;
    };

    const placeBlock = (position) => {
        const snapped = snapToGrid(position);
        const key = getBlockKey(snapped);

        if (blocksRef.current.has(key)) {
            console.log("Block already exists");
            return;
        }

        // Create block
        const geometry = new THREE.BoxGeometry(
            BLOCK_SIZE * 0.9,
            BLOCK_SIZE * 0.9,
            BLOCK_SIZE * 0.9
        );
        const material = new THREE.MeshStandardMaterial({
            color: 0x00ff00,
            roughness: 0.7,
            metalness: 0.3,
        });

        const block = new THREE.Mesh(geometry, material);

        // Add edges
        const edges = new THREE.EdgesGeometry(geometry);
        const edgeLines = new THREE.LineSegments(
            edges,
            new THREE.LineBasicMaterial({ color: 0x000000, linewidth: 2 })
        );

        const blockGroup = new THREE.Group();
        blockGroup.add(block);
        blockGroup.add(edgeLines);
        blockGroup.position.copy(snapped);

        gridGroupRef.current.add(blockGroup);
        blocksRef.current.set(key, blockGroup);
        setBlockCount(blocksRef.current.size);
    };

    const deleteBlock = (position) => {
        const snapped = snapToGrid(position);
        const key = getBlockKey(snapped);

        if (!blocksRef.current.has(key)) {
            console.log("No block to delete");
            return;
        }

        const block = blocksRef.current.get(key);
        gridGroupRef.current.remove(block);
        blocksRef.current.delete(key);
        setBlockCount(blocksRef.current.size);
    };

    const showHoverBlock = (worldPos, color = 'green', progress = 0) => {
        const snapped = snapToGrid(worldPos);

        if (!hoverBlockRef.current) {
            const geometry = new THREE.BoxGeometry(
                BLOCK_SIZE * 0.9,
                BLOCK_SIZE * 0.9,
                BLOCK_SIZE * 0.9
            );
            const material = new THREE.MeshBasicMaterial({
                color: 0x00ff00,
                opacity: 0.3,
                transparent: true,
            });
            hoverBlockRef.current = new THREE.Mesh(geometry, material);
            gridGroupRef.current.add(hoverBlockRef.current);
        }

        // Update color based on hover type
        const hexColor = color === 'red' ? 0xff0000 : 0x00ff00;
        hoverBlockRef.current.material.color.setHex(hexColor);

        // Update opacity based on progress (0.3 to 0.8)
        hoverBlockRef.current.material.opacity = 0.3 + (progress * 0.5);

        // Scale up slightly as progress increases
        const scale = 0.9 + (progress * 0.1);
        hoverBlockRef.current.scale.set(scale, scale, scale);

        hoverBlockRef.current.position.copy(snapped);
        hoverBlockRef.current.visible = true;
    };

    const removeHoverBlock = () => {
        if (hoverBlockRef.current) {
            hoverBlockRef.current.visible = false;
        }
    };

    const handleSingleFistRotate = (hand) => {
        const palm = hand.landmarks[9];
        // Use screen-space coordinates directly instead of converting to world space
        const screenPos = { x: palm.x, y: palm.y };

        if (prevFistPosRef.current) {
            // Calculate delta in normalized screen space (0-1)
            const deltaX = screenPos.x - prevFistPosRef.current.x;
            const deltaY = screenPos.y - prevFistPosRef.current.y;

            // Map screen motion to rotation:
            // - Horizontal hand motion (deltaX) -> Y-axis rotation (turning left/right)
            // - Vertical hand motion (deltaY) -> X-axis rotation (tilting up/down)
            // Multiply by larger factor since we're in normalized coords (0-1 range)
            gridGroupRef.current.rotation.y -= deltaX * 3.0;
            gridGroupRef.current.rotation.x += deltaY * 3.0;  // Note: + because screen Y goes down
        }

        prevFistPosRef.current = screenPos;
    };

    const handleTwoFistPan = (leftHand, rightHand) => {
        const leftPalm = leftHand.landmarks[9];
        const rightPalm = rightHand.landmarks[9];

        const leftWorld = screenToWorld(leftPalm.x, leftPalm.y, leftHand);
        const rightWorld = screenToWorld(rightPalm.x, rightPalm.y, rightHand);

        const centerX = (leftWorld.x + rightWorld.x) / 2;
        const centerY = (leftWorld.y + rightWorld.y) / 2;

        if (twoFistsPanRef.current) {
            const deltaX = centerX - twoFistsPanRef.current.x;
            const deltaY = centerY - twoFistsPanRef.current.y;

            cameraRef.current.position.x -= deltaX * 2;
            cameraRef.current.position.y -= deltaY * 2;
        }

        twoFistsPanRef.current = { x: centerX, y: centerY };
    };

    const handleTwoHandZoom = (leftHand, rightHand) => {
        const leftIndex = leftHand.landmarks[8];
        const rightIndex = rightHand.landmarks[8];

        const distance = Math.sqrt(
            (leftIndex.x - rightIndex.x) ** 2 +
                (leftIndex.y - rightIndex.y) ** 2
        );

        if (twoHandsZoomRef.current !== null) {
            const delta = distance - twoHandsZoomRef.current;
            const zoomSpeed = 50;

            const direction = new THREE.Vector3();
            cameraRef.current.getWorldDirection(direction);

            // REVERSED: Hands apart (positive delta) = zoom IN (move camera closer)
            cameraRef.current.position.addScaledVector(
                direction,
                delta * zoomSpeed  // Removed the negative sign
            );
        }

        twoHandsZoomRef.current = distance;
    };

    const checkButtonHover = (normalizedX, normalizedY) => {
        // Button is at top-left of screen: x=0.1, y=0.1 (in normalized coords)
        const buttonX = 0.1;
        const buttonY = 0.1;
        const buttonRadius = 0.05; // 5% of screen width/height

        const distance = Math.sqrt(
            (normalizedX - buttonX) ** 2 + (normalizedY - buttonY) ** 2
        );

        return distance < buttonRadius;
    };

    const highlightButton = (isHighlighted) => {
        // Update button DOM element (handled in JSX)
        if (recenterButtonRef.current) {
            recenterButtonRef.current.style.backgroundColor = isHighlighted
                ? "rgba(255, 68, 68, 0.9)"
                : "rgba(68, 68, 255, 0.8)";
            recenterButtonRef.current.style.transform = isHighlighted
                ? "scale(1.1)"
                : "scale(1)";
        }
    };

    const recenterCamera = () => {
        console.log("Re-centering camera and grid");

        // Reset grid rotation
        gridGroupRef.current.rotation.set(0, 0, 0);

        // Reset camera position
        cameraRef.current.position.set(25, 25, 25);
        cameraRef.current.lookAt(0, 0, 0);

        // Flash button green
        if (recenterButtonRef.current) {
            recenterButtonRef.current.style.backgroundColor = "rgba(0, 255, 0, 0.9)";
            setTimeout(() => {
                recenterButtonRef.current.style.backgroundColor = "rgba(68, 68, 255, 0.8)";
            }, 200);
        }
    };

    return (
        <div
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100vw",
                height: "100vh",
                margin: 0,
                padding: 0,
                overflow: "hidden",
            }}
        >
            <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    zIndex: 0,
                    backgroundColor: "black",
                    transform: "scaleX(-1)",
                }}
            />

            <canvas
                ref={overlayCanvasRef}
                style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    zIndex: 3,
                    pointerEvents: "none",
                    transform: "scaleX(-1)",
                }}
            />

            <div
                ref={mountRef}
                style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    zIndex: 1,
                    pointerEvents: "none",
                }}
            />

            <button
                ref={recenterButtonRef}
                style={{
                    position: "absolute",
                    top: 20,
                    left: 20,
                    width: "80px",
                    height: "80px",
                    borderRadius: "50%",
                    backgroundColor: "rgba(68, 68, 255, 0.8)",
                    border: "3px solid white",
                    color: "white",
                    fontFamily: "monospace",
                    fontSize: "12px",
                    fontWeight: "bold",
                    cursor: "pointer",
                    zIndex: 5,
                    transition: "all 0.2s ease",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    pointerEvents: "none",
                }}
            >
                PINCH TO RECENTER
            </button>

            <div
                style={{
                    position: "absolute",
                    bottom: 20,
                    left: 20,
                    color: "white",
                    fontFamily: "monospace",
                    fontSize: "14px",
                    backgroundColor: "rgba(0,0,0,0.8)",
                    padding: "15px",
                    borderRadius: "8px",
                    zIndex: 4,
                }}
            >
                <div style={{ fontSize: "18px", marginBottom: "10px" }}>
                    Blocks: {blockCount}
                </div>
                <div style={{ fontSize: "12px" }}>
                    <div>Right Hand Pinch: Place Block</div>
                    <div>Left Hand Pinch: Delete Block</div>
                    <div>Fist + Drag: Rotate Grid</div>
                    <div>Two Fists + Drag: Pan Camera</div>
                    <div>Two Hands Pinch: Zoom In/Out</div>
                </div>
            </div>
        </div>
    );
};

export default BlockBuilder3D;
