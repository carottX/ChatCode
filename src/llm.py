import os
import subprocess
import sys

import inquirer
from langchain.callbacks.manager import CallbackManager
from langchain_openai import AzureChatOpenAI, ChatOpenAI, OpenAI

import utils
from constants import LlmHost

class LLM:
    def __init__(
        self, llm_host: LlmHost, chat_model: str, max_tokens=2048, deployment=None
    ):
        """
        Initializes the LLM class with the specified parameters.

        Args:
            llm_host (LlmHost): The host for the language model (e.g., OPENAI, AZURE_OPENAI, ANTHROPIC, LLAMACPP, OLLAMA).
            chat_model (str): The chat model to use.
            max_tokens (int, optional): The maximum number of tokens for the model. Defaults to 2048.
            deployment (str, optional): The deployment name for Azure OpenAI. Defaults to None.

        Raises:
            ValueError: If the required environment variable for Azure OpenAI is not set.
        """
        
        # print(self.chat_model.invoke("Hello, world!"))