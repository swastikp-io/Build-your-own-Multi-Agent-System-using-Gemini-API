# Multi-Agent Research System (Terminal Version)

This guide explains how to set up and run a multi-agent research system, similar to the web version, but entirely within your VS Code terminal using Python.

## 1. Project Setup

Follow these steps to get your project ready.

### a. Create a Project Folder

First, create a new folder for your project in VS Code.

### b. Set up a Python Virtual Environment

It's a best practice to use a virtual environment to manage project-specific libraries. Open your VS Code terminal (`View` > `Terminal`) and run:

```
# Create the virtual environment
python -m venv .venv

# Activate the environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate
# On macOS/Linux:
source .venv/bin/activate

```

### c. Install Required Libraries

You'll need the Google Gemini library and `python-dotenv` to manage your API key securely.

```
pip install google-generativeai python-dotenv

```

## 2. Create Your Project Files

You will need two files in your project folder:

### a. `.env` file (for your API Key)

Create a new file named `.env` (just `.env`). This is where you'll securely store your API key. **Do not share this file with anyone.**

```
GEMINI_API_KEY="YOUR_API_KEY_HERE"

```

Replace `YOUR_API_KEY_HERE` with your actual Gemini API key.

### b. `multi_agent_terminal.py`

Create a file named `multi_agent_terminal.py`. This is where the main Python script (provided in the other file) will go.

## 3. How to Run the System

Once you have:

1. Activated your virtual environment (`.venv`).
2. Installed the libraries (`pip install ...`).
3. Created your `.env` file with your API key.
4. Saved the Python code into `multi_agent_terminal.py`.

You can run the system from your VS Code terminal. You pass your research goal as an argument after the script name.

**Example:**

```
python multi_agent_terminal.py "What are the latest breakthroughs in battery technology for electric vehicles?"

```

The script will then start, and you'll see the "System Log" printed directly to your terminal, followed by the "Final Report" at the end.

### Next Steps: Advanced Frameworks

This script is a great way to understand the fundamentals. When you're ready to build more complex, stateful, and robust systems, I recommend looking into dedicated multi-agent frameworks that work with Gemini:

- **Microsoft AutoGen:** A very popular framework for creating conversations between multiple agents. (See: `https://github.com/microsoft/autogen`)
- **Google's Agent Development Kit (ADK):** A code-first Python toolkit from Google, optimized for Gemini, for building and deploying sophisticated AI agents. (See: `https://github.com/google/adk-python`)
