import json
import uuid
import random
from datetime import datetime, timedelta

# --- Constants & Configuration ---

VALUES = [
    "Minimalism", "Frugality", "Speed", "Privacy", "Innovation",
    "Reliability", "Esthetics", "Data-Driven"
]

EMOTIONS = [
    "Joy", "Frustration", "Anxiety", "Excitement", "Boredom",
    "Confusion", "Determination", "Anger"
]

TOPICS = [
    "Design", "Budget", "Timeline", "Architecture", "Hiring",
    "Marketing", "User Research", "Security"
]

CHANNELS = ["Slack", "Email", "Voice_Transcript", "Jira"]

# --- Classes ---

class Profile:
    def __init__(self, name, role):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        # Hidden values that drive behavior
        self.values = random.sample(VALUES, 3)
        print(f"Created Profile: {self.name} ({self.role}) with Values: {self.values}")

class DataGenerator:
    def __init__(self, output_file):
        self.output_file = output_file
        self.data_stream = []
        self.current_time = datetime(2023, 10, 1, 9, 0, 0)

    def advance_time(self, minutes=0, hours=0, days=0):
        self.current_time += timedelta(minutes=minutes, hours=hours, days=days)
        return self.current_time.isoformat()

    def generate_event(self, profile, goal, event_type, description):
        event = {
            "id": str(uuid.uuid4()),
            "type": "Episodic",
            "timestamp": self.advance_time(hours=1),
            "actor_id": profile.id,
            "actor_name": profile.name,
            "event_type": event_type,
            "description": description,
            "related_goal": goal,
            "metadata": {
                "location": "Virtual",
                "participants": [profile.name, "AI_Agent"]
            }
        }
        self.data_stream.append(event)
        return event

    def generate_communication(self, profile, goal, content, sentiment=None, implied_value=None):
        if not sentiment:
            sentiment = random.choice(EMOTIONS)

        comm = {
            "id": str(uuid.uuid4()),
            "type": "Communication",
            "timestamp": self.advance_time(minutes=random.randint(5, 60)),
            "actor_id": profile.id,
            "actor_name": profile.name,
            "channel": random.choice(CHANNELS),
            "content": content,
            "related_goal": goal,
            "metadata": {
                "sentiment": sentiment,
                "implied_value": implied_value if implied_value else "None"
            }
        }
        self.data_stream.append(comm)
        return comm

    def generate_intent(self, profile, goal_name, description):
        intent = {
            "id": str(uuid.uuid4()),
            "type": "Intent",
            "timestamp": self.advance_time(),
            "actor_id": profile.id,
            "actor_name": profile.name,
            "goal_name": goal_name,
            "description": description,
            "status": "Active",
            "metadata": {
                "priority": "High"
            }
        }
        self.data_stream.append(intent)
        return intent

    def save(self):
        with open(self.output_file, 'w') as f:
            json.dump(self.data_stream, f, indent=2)
        print(f"Generated {len(self.data_stream)} records in {self.output_file}")

# --- Scenarios ---

def scenario_product_launch(gen, profile):
    # Goal: Launch New Feature
    goal = "Launch 'Dark Mode' Feature"
    gen.generate_intent(profile, goal, "Implement and release dark mode for the mobile app.")

    # 1. Planning Phase (Expresses Value: Speed)
    gen.generate_event(profile, goal, "Meeting", "Kickoff meeting for Dark Mode.")

    val = "Speed" if "Speed" in profile.values else "Reliability"
    if val == "Speed":
        msg = "Let's just ship the MVP. We don't need perfect contrast ratios yet."
        sent = "Determination"
    else:
        msg = "We need to make sure this doesn't break accessibility. Take your time."
        sent = "Anxiety"

    gen.generate_communication(profile, goal, msg, sentiment=sent, implied_value=val)

    # 2. Design Phase (Expresses Value: Esthetics or Minimalism)
    gen.advance_time(days=2)
    gen.generate_event(profile, goal, "Design Review", "Reviewing Figma mocks.")

    val = "Minimalism" if "Minimalism" in profile.values else "Innovation"
    if val == "Minimalism":
        msg = "This is too cluttered. Remove the gradient borders."
        sent = "Frustration"
    else:
        msg = "Can we add some glowing effects? It looks too plain."
        sent = "Excitement"

    gen.generate_communication(profile, goal, msg, sentiment=sent, implied_value=val)

def scenario_budget_review(gen, profile):
    # Goal: Cut Costs
    goal = "Q4 Budget Review"
    gen.generate_intent(profile, goal, "Reduce cloud infrastructure costs by 20%.")

    # 1. Discovery
    gen.generate_event(profile, goal, "Analysis", "Reviewing AWS bills.")

    val = "Frugality" if "Frugality" in profile.values else "Innovation"
    if val == "Frugality":
        msg = "Why are we paying for these idle instances? Shut them down immediately."
        sent = "Anger"
    else:
        msg = "We shouldn't cut R&D servers. We need them for experiments."
        sent = "Determination"

    gen.generate_communication(profile, goal, msg, sentiment=sent, implied_value=val)


# --- Main Execution ---

if __name__ == "__main__":
    gen = DataGenerator("experiments/exp-05/data/synthetic_dataset.json")

    # Create a primary user
    user = Profile("Sam Patel", "CTO")

    # Generate scenarios based on the user's hidden values
    scenario_product_launch(gen, user)
    scenario_budget_review(gen, user)

    # Generate random noise/chatter
    for _ in range(5):
        gen.generate_communication(user, "General", "Just checking in.", sentiment="Neutral")

    gen.save()
