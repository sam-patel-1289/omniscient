import difflib

class FuzzyResolver:
    def __init__(self):
        # A simple "database" of known entities
        self.entities = [
            "company:apple",
            "fruit:apple",
            "animal:jaguar",
            "car:jaguar",
            "animal:python",
            "tech:python"
        ]

    def resolve(self, mention):
        """
        Resolves a mention to an entity ID using string similarity.
        Ignores context completely.
        """
        # We are matching the mention (e.g. "Apple") against the parts of the ID or tags
        # For this simple experiment, let's assume the ID *contains* the name.
        
        best_match = None
        best_ratio = 0.0
        
        # Naive matching: find which entity ID has the highest similarity to the mention
        # This is naturally flawed because "fruit:apple" and "company:apple" both contain "apple"
        
        candidates = []
        
        for entity_id in self.entities:
            # We compare the mention against the "name" part of the ID (after the colon)
            # or just the whole string? Let's try matching against the name part for realism.
            name_part = entity_id.split(":")[1]
            
            ratio = difflib.SequenceMatcher(None, mention.lower(), name_part.lower()).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                candidates = [entity_id]
            elif ratio == best_ratio:
                candidates.append(entity_id)
                
        # If we have ties (which we expect for homonyms), we just pick the first one
        # This demonstrates the randomness/failure of fuzzy matching on homonyms
        if candidates:
            return candidates[0]
        return None
