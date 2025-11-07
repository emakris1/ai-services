# ACV-CGT-AI
A collection of AI services and service infrastructure designed for use with the Crew Gunnery Trainer.

## Prerequisites
- [Python v3.13.9](https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe)
- [uv v0.9.5](https://docs.astral.sh/uv/getting-started/installation/)
- [Erlang OTP v28.1.1](https://github.com/erlang/otp/releases/download/OTP-28.1.1/otp_win64_28.1.1.exe)
- [RabbitMQ Server v4.1.4](https://github.com/rabbitmq/rabbitmq-server/releases/download/v4.1.4/rabbitmq-server-4.1.4.exe)
- [espeak-ng v1.52](https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-X64.msi)
- [NVIDIA CUDA Toolkit 12 Update 1](https://developer.download.nvidia.com/compute/cuda/12.9.1/network_installers/cuda_12.9.1_windows_network.exe)
- [NVIDIA cuDNN 9.15.0](https://developer.download.nvidia.com/compute/cudnn/9.15.0/local_installers/cudnn_9.15.0_windows.exe)

## Setup
1. Install all prerequisites
2. Run `services\uv-sync-services.ps1` to generate virtual environments and download dependencies with uv

## Modifying Core
Since the **cgt-ai-core** library package is not an editable dependency, any source changes you make will not be
reflected in dependent service applications until the package is reinstalled.

The simplest way to fix this is to force uv to reinstall packages in the given service project:
```
cd services\<service>
uv sync --reinstall
```
Alternatively, you can re-run `uv-sync-services.ps1`, which does this for all services.

## Running Services
Open a shell and start the test producer:
```
cd <path-to-project>\services\test_services
uv run test_producer.py
```
Open another shell and start the test consumer:
```
cd <path-to-project>\services\test_services
uv run test_consumer.py
```
