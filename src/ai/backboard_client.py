"""
Backboard.io client using their actual API structure (not OpenAI-compatible).

Based on official quickstart from https://app.backboard.io/api
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

import requests
from loguru import logger


class TaskType(Enum):
    """Types of tasks that determine which AI model to use."""

    CONVERSATIONAL = "conversational"  # Casual chat, quick responses
    ANALYTICAL = "analytical"  # Technical analysis, problem-solving
    CREATIVE = "creative"  # Storytelling, creative content
    TECHNICAL = "technical"  # Code generation, technical explanations


class BackboardClient:
    """
    Client for Backboard.io API with intelligent multi-model routing.

    Uses Backboard's native API structure:
    - Create assistant (with model selection)
    - Create thread (conversation)
    - Send messages
    """

    def __init__(self, api_key: str, user_id: str = "default_user"):
        """
        Initialize Backboard.io client.

        Args:
            api_key: Backboard.io API key (espr_...)
            user_id: User identifier for memory/personalization
        """
        self.api_key = api_key
        self.base_url = "https://app.backboard.io/api"
        self.headers = {"X-API-Key": api_key}
        self.user_id = user_id

        # Model routing configuration
        self.models = {
            TaskType.CONVERSATIONAL: "google/gemini-2.0-flash-exp",
            TaskType.ANALYTICAL: "anthropic/claude-3-5-sonnet-20241022",
            TaskType.CREATIVE: "openai/gpt-4o",
            TaskType.TECHNICAL: "anthropic/claude-3-5-sonnet-20241022",
        }

        # Backboard uses assistants + threads
        self.assistant_id = None
        self.thread_id = None
        self.current_model = self.models[TaskType.CONVERSATIONAL]
        self.current_task_type = TaskType.CONVERSATIONAL

        # Conversation history (for context)
        self.conversation_history: List[Dict] = []

        # Rate limiting
        self.last_api_call_time = time.time() - 10
        self.min_request_interval = 1.0

        logger.info("BackboardClient initialized with Backboard.io native API")
        logger.info(f"Available models: {self.models}")

    def classify_task_type(self, user_message: str) -> TaskType:
        """
        Classify the user's message to determine which AI model to use.

        Args:
            user_message: The user's input text

        Returns:
            TaskType enum indicating which model to use
        """
        message_lower = user_message.lower()

        # Technical/coding keywords
        technical_keywords = [
            "code", "function", "debug", "error", "api", "implement",
            "algorithm", "program", "script", "syntax", "bug", "compile",
            "variable", "class", "method", "import", "library"
        ]

        # Analytical keywords
        analytical_keywords = [
            "analyze", "explain", "why", "how does", "what if", "compare",
            "evaluate", "assess", "think about", "consider", "examine",
            "problem", "solve", "figure out", "understand"
        ]

        # Creative keywords
        creative_keywords = [
            "story", "write", "create", "imagine", "describe", "tell me about",
            "make up", "invent", "generate", "compose", "creative"
        ]

        # Check for technical queries
        if any(keyword in message_lower for keyword in technical_keywords):
            return TaskType.TECHNICAL

        # Check for analytical queries
        if any(keyword in message_lower for keyword in analytical_keywords):
            return TaskType.ANALYTICAL

        # Check for creative queries
        if any(keyword in message_lower for keyword in creative_keywords):
            return TaskType.CREATIVE

        # Default to conversational
        return TaskType.CONVERSATIONAL

    def get_model_for_task(self, task_type: TaskType) -> str:
        """Get the appropriate model for a given task type."""
        return self.models[task_type]

    def _create_assistant(self, model: str, system_prompt: str) -> str:
        """
        Create a new assistant with specified model.

        Args:
            model: Model identifier (e.g., "google/gemini-2.0-flash-exp")
            system_prompt: System prompt for the assistant

        Returns:
            Assistant ID
        """
        try:
            response = requests.post(
                f"{self.base_url}/assistants",
                json={
                    "name": f"Assistant_{self.user_id}",
                    "system_prompt": system_prompt,
                    "model": model  # Specify which model to use
                },
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            assistant_id = response.json()["assistant_id"]
            logger.info(f"Created assistant {assistant_id} with model {model}")
            return assistant_id
        except Exception as e:
            logger.error(f"Failed to create assistant: {e}")
            raise

    def _create_thread(self, assistant_id: str) -> str:
        """
        Create a new thread (conversation) for an assistant.

        Args:
            assistant_id: The assistant ID

        Returns:
            Thread ID
        """
        try:
            response = requests.post(
                f"{self.base_url}/assistants/{assistant_id}/threads",
                json={},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            thread_id = response.json()["thread_id"]
            logger.info(f"Created thread {thread_id}")
            return thread_id
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    def _send_message(self, thread_id: str, content: str) -> str:
        """
        Send a message to a thread.

        Args:
            thread_id: The thread ID
            content: Message content

        Returns:
            AI response content
        """
        try:
            response = requests.post(
                f"{self.base_url}/threads/{thread_id}/messages",
                headers=self.headers,
                data={
                    "content": content,
                    "stream": "false",
                    "memory": "Auto"  # Enable Backboard.io memory
                },
                timeout=30
            )
            response.raise_for_status()
            ai_response = response.json().get("content", "")
            return ai_response
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        force_task_type: Optional[TaskType] = None,
        temperature: float = 1.0,
        max_tokens: int = 150
    ) -> Tuple[str, float, str, TaskType]:
        """
        Generate AI response with intelligent model routing.

        Args:
            user_message: User's input text
            system_prompt: Optional system prompt
            force_task_type: Force a specific task type
            temperature: Sampling temperature (not used with Backboard API)
            max_tokens: Maximum tokens (not used with Backboard API)

        Returns:
            Tuple of (response_text, generation_time, model_used, task_type)
        """
        start_time = time.time()

        # Classify task type
        task_type = force_task_type or self.classify_task_type(user_message)
        model = self.get_model_for_task(task_type)

        # Check if we need to switch models (create new assistant)
        if model != self.current_model or self.assistant_id is None:
            logger.info(f"[MODEL SWITCH] {self.current_model} -> {model}")
            logger.info(f"[TASK TYPE] {self.current_task_type.value} -> {task_type.value}")

            # Create new assistant with the appropriate model
            self.assistant_id = self._create_assistant(
                model=model,
                system_prompt=system_prompt or "You are a helpful AI assistant."
            )

            # Create new thread
            self.thread_id = self._create_thread(self.assistant_id)

            self.current_model = model
            self.current_task_type = task_type

        # Rate limiting
        time_since_last_call = time.time() - self.last_api_call_time
        if time_since_last_call < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_call
            logger.debug(f"[RATE LIMIT] Waiting {wait_time:.2f}s")
            time.sleep(wait_time)

        try:
            self.last_api_call_time = time.time()

            # Send message
            response_text = self._send_message(self.thread_id, user_message)
            generation_time = time.time() - start_time

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response_text})

            logger.info(f"[{model}] Generated response in {generation_time:.2f}s")

            return response_text, generation_time, model, task_type

        except Exception as e:
            logger.error(f"Backboard.io API error: {e}")
            generation_time = time.time() - start_time
            return f"[Error: {e}]", generation_time, model, task_type

    def get_current_model_info(self) -> Dict[str, str]:
        """
        Get information about the currently active model.

        Returns:
            Dict with model name, task type, and provider
        """
        provider = self.current_model.split("/")[0]
        model_name = self.current_model.split("/")[1]

        return {
            "full_model": self.current_model,
            "provider": provider,
            "model_name": model_name,
            "task_type": self.current_task_type.value
        }
