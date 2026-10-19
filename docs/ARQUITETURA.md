# Architecture

JARVIS local dashboard (Python HTTP server on 127.0.0.1) creates a new Obsidian-compatible vault under the current user's home directory. Six agent templates represent roles, not autonomous processes. Mission state is saved in a local JSON file, with SHA-256 duplicate detection. All external model providers and desktop control are opt-in extensions.
