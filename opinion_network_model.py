from mesa import Model
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
from agent import OpinionAgent


def generate_opinion_distribution(distribution_type, num_agents, random_state):
    """Generate opinion scores based on selected distribution type."""
    if distribution_type == "uniform":
        # Uniform distribution (-5, 5)
        return [random_state.uniform(-5, 5) for _ in range(num_agents)]

    elif distribution_type == "normal":
        # Normal distribution, mean = 0, std = 2 (most values fall between -4 and 4)
        return [max(-5, min(5, random_state.normalvariate(0, 2))) for _ in range(num_agents)]

    elif distribution_type == "bimodal":
        # Bimodal distribution (polarized)
        bimodal = []
        for _ in range(num_agents):
            # 50% chance from [-5, -2], 50% from [2, 5]
            if random_state.random() < 0.5:
                bimodal.append(random_state.uniform(-5, -2))
            else:
                bimodal.append(random_state.uniform(2, 5))
        return bimodal

    elif distribution_type == "trimodal":
        # Trimodal distribution (left, center, right)
        trimodal = []
        for _ in range(num_agents):
            prob = random_state.random()
            if prob < 0.33:
                trimodal.append(random_state.uniform(-5, -3))
            elif prob < 0.67:
                trimodal.append(random_state.uniform(-1, 1))
            else:
                trimodal.append(random_state.uniform(3, 5))
        return trimodal

    elif distribution_type == "skewed_left":
        # Left-skewed distribution (most agents hold negative opinions)
        return [-abs(random_state.normalvariate(0, 2.5)) for _ in range(num_agents)]

    elif distribution_type == "skewed_right":
        # Right-skewed distribution (most agents hold positive opinions)
        return [abs(random_state.normalvariate(0, 2.5)) for _ in range(num_agents)]

    else:
        # Default: uniform distribution
        return [random_state.uniform(-5, 5) for _ in range(num_agents)]


class OpinionModel(Model):
    def __init__(self, N=200, avg_node_degree=4, seed=None, opinion_distribution="uniform"):
        super().__init__(seed=seed)
        self.num_agents = N

        # Create the base network
        self.G = nx.watts_strogatz_graph(N, avg_node_degree, 1, seed=seed)
        self.grid = NetworkGrid(self.G)  # Place the graph into Mesa-compatible grid space

        # Add weights to edges, used in spring layout to determine spacing;
        # higher weight → nodes are drawn closer together.
        for u, v in self.G.edges():  # u, v are the endpoints of each edge
            self.G[u][v]["weight"] = 3.0

        # spring_layout is a force-directed layout for network visualization.
        # It places nodes in 2D space using spring-like attractive/repulsive forces.
        initial_pos = nx.spring_layout(
            self.G,
            seed=42,
            weight="weight",
            k=0.15,         # Ideal distance between nodes
            iterations=500
        )

        # Assign initial layout to the model
        self.layout_pos = initial_pos

        # Generate opinion scores based on selected distribution
        opinions = generate_opinion_distribution(opinion_distribution, N, self.random)

        # Initialize agents
        self.my_agents = []
        for i in range(self.num_agents):
            agent = OpinionAgent(i, self, initial_opinion=opinions[i])
            self.my_agents.append(agent)  # Add agent to list
            self.grid.place_agent(agent, i)  # Place agent at corresponding node

        # Initialize data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Polarization": self.compute_polarization,
                "ConnectedComponents": lambda m: nx.number_connected_components(m.G),
                "Density": lambda m: nx.density(m.G),
                "AvgDegree": lambda m: sum(dict(m.G.degree()).values()) / m.num_agents
            },
            agent_reporters={"Opinion": "opinion_score"}
        )

    def compute_polarization(self):
        opinions = [agent.opinion_score for agent in self.my_agents]
        mean_opinion = sum(opinions) / len(opinions)
        return sum((x - mean_opinion) ** 2 for x in opinions) / len(opinions)

    def step(self):
        # Update all agents
        for agent in self.my_agents:
            agent.step()
        self.datacollector.collect(self)

        # Update layout for visualization (based on updated graph)
        self.layout_pos = nx.spring_layout(
            self.G,
            pos=self.layout_pos,
            seed=42,
            weight="weight",
            k=0.15,
            iterations=50
        )
