import numpy as np
import pandas as pd
from bisect import insort
from collections import OrderedDict


class Person(object):
    mean_dormancy = 24
    var_dormancy = 2

    mean_duration_until_symptoms = 24*5
    var_duration_until_symptoms = 8

    mean_symptoms_duration = 24*7
    var_symptoms_duration = 12

    def __init__(self, name, infected):
        self.name = name
        self.infected = infected
        self.infection_time = None
        self.dormancy_time = np.random.normal(Person.mean_dormancy, Person.var_dormancy) # how long (after infection) until they can transmit
        self.duration_to_symptoms = np.random.normal(Person.mean_duration_until_symptoms, Person.var_duration_until_symptoms) # how long until symptoms manifest
        self.symptoms_duration = np.random.normal(Person.mean_symptoms_duration, Person.var_symptoms_duration) # how long symptoms last for
        self.total_duration = self.duration_to_symptoms + self.symptoms_duration
        self.infectious_time_duration = self.total_duration - self.dormancy_time

    def set_infected(self, t0):
        self.infected = True
        self.infection_time = t0

    def reset_person(self):
        '''
        This is used if we run a second simulation.  In that case, we may want to preserve
        the random times we sampled (so the individual disease dynamics are the same)
        but use that person in a different network
        '''
        self.infected = False
        self.infection_time = None

    
class ScheduledInfection(object):
    def __init__(self, source_idx, target_idx, time):
        '''
        source and target are integers, referring to the index of the Person 
        instances in the master node array.  
        '''
        self.source_idx = source_idx
        self.target_idx = target_idx
        self.time = time
    
    def __lt__(self, other):
        return self.time < other.time

    def __repr__(self):
        return '%s --> %s at t=%.2f' % (self.source_idx, self.target_idx, self.time)


def create_adjacency_matrix(nodes, neighbors):
    '''
    Creates and retuns an adjacency matrix
    nodes is a list of dicts: [{"name": "n0"}, {"name": "n3"},...]
    neighbors is also a list of dicts:
    [{"source": "n0","target": "n2"},{"source": "n0","target": "n3"}, ... ]
    '''
    n_persons = len(nodes)
    idx_dict = dict(
        zip(
                [x['name'] for x in nodes],
                np.arange(n_persons)
            )
        )
    adj = np.zeros((n_persons,n_persons), dtype=np.int)
    for pairing in neighbors:
        src_idx = idx_dict[pairing['source']]
        target_idx = idx_dict[pairing['target']]
        adj[src_idx, target_idx] = 1
        adj[target_idx, src_idx] = 1
    return adj

    
def simulate_network(nodes, adj):
    '''
    Given a list of nodes (a list of dicts: [{"name": "n0"}, {"name": "n3"},...])
    and an adjacency matrix (already made more "sparse" by sampling infection probabilities)
    run the simulated dynamics of the network.
    '''
    # a list of Person instances
    population = [Person(n['name'],n['infected']) for n in nodes]
    
    running_adj = adj.copy()

    # initiate the data structure that tracks the infection history
    infections_queue = []
    current_time = 0.0
    for i,p in enumerate(population):
        if p.infected:
            infect_and_project(infections_queue, 
                p, 
                i, 
                running_adj, 
                current_time)
    # now that we have the initial data structure setup, we can run the simulation until the list of ScheduledInfections 
    # becomes empty, indicating all the potential infections have occurred.
    while len(infections_queue) > 0:
        current_infection = infections_queue.pop(0) # get the earliest infection
        current_time = current_infection.time # the absolute time this infection is modeled to occur
        target_idx = current_infection.target_idx # the person (addressed by their index) being infected at this time

        # if target is now being infected, go ahead and remove other sources of infection for this same target...they are already sick
        infections_queue = cleanup_queue(infections_queue, target_idx)

        infect_and_project(infections_queue, 
            population[target_idx], 
            target_idx, 
            running_adj, 
            current_time)

    #TODO: ensure we handle edge case where a single node with no neighbors was infected (nothing!)
    return population


def infect_and_project(infections_queue, target, target_idx, running_adj, current_time):
    '''
    Once a person gets infected, we find its neighbors and "project out" when they will infect their
    neighbors.  

    target is a Person instance
    target_idx is the integer of the row/column where that "Person" is in the adjacency matrix
    '''
    target.set_infected(current_time)
    neighbors = get_neighbor_idx(running_adj, target_idx) # gets the uninfected neighbors of the person who was just infected
    if len(neighbors) > 0:
        infection_times = sample_infection_times(target, len(neighbors)) # these times are relative to the time of infection for the current target
        infection_times = current_time + infection_times # this makes those absolute times
        # add these to the list of "planned" infections
        for n, t_inf in zip(neighbors, infection_times):
            insort(infections_queue, ScheduledInfection(target_idx, n, t_inf))
    # "cross-out" the corresponding column of the running adjacency matrix so other Persons do not look to re-infect the person who was just infected (target_idx)
    running_adj[:,target_idx] = 0


def cleanup_queue(infections_queue, target_idx):
    '''
    Once a node is infected (target), no other nodes can infect.  Hence, we can cleanup
    the sorted list of "planned" infections by removing all that *would have* infected
    that target at a later time.
    '''
    i = 0
    while i < len(infections_queue):
        item = infections_queue[i]
        if item.target_idx == target_idx:
            infections_queue.pop(i)
        else:
            i += 1
    return infections_queue


def sample_infection_times(person, n):
    '''
    A particular Person has a period of time during
    which they are infectious.  This occurs AFTER dormancy
    but before they are again healthy

    This function returns an array of n floats
    where each float is how long (after the current Person
    is infected) it takes to infect each neighbor

    Samples from a beta(2,5) distribution, which tries to capture
    the higher probability of infecting during the early period
    before one is sick

    `person` is a Person instance
    `n` is an integer (how many samples to return)
    '''
    t = person.infectious_time_duration
    samples = np.random.beta(2,5,n)
    return t*samples


def get_neighbor_idx(A, i):
    '''
    A is an adjacency matrix
    i is an integer
    Returns the non-zero indices present in row i of A
    '''
    return np.where(A[i,:])[0]


def create_infection_history(population):
    '''
    After running the simulation, we are interested in how many people were symptomatic
    at any given time.  

    `population` is a list of Person instances
    '''
    start_times = []
    end_times = []
    for p in population:
        if p.infected:
            # the start time is when they start showing symptoms (and would presumably seek treatment)
            ts = p.infection_time + p.duration_to_symptoms
            tf = ts + p.symptoms_duration
            start_times.append(ts)
            end_times.append(tf)

    # sort those lists:
    start_times = sorted(start_times)
    end_times = sorted(end_times)

    counter = 0
    history = OrderedDict()
    p1 = 0 # pointer in the list of starting times
    p2 = 0 # pointer in the list of ending times
    N = len(start_times)
    while p1 < N:
        ts = start_times[p1]
        tf = end_times[p2]
        if ts < tf:
            counter += 1
            history[ts] = counter
            p1 += 1
        else:
            counter -= 1
            history[tf] = counter
            p2 += 1

    for i in range(p2,N):
        counter -= 1
        history[end_times[i]] = counter

    return history


def setup_and_run_simulation(nodes, neighbors, infection_prob):

    n_sim = 100
    tmax = 100*24 # a time that is longer than really any individual simulation will last
    bins = np.arange(0,tmax, step=12) # 12 hr increments
    n_bins = len(bins)
    master_df = pd.DataFrame(index = np.arange(1,n_bins+1))
    node_infection_counts = OrderedDict()
    for n in nodes:
        node_infection_counts[n['name']] = 0

    total_infected_counts = []
    for i in range(n_sim):
        population_dict, times, counts = run_single(nodes, neighbors, infection_prob)
        idx = np.digitize(times, bins)
        df = pd.DataFrame({'bin': idx, 'counts': counts})
        mean_df = df.groupby('bin').apply(lambda x: np.mean(x['counts']))
        master_df = pd.concat([master_df, mean_df], axis=1)

        num_infected = 0
        for p in population_dict:
            if p['infected']:
                node_infection_counts[p['name']] += 1
                num_infected += 1
        total_infected_counts.append(num_infected)

    master_df = master_df.fillna(0)

    # compute the variance of the counts in each bin
    binwise_stdev = np.sqrt(np.var(master_df.values, axis=1))
    binwise_means = np.mean(master_df.values, axis=1)
    final_infection_pct = []

    # trim off the excess in the time array
    buffer = 5
    running_idx = n_bins
    while ((running_idx > 0) & (binwise_means[running_idx-1] < 0.001)):
        running_idx -= 1
    cut_idx = running_idx + buffer
    binwise_means = binwise_means[:cut_idx]
    binwise_stdev = binwise_stdev[:cut_idx]
    bins = bins[:cut_idx]

    for k,v in node_infection_counts.items():
        final_infection_pct.append(v/n_sim)
    return (final_infection_pct, bins, binwise_means, binwise_stdev, total_infected_counts)


def run_single(nodes, neighbors, infection_prob):
    infecting_connections = list(filter(
        lambda x: np.random.random() < infection_prob,
        neighbors
    ))
    adj = create_adjacency_matrix(nodes, infecting_connections)    
            
    population = simulate_network(nodes, adj)
    history = create_infection_history(population)

    times = list(history.keys())
    counts = list(history.values())
    return ([{'name': p.name, 'infected':p.infected} for p in population], times, counts)

