import solara
import networkx as nx
import plotly.graph_objects as go
from opinion_network_model import OpinionModel
import numpy as np

# ---------- Reactive States ----------
num_agents_state = solara.reactive(100)
model_state = solara.reactive(None)
fig_state = solara.reactive(None)
opinion_distribution_state = solara.reactive("uniform")  # Added: opinion distribution type

# ---------- Agent Display Settings ----------
def draw_plotly_network(model):
    pos = model.layout_pos
    
    node_x = []
    node_y = []
    node_color = []
    node_text = []
    
    for node_id in model.G.nodes:
        agent_list = model.grid.G.nodes[node_id].get("agent", [])
        if agent_list:
            agent = agent_list[0]
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            # Set color based on opinion_score
            if agent.opinion_score > 2.5:
                node_color.append("blue")
            elif agent.opinion_score < -2.5:
                node_color.append("red")
            else:
                node_color.append("gray")
            
            # Set hover text content
            node_text.append(
                f"ID: {agent.unique_id}<br>"
                f"Opinion: {agent.opinion_score:.2f}<br>"
                f"Engagement: {agent.engagement:.2f}<br>"
                f"Uncertainty: {agent.uncertainty:.2f}<br>"
                f"Tolerance: {agent.tolerance:.2f}"
            )
    
    # Draw edges
    edge_x = []
    edge_y = []
    for edge in model.G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.0, color="#888"),
        hoverinfo='none',
        mode='lines'
    )
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            size=12,
            color=node_color,
            line=dict(width=1, color='#000')
        ),
        text=node_text
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    return fig

# ---------- Create Model ----------
def create_model():
    model = OpinionModel(
        N=num_agents_state.value, 
        opinion_distribution=opinion_distribution_state.value
    )
    fig = draw_plotly_network(model)
    return model, fig

# ---------- Solara Page ----------
@solara.component
def Page():
    with solara.Sidebar():
        solara.InputInt("Number of Agents", value=num_agents_state)
        
        # Show current opinion distribution
        solara.Markdown("### Initial Opinion Distribution")
        current_distribution = opinion_distribution_state.value
        solara.Markdown(f"Current: **{current_distribution}**")
        
        # Create distribution type selection buttons
        with solara.Column():
            for dist_type in ["uniform", "normal", "bimodal", "trimodal", "skewed_left", "skewed_right"]:
                def set_distribution(dist=dist_type):
                    opinion_distribution_state.set(dist)
                    
                solara.Button(
                    label=dist_type,
                    on_click=set_distribution,
                    # Highlight the current selection
                    variant="outlined" if dist_type != current_distribution else "filled"
                )
        
        solara.Button("Start New Model", on_click=start_new_model)
        solara.Button("Run One Step", on_click=run_one_step)
    
    if fig_state.value:
        solara.FigurePlotly(fig_state.value)
    else:
        start_new_model()

# ---------- Button Actions ----------
def start_new_model():
    model, fig = create_model()
    model_state.set(model)
    fig_state.set(fig)

def run_one_step():
    if model_state.value:
        model_state.value.step()
        fig = draw_plotly_network(model_state.value)
        fig_state.set(fig)
