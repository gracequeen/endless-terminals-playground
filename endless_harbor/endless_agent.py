# echos_harbor/echos_agent.py
"""Echos agent for Harbor benchmark framework."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field

from transformers import AutoTokenizer

# Regex to strip ANSI escape codes (same as generator/env.py)
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

# Shell initialization noise patterns to filter out
SHELL_NOISE_PATTERNS = [
    re.compile(r"^bash: cannot set terminal process group.*$", re.MULTILINE),
    re.compile(r"^bash: no job control in this shell.*$", re.MULTILINE),
    re.compile(r"^mesg: ttyname failed:.*$", re.MULTILINE),
    re.compile(r"^stdin: is not a tty.*$", re.MULTILINE),
    re.compile(r"^the input device is not a TTY.*$", re.MULTILINE),
    re.compile(r"^warning: TERM environment variable not set.*$", re.MULTILINE | re.IGNORECASE),
]

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.sample_solutions import SYSTEM_MESSAGE, USER_TEMPLATE, _extract_action
from generator import chat_completion_batch

# Harbor imports
from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


MAX_OUTPUT_LENGTH = 50000


def _clean_output(output: str) -> str:
    """
    Clean command output by removing ANSI codes, carriage returns,
    and common shell initialization noise.
    """
    # Strip ANSI escape codes
    cleaned = ANSI_RE.sub("", output)
    
    # Remove carriage returns
    cleaned = cleaned.replace("\r", "")
    
    # Filter out shell initialization noise
    for pattern in SHELL_NOISE_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    
    # Clean up multiple blank lines that may result from filtering
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    return cleaned.strip()


class LLMActionDecision(BaseModel):
    """
    STRICT JSON the model must return each turn.
    """
    type: Literal["command", "done", "invalid"] = Field(
        description="Choose 'command' to run a shell command, or 'done' to finish."
    )
    command: Optional[str] = Field(
        default=None,
        description="Required when type == 'command'. Exact shell command to run.",
    )
    timeout_sec: Optional[float] = Field(
        default=180.0,
        description="Optional per-command timeout (seconds) when blocking on output.",
    )

    model_config = ConfigDict(extra="forbid")


class EndlessAgent(BaseAgent):
    """
    Echos terminal agent for Harbor benchmark.
    
    Prompts the LLM using the echos format (SYSTEM_MESSAGE + USER_TEMPLATE)
    and executes commands directly via environment.exec().
    """

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        *args,
        temperature: float = 0.6,
        max_episodes: int = 64,
        max_time_sec: float = 600,
        max_completion_tokens: int = 2048,
        agent_version: str = "1.0.0",
        **kwargs,
    ):
        """
        Initialize the Echos agent.
        
        Args:
            logs_dir: Directory to store logs.
            model_name: The model to use for completions.
            temperature: Sampling temperature.
            max_episodes: Maximum number of action turns.
            max_time_sec: Maximum wall-clock time for task execution.
            max_completion_tokens: Maximum tokens per completion.
            agent_version: Version string for this agent.
        """
        super().__init__(logs_dir, model_name, *args, **kwargs)
        # Harbor passes agent env vars (--ae KEY=VAL) via `extra_env`; it does not
        # propagate them to os.environ. chat_completion_batch reads VLLM_BASE_URL
        # from os.environ, so bridge it here to route requests to the right vLLM server.
        extra_env = kwargs.get("extra_env") or {}
        if "VLLM_BASE_URL" in extra_env:
            os.environ["VLLM_BASE_URL"] = extra_env["VLLM_BASE_URL"]
        self._model_name = model_name or "obiwan96/ota-350"
        self.max_completion_tokens = max_completion_tokens
        self.temperature = temperature
        self._max_episodes = max_episodes
        self._max_time = max_time_sec
        self._agent_version = agent_version
        self._chat: list[dict[str, str]] = []
        self._original_first_user_content: str = ""  # Store original to avoid accumulating history summaries
        self.start_time = time.time()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._tokenizer = None
        self._tokenizer_loaded = False

    @staticmethod
    def name() -> str:
        """The name of the agent."""
        return "echos"

    def version(self) -> str | None:
        """The version of the agent."""
        return self._agent_version

    async def setup(self, environment: BaseEnvironment) -> None:
        """
        Run commands to setup the agent & its tools.
        No special setup required - we use environment.exec() directly.
        """
        # Reset chat history and token counters for new task
        self._chat = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        
        # Reset terminal to fix alternate character set issues
        # \ec is the escape sequence for RIS (Reset to Initial State)
        await environment.exec(command="echo -e '\\ec'", timeout_sec=5)

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """
        Runs the agent in the environment.
        
        Args:
            instruction: The task instruction.
            environment: The environment in which to complete the task.
            context: The context to populate with the results of the agent execution.
        """
        # Render initial prompt using echos-style templates
        initial_user = self._render_initial_user(instruction)

        # Seed chat with echos-style system+user
        self._chat = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": initial_user},
        ]
        # Store original first user content to avoid accumulating history summaries on retries
        self._original_first_user_content = initial_user

        n_episodes = 0
        # Main loop
        start = time.perf_counter()
        try:
            for episode in range(1, self._max_episodes + 1):
                n_episodes = episode
                
                # Get decision from model
                decision, raw_response = await self._ask_for_decision()
                
                # Record assistant response
                self._chat.append({"role": "assistant", "content": raw_response})

                if decision["type"] == "done":
                    print(f"[Episode {episode}] Agent finished (done)")
                    break

                elif decision["type"] == "command":
                    cmd = decision["command"] or ""
                    timeout = decision.get("timeout_sec", 180.0) or 180.0
                    print(f"[Episode {episode}] Sending command (timeout={timeout}s): {cmd}")

                    # Execute command directly via environment.exec()
                    try:
                        result = await environment.exec(command=cmd, timeout_sec=int(300))
                        exit_code = result.return_code
                        # Combine stdout and stderr for output
                        output = (result.stdout or "") + (result.stderr or "")
                        
                        # Clean output (ANSI codes + carriage returns)
                        output = _clean_output(output)
                        output, truncated_msg = self._truncate_output(output)
                        
                        print(f"[Episode {episode}] Output (exit={exit_code}): {output[:500]}{'...' if len(output) > 500 else ''}")
                        
                        if exit_code == 0:
                            result_back = f"Command executed successfully. Output: {output}{truncated_msg}\n\n(exit_code={exit_code})"
                        else:
                            result_back = f"Command failed. Output: {output}{truncated_msg}\n\n(exit_code={exit_code})"
                            
                    except Exception as e:
                        print(f"[Episode {episode}] Command failed with error: {e}")
                        result_back = f"Command failed with error: {str(e)}\n\n(exit_code=1)"

                    self._chat.append({"role": "user", "content": result_back})

                else:
                    # Invalid parse -> nudge the agent
                    result_back = (
                        "Could not parse a single <command>...</command> or <action>done</action>. "
                        "Please respond with exactly one of those."
                    )
                    self._chat.append({"role": "user", "content": result_back})

                # Wall-clock safety
                if (time.perf_counter() - start) > self._max_time:
                    break
        finally:
            # Populate context with metrics
            context.n_input_tokens = self._total_input_tokens
            context.n_output_tokens = self._total_output_tokens
            context.cost_usd = None
            context.metadata = {
                "n_episodes": n_episodes,
                "all_messages": self._chat,
            }

    def _truncate_output(self, output: str) -> tuple[str, str]:
        """Truncate very long outputs to prevent memory issues.
        
        Returns:
            Tuple of (truncated_output, truncated_msg)
        """
        truncated_msg = ""
        original_len = len(output)
        if original_len > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH]  # + "..." + output[-MAX_OUTPUT_LENGTH:]
            truncated_msg = f"\n[Output truncated: showing first {MAX_OUTPUT_LENGTH} of {original_len} characters]"
        return output, truncated_msg

    def _get_tokenizer(self):
        """Lazy-load and cache the tokenizer for the model."""
        if self._tokenizer_loaded:
            return self._tokenizer
        
        self._tokenizer_loaded = True

        
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        print(f"[Info] Loaded tokenizer for {self._model_name}")

        
        return self._tokenizer

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer."""
        tokenizer = self._get_tokenizer()
        return len(tokenizer.encode(text, add_special_tokens=False))

    def _count_chat_tokens(self, messages: list[dict[str, str]]) -> int:
        """Count total tokens in a chat message list."""
        tokenizer = self._get_tokenizer()
        total = 0
        chat = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        return len(chat)

    def _render_initial_user(self, instruction: str) -> str:
        """
        Render the initial user message using echos-style USER_TEMPLATE.
        """
        # Add restrictions to the instruction
        restrictions = (
            "\n\nRESTRICTIONS:\n"
            "- You cannot use sudo or any commands requiring root privileges.\n"
            "- You cannot use interactive tools like vim, nano, etc.\n"
            "- When running commands that prompt for input (yes/no, etc.), use non-interactive flags (e.g., `-y`, `--yes`, `--non-interactive`) when available, or pipe the inputs (e.g., `echo -e 'yes\\nno' | ./script.sh` or `yes | ./script.sh`) since you cannot interact with running processes.\n"
        )
        instruction_with_restrictions = instruction + restrictions
        
        try:
            return USER_TEMPLATE.format(task_description=instruction_with_restrictions)
        except Exception as e:
            raise ValueError(
                "generator.sample_solutions.USER_TEMPLATE must include '{task_description}'."
            ) from e

    def _build_command_history_summary(self) -> str:
        """
        Build a summary of commands and outputs from the chat history.
        
        Returns:
            A formatted string summarizing the command history.
        """
        history_parts = []
        # Skip system (index 0) and first user message (index 1)
        # Chat structure: system, user, assistant, user (output), assistant, user (output), ...
        i = 2
        cmd_num = 1
        while i < len(self._chat):
            msg = self._chat[i]
            if msg["role"] == "assistant":
                # Extract command from assistant response
                action = _extract_action(msg["content"])
                if action["type"] == "command" and action.get("command"):
                    cmd = action["command"]
                    # Next message should be the output (user role)
                    output = ""
                    if i + 1 < len(self._chat) and self._chat[i + 1]["role"] == "user":
                        output = self._chat[i + 1]["content"]
                        # Truncate output for summary
                        if len(output) > 500:
                            output = output[:500] + "... [truncated]"
                    history_parts.append(f"Command {cmd_num}: {cmd}\nOutput: {output}")
                    cmd_num += 1
            i += 1
        
        if not history_parts:
            return ""
        
        return "Here is a summary of commands and outputs from your previous attempts:\n\n" + "\n\n---\n\n".join(history_parts) + "\n\nPlease continue from where you left off."

    async def _ask_for_decision(self, retry_on_error: bool = True) -> tuple[dict, str]:
        """
        Ask the model for the next action.
        
        Args:
            retry_on_error: If True and response is None, truncate chat and retry.
        
        Returns:
            Tuple of (parsed action dict, raw response string)
        """
        # Run sync chat_completion_batch in executor to not block event loop
        loop = asyncio.get_event_loop()
        responses = await loop.run_in_executor(
            None,
            lambda: chat_completion_batch(
                [self._chat],
                model=self._model_name,
                temperature=self.temperature,
                max_tokens=self.max_completion_tokens,
                num_completions=1,
                max_concurrency=1,
            )
        )

        # Check for None response (batch completion error)
        if responses[0] is None:
            print("[Warning] Chat completion returned None, likely context too long or API error")
            
            if retry_on_error and len(self._chat) > 2:
                # Build command history summary before truncating
                history_summary = self._build_command_history_summary()
                
                # Keep system message and rebuild first user message from ORIGINAL content
                # This prevents accumulating history summaries on repeated failures
                system_msg = self._chat[0]
                first_user_content = self._original_first_user_content
                
                # Concatenate history summary to original first user message if we have any commands
                if history_summary:
                    first_user_content = first_user_content + "\n\n" + history_summary
                
                # Truncate chat with rebuilt first user message
                self._chat = [system_msg, {"role": "user", "content": first_user_content}]
                
                print("[Info] Truncated chat and added command history summary, retrying...")
                
                # Retry without allowing another retry to avoid infinite loop
                return await self._ask_for_decision(retry_on_error=False)
            else:
                # Return invalid action if we can't retry
                return {"type": "invalid", "command": None}, "Error: API returned None response"

        raw_str = responses[0].choices[0].message.content
        
        # Track token usage
        input_tokens = self._count_chat_tokens(self._chat)
        output_tokens = self._count_tokens(raw_str)
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        print(f"[Tokens] input={input_tokens}, output={output_tokens}, total_input={self._total_input_tokens}, total_output={self._total_output_tokens}")
        
        action = _extract_action(raw_str)
        return action, raw_str
