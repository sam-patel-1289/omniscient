"""
EXP-006: Synthetic Data Generator for Hybrid Store Testing

Generates realistic human context data for benchmarking.
"""

import random
from datetime import datetime, timedelta
import json


# Sample data pools
PEOPLE = ["Sam", "Bob", "Alice", "Carol", "David", "Emma", "Frank", "Grace"]
COMPANIES = ["Amazon", "Google", "Meta", "Apple", "Microsoft", "Netflix"]
CITIES = ["New York", "San Francisco", "Seattle", "Austin", "Boston", "Denver"]
ROLES = ["Software Engineer", "Product Manager", "Designer", "Data Scientist", "Manager"]
VALUES = ["minimalism", "speed", "quality", "privacy", "collaboration", "innovation"]
EMOTIONS = ["happy", "frustrated", "anxious", "excited", "tired", "focused", "stressed"]
GOALS = ["Launch MVP", "Redesign homepage", "Migrate to cloud", "Hire team", "Learn Python", "Write book"]
TOPICS = ["design", "code", "meeting", "deadline", "budget", "performance", "security"]

# Message templates
MESSAGE_TEMPLATES = [
    "I {emotion_verb} this {adjective} {topic}.",
    "Just finished the {topic} review with {person}.",
    "Moving forward with the {goal} project.",
    "{person} mentioned concerns about {topic}.",
    "The {topic} is taking longer than expected.",
    "Great progress on {goal} today!",
    "Need to discuss {topic} with {person} tomorrow.",
    "Feeling {emotion} about the upcoming {topic} deadline.",
    "{person} is really helpful with {topic}.",
    "Changed my mind about {topic} after talking to {person}.",
]

EMOTION_VERBS = {
    "frustrated": ["hate", "can't stand", "am frustrated with"],
    "happy": ["love", "really like", "am happy with"],
    "anxious": ["worry about", "am concerned about", "stress about"],
    "excited": ["can't wait for", "am excited about", "look forward to"],
}

ADJECTIVES = ["cluttered", "slow", "complex", "elegant", "simple", "broken", "amazing"]


def generate_person_profile(name: str) -> dict:
    """Generate a realistic person profile."""
    return {
        "id": f"person_{name.lower()}",
        "type": "Person",
        "name": name,
        "role": random.choice(ROLES),
        "company": random.choice(COMPANIES),
        "location": random.choice(CITIES),
        "values": random.sample(VALUES, k=random.randint(2, 4)),
        "created_at": datetime.utcnow().isoformat()
    }


def generate_relationship(person1: str, person2: str) -> dict:
    """Generate a relationship between two people."""
    rel_types = [
        ("REPORTS_TO", "manager"),
        ("WORKS_WITH", "colleague"),
        ("MENTORS", "mentor"),
        ("COLLABORATES_WITH", "collaborator"),
    ]
    rel_type, desc = random.choice(rel_types)
    return {
        "source": f"person_{person1.lower()}",
        "target": f"person_{person2.lower()}",
        "type": rel_type,
        "description": f"{person1}'s {desc} is {person2}"
    }


def generate_message(actor: str, timestamp: datetime) -> dict:
    """Generate a realistic message/context."""
    template = random.choice(MESSAGE_TEMPLATES)
    emotion = random.choice(EMOTIONS)
    
    # Fill in template
    content = template.format(
        emotion_verb=random.choice(EMOTION_VERBS.get(emotion, ["think about"])),
        adjective=random.choice(ADJECTIVES),
        topic=random.choice(TOPICS),
        person=random.choice([p for p in PEOPLE if p != actor]),
        goal=random.choice(GOALS),
        emotion=emotion
    )
    
    # Detect implied values from content
    implied_values = []
    if any(w in content.lower() for w in ["cluttered", "simple", "clean"]):
        implied_values.append("minimalism")
    if any(w in content.lower() for w in ["slow", "fast", "quick"]):
        implied_values.append("speed")
    if any(w in content.lower() for w in ["quality", "elegant", "amazing"]):
        implied_values.append("quality")
    
    return {
        "id": f"msg_{timestamp.strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}",
        "type": "Communication",
        "actor": actor,
        "content": content,
        "timestamp": timestamp.isoformat(),
        "channel": random.choice(["slack", "email", "voice", "meeting"]),
        "metadata": {
            "emotion": emotion,
            "implied_values": implied_values,
            "related_goal": random.choice(GOALS + [None, None]),  # 33% chance of no goal
            "mentioned_people": [p for p in PEOPLE if p.lower() in content.lower()]
        }
    }


def generate_goal(actor: str, timestamp: datetime) -> dict:
    """Generate a goal/intent."""
    goal_name = random.choice(GOALS)
    return {
        "id": f"goal_{goal_name.lower().replace(' ', '_')}",
        "type": "Goal",
        "actor": actor,
        "name": goal_name,
        "status": random.choice(["active", "completed", "blocked", "planned"]),
        "priority": random.choice(["high", "medium", "low"]),
        "created_at": timestamp.isoformat(),
        "constraints": random.sample([
            "Must finish by end of quarter",
            "Budget limited to $10k",
            "Need approval from manager",
            "Depends on hiring",
        ], k=random.randint(0, 2))
    }


def generate_state_change(actor: str, timestamp: datetime) -> dict:
    """Generate an episodic state change event."""
    change_types = [
        ("location", CITIES),
        ("role", ROLES),
        ("company", COMPANIES),
        ("mood", EMOTIONS),
        ("energy", ["high", "medium", "low"]),
    ]
    
    field, options = random.choice(change_types)
    old_value = random.choice(options)
    new_value = random.choice([v for v in options if v != old_value])
    
    return {
        "id": f"event_{timestamp.strftime('%Y%m%d%H%M%S')}",
        "type": "StateChange",
        "actor": actor,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "timestamp": timestamp.isoformat(),
        "description": f"{actor}'s {field} changed from {old_value} to {new_value}"
    }


def generate_dataset(num_people: int = 5, 
                     num_messages: int = 50,
                     num_goals: int = 10,
                     num_state_changes: int = 10,
                     days_range: int = 30) -> dict:
    """Generate a complete synthetic dataset."""
    
    # Select people
    people = random.sample(PEOPLE, k=min(num_people, len(PEOPLE)))
    
    # Generate profiles
    profiles = [generate_person_profile(p) for p in people]
    
    # Generate relationships
    relationships = []
    for i, p1 in enumerate(people):
        for p2 in people[i+1:]:
            if random.random() < 0.5:  # 50% chance of relationship
                relationships.append(generate_relationship(p1, p2))
    
    # Generate timeline of events
    base_time = datetime.utcnow() - timedelta(days=days_range)
    
    messages = []
    for _ in range(num_messages):
        actor = random.choice(people)
        timestamp = base_time + timedelta(
            days=random.randint(0, days_range),
            hours=random.randint(8, 18),
            minutes=random.randint(0, 59)
        )
        messages.append(generate_message(actor, timestamp))
    
    goals = []
    for _ in range(num_goals):
        actor = random.choice(people)
        timestamp = base_time + timedelta(days=random.randint(0, days_range // 2))
        goals.append(generate_goal(actor, timestamp))
    
    state_changes = []
    for _ in range(num_state_changes):
        actor = random.choice(people)
        timestamp = base_time + timedelta(days=random.randint(0, days_range))
        state_changes.append(generate_state_change(actor, timestamp))
    
    # Sort by timestamp
    messages.sort(key=lambda x: x["timestamp"])
    state_changes.sort(key=lambda x: x["timestamp"])
    
    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "num_people": len(profiles),
            "num_relationships": len(relationships),
            "num_messages": len(messages),
            "num_goals": len(goals),
            "num_state_changes": len(state_changes),
            "days_range": days_range
        },
        "profiles": profiles,
        "relationships": relationships,
        "messages": messages,
        "goals": goals,
        "state_changes": state_changes
    }


def generate_test_queries() -> list[dict]:
    """Generate realistic test queries with expected behavior."""
    return [
        {
            "query": "What makes Sam frustrated?",
            "type": "semantic",
            "expected_store": "vector",
            "description": "Requires semantic understanding of emotions"
        },
        {
            "query": "Who does Sam report to?",
            "type": "relationship",
            "expected_store": "graph",
            "description": "Direct graph traversal"
        },
        {
            "query": "What are Sam's values?",
            "type": "profile",
            "expected_store": "both",
            "description": "Graph for explicit values, Vector for implied"
        },
        {
            "query": "Is Sam's manager happy?",
            "type": "hybrid",
            "expected_store": "both",
            "description": "Graph traversal + emotional state lookup"
        },
        {
            "query": "What was discussed about the deadline?",
            "type": "semantic",
            "expected_store": "vector",
            "description": "Topic-based semantic search"
        },
        {
            "query": "What changed for Sam last week?",
            "type": "temporal",
            "expected_store": "vector",
            "description": "Time-filtered search"
        },
        {
            "query": "Who works at Amazon?",
            "type": "filter",
            "expected_store": "graph",
            "description": "Entity attribute filter"
        },
        {
            "query": "What are the active goals?",
            "type": "filter",
            "expected_store": "graph",
            "description": "Status filter on goal entities"
        },
    ]


if __name__ == "__main__":
    # Generate sample dataset
    dataset = generate_dataset(
        num_people=5,
        num_messages=100,
        num_goals=15,
        num_state_changes=20,
        days_range=30
    )
    
    print(f"Generated dataset:")
    print(f"  - {dataset['metadata']['num_people']} people")
    print(f"  - {dataset['metadata']['num_relationships']} relationships")
    print(f"  - {dataset['metadata']['num_messages']} messages")
    print(f"  - {dataset['metadata']['num_goals']} goals")
    print(f"  - {dataset['metadata']['num_state_changes']} state changes")
    
    # Save to file
    with open("synthetic_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)
    print("\nSaved to synthetic_dataset.json")
    
    # Generate test queries
    queries = generate_test_queries()
    print(f"\nGenerated {len(queries)} test queries")
    for q in queries[:3]:
        print(f"  - {q['query']} ({q['type']})")
