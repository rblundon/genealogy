import json
import logging
from typing import Dict, Any, Optional
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

logger = logging.getLogger(__name__)

class RelationshipVisualizer:
    """Visualize relationship graphs."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the visualizer."""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / 'output'
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_graph(self, graph_data: Dict[str, Any]) -> nx.DiGraph:
        """Create a NetworkX graph from the relationship data."""
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data['nodes']:
            G.add_node(
                node['id'],
                label=node['label'],
                **node['properties']
            )
        
        # Add edges
        for edge in graph_data['edges']:
            G.add_edge(
                edge['from'],
                edge['to'],
                label=edge['label'],
                **edge['properties']
            )
        
        return G
    
    def visualize_graph(self, graph_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Create a visualization of the relationship graph."""
        try:
            G = self.create_graph(graph_data)
            
            # Create the plot
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=2000, alpha=0.6)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20)
            
            # Add labels
            nx.draw_networkx_labels(G, pos, 
                                  {n: G.nodes[n]['label'] for n in G.nodes()})
            
            # Add edge labels
            edge_labels = {(u, v): G.edges[u, v]['label'] 
                          for u, v in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            
            # Save the plot
            if output_file is None:
                output_file = self.output_dir / 'relationship_graph.png'
            else:
                output_file = Path(output_file)
            
            plt.savefig(output_file, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return None
    
    def export_graph_json(self, graph_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Export the graph data to a JSON file."""
        try:
            if output_file is None:
                output_file = self.output_dir / 'relationship_graph.json'
            else:
                output_file = Path(output_file)
            
            with open(output_file, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error exporting graph data: {str(e)}")
            return None 