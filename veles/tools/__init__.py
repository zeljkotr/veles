"""Veles - a self-hosted DevOps assistant.

Minimal, dependency-light agent core: an LLM client, a tool registry,
an audit/confirmation gate, and a ReAct-style loop tying them together.
Designed to run against a local Ollama endpoint (currently tested with
Qwen3 8B on a GPU laptop, falls back to any smaller CPU model for
development).
"""
