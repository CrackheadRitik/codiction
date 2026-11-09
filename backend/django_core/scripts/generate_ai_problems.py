"""
Codiction — AI Problem Generator

Uses Ollama (Llama 3) to generate unique coding problems.
Run: python manage.py shell < scripts/generate_ai_problems.py
"""

import json
import re
import subprocess
import time
from django.utils.text import slugify

from apps.problems.models import Problem, Topic, ProblemTopic, TestCase


# =====================================================
# CONFIG
# =====================================================
TOTAL_PROBLEMS = 100  # How many to generate
MODEL = "llama3"


TOPICS = [
    "Arrays", "Strings", "Dynamic Programming", "Trees", "Graphs",
    "Hash Table", "Two Pointers", "Sorting", "Searching", "Recursion",
    "Linked List", "Stack", "Queue", "Heap", "Greedy",
    "Backtracking", "Binary Search", "Breadth-First Search", "Depth-First Search",
    "Sliding Window", "Divide and Conquer", "Bit Manipulation", "Math"
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]


def generate_problem_prompt(topic, difficulty):
    """Create prompt for LLM."""
    return f"""Generate ONE {difficulty} difficulty coding problem on the topic "{topic}".

CRITICAL: Return ONLY valid JSON. No markdown, no explanations, no code blocks. Just raw JSON.

The JSON must have EXACTLY this structure:
{{"title": "Short Problem Title", "description": "Full 2-3 paragraph problem description explaining what to solve", "examples": [{{"input": "5", "output": "25", "explanation": "5 squared is 25"}}], "constraints": ["1 <= n <= 1000"], "hints": ["Think about math operations"], "solution_python": "def solve(n):\\n    return n * n", "test_cases": [{{"input": "5", "output": "25", "is_sample": true}}, {{"input": "10", "output": "100", "is_sample": false}}]}}

RULES:
1. Output ONLY the JSON object — nothing before or after
2. No markdown code blocks (```)
3. No explanations or comments
4. test_cases must have at least 1 sample and 1 hidden
5. Solution must be complete Python code
6. Use simple single-line input/output
7. Make it UNIQUE, not from LeetCode"""

def call_ollama(prompt):
    """Call Ollama API to generate text."""
    try:
        result = subprocess.run(
            ["ollama", "run", MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"  ⏱ Timeout")
        return None
    except Exception as e:
        print(f"  ❌ Ollama error: {e}")
        return None


def parse_json_response(text):
    """Extract JSON from LLM response (handles markdown wrappers, extra text)."""
    if not text:
        return None
    
    # Clean up common issues
    text = text.strip()
    
    # Try 1: Find JSON in markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try 2: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try 3: Find first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    # Try 4: Fix common JSON issues
    # - Replace smart quotes
    # - Remove trailing commas
    # - Remove control characters
    if start != -1 and end != -1:
        extracted = text[start:end+1]
        
        # Fix smart quotes
        extracted = extracted.replace('"', '"').replace('"', '"')
        extracted = extracted.replace(''', "'").replace(''', "'")
        
        # Remove trailing commas before } or ]
        extracted = re.sub(r',\s*([}\]])', r'\1', extracted)
        
        # Remove control characters (keep \n, \t)
        extracted = ''.join(c for c in extracted if ord(c) >= 32 or c in '\n\t\r')
        
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    
    # Try 5: Manual extraction with a simpler approach
    try:
        # Find first { and count braces
        start = text.find("{")
        if start != -1:
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(start, len(text)):
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == "\\":
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            candidate = text[start:i+1]
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                break
    except Exception:
        pass
    
    return None


def import_ai_problem(data, topic_name, difficulty):
    """Import AI-generated problem into database."""
    title = data.get("title", "").strip()
    if not title or len(title) > 250:
        return None
    
    slug = slugify(title)[:250]
    
    # Skip if exists
    if Problem.objects.filter(slug=slug).exists():
        return None
    
    try:
        problem = Problem.objects.create(
            title=title,
            slug=slug,
            description=data.get("description", ""),
            difficulty=difficulty,
            acceptance_rate=50.00,
            source="AI_Generated",
            is_published=True,
            examples=data.get("examples", []),
            constraints=data.get("constraints", []),
            hints=data.get("hints", []),
            solution_python=data.get("solution_python", ""),
        )
    except Exception as e:
        print(f"  ⚠️ Failed to create problem: {e}")
        return None
    
    # Add topic
    topic, _ = Topic.objects.get_or_create(
        slug=slugify(topic_name),
        defaults={"name": topic_name, "description": f"Problems about {topic_name}"},
    )
    ProblemTopic.objects.get_or_create(problem=problem, topic=topic)
    
    # Add test cases
    for idx, tc in enumerate(data.get("test_cases", []), 1):
        try:
            TestCase.objects.create(
                problem=problem,
                input_data=str(tc.get("input", "")),
                expected_output=str(tc.get("output", "")),
                is_sample=tc.get("is_sample", False),
                is_hidden=not tc.get("is_sample", False),
                order=idx,
            )
        except Exception:
            pass
    
    return problem


def main():
    """Generate and import problems."""
    print("=" * 60)
    print("CODICTION — AI PROBLEM GENERATOR")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Target: {TOTAL_PROBLEMS} problems")
    print(f"Current DB count: {Problem.objects.count()}")
    print()
    
    generated = 0
    failed = 0
    
    for i in range(TOTAL_PROBLEMS):
        topic = TOPICS[i % len(TOPICS)]
        difficulty = DIFFICULTIES[i % len(DIFFICULTIES)]
        
        print(f"[{i+1}/{TOTAL_PROBLEMS}] Generating {difficulty} problem on {topic}...")
        
        prompt = generate_problem_prompt(topic, difficulty)
        response = call_ollama(prompt)
        
        if not response:
            failed += 1
            continue
        
        data = parse_json_response(response)
        if not data:
            print(f"  ❌ Could not parse JSON from response")
            failed += 1
            continue
        
        problem = import_ai_problem(data, topic, difficulty)
        if problem:
            generated += 1
            print(f"  ✅ Created: {problem.title}")
        else:
            failed += 1
            print(f"  ⚠️ Skipped (duplicate or invalid)")
    
    print()
    print("=" * 60)
    print(f"AI GENERATION COMPLETE")
    print(f"  Generated: {generated}")
    print(f"  Failed: {failed}")
    print(f"  Total problems in DB: {Problem.objects.count()}")
    print("=" * 60)


# Run
main()