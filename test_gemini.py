#!/usr/bin/env python3
"""Quick validation script for Gemini 2.5 integration."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.intelligence import LLMClient

llm = LLMClient()
print(f"Provider: {llm.preferred}")
print(f"Available: {llm.is_available()}")

if not llm.is_available():
    print("\n❌ No LLM API key found.")
    print("   Set one of:")
    print("     export GEMINI_API_KEY='your-key-here'")
    print("     export GOOGLE_API_KEY='your-key-here'")
    print("     export OPENAI_API_KEY='your-key-here'")
    print("     export ANTHROPIC_API_KEY='your-key-here'")
    sys.exit(1)

print(f"\n▶ Sending test prompt to {llm.preferred}...")
try:
    response = llm.generate(
        prompt='Generate a 2-sentence casting assessment of actor Zendaya. Focus on one specific behavioral observation.',
        system='You are a forensic casting analyst. Be specific and diagnostic.',
        max_tokens=200,
        temperature=0.3,
    )
    print(f"\n✅ Model: {response.model}")
    print(f"   Usage: {response.usage}")
    print(f"   Output:\n   {response.text[:300]}...")
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
