"""Reads a traced conduct prompt with a small open model and reports what it sees inside.

The hosted model that conducts a survey exposes no hidden layers and no attention, so this
service reads the exact same prompt with Qwen3-0.6B and reports what that model does with
it. Every figure it returns is about Qwen reading the prompt, never about the hosted
model's internals, and the pages that draw it say so.
"""
