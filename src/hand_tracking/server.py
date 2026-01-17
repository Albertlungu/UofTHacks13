"""
WebSocket server for streaming hand tracking data to the frontend.
Clean implementation with proper error handling.
"""

import asyncio
import json
from typing import Set
import cv2
import numpy as np
import websockets
from loguru import logger

from src.hand_tracking.tracker import HandTracker


class HandTrackingServer:
    """WebSocket server for streaming hand tracking data."""

    def __init__(self, camera_index: int = 0, port: int = 8765):
        """
        Initialize the hand tracking server.

        Args:
            camera_index: Camera device index
            port: WebSocket port
        """
        self.camera_index = camera_index
        self.port = port
        self.tracker = HandTracker()
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        logger.info(f"HandTrackingServer initialized on port {port}")

    async def handle_client(self, websocket):
        """Handle new WebSocket client connection."""
        self.clients.add(websocket)
        logger.info(
            f"Client connected: {websocket.remote_address} | Total: {len(self.clients)}"
        )

        try:
            await websocket.wait_closed()
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
            logger.info(
                f"Client disconnected: {websocket.remote_address} | Remaining: {len(self.clients)}"
            )

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        # Send to each client, removing failed connections
        failed_clients = []
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.warning(
                    f"Failed to send to {client.remote_address}: {e}"
                )
                failed_clients.append(client)

        # Clean up failed connections
        for client in failed_clients:
            self.clients.discard(client)

    def _sanitize_for_json(self, obj):
        """Convert numpy types to native Python for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(self._sanitize_for_json(v) for v in obj)
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    async def stream_hand_data(self):
        """Capture camera frames and stream hand tracking data."""
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return

        # Set camera properties for optimal performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 60)

        logger.info("Camera opened, starting hand tracking stream...")

        try:
            frame_count = 0
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    await asyncio.sleep(0.1)
                    continue

                frame_count += 1

                try:
                    # Process frame
                    hand_data = self.tracker.process_frame(frame)

                    # Sanitize for JSON
                    hand_data = self._sanitize_for_json(hand_data)

                    # Broadcast if we have data and clients
                    if hand_data.get("hands") and self.clients:
                        message = json.dumps(hand_data)
                        await self.broadcast(message)

                        # Log every 60 frames
                        if frame_count % 60 == 0:
                            logger.info(
                                f"Frame {frame_count}: {len(hand_data['hands'])} hands detected"
                            )

                except Exception as e:
                    logger.error(f"Error processing frame {frame_count}: {e}")

                # 60 FPS target
                await asyncio.sleep(1 / 60)

        except Exception as e:
            logger.error(f"Error in capture loop: {e}")
        finally:
            cap.release()
            logger.info("Camera released")

    async def start(self):
        """Start the WebSocket server."""
        self.is_running = True

        logger.info(f"Starting WebSocket server on ws://localhost:{self.port}")

        async with websockets.serve(self.handle_client, "localhost", self.port):
            logger.info("WebSocket server running")
            logger.info("Waiting for client connections...")

            # Start camera streaming
            await self.stream_hand_data()

    def stop(self):
        """Stop the server."""
        self.is_running = False
        self.tracker.cleanup()
        logger.info("HandTrackingServer stopped")


async def main():
    """Run the hand tracking server."""
    import sys

    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    logger.info("=== 3D Block Builder - Hand Tracking Server ===")
    logger.info(f"Camera index: {camera_index}")
    logger.info("")
    logger.info("Gestures:")
    logger.info("- Right hand pinch: Add block")
    logger.info("- Left hand pinch: Remove block")
    logger.info("- Single fist + drag: Rotate plane")
    logger.info("- Two fists + drag: Pan camera")
    logger.info("- Two hands pinch + spread: Zoom")
    logger.info("")

    server = HandTrackingServer(camera_index=camera_index, port=8765)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        server.stop()


if __name__ == "__main__":
    asyncio.run(main())
