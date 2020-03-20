from flask import render_template, jsonify, session, request

from simulator_app import app
from simulator_app import generate_data, simulate, plotting

@app.route('/')
def index():
    return render_template('simulator_app/index.html')

@app.route('/generate-graph', methods=['GET'])
def create_initial_graph():
    node_names, neighbors, adj = generate_data.generate_graph()
    session['orig_nodes'] = node_names
    session['orig_neighbors'] = neighbors
    return jsonify(nodes=node_names, neighbors=neighbors)

@app.route('/simulate-graph', methods=['POST'])
def simulate_graph():

    # get the unmodified graph from the session
    orig_nodes = session.get('orig_nodes', None)
    orig_neighbors = session.get('orig_neighbors', None)

    # grab the data specifying the modified graph
    data = request.json
    nodes = data['nodes']
    neighbors = data['links']
    infection_prob = float(data['infection_prob'])

    # for comparison, we will be infecting the same nodes in the unmodified graph.
    # first collect the names of the infected nodes
    existing_infections = False
    infected_nodes = set()
    for n in nodes:
        if n['infected']:
            existing_infections = True
            infected_nodes.add(n['name'])

    # now roll through the original nodes and infect those:
    for n in orig_nodes:
        if n['name'] in infected_nodes:
            n['infected'] = True

    if existing_infections:
        # simulate both the modified graph and the original one to show how graph modification can affect transmission
  
        infected_nodes_pct, t1, mc1, std1, total_infected_counts1 = simulate.setup_and_run_simulation(nodes, neighbors, infection_prob)
        simulated_orig_nodes, t2, mc2, std2, total_infected_counts2 = simulate.setup_and_run_simulation(orig_nodes, orig_neighbors, infection_prob)

        history_plot_svg = plotting.history_plot(t1, mc1, t2, mc2)
        violin_plot_svg = plotting.violin_plot(total_infected_counts1, total_infected_counts2)

        # just send back the infected nodes as a list:
        #final_infected_nodes = list(set([x['name'] for x in simulated_nodes if x['infected']]))
        return jsonify(infected_nodes_pct=infected_nodes_pct,
            vpt=violin_plot_svg,
            hp=history_plot_svg
        )
    else:
        return jsonify(message='No people were infected.  Start by infecting one or more people.')

    return 'Thanks!'
