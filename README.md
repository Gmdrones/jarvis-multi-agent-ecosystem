# JARVIS Multi-Agent Ecosystem — Community Edition

> Build your own local AI command center with Obsidian memory, multiple agents, Ollama, and integration guides for Gemini, ChatGPT, Maestri and MCP Remote Desktop Commander.

![Status](https://img.shields.io/badge/status-community%20MVP-blue) ![Platform](https://img.shields.io/badge/platform-Windows-0078D4) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Local JARVIS-inspired mission control dashboard
- Independent Obsidian vault with mission records and searchable memory
- Supervisor, planning, execution, memory and audit agent templates
- Local Ollama integration
- Guides for OpenAI, Gemini, Maestri and Remote Desktop Commander MCP
- Mission duplicate detection and tests

## Install on Windows

Download the complete project ZIP from the repository's **Code → Download ZIP** option after all project files have been uploaded.

1. Install Python 3.10+.
2. Review `install.ps1` and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1`.
3. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1`.
4. Open http://127.0.0.1:8765.
5. Open the newly created vault in Obsidian.

## Important limitations

This is an educational community MVP, **not** a fully integrated autonomous multi-agent installer. The local dashboard, memory, mission registration and optional Ollama query are implemented in the distribution. Gemini/OpenAI requests, Maestri orchestration and MCP remote pairing require additional configuration or development. No existing vaults, personal memories, credentials or private projects are bundled.

## Security

Never commit API keys, personal memories, production configurations or authentication tokens. Keep the dashboard bound to localhost and review all scripts before execution.

## License

MIT. Independent community project; not affiliated with Obsidian, Maestri, Google, OpenAI, Ollama or Desktop Commander.
