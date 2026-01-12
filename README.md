# ACV-CGT-AI
A collection of AI services and service infrastructure designed for use with the Crew Gunnery Trainer.

## Prerequisites
- [Python v3.13.9](https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe)
- [uv v0.9.5](https://docs.astral.sh/uv/getting-started/installation/)
- [Erlang OTP v28.1.1](https://github.com/erlang/otp/releases/download/OTP-28.1.1/otp_win64_28.1.1.exe)
- [RabbitMQ Server v4.1.4](https://github.com/rabbitmq/rabbitmq-server/releases/download/v4.1.4/rabbitmq-server-4.1.4.exe)
- [NVIDIA CUDA Toolkit 12 Update 1](https://developer.download.nvidia.com/compute/cuda/12.9.1/network_installers/cuda_12.9.1_windows_network.exe)
- [NVIDIA cuDNN v9.15.0](https://developer.download.nvidia.com/compute/cudnn/9.15.0/local_installers/cudnn_9.15.0_windows.exe)
- [Flutter v3.35.7](https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.35.7-stable.zip)
- [espeak-ng v1.52](https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-X64.msi)

## Setup
1. Install all prerequisites
    1. Follow the [setup instructions](https://docs.flutter.dev/install/manual#install-flutter) for a manual Flutter installation.
2. [Add a user](https://www.rabbitmq.com/docs/access-control#adding-a-user) to your RabbitMQ server with the credentials
   specified in `core/src/cgt_ai_core/rmq_default_config.py` and
   [read/write permissions](https://www.rabbitmq.com/docs/access-control#grant-permissions) on the `/` virtual host
   (or the virtual host of your choice).
3. If you have not previously run PowerShell scripts in your environment before,
   run the following command in an admin-elevated PowerShell terminal to enable PowerShell script execution:
   ```
   Set-ExecutionPolicy RemoteSigned
   ```
4. Run `setup.ps1` to generate virtual environments and download dependencies with **uv**, and build the **Flutter** UI.

## Reinstalling Core
Since the **cgt-ai-core** library package is not an editable dependency, any source changes you make will not be
reflected in dependent service applications until the package is reinstalled.

The simplest way to fix this is to force **uv** to reinstall the **cgt-ai-core** package in the given service project:
```
cd services\<service>
uv sync --reinstall-package cgt-ai-core
```
Alternatively, you can run `services\uv-sync-services.ps1`, which does this for all services.

## Rebuilding the UI
To rebuild the UI, run `ui\build-ui.ps1`.

## Quick Start
To run all services and the command editor UI, run `run.ps1`.

## Running Services
To run a service, open a terminal in the desired service directory and run `uv run <service>.py`.

Each service has its own set of arguments, which can be viewed by running `uv run <service>.py --help`.

Alternatively, you can run `uv-run-services.ps1` to open a new terminal window
that will contain each service running in its own tab.

## Running the UI
To run the UI, open a terminal in the `ui` directory and run `run-ui.ps1`.
