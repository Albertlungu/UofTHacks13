"""
Gemini Image Generator - Creates visual memory collages for conversations.

Uses Google's Imagen 3 to generate images when topics are visually relevant,
creating a 3D collage of the conversation in the BlockBuilder.
"""

import base64
import io
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import google.generativeai as genai
from google.cloud import aiplatform
from PIL import Image as PILImage
from loguru import logger


class GeminiImageGenerator:
    """
    Generates images using Gemini's Imagen 3 when conversation topics are visually relevant.
    """

    def __init__(self, api_key: str, output_dir: str = "data/generated_images", project_id: str = None):
        """
        Initialize the image generator.

        Args:
            api_key: Google AI API key (same as used for chat)
            output_dir: Directory to save generated images
            project_id: Google Cloud project ID (for Imagen 3)
        """
        genai.configure(api_key=api_key)
        self.api_key = api_key

        # Set up Google Cloud AI Platform for Imagen
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if self.project_id:
            aiplatform.init(project=self.project_id, location="us-central1")
            logger.info(f"Imagen 3 initialized with project: {self.project_id}")
        else:
            logger.warning("No GOOGLE_CLOUD_PROJECT set - will use placeholder images")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Model for deciding if we should generate
        self.decision_model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Rate limiting
        self.last_generation_time = 0
        self.min_generation_interval = 15.0  # Min 15s between images

        # Track recent conversation context
        self.recent_messages = []
        self.max_context_messages = 10

        logger.info(f"GeminiImageGenerator initialized, saving to {self.output_dir}")

    def should_generate_image(self, user_message: str, ai_response: str) -> Tuple[bool, Optional[str]]:
        """
        Decide if the current conversation topic warrants an image.

        Args:
            user_message: What the user just said
            ai_response: How the AI responded

        Returns:
            Tuple of (should_generate, prompt_for_image)
        """
        # Rate limit check
        current_time = time.time()
        if current_time - self.last_generation_time < self.min_generation_interval:
            return False, None

        # Update context
        self.recent_messages.append({"user": user_message, "ai": ai_response})
        if len(self.recent_messages) > self.max_context_messages:
            self.recent_messages.pop(0)

        # Build context string
        context_str = "\n".join([
            f"User: {msg['user']}\nAI: {msg['ai']}"
            for msg in self.recent_messages[-5:]  # Last 5 exchanges
        ])

        # Ask Gemini if we should generate
        decision_prompt = f"""You're analyzing a voice conversation to determine if we should generate a visual representation.

Recent conversation:
{context_str}

Should we generate an image for this conversation? Only say YES if:
- The topic is VISUALLY concrete (places, objects, scenes, people, concepts that can be visualized)
- It's a significant topic that's been discussed for a bit
- It would be meaningful to remember visually

DON'T generate for:
- Abstract concepts with no visual representation
- Technical discussions about code/APIs
- Quick casual chat

If YES, respond EXACTLY in this format:
YES: [a detailed, vivid image generation prompt in 1-2 sentences that captures the essence of what's being discussed]

If NO, respond with just:
NO

Your response:"""

        try:
            response = self.decision_model.generate_content(decision_prompt)
            decision = response.text.strip()

            if decision.startswith("YES:"):
                image_prompt = decision[4:].strip()
                logger.info(f"Image generation triggered: {image_prompt[:100]}...")
                return True, image_prompt
            else:
                return False, None

        except Exception as e:
            logger.error(f"Error deciding image generation: {e}")
            return False, None

    def generate_and_save_image(self, prompt: str) -> Optional[str]:
        """
        Generate an image using Imagen 3 and save it.

        Args:
            prompt: Image generation prompt

        Returns:
            Path to saved image, or None if failed
        """
        try:
            logger.info(f"Generating image with Imagen 3: {prompt[:100]}...")

            # Try Imagen 3 first
            if self.project_id:
                try:
                    image_bytes = self._generate_with_imagen3(prompt)
                    if image_bytes:
                        return self._save_image_bytes(image_bytes, prompt)
                except Exception as e:
                    logger.warning(f"Imagen 3 failed, falling back to placeholder: {e}")

            # Fallback to colorful placeholder
            logger.info("Using placeholder image generation")
            return self._generate_placeholder(prompt)

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

    def _generate_with_imagen3(self, prompt: str) -> Optional[bytes]:
        """Generate image using Imagen 3 via Vertex AI."""
        from vertexai.preview.vision_models import ImageGenerationModel

        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",  # Square for cube textures
            safety_filter_level="block_few",
            person_generation="allow_adult",
        )

        if response.images:
            # Get the image bytes
            image = response.images[0]
            return image._image_bytes

        return None

    def _generate_placeholder(self, prompt: str) -> Optional[str]:
        """Generate colorful placeholder image with text."""
        import random
        from PIL import Image, ImageDraw, ImageFont

        size = 512
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)

        # Random gradient
        colors = [
            [(255, 100, 100), (100, 100, 255)],
            [(100, 255, 100), (255, 255, 100)],
            [(255, 150, 200), (150, 100, 255)],
            [(100, 200, 255), (255, 200, 100)],
            [(200, 100, 255), (100, 255, 200)],
        ]
        color_pair = random.choice(colors)

        for y in range(size):
            ratio = y / size
            r = int(color_pair[0][0] * (1 - ratio) + color_pair[1][0] * ratio)
            g = int(color_pair[0][1] * (1 - ratio) + color_pair[1][1] * ratio)
            b = int(color_pair[0][2] * (1 - ratio) + color_pair[1][2] * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b))

        # Add text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()

        text = prompt[:50] + ("..." if len(prompt) > 50 else "")
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2

        draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 128), font=font)
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_{timestamp}.png"
        filepath = self.output_dir / filename
        img.save(filepath)

        logger.info(f"Placeholder image saved: {filepath}")
        self.last_generation_time = time.time()
        return str(filepath)

    def _save_image_bytes(self, image_bytes: bytes, prompt: str) -> str:
        """Save image bytes to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_{timestamp}.png"
        filepath = self.output_dir / filename

        # Convert bytes to PIL Image and save
        img = PILImage.open(io.BytesIO(image_bytes))
        img.save(filepath)

        logger.info(f"Imagen 3 image saved: {filepath}")
        self.last_generation_time = time.time()
        return str(filepath)

    def process_conversation_turn(
        self,
        user_message: str,
        ai_response: str
    ) -> Optional[str]:
        """
        Process a conversation turn and potentially generate an image.

        Args:
            user_message: What the user said
            ai_response: How the AI responded

        Returns:
            Path to generated image, or None if no image generated
        """
        should_generate, prompt = self.should_generate_image(user_message, ai_response)

        if should_generate and prompt:
            return self.generate_and_save_image(prompt)

        return None

    def get_recent_images(self, count: int = 10) -> list[str]:
        """
        Get paths to the most recent generated images.

        Args:
            count: Number of recent images to return

        Returns:
            List of image paths, most recent first
        """
        images = sorted(
            self.output_dir.glob("memory_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return [str(img) for img in images[:count]]


# Test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found")
        exit(1)

    generator = GeminiImageGenerator(api_key)

    # Test conversation
    test_exchanges = [
        ("Hey, I just visited the Grand Canyon", "Oh wow! What was it like?"),
        ("It was incredible, the sunset colors were amazing", "That sounds beautiful! The red rocks must have been stunning"),
    ]

    for user_msg, ai_msg in test_exchanges:
        print(f"\nUser: {user_msg}")
        print(f"AI: {ai_msg}")

        image_path = generator.process_conversation_turn(user_msg, ai_msg)
        if image_path:
            print(f"✓ Generated image: {image_path}")
        else:
            print("✗ No image generated")

        time.sleep(2)
