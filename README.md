# Setup Instructions

This repository contains multiple backend modules under `se-backend` and
now also includes the `gpt_academic` project. Use the `setup_envs.sh`
script to create a separate Python 3.12 virtual environment for each
module. Requirements listed in each module's `requirements.txt` (and the
one under `gpt_academic`) will be installed automatically.

```bash
bash setup_envs.sh
```

The script assumes `python3.12` is available on your system. After the
setup you can launch the academic assistant with:

```bash
cd gpt_academic && .venv/bin/python main.py
```

GPT Academic listens on port **8001** and exposes its UI under the
`/llms` path. The Vue frontend proxies this path so you can access the
assistant through `http://localhost:5173/llms` while keeping the main
frontend available at the root.

The academic assistant now reuses the same account system as the
backend. Use the credentials you registered through the backend API to
log in when accessing `/llms`. A simple login screen will appear when you
open the assistant; enter your existing account details there.
