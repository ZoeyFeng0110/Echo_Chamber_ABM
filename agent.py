from mesa import Agent

class OpinionAgent(Agent):
    def __init__(self, unique_id, model, initial_opinion=None):
        # Directly set basic attributes without using super().__init__
        self.unique_id = unique_id
        self.model = model
        self.pos = None 
        
        # Use a different variable name for the random number generator
        self._random_generator = model.random  # You use _random_generator to avoid conflicts with Mesa’s built-in self.random property, which previously caused persistent errors when calling .random()

        # Other initialization code using the renamed generator
        # Use the provided initial opinion if available; otherwise generate one randomly
        if initial_opinion is not None:
            self.opinion_score = initial_opinion
        else:
            self.opinion_score = self._random_generator.uniform(-5, 5)
        normalized_opinion = abs(self.opinion_score) / 5  # Normalize to the [0, 1] range
        self.uncertainty = max(0, min(1, 1 - normalized_opinion + self._random_generator.gauss(0, 0.05)))
        self.engagement = self._random_generator.uniform(0, 1)
        self.tolerance = max(0, min(1, 0.6 - 0.3 * normalized_opinion + self._random_generator.gauss(0, 0.05)))

        
    def step(self):
        # Get current neighbors (connected agent objects)
        neighbors = self.model.grid.get_neighbors(self.unique_id, include_center=False)

        # ===== 1. Determine whether to disconnect from current neighbors =====
        for neighbor in neighbors:
            similarity = 1 - abs(self.opinion_score - neighbor.opinion_score)

            if similarity < self.tolerance:
                # prob_disconnect = self.engagement * (1 - similarity)
                prob_disconnect = self.engagement * (1 - similarity) * (1 + abs(self.opinion_score))

                if self._random_generator.random() < prob_disconnect:  # Use the renamed generator
                    if self.model.G.has_edge(self.unique_id, neighbor.unique_id):
                        self.model.G.remove_edge(self.unique_id, neighbor.unique_id)

        # ===== 2. Evaluate whether to form a new connection with a non-neighbor =====
        connected_ids = {neighbor.unique_id for neighbor in neighbors} | {self.unique_id}  # Store the IDs of all currently connected agents plus self

        # Add a directional constraint: only consider agents with a higher ID to avoid duplicate connections
        potential_new_neighbors = [
            agent for agent in self.model.my_agents
            if agent.unique_id > self.unique_id and agent.unique_id not in connected_ids  # Only to avoid duplicate edges, e.g., if id1 connects to id2, then id2 does not need to connect back to id1
        ]

        for agent in potential_new_neighbors:
            similarity = 1 - abs(self.opinion_score - agent.opinion_score)

            if similarity > self.tolerance:
                prob_connect = self.engagement * similarity 
                if self._random_generator.random() < prob_connect:  
                    self.model.G.add_edge(self.unique_id, agent.unique_id)
                    break  # Ensure that each agent creates at most one new connection per step

        # # ===== 3. Update opinion_score based on neighbors' opinions =====
        # updated_neighbors = self.model.grid.get_neighbors(self.unique_id, include_center=False)

        # if updated_neighbors:
        #     total_weight = 0
        #     weighted_sum = 0

        #     for neighbor in updated_neighbors:
        #         similarity = 1 - abs(self.opinion_score - neighbor.opinion_score)
        #         weight = similarity * (1 - self.uncertainty)
        #         weighted_sum += weight * neighbor.opinion_score
        #         total_weight += weight

        #     if total_weight > 0:
        #         self.opinion_score = (self.opinion_score + weighted_sum / total_weight) / 2
