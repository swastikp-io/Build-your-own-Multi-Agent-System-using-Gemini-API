import google.generativeai as genai
import google.api_core.exceptions
import os
import sys
import json
import argparse
import time
from dotenv import load_dotenv

# --- Configuration ---

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not found. Please create a .env file and add it.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# Define safety settings for content generation
# This is a permissive setting; adjust as needed for your use case.
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- Agent "Personas" (System Prompts) ---

MANAGER_PROMPT = """You are a meticulous Project Manager. Your job is to break down a complex research goal into a small list of 3-5 specific, sequential research questions.
You must respond ONLY with a valid JSON array of strings. Do not include any other text, markdown, or explanations.
Example: ["question 1", "question 2", "question 3"]"""

RESEARCHER_PROMPT = """You are an expert Research Analyst. Your job is to find the most relevant, up-to-date information for a specific query.
You MUST use your search tool to find this information.
Respond with a concise, factual summary of your findings. Cite sources if possible."""

WRITER_PROMPT = """You are a professional Report Writer. Your job is to take a collection of research notes (each tied to a specific question) and synthesize them into a single, cohesive, well-structured report.
Do not just list the findings; weave them into a narrative.
Start with an introduction, then present the findings in body paragraphs, and conclude with a summary.
Respond in well-formatted Markdown (use headings, bold text, and lists where appropriate)."""

# --- Helper Functions ---

def log_message(agent, message):
    """Helper function to print formatted log messages to the terminal."""
    print(f"\n--- 🤖 {agent} ---\n{message}")

def log_system(message):
    """Helper function for system-level log messages."""
    print(f"\n--- ▶️ [System] ---\n{message}")

async def call_gemini(system_prompt, user_prompt, use_search=False, retries=3, delay=5):
    """
    Helper function to call the Gemini API with exponential backoff.
    
    Args:
        system_prompt (str): The role/persona for the agent.
        user_prompt (str): The specific task/question.
        use_search (bool): Whether to enable Google Search grounding.
        retries (int): Number of retries on failure.
        delay (int): Initial delay in seconds for backoff.
    
    Returns:
        str: The text response from the model.
    """
    log_system(f"Calling Gemini (Search Enabled: {use_search}). Task: {user_prompt[:50]}...")
    
    model_name = "gemini-2.5-flash-preview-09-2025"
    
    # Fix: The Python SDK accepts the string "google_search_retrieval" to enable grounding.
    # "google_search" was incorrect.
    tools = ["google_search_retrieval"] if use_search else []

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        tools=tools,
        safety_settings=SAFETY_SETTINGS
    )
    
    for attempt in range(retries):
        try:
            response = await model.generate_content_async(user_prompt)
            
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            else:
                # Handle cases where the response might be blocked or empty
                finish_reason = response.candidates[0].finish_reason
                safety_ratings = response.candidates[0].safety_ratings
                if finish_reason and finish_reason.name == "SAFETY":
                    log_system(f"Warning: Response blocked by safety filter: {safety_ratings}")
                    return f"[Response blocked by safety filter: {safety_ratings}]"
                
                # Check for empty response (e.g., successful call but no output)
                if response.candidates and not response.candidates[0].content.parts:
                     log_system("Warning: API call successful but returned no content parts.")
                     return "[No content returned from API]"

                raise Exception(f"Invalid response structure from API. Response: {response}")
                
        except (google.api_core.exceptions.ResourceExhausted, 
                google.api_core.exceptions.ServiceUnavailable, 
                google.api_core.exceptions.InternalServerError) as e:
            log_system(f"API call failed (Attempt {attempt + 1}/{retries}): {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
        except Exception as e:
            log_system(f"An unexpected error occurred: {e}")
            if hasattr(e, 'response'):
                log_system(f"Error details: {e.response}")
            return f"[Error: {e}]"
            
    log_system("All retries failed.")
    raise Exception("API call failed after multiple retries.")


# --- Main Orchestration Function ---

async def run_agent_system(user_goal):
    """
    Main orchestration function to run the multi-agent system.
    """
    
    print("="*50)
    print(f"Starting Multi-Agent System for: {user_goal}")
    print("="*50)

    try:
        # --- 1. MANAGER AGENT ---
        log_message("Manager", f"Task: {user_goal}")
        plan_text = await call_gemini(MANAGER_PROMPT, user_goal, use_search=False)
        log_message("Manager", f"Output (Plan):\n{plan_text}")

        research_queries = []
        try:
            # The prompt asks for JSON, so we try to parse it
            research_queries = json.loads(plan_text)
            if not isinstance(research_queries, list) or not all(isinstance(q, str) for q in research_queries):
                raise json.JSONDecodeError("Not a list of strings", plan_text, 0)
        except json.JSONDecodeError:
            log_system("Warning: Manager did not return valid JSON. Splitting by newline as fallback.")
            research_queries = [q.strip() for q in plan_text.split('\n') if q.strip()]
            
        if not research_queries:
             log_system("Error: Manager failed to create a plan. Defaulting to single-step research.")
             research_queries = [user_goal] # Fallback

        log_system("Manager's plan received. Starting research...")
        all_research = []

        # --- 2. RESEARCHER AGENT (Loop) ---
        for query in research_queries:
            log_message("Researcher", f"Task: {query}")
            # Fix: Corrected typo from call_geimini to call_gemini
            research_result = await call_gemini(RESEARCHER_PROMPT, query, use_search=True)
            log_message("Researcher", f"Output (Findings):\n{research_result}")
            all_research.append({"question": query, "finding": research_result})

        log_system("All research complete. Tasking writer...")

        # --- 3. WRITER AGENT ---
        writer_task = f"Please write a final report based on the following research notes:\n\n{json.dumps(all_research, indent=2)}"
        log_message("Writer", "Task: Synthesize all research notes into a final report.")
        
        final_report = await call_gemini(WRITER_PROMPT, writer_task, use_search=False)
        log_system("Report complete.")

        # --- 4. Display Results ---
        print("\n" + "="*20 + " FINAL REPORT " + "="*20 + "\n")
        print(final_report)
        print("\n" + "="*54 + "\n")
        
    except Exception as e:
        print(f"\n" + "="*20 + " SYSTEM ERROR " + "="*20 + "\n")
        print(f"An error occurred in the agent system: {e}")
        # Fix: Corrected syntax error in print statement
        print("\nRead the traceback for more details.")
        print("="*54 + "\n")

# --- Entry Point ---
if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Run a multi-agent research system.")
    parser.add_argument("goal", type=str, help="The research goal you want the agents to achieve.")
    
    args = parser.parse_args()
    
    # Check if goal was provided
    if not args.goal:
        print("Error: No research goal provided.")
        parser.print_help()
        sys.exit(1)

    # Use asyncio.run() to execute the async main function
    import asyncio
    try:
        asyncio.run(run_agent_system(args.goal))
    except KeyboardInterrupt:
        log_system("Process interrupted by user. Exiting.")
        sys.exit(0)

