# AI Enterprise Bug Tracker

An AI-powered Enterprise Bug Tracking System built with Flask, SQLAlchemy, Bootstrap, and Groq/Gemini AI for intelligent bug severity prediction, automatic summarization, and static code analysis.

## Features

- **User Authentication**: Secure registration and login with hashed passwords and role management.
- **Bug Management**: Create, view, update, and manage bug reports with file attachments.
- **AI-Powered Bug Triage**:
  - Automatic bug severity prediction based on heuristic analysis and LLM intelligence.
  - One-click AI bug summarization using Groq.
- **DevMind Code Analyzer (`analyze_code.py`)**: Multi-backend code analyzer supporting Google Gemini and Groq models via LangChain to detect security vulnerabilities, logic bugs, and code smells.
- **Modern Responsive UI**: Clean interface built with Bootstrap 5 and custom styling.

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harshtonge2909/ai-enterprise-bug-tracker.git
   cd ai-enterprise-bug-tracker
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   Add your `GROQ_API_KEY` (and optionally `GEMINI_API_KEY` / `GOOGLE_API_KEY`).

5. **Run the application**:
   ```bash
   python app.py
   ```
   The application will be accessible at `http://127.0.0.1:5000`.

## Code Analyzer Usage

To analyze any Python file with the built-in AI code analyzer:

```bash
# Using default Groq backend
python analyze_code.py app.py

# Using Gemini backend
python analyze_code.py app.py --backend gemini
```

## License

This project is open source and available under the MIT License.
