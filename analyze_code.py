import os
import sys
import argparse
from dotenv import load_dotenv

# Reconfigure stdout/stderr to UTF-8 on Windows if supported to avoid UnicodeEncodeError
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Load environment variables from .env file
load_dotenv()

# Setup placeholders to ignore
placeholder_vals = {"your_google_api_key_here", "your_gemini_api_key_here", "your_groq_api_key_here", ""}

# Retrieve raw keys
env_google_key = os.getenv("GOOGLE_API_KEY", "").strip()
env_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
env_groq_key = os.getenv("GROQ_API_KEY", "").strip()

# Resolve Gemini API Key
gemini_api_key = None
if env_google_key and env_google_key not in placeholder_vals:
    gemini_api_key = env_google_key
elif env_gemini_key and env_gemini_key not in placeholder_vals:
    gemini_api_key = env_gemini_key

# Resolve Groq API Key
groq_api_key = None
if env_groq_key and env_groq_key not in placeholder_vals:
    groq_api_key = env_groq_key


def main():
    parser = argparse.ArgumentParser(description="DevMind AI - Code Analyzer (Brick 1)")
    parser.add_argument(
        "file_path", 
        type=str, 
        nargs="?", 
        default="app.py",
        help="Path to the Python file to analyze (default: app.py)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["gemini", "groq"],
        default=None,
        help="Backend to use: gemini or groq (default: auto-detect, preferring gemini)"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default=None,
        help="Model name to use (default: gemini-1.5-flash for gemini, llama-3.1-8b-instant for groq)"
    )
    args = parser.parse_args()

    file_path = args.file_path

    # Check if target file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Target file '{file_path}' does not exist.")
        sys.exit(1)

    # Determine backend
    selected_backend = args.backend
    if not selected_backend:
        if gemini_api_key:
            selected_backend = "gemini"
        elif groq_api_key:
            selected_backend = "groq"
        else:
            print("❌ ERROR: No valid API Key found.")
            print("Please set GOOGLE_API_KEY (or GEMINI_API_KEY) or GROQ_API_KEY in your .env file.")
            sys.exit(1)

    # Setup LLM based on backend
    llm = None
    resolved_model = args.model

    if selected_backend == "gemini":
        if not gemini_api_key:
            print("❌ ERROR: Gemini backend requested, but no valid Gemini/Google API Key was found.")
            sys.exit(1)
        
        # Configure the environment variable expected by langchain-google-genai
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            print("❌ ERROR: langchain-google-genai is not installed.")
            print("Run: pip install langchain-google-genai")
            sys.exit(1)
            
        if not resolved_model:
            resolved_model = "gemini-1.5-flash"
            
        print(f"🧠 Initializing LangChain with Google Gemini model '{resolved_model}'...")
        try:
            llm = ChatGoogleGenerativeAI(
                model=resolved_model,
                temperature=0.2,
                max_retries=2,
            )
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize ChatGoogleGenerativeAI: {e}")
            sys.exit(1)

    elif selected_backend == "groq":
        if not groq_api_key:
            print("❌ ERROR: Groq backend requested, but no valid Groq API Key was found.")
            sys.exit(1)
            
        # Configure standard environment variable for langchain-groq
        os.environ["GROQ_API_KEY"] = groq_api_key
        
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            print("❌ ERROR: langchain-groq is not installed.")
            print("Run: pip install langchain-groq")
            sys.exit(1)
            
        if not resolved_model:
            resolved_model = "groq/compound"
            
        print(f"🧠 Initializing LangChain with Groq model '{resolved_model}'...")
        try:
            llm = ChatGroq(
                model=resolved_model,
                temperature=0.2,
                max_retries=2,
            )
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize ChatGroq: {e}")
            sys.exit(1)

    # Read the file to analyze
    print(f"📖 Reading file: {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
    except Exception as e:
        print(f"❌ ERROR: Failed to read file '{file_path}': {e}")
        sys.exit(1)

    print(f"⚡ Analyzing '{os.path.basename(file_path)}' using {selected_backend.upper()} ({resolved_model})...")
    
    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
        print("❌ ERROR: langchain-core is not installed. Please reinstall langchain.")
        sys.exit(1)

    # Prompt Template
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are DevMind AI, an elite software engineering assistant. "
            "Analyze the provided Python code and generate a high-quality, professional markdown report."
        )),
        ("user", (
            "Please perform a comprehensive code review and analysis of the following Python file.\n\n"
            "File Name: {filename}\n\n"
            "Code:\n"
            "```python\n"
            "{code}\n"
            "```\n\n"
            "Provide the output in the following structured markdown format:\n"
            "1. **Overview & Architecture**: Briefly explain the main purpose of this code and its architecture.\n"
            "2. **Detailed Library/Dependency Review**: List and explain the primary third-party libraries used.\n"
            "3. **Code Quality & Redundancies**: Identify bugs, duplicate functions, redundant lines, or bad practices.\n"
            "4. **Security & Vulnerabilities**: Identify any security weaknesses (e.g., hardcoded secrets, dangerous functions).\n"
            "5. **Actionable Recommendations**: Give concrete, copy-pasteable code block improvements to resolve the main issues found."
        ))
    ])

    # Chain definition
    chain = prompt | llm

    try:
        # Invoke LLM
        response = chain.invoke({
            "filename": os.path.basename(file_path),
            "code": code_content
        })
        
        # Display results
        print("\n" + "="*50)
        print(f"📝 DEVMIND AI - CODE ANALYSIS REPORT FOR: {file_path}")
        print("="*50 + "\n")
        print(response.content)
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"❌ ERROR: Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
