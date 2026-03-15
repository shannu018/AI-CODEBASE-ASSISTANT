"""
services/rag.py
RAG Pipeline using Google Gemini.
Supports both new (google-genai) and old (google-generativeai) SDK.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CHAT_MODEL = "models/gemini-2.5-flash"
TOP_K = 5

# Support both SDKs
try:
    from google import genai
    _client = genai.Client(api_key=GEMINI_API_KEY)
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai_old
    genai_old.configure(api_key=GEMINI_API_KEY)
    _USE_NEW_SDK = False


def _generate(prompt: str) -> str:
    """Call Gemini to generate a response — works with both SDKs."""
    if _USE_NEW_SDK:
        response = _client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )
        return response.text
    else:
        model = genai_old.GenerativeModel(CHAT_MODEL)
        return model.generate_content(prompt).text


def build_rag_prompt(query: str, chunks: list[dict], history: list[dict]) -> str:
    """Build the full prompt with retrieved code + history."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk['metadata']
        context_parts.append(
            f"[Source {i}] File: {meta.get('relative_path', 'unknown')} "
            f"(Lines {meta.get('start_line', '?')}-{meta.get('end_line', '?')})\n"
            f"```{meta.get('language', '')}\n{chunk['content']}\n```"
        )
    context_text = "\n\n".join(context_parts) if context_parts else "No relevant code found."

    history_text = ""
    if history:
        parts = []
        for msg in history[-6:]:
            role = "User" if msg['role'] == 'user' else "Assistant"
            parts.append(f"{role}: {msg['content']}")
        history_text = "\n".join(parts)

    return f"""You are an expert AI assistant helping a developer understand their codebase.

RETRIEVED CODE CONTEXT:
{context_text}

{"CONVERSATION HISTORY:\n" + history_text if history_text else ""}

CURRENT QUESTION: {query}

Instructions:
- Answer based on the retrieved code context above
- Reference specific files and line numbers when relevant
- If the context doesn't contain enough info, say so clearly
- Format code examples with markdown code blocks
- Be concise but thorough
"""


def query_rag(query: str, collection, embed_query_fn, history: list[dict] = None) -> dict:
    """Main RAG pipeline: embed → retrieve → generate."""
    from services.vectordb import semantic_search

    query_embedding = embed_query_fn(query)
    retrieved = semantic_search(collection, query_embedding, top_k=TOP_K)
    prompt = build_rag_prompt(query, retrieved, history or [])
    answer = _generate(prompt)

    sources = []
    for chunk in retrieved:
        meta = chunk['metadata']
        sources.append({
            'file':     meta.get('relative_path', 'unknown'),
            'lines':    f"{meta.get('start_line', '?')}-{meta.get('end_line', '?')}",
            'language': meta.get('language', ''),
            'score':    round(chunk['score'], 3)
        })

    return {'answer': answer, 'sources': sources}


def security_scan(code_snippet: str) -> str:
    prompt = f"""You are a security expert. Analyze this code for vulnerabilities:
- SQL injection risks
- Hardcoded secrets or API keys
- Insecure authentication patterns
- Input validation issues
- Dangerous imports or shell commands

Code:
```
{code_snippet}
```

For each issue: name it, rate severity (CRITICAL/HIGH/MEDIUM/LOW), show the risky line, suggest a fix.
If no issues found, confirm the code appears secure."""
    return _generate(prompt)


def analyze_code(code_snippet: str, task: str) -> str:
    prompts = {
        'explain': f"Explain this code clearly and concisely:\n\n```\n{code_snippet}\n```",
        'impact':  f"Analyze the potential impact of modifying this code. What might break?\n\n```\n{code_snippet}\n```",
        'tests':   f"Generate comprehensive unit tests for this code:\n\n```\n{code_snippet}\n```"
    }
    return _generate(prompts.get(task, f"Analyze this code:\n\n```\n{code_snippet}\n```"))
