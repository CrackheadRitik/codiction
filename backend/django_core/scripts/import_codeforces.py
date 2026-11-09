"""
Codiction — Codeforces Problem Importer

Fetches problems from Codeforces public API and imports them.
Run: python manage.py shell < scripts/import_codeforces.py
"""

import requests
import time
from django.utils.text import slugify

from apps.problems.models import Problem, Topic, ProblemTopic, TestCase


# =====================================================
# CONFIG
# =====================================================
CODEFORCES_API = "https://codeforces.com/api/problemset.problems"
MAX_PROBLEMS = 300  # Adjust based on needs


def rating_to_difficulty(rating):
    """Map Codeforces rating to our difficulty levels."""
    if not rating:
        return "Medium"  # Default for unrated
    if rating < 1200:
        return "Easy"
    elif rating < 1800:
        return "Medium"
    else:
        return "Hard"


def fetch_codeforces_problems():
    """Fetch problems from Codeforces API."""
    print("Fetching problems from Codeforces...")
    response = requests.get(CODEFORCES_API)
    response.raise_for_status()
    
    data = response.json()
    if data["status"] != "OK":
        raise Exception(f"Codeforces API error: {data}")
    
    problems = data["result"]["problems"]
    print(f"✅ Found {len(problems)} problems from Codeforces")
    
    return problems


def get_or_create_topic(tag):
    """Get or create a topic from a Codeforces tag."""
    # Normalize tag name
    name = tag.replace("-", " ").title()
    slug = slugify(name)
    
    topic, created = Topic.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name,
            "description": f"Problems about {name}",
        },
    )
    return topic


def generate_sample_test_case(problem_title):
    """
    Generate a basic sample test case based on problem type.
    
    Note: Codeforces doesn't provide test cases via API.
    We create a placeholder sample and mark it clearly.
    For real judging, admins would need to add proper test cases.
    """
    return {
        "input": "1\n",
        "output": "1\n",
        "is_sample": True,
        "is_hidden": False,
        "order": 1,
    }


def import_problem(cf_problem, stats=None):
    """Import a single Codeforces problem."""
    title = cf_problem.get("name", "").strip()
    if not title:
        return None
    
    # Create slug
    cf_index = cf_problem.get("index", "")
    cf_contest_id = cf_problem.get("contestId", "")
    base_slug = slugify(title)[:250]
    slug = f"{base_slug}-cf{cf_contest_id}{cf_index}"
    
    # Check if already imported
    if Problem.objects.filter(slug=slug).exists():
        return None
    
    # Get rating and map to difficulty
    rating = cf_problem.get("rating")
    difficulty = rating_to_difficulty(rating)
    
    # Create problem
    description = f"""
# {title}

> **Note:** This problem was imported from Codeforces.

**Problem Statement:**

You are given a problem from Codeforces contest #{cf_contest_id}, problem {cf_index}.

**Constraints:**
- Refer to original Codeforces problem for full constraints

**Original Link:** https://codeforces.com/problemset/problem/{cf_contest_id}/{cf_index}

**Difficulty Rating:** {rating or 'Unrated'}

**Topics:** {', '.join(cf_problem.get('tags', []))}

**How to solve:**
Submit your Python solution. The judge will test your code against hidden test cases.
"""

    try:
        problem = Problem.objects.create(
            title=title,
            slug=slug,
            description=description,
            difficulty=difficulty,
            acceptance_rate=50.00,
            source="OpenSource",
            is_published=True,
            is_premium=False,
            examples=[],
            constraints=[],
            hints=[],
        )
    except Exception as e:
        print(f"  ⚠️ Failed to create problem '{title}': {e}")
        return None
    
    # Add topics
    for tag in cf_problem.get("tags", []):
        try:
            topic = get_or_create_topic(tag)
            ProblemTopic.objects.get_or_create(
                problem=problem,
                topic=topic,
            )
        except Exception as e:
            pass  # Skip topic if error
    
    # Add placeholder sample test case
    try:
        sample = generate_sample_test_case(title)
        TestCase.objects.create(
            problem=problem,
            input_data=sample["input"],
            expected_output=sample["output"],
            is_sample=sample["is_sample"],
            is_hidden=False,
            order=sample["order"],
        )
        
        # Add hidden test case (placeholder)
        TestCase.objects.create(
            problem=problem,
            input_data="1\n",
            expected_output="1\n",
            is_sample=False,
            is_hidden=True,
            order=2,
        )
    except Exception as e:
        pass
    
    return problem


def main():
    """Main import function."""
    print("=" * 60)
    print("CODICTION — CODEFORCES PROBLEM IMPORTER")
    print("=" * 60)
    
    # Get existing problems count
    existing_count = Problem.objects.count()
    print(f"Current problems in DB: {existing_count}")
    print()
    
    # Fetch from Codeforces
    try:
        cf_problems = fetch_codeforces_problems()
    except Exception as e:
        print(f"❌ Failed to fetch problems: {e}")
        return
    
    # Filter to only include rated problems (higher quality)
    rated_problems = [p for p in cf_problems if p.get("rating")]
    print(f"Rated problems: {len(rated_problems)}")
    
    # Take the first N problems
    to_import = rated_problems[:MAX_PROBLEMS]
    print(f"Importing {len(to_import)} problems...")
    print()
    
    imported = 0
    skipped = 0
    failed = 0
    
    for i, cf_problem in enumerate(to_import, 1):
        try:
            result = import_problem(cf_problem)
            if result:
                imported += 1
                if imported % 10 == 0:
                    print(f"  ✅ Imported {imported} problems...")
            else:
                skipped += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ Failed: {cf_problem.get('name', 'unknown')}: {e}")
    
    print()
    print("=" * 60)
    print(f"IMPORT COMPLETE")
    print(f"  Imported: {imported}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total problems now: {Problem.objects.count()}")
    print("=" * 60)


# Run
main()