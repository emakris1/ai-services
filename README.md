# AI-Services
A collection of AI services and service infrastructure for use with interactive training applications.

## Prerequisites
- [Python v3.13.9](https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe)
- [uv v0.9.5](https://docs.astral.sh/uv/getting-started/installation/)
- [Erlang OTP v28.1.1](https://github.com/erlang/otp/releases/download/OTP-28.1.1/otp_win64_28.1.1.exe)
- [RabbitMQ Server v4.1.4](https://github.com/rabbitmq/rabbitmq-server/releases/download/v4.1.4/rabbitmq-server-4.1.4.exe)
- [NVIDIA CUDA Toolkit 12 Update 1](https://developer.download.nvidia.com/compute/cuda/12.9.1/network_installers/cuda_12.9.1_windows_network.exe)
- [NVIDIA cuDNN v9.15.0](https://developer.download.nvidia.com/compute/cudnn/9.15.0/local_installers/cudnn_9.15.0_windows.exe)
- [espeak-ng v1.52](https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-X64.msi)

## Setup
1. Install all prerequisites
2. [Add a user](https://www.rabbitmq.com/docs/access-control#adding-a-user) to your RabbitMQ server with the credentials
   specified in `rmq/src/ai_rmq/default_config.py` and
   [read/write permissions](https://www.rabbitmq.com/docs/access-control#grant-permissions) on the `/` virtual host
   (or the virtual host of your choice).
3. If you have not previously run PowerShell scripts in your environment before,
   run the following command in an admin-elevated PowerShell terminal to enable PowerShell script execution:
   ```
   Set-ExecutionPolicy RemoteSigned
   ```
4. Run `setup.ps1` to generate virtual environments and download dependencies with **uv**.

## Shared Packages
The services are built on two shared library packages:
- **ai-rmq** (`rmq/`) - RabbitMQ infrastructure: connections, consumers, producers, the `RmqService` that manages
  them, message serialization hooks, and default connection configuration.
- **ai-common** (`common/`) - Messages, enums, logging configuration, and utilities shared by multiple services.
  Depends on **ai-rmq**.

## Reinstalling Shared Packages
Since the **ai-rmq** and **ai-common** library packages are not editable dependencies, any source changes you make
will not be reflected in dependent service applications until the packages are reinstalled.

The simplest way to fix this is to force **uv** to reinstall the packages in the given service project:
```
cd services\<service>
uv sync --reinstall-package ai-common --reinstall-package ai-rmq
```
Alternatively, you can run `services\uv-sync-services.ps1`, which does this for all services.

Since **ai-common** depends on **ai-rmq**, changes to **ai-rmq** also require reinstalling it in the **ai-common**
project, which `common\uv-sync-common.ps1` does.

## Services
The services form a voice conversation loop, each stage handing off to the next through RabbitMQ:

1. **audio_capture_service** - Streams microphone audio, pausing while responses are played back so the AI doesn't
   hear itself.
2. **speech_recognition_service** - Detects speech with Silero VAD and transcribes it with Whisper.
3. **llm_response_service** - Generates a conversational reply to the transcribed speech with a local LLM, streaming
   it to speech synthesis one sentence at a time to minimize response latency.
4. **speech_synthesis_service** - Synthesizes speech for each sentence with Kokoro.
5. **audio_playback_service** - Plays the synthesized speech.

## LLM Response Service
By default, the LLM response service runs [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B), which is downloaded
from Hugging Face (~4.5 GB) on first run and uses ~3.6 GB of VRAM. Any Hugging Face chat model that works with
`AutoModelForCausalLM` can be swapped in with `--model`.

The persona and behavior of the AI are set by its system prompt, which can be customized with `--system-prompt` or
`--system-prompt-file`. Since every reply is spoken aloud, prompts should ask for brief, conversational responses
without formatting. The voice, which also determines the speech synthesis language, is set with `--voice`.

Run `uv run llm_response_service.py --help` for the full list of options.

## Quick Start
To run all services, run `run.ps1`.

## Running Services
To run a service, open a terminal in the desired service directory and run `uv run <service>.py`.

Each service has its own set of arguments, which can be viewed by running `uv run <service>.py --help`.

Alternatively, you can run `uv-run-services.ps1` to open a new terminal window
that will contain each service running in its own tab.
