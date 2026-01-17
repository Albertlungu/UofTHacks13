"""
Style analyzer using HelpingAI-9B to analyze user communication patterns.
"""

import queue
import threading
from typing import Dict, List, Optional

import torch
from loguru import logger
from transformers import AutoModelForCausalLM, AutoTokenizer


class StyleAnalyzer:
    """
    Analyzes user speech patterns using HelpingAI-9B to generate
    style summaries for Gemini adaptation.
    """

    def __init__(self, model_name: str = "OEvortex/HelpingAI2-9B"):
        """
        Initialize the style analyzer.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"

        # Processing queue for background analysis
        self.analysis_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None
        self.is_running = False

        logger.info(f"StyleAnalyzer initialized (device: {self.device})")

    def load_model(self):
        """Load the HelpingAI model and tokenizer."""
        if self.model is not None:
            logger.info("Model already loaded")
            return

        logger.info(f"Loading {self.model_name}... (this may take a minute)")

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
            )

            # Move to device
            self.model.to(self.device)

            logger.info(f"Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def create_analysis_prompt(
        self, user_transcripts: List[str], analysis_type: str = "initial"
    ) -> str:
        """
        Create a prompt for HelpingAI to analyze user style.

        Args:
            user_transcripts: List of things user said
            analysis_type: 'initial' (calibration) or 'refinement' (ongoing)

        Returns:
            Formatted prompt for analysis
        """
        combined_speech = "\n".join([f"- {t}" for t in user_transcripts])

        if analysis_type == "initial":
            prompt = f"""Analyze the following speech samples from a user during their first minute of conversation. Create a detailed communication style profile that another AI (Gemini) can use to adapt its responses to match the user's style.

User's Speech Samples:
{combined_speech}

Please provide a structured analysis in XML format covering:

1. **Communication Style**:
   - Vocabulary level (casual, formal, technical, mixed)
   - Sentence complexity (simple, moderate, complex)
   - Tone (analytical, enthusiastic, contemplative, pragmatic, etc.)

2. **Speech Patterns**:
   - Pace and rhythm
   - Use of pauses and thinking time
   - Directness vs elaboration

3. **Personality Indicators**:
   - Key personality traits evident from speech
   - Communication preferences
   - Likely approach to problem-solving

4. **Topics & Interests**:
   - What topics did they discuss?
   - What seems to interest them?

5. **Example Phrases**:
   - Include 3-5 actual phrases they used that exemplify their style

Format your response as XML with clear tags. Be specific and actionable so another AI can use this to mirror their communication style."""

        else:  # refinement
            prompt = f"""Update the user's communication style profile based on these recent conversation exchanges. Focus on identifying any shifts in style, new topics of interest, or communication patterns.

Recent User Speech:
{combined_speech}

Provide an XML update focusing on:
- Any changes in communication style
- New topics or interests mentioned
- Evolving personality traits
- Additional example phrases

Keep the format consistent with the initial analysis."""

        return prompt

    def analyze_style(
        self,
        user_transcripts: List[str],
        analysis_type: str = "initial",
        callback: Optional[callable] = None,
    ) -> Optional[str]:
        """
        Analyze user's communication style.

        Args:
            user_transcripts: List of user's speech transcripts
            analysis_type: 'initial' or 'refinement'
            callback: Optional callback function(result: str) called when done

        Returns:
            Style analysis as XML string, or None if queued for background processing
        """
        if not self.model:
            logger.error("Model not loaded. Call load_model() first.")
            return None

        if not user_transcripts:
            logger.warning("No transcripts provided for analysis")
            return None

        # Create the analysis prompt
        analysis_prompt = self.create_analysis_prompt(user_transcripts, analysis_type)

        # Queue for background processing if callback provided
        if callback:
            self.analysis_queue.put((analysis_prompt, callback))
            if not self.is_running:
                self.start_background_processing()
            return None

        # Otherwise, process synchronously
        return self._run_analysis(analysis_prompt)

    def _run_analysis(self, prompt: str) -> str:
        """
        Run the actual analysis with HelpingAI.

        Args:
            prompt: The analysis prompt

        Returns:
            Generated style analysis
        """
        logger.info("Running style analysis...")

        try:
            # Create chat input
            chat = [
                {
                    "role": "system",
                    "content": "You are an expert communication analyst. Analyze speech patterns and create detailed style profiles in structured XML format.",
                },
                {"role": "user", "content": prompt},
            ]

            # Tokenize
            inputs = self.tokenizer.apply_chat_template(
                chat, add_generation_prompt=True, return_tensors="pt"
            ).to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=1024,  # Longer for detailed analysis
                    do_sample=True,
                    temperature=0.6,
                    top_p=0.9,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # Decode response
            response = outputs[0][inputs.shape[-1] :]
            analysis = self.tokenizer.decode(response, skip_special_tokens=True)

            logger.info(f"Style analysis complete ({len(analysis)} characters)")
            return analysis.strip()

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return ""

    def start_background_processing(self):
        """Start background thread for processing analysis queue."""
        if self.is_running:
            return

        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._background_processor, daemon=True
        )
        self.processing_thread.start()
        logger.info("Started background style analysis processor")

    def _background_processor(self):
        """Background thread that processes analysis requests."""
        logger.info("Background processor started")

        while self.is_running:
            try:
                # Get next analysis request (blocking with timeout)
                prompt, callback = self.analysis_queue.get(timeout=1.0)

                # Run analysis
                result = self._run_analysis(prompt)

                # Call callback with result
                if callback:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                self.analysis_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Background processor error: {e}")

        logger.info("Background processor stopped")

    def stop_background_processing(self):
        """Stop the background processing thread."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
            logger.info("Stopped background style analysis processor")

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None

            # Clear GPU cache
            if self.device == "mps":
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Model unloaded")


# Example usage function
def example_usage():
    """Example of how to use the StyleAnalyzer."""
    analyzer = StyleAnalyzer()
    analyzer.load_model()

    # Example user transcripts from calibration
    user_speech = [
        "So I've been thinking about this machine learning project",
        "I want to build something that actually helps people, you know?",
        "Not just another demo or tutorial thing",
        "Something real that solves a problem I care about",
    ]

    # Synchronous analysis
    style_summary = analyzer.analyze_style(user_speech, analysis_type="initial")
    print("Style Analysis:")
    print(style_summary)

    # Background analysis with callback
    def on_analysis_complete(result):
        print("Background analysis complete!")
        print(result)

    analyzer.analyze_style(
        user_speech, analysis_type="refinement", callback=on_analysis_complete
    )

    # Clean up
    analyzer.stop_background_processing()
    analyzer.unload_model()


if __name__ == "__main__":
    example_usage()
