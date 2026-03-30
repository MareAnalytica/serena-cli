#!/usr/bin/env python3
"""setup.py for serena-cli"""

from setuptools import setup, find_namespace_packages

setup(
    name="serena-cli",
    version="1.0.0",
    author="MareAnalytica",
    author_email="",
    description="Code intelligence CLI via Serena LSP-based MCP server. Structural symbol navigation, cross-codebase refactoring, and semantic code understanding.",
    long_description="serena-cli: Code intelligence CLI wrapping Serena MCP server for AI agent use.",
    long_description_content_type="text/plain",
    url="https://github.com/MareAnalytica/serena-cli",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "mcp>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "serena=cli_anything.serena.serena_cli:main",
        ],
    },
    package_data={
        "cli_anything.serena": ["skills/*.md"],
    },
    include_package_data=True,
    zip_safe=False,
)
