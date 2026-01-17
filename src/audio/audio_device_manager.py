"""
./src/audio/audio_device_manager.py

Audio device manager for detecting and connecting to AirPods.
"""

from typing import Dict, List, Optional, Union

import pyaudio
from loguru import logger


class AudioDeviceManager:
    """Manages audio I/O devices, specifically for AirPods."""

    def __init__(self) -> None:
        self.audio = pyaudio.PyAudio()
        self.input_device_index: Optional[int] = None
        self.output_device_index: Optional[int] = None

    def list_all_devices(self) -> List[Dict]:
        """
        List all available audio devices.
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                devices.append(
                    {
                        "index": i,
                        "name": device_info.get("name"),
                        "max_input_channels": device_info.get("maxInputChannels"),
                        "max_output_channels": device_info.get("maxOutputChannels"),
                        "default_sample_rate": device_info.get("defaultSampleRate"),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not get info for device {i}: {e}")
        return devices

    def find_airpods(self) -> Optional[Dict[str, int]]:
        """
        Find AirPods device indices for input and output.
        Returns dict with 'input' and 'output' keys, or None if not found.
        """
        airpods_keywords = ["airpod", "airpods", "bluetooth"]
        devices = self.list_all_devices()

        input_device = None
        output_device = None

        for device in devices:
            name_lower = device["name"].lower()

            # Check if it's an AirPods device
            if any(keyword in name_lower for keyword in airpods_keywords):
                if device["max_input_channels"] > 0 and input_device is None:
                    input_device = device["index"]
                    logger.info(
                        f"Found AirPods input: {device['name']} (index: {device['index']})"
                    )

                if device["max_output_channels"] > 0 and output_device is None:
                    output_device = device["index"]
                    logger.info(
                        f"Found AirPods output: {device['name']} (index: {device['index']})"
                    )

        if input_device is not None and output_device is not None:
            self.input_device_index = input_device
            self.output_device_index = output_device
            return {"input": input_device, "output": output_device}

        logger.warning("AirPods not found. Available devices:")
        for device in devices:
            logger.info(
                f"  [{device['index']}] {device['name']} "
                f"(in: {device['max_input_channels']}, out: {device['max_output_channels']})"
            )

        return None

    def get_default_input_device(self) -> Union[str, int, float]:
        """Get the default input device index."""
        try:
            device_info = self.audio.get_default_input_device_info()
            return device_info["index"]
        except Exception as e:
            logger.error(f"Could not get default input device: {e}")
            return 0

    def get_default_output_device(self) -> int:
        """Get the default output device index."""
        try:
            device_info = self.audio.get_default_output_device_info()
            return device_info["index"]
        except Exception as e:
            logger.error(f"Could not get default output device: {e}")
            return 0

    def verify_device(self, device_index: int, input_device: bool = True) -> bool:
        """
        Verify that a device index is valid and supports input/output.

        Args:
            device_index: Device index to verify
            input_device: True to check input capabilities, False for output

        Returns:
            True if device is valid, False otherwise
        """
        try:
            device_info = self.audio.get_device_info_by_index(device_index)
            if input_device:
                return device_info.get("maxInputChannels", 0) > 0
            else:
                return device_info.get("maxOutputChannels", 0) > 0
        except Exception as e:
            logger.error(f"Could not verify device {device_index}: {e}")
            return False

    def cleanup(self):
        """Clean up PyAudio resources."""
        if self.audio:
            self.audio.terminate()
            logger.info("Audio device manager cleaned up")
