import networkx as nx
import json

class GraphContextStore:
    def __init__(self):
        self.graph = nx.DiGraph()

    def ingest(self, data):
        """
        Ingests JSON records into the Graph.
        """
        for record in data:
            self._process_record(record)

        print(f"Ingested {len(data)} records. Graph has {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")

    def _process_record(self, record):
        # 1. Ensure Actor Exists
        actor_name = record.get('actor_name', 'Unknown')
        self.graph.add_node(actor_name, type='Person')

        # 2. Process Intent (Goal Definition)
        if record['type'] == 'Intent':
            goal_name = record['goal_name']
            self.graph.add_node(goal_name, type='Goal', status=record.get('status'))
            self.graph.add_edge(actor_name, goal_name, relation='CREATED')
            self.graph.add_edge(actor_name, goal_name, relation='WORKING_ON')

        # 3. Process Communication
        elif record['type'] == 'Communication':
            msg_id = record['id']
            # Truncate content for node label
            content_preview = record['content'][:20] + "..."
            self.graph.add_node(msg_id, type='Message', content=record['content'], timestamp=record['timestamp'])

            # Edges
            self.graph.add_edge(actor_name, msg_id, relation='SENT')

            # Link to Goal
            if record.get('related_goal') and record['related_goal'] != "None":
                self.graph.add_node(record['related_goal'], type='Goal') # Ensure it exists
                self.graph.add_edge(msg_id, record['related_goal'], relation='RELATED_TO')

            # Link to Value (Implicit)
            meta = record.get('metadata', {})
            if meta.get('implied_value') and meta['implied_value'] != "None":
                val = meta['implied_value']
                self.graph.add_node(val, type='Value')
                self.graph.add_edge(msg_id, val, relation='IMPLIES_VALUE')
                # Also reinforce the person's value
                self.graph.add_edge(actor_name, val, relation='EXHIBITS_VALUE')

            # Link to Sentiment (Emotion)
            if meta.get('sentiment'):
                emotion = meta['sentiment']
                self.graph.add_node(emotion, type='Emotion')
                self.graph.add_edge(msg_id, emotion, relation='EXPRESSES')

        # 4. Process Episodic (Events)
        elif record['type'] == 'Episodic':
            event_id = record['id']
            self.graph.add_node(event_id, type='Event', description=record['description'], timestamp=record['timestamp'])
            self.graph.add_edge(actor_name, event_id, relation='PARTICIPATED_IN')

            if record.get('related_goal'):
                self.graph.add_node(record['related_goal'], type='Goal')
                self.graph.add_edge(event_id, record['related_goal'], relation='RELATED_TO')

    def find_implicit_constraints(self, goal_name):
        """
        Traverses the graph to find values implied by messages related to a goal.
        Path: Goal <-[RELATED_TO]- Message -[IMPLIES_VALUE]-> Value
        """
        if goal_name not in self.graph:
            return []

        constraints = []
        # Incoming edges to goal (Messages/Events related to it)
        predecessors = self.graph.predecessors(goal_name)

        for node in predecessors:
            if self.graph.nodes[node].get('type') == 'Message':
                # Check what this message implies
                for neighbor in self.graph.successors(node):
                    if self.graph.nodes[neighbor].get('type') == 'Value':
                        constraints.append(neighbor)

        return list(set(constraints)) # Dedupe

    def get_person_profile(self, name):
        """
        Returns known values and active goals for a person.
        """
        if name not in self.graph:
            return {}

        values = []
        goals = []

        for neighbor in self.graph.successors(name):
            node_type = self.graph.nodes[neighbor].get('type')
            relation = self.graph[name][neighbor]['relation']

            if node_type == 'Value' and relation == 'EXHIBITS_VALUE':
                values.append(neighbor)
            elif node_type == 'Goal' and relation == 'WORKING_ON':
                goals.append(neighbor)

        return {"values": list(set(values)), "goals": goals}

    def reset(self):
        self.graph.clear()

# Quick test
if __name__ == "__main__":
    store = GraphContextStore()

    with open("experiments/exp-05/data/synthetic_dataset.json", "r") as f:
        data = json.load(f)

    store.ingest(data)

    goal = "Launch 'Dark Mode' Feature"
    print(f"\n--- Implicit Constraints for '{goal}' ---")
    print(store.find_implicit_constraints(goal))

    user = "Sam Patel"
    print(f"\n--- Profile for '{user}' ---")
    print(store.get_person_profile(user))
