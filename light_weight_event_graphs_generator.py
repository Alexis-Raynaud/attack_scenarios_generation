#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import join 
from os import listdir, getcwd, mkdir, remove
from sys import argv, platform
import copy
import time
import json
from matplotlib import pyplot as plt
import graphviz as gv
from configparser import ConfigParser, BasicInterpolation




def read_json(path, field="" ):
        """ Read the json file and return the list of events """
        with open(path) as f:
            data = json.load(f)
        if field == "":
            return data
        else :
            return data[field]
        
def create_states(path_initial_conditions):
    """ Create and initialize all the states of the system """
    initial_states = {}
    initial_conditions = read_json(path=path_initial_conditions)
    for name, value in initial_conditions.items():
        initial_states[name] = value
    
    return initial_states

def create_events(path_events, initial_states):
    """ According to the json file, create the events """
    caracteristics_changed = {}
    conditions = {} 
    events_names = {}       
    events_list = read_json(path=path_events, field = 'atomic-attacks')
    for item in events_list:
        caracteristics_changed[item["id"]] = item["results"]
        conditions[item["id"]] = item["conditions"]
        events_names[item["id"]] = item["name"]
    
    events_names["0.0.0"] = "outside"
    conditions["0.0.0"] = initial_states
    caracteristics_changed["0.0.0"] = {}
    
    return events_names, conditions,caracteristics_changed 


def state_condition_comparison(  condition, state):
    """ Compare the state of the system with the condition of the attack
        If the strict conditions are activated, the state must be equal to the condition
        Else it's enough if the state is superior or equal to the condition
    """
    if state == condition:
        return True
    if len(condition)<2:
        return False
    # if the condition is a list, we need to check if the unvalid values are not -1
    for i in range (len(state)):
        if (state[i] != condition[i]) and (condition[i] != "-1"): # if the value is -1, it means that the condition is not important
            return False
    return True
    

def check_conditions(conditions, states ):
    """ Check if the attack is possible """
    for name, value in conditions.items():
        if not state_condition_comparison(value, states[name]) :
            return False
    return True # if the systeme states are sufficient, the attack is possible

def check_final_states(final_states, graph):
    for final_state in final_states :
        if set(final_state).issubset(set(graph[0])) :
            return True
    return False


def create_graphs(initial_states, conditions, caracteristics_changed,final_states,instant_transitions_states,not_superposable_states, max_iterations,max_length, max_footprint):

    events_graphs = [] #list of graphs, a graph  is a list containing a list of nodes (events), the global states of the system under this graph ,the actual footprint and the possible events at n-1

    not_critic_finished_graphs = []
    critic_finished_graphs = []
    initial_event = "0.0.0"
    events_graphs.append([[initial_event], initial_states,0, [],0]) # [events, states, footprint, possible_events, if contains a not superposable state]
    counter = 0

    efficiency_graph = []
    #start the timer for the global function
    start_time_global = time.time()

    possible_events = []


    index = 0



    while len(events_graphs) > 0  and counter < max_iterations and len(events_graphs[-1][0])<= max_length +1 : # max_length +1 because the first event is the initial eventit doesn't count as an action done by the attacker

        
        new_events_graphs = []

        for graph in events_graphs :
            if counter > max_iterations :
                break
            
            
            #start the timer for each loop
            start_time = time.time()
            
            states = copy.deepcopy(graph[1])
            possible_events.clear()

            # gather all the possible events for this given states
            for  associated_event, event_conditions in conditions.items() :
                if associated_event not in graph[0] and  check_conditions(event_conditions, states):
                    possible_events.append(associated_event)
            


            #check if one of the final states list is in the graph :

            if check_final_states(final_states, graph) :
                if graph not in critic_finished_graphs :
                    critic_finished_graphs.append(graph)
                events_graphs.remove(graph)
                    

            elif len(possible_events) == 0 : #    if there is no possible event, the graph is finish 
                
                if  graph not in  not_critic_finished_graphs :
                    not_critic_finished_graphs.append(graph)
                    events_graphs.remove(graph)


            else  : # if there is possible events, we create a new graph for each possible event
                
                
                #check if any element in possible_events is in instant_transitions_states
                direct_transition = []
                for event in instant_transitions_states :
                    if event in possible_events :
                        direct_transition.append(event)


                if len(direct_transition) > 0 :
                    for new_event in direct_transition :
                        new_graph = copy.deepcopy(graph)
                        new_states = copy.deepcopy(states)
                        for caracteristic_name, value in caracteristics_changed[new_event].items():
                            for index in range(len(value)) :
                                if value[index] != "-1" :
                                    new_states[caracteristic_name][index] = value[index]

                        new_graph[0].append(new_event)
                        new_graph[1] = copy.deepcopy(new_states)
                        new_graph[3] = copy.deepcopy(possible_events)
                        new_events_graphs.append(new_graph)
                        possible_events.remove(new_event)
                        
                
                else : 
                    for new_event in possible_events :
                        counter += 1
                        if counter > max_iterations :
                            break
                        
                        event_superposable = True
                        
                        if new_event in not_superposable_states :
                            if graph[4] == 0 :
                                graph[4] = 1
                            else :
                                event_superposable = False
                            
                                

                        if max_footprint > 0 and event_superposable:
                            new_footprint = copy.deepcopy(graph[2])
                            if new_event in graph[3] : # graph[3] is the possible events at n-1
                                new_footprint += 1
                            
                            if new_footprint <= max_footprint :
                                new_graph = copy.deepcopy(graph)
                                new_states = copy.deepcopy(states)
                                for caracteristic_name, value in caracteristics_changed[new_event].items():
                                    for index in range(len(value)) :
                                        if value[index] != "-1" :
                                            new_states[caracteristic_name][index] = value[index]

                                new_graph[0].append(new_event)
                                new_graph[1] = copy.deepcopy(new_states)
                                new_graph[2] = copy.deepcopy(new_footprint)
                                new_graph[3] = copy.deepcopy(possible_events)
                                new_events_graphs.append(new_graph)
                        elif event_superposable : 
                            new_graph = copy.deepcopy(graph)
                            new_states = copy.deepcopy(states)
                            for caracteristic_name, value in caracteristics_changed[new_event].items():
                                for index in range(len(value)) :
                                    if value[index] != "-1" :
                                        new_states[caracteristic_name][index] = value[index]
                            new_graph[0].append(new_event)
                            new_graph[1] = copy.deepcopy(new_states)
                            new_graph[3] = copy.deepcopy(possible_events)
                            new_events_graphs.append(new_graph)

                        
                    
                if max_footprint <=0 :
                    if len(new_events_graphs) > 0 :
                        last_graph_length = len(new_events_graphs[-1][0])
                        for grand_pa_graph in new_events_graphs : # remove the "grand-parents" graphs
                            if len(grand_pa_graph[0]) == last_graph_length-1 : # the list is sorted by length, so if the length is not the same, we can exit the loop
                                break
                            if len(grand_pa_graph[0]) < last_graph_length-1 :
                                new_events_graphs.remove(grand_pa_graph)
                    
                
            
            #end the timer for each loop
            end_time = time.time()
            efficiency_graph.append([len(events_graphs), end_time-start_time])

            
        
        events_graphs = copy.deepcopy(new_events_graphs)

    

    end_time_global = time.time()

    global_timer = end_time_global - start_time_global

    return critic_finished_graphs, not_critic_finished_graphs, events_graphs, efficiency_graph, global_timer, counter


def create_results_folder_path() :
    main_path = getcwd()
    directories = listdir(main_path)
    folder_root_name = "Results"
    counter = 0
    folder_name = folder_root_name + str(counter)
    while folder_name in directories :
        counter += 1
        folder_name = folder_root_name + str(counter)
    mkdir(join(main_path,folder_name))
    return join(main_path,folder_name)

def create_new_render_file(file_name, folder_path) :
    count_files =0
    original_file_name = file_name
    file_name = original_file_name+ str(count_files)+".txt"
    
    existing_files = listdir(folder_path) 
    while file_name in existing_files:
        count_files += 1
        file_name = original_file_name + str(count_files)+".txt"
    
    return join(folder_path,file_name)

def visualize_time (efficiency_graph, folder_path) :
    plt.xlabel('Time')
    plt.ylabel('Nb of graphs')
    plt.title('Nb of graphs vs time taken for generation')
    plt.plot(efficiency_graph[0], efficiency_graph[1])
    plt.savefig(fname = join(folder_path, "time") ) 

def write_results ( folder_path, final_states, minimality_graphs, critic_finished_graphs, not_critic_finished_graphs, events_graphs, events_names, global_timer, max_footprint, max_iterations, counter, max_length) :
        
    file_results_long = create_new_render_file("results", folder_path)
    with open(file_results_long, "w") as f:
        #describe the configuration$
        f.write("Footprint: " + str(max_footprint) +"\nMax length : "+ str(max_length) +"\nMax iterations : " + str(max_iterations) + "\nNumber of iterations : " + str(counter) ) 
        f.write("\nDifferents minimum scenarios that lead to a final state graphs : " + str(len(minimality_graphs)) )
        f.write("\nScenarios that lead to a final state without minimality : " + str(len(critic_finished_graphs)) + "\nScenarios that do not lead to final state : " + str(len(not_critic_finished_graphs)) + "\nScenarios that were still running whe the algorithm stops : " + str(len(events_graphs)) + "\nGlobal timer : " + str(global_timer) + "s" )
        f.write("\n\nThe final states wanted are :" )
        for final_state in final_states :
            f.write("\n"+ str(final_state) )
            f.write("\n"+ str([events_names[event] for event in final_state]) )
            
        
        f.write("\n\nDifferents minimum scenarios that lead to a final state graphs (with event id) : ")
        for graph in minimality_graphs :
            f.write("\n"+ str(graph[0]) )
        
        f.write("\nWith events names :")
        for graph in minimality_graphs :
            f.write("\n"+ str([events_names[event] for event in graph[0]]) )
        
        f.write("\n\nScenarios that lead to final state without minimality (with event id) : ")
        for graph in critic_finished_graphs :
            f.write("\n"+ str(graph[0]) )
        
        f.write("\nWith events names :")
        for graph in critic_finished_graphs :
            f.write("\n"+ str([events_names[event] for event in graph[0]]) )
        
        f.write("\n\nScenarios that do not lead to final state (with event id) : ")
        for graph in not_critic_finished_graphs :
            f.write("\n"+ str(graph[0]) )
        
        f.write("\nWith events names :")
        for graph in not_critic_finished_graphs :
            f.write("\n"+ str([events_names[event] for event in graph[0]]) )

        f.write("\n\nScenarios that were still running when the algorithm stops (with event id) : ")
        for graph in events_graphs :
            f.write("\n"+ str(graph[0]) )
        
        f.write("\nWith events names :")
        for graph in events_graphs :
            f.write("\n"+ str([events_names[event] for event in graph[0]]) )



def check_conditions_with_previous_event(previous_event, current_event, conditions, caracteristics_changed) :
    """ If at least 1 caracteristic changed is in the conditions it's true, previous and current event are directly linked"""
    for condition_name, condition_value in conditions[current_event].items() :
        for caracteristic_name, caracteristic_value in caracteristics_changed[previous_event].items() :
            if condition_name == caracteristic_name :
                if condition_value == caracteristic_value :
                    return True
                elif len(condition_value) > 1 :
                    if condition_value[0] == "-1" and condition_value[1] == caracteristic_value[1] :
                        return True
                    elif condition_value[1] == "-1" and condition_value[0] == caracteristic_value[0] :
                        return True
                    else :
                        pass
                else :
                    pass
    
    return False
            

def visualize_top_events_graphs(critic_finished_graphs, events_names, conditions, caracteristics_changed, folder_path ) :

    colors = ["black","red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "grey" ]
    count_nb_graphs = 0
    no_previous_event = True
    for graph in critic_finished_graphs :
        filename = "graph" + str(count_nb_graphs)
        
        G = gv.Digraph(filename= filename, directory=folder_path,format='png' )
        count_nb_graphs += 1
        different_branchs = 0
        for index in range (len (graph[0])) :
            if index == 0 :
                G.node(str(graph[0][index]),label = events_names[graph[0][index]], color = colors[different_branchs])
            if index == 1 :
                G.node(str(graph[0][index]),label = events_names[graph[0][index]], color = colors[different_branchs])
                G.edge(str(graph[0][index-1]), str(graph[0][index]), color = colors[different_branchs])
            
            if index > 1 :
                if check_conditions_with_previous_event(graph[0][index-1], graph[0][index], conditions, caracteristics_changed) :
                    G.node(str(graph[0][index]),label = events_names[graph[0][index]], color = colors[different_branchs])
                    G.edge(str(graph[0][index-1]), str(graph[0][index]), color = colors[different_branchs])
                else :
                    different_branchs += 1
                    for i in range(1, index) :
                        if check_conditions_with_previous_event(graph[0][i], graph[0][index], conditions, caracteristics_changed) :
                            G.node(str(graph[0][index]),label = events_names[graph[0][index]], color = colors[different_branchs])
                            G.edge(str(graph[0][i]), str(graph[0][index]), color = colors[different_branchs])
                            no_previous_event = False
                            break
                    if no_previous_event:
                        G.node(str(graph[0][index]),label = events_names[graph[0][index]], color = colors[different_branchs])
                        G.edge(str(graph[0][0]), str(graph[0][index]), color = colors[different_branchs])
                        no_previous_event = True
                        
                    else :
                        no_previous_event = True
        
        G.render(view = False)
    
   
def minimality (critic_finished_graphs) :
    """ Check if the graphs are minimal, if not, remove the graph that is not minimal"""
    minimals_graphs = copy.deepcopy(critic_finished_graphs)
    graphs_to_remove = []
    for i in range(len(critic_finished_graphs)) :
        for j in range(len(critic_finished_graphs)) :
            if i != j :
                if set(critic_finished_graphs[i][0]).issubset(set(critic_finished_graphs[j][0])) :
                    if len(critic_finished_graphs[i][0]) > len(critic_finished_graphs[j][0]) : #
                        graphs_to_remove.append(i)
                    else :
                        graphs_to_remove.append(j)
    
    graphs_to_remove = list(set(graphs_to_remove))
    graphs_to_remove.sort(reverse=True)
    for index in graphs_to_remove :
        del minimals_graphs[index]
    
    return minimals_graphs

def read_config_file_return_variables ():
    config = ConfigParser()
    config.read('configuration.ini')
    max_length = int(config.get('Algorithm_settings', 'scenario_max_length'))
    not_superposable_states = config.get('Vessel_settings', 'not_superposable_states').split(',')
    instant_transitions_states= config.get('Vessel_settings', 'instant_transitions_states').split(',')

    file_dir = getcwd()
    config.set('Common', 'file_dir', file_dir)
    max_iterations = int(config.get('Algorithm_settings', 'max_iterations'))
    max_footprint = int(config.get('Algorithm_settings', 'max_footprint'))
    json_path = config.get('Common', 'json_path').replace("$(file_dir)", file_dir)
    Vessel_initial_conditions_path = config.get('Vessel_settings', 'json_path_initial_conditions').replace("$(json_path)", json_path)
    Vessel_events_path = config.get('Vessel_settings', 'json_path_attacks').replace("$(json_path)", json_path)
    final_states = []
    final_states_strings = config.get('Algorithm_settings', 'final_states').split('],[')
    for final_states_combination in final_states_strings :
        states_combination = []
        final_states_separated = final_states_combination.split(',')
        for state in final_states_separated :
            state = state.replace('[','').replace(']','')
            states_combination.append(state)
        final_states.append(states_combination)
    
    want_minimality = int(config.get('Render_settings', 'want_minimality'))
    want_to_see_results = int(config.get('Render_settings', 'want_to_see_results'))

    return max_length, not_superposable_states, instant_transitions_states, Vessel_initial_conditions_path, Vessel_events_path, final_states, max_iterations, max_footprint, want_minimality, want_to_see_results   

def clear_unuseful_files (folder_path) :
    """ Clear the folder of the unuseful files """
    files = listdir(folder_path)
    for file in files :
        if file.endswith(".png")  :
            try :
                remove(folder_path + "/" + file.split('.')[0])
            except : pass


def main(argc = 0, argv = []):

    # Read the configuration file
    max_length, not_superposable_states, instant_transitions_states, Vessel_initial_conditions_path, Vessel_events_path, final_states, max_iterations, max_footprint, want_minimality, want_to_see_results = read_config_file_return_variables()
    
    if argc == 0 or argc > 5:
        print("Error: the program needs between 0 and 4 arguments, if 0 arguments the program will use values in the configuration file")
        print("1) The maximum length of a sequence (default = 10)")
        print("2) The maximum footprint (if 0 the footprint isn't taken into account)")
        print("3) The maximum number of iteration (default = 100 000)")
        print("4) If you want to see the results with graphs (default = 0, no) (1 = yes) ")
        print("Example : python3 light_weight_event_graphs_generator.py 10 3 100000")
        exit()
    
    else:
        if argc > 1 :
            max_length = int(argv[1])
        if argc > 2 :
            max_footprint = int(argv[2])
        if argc > 3 :
            max_iterations = int(argv[3])
        if argc > 4 :
            want_to_see_results = int(argv[4])
        
   
    try : 

        initial_states = create_states(Vessel_initial_conditions_path)
        events_names, conditions,caracteristics_changed = create_events(Vessel_events_path, initial_states)

        critic_finished_graphs, not_critic_finished_graphs, events_graphs, efficiency_graph, global_timer, counter = create_graphs(initial_states, conditions, caracteristics_changed, final_states, instant_transitions_states,not_superposable_states, max_iterations, max_length, max_footprint)
        
        folder_path = create_results_folder_path()
        
        minimality_graphs = minimality(critic_finished_graphs)

        write_results(folder_path , final_states, minimality_graphs, critic_finished_graphs, not_critic_finished_graphs, events_graphs, events_names, global_timer, max_footprint, max_iterations, counter, max_length)
        
        visualize_time(efficiency_graph, folder_path)

        if want_minimality and (platform == "linux" or platform == "linux2") and want_to_see_results:
            visualize_top_events_graphs(minimality_graphs, events_names, conditions, caracteristics_changed, folder_path=folder_path)
        elif (platform == "linux" or platform == "linux2") and want_to_see_results :
            visualize_top_events_graphs(critic_finished_graphs, events_names, conditions, caracteristics_changed, folder_path=folder_path)
        
        clear_unuseful_files(folder_path)
        
        print("Not finished : " + str(len(events_graphs)))
        print("Finished but no final event reach : " + str(len(not_critic_finished_graphs)))
        print("Finished with final event reach and minimality : " + str(len(minimality_graphs)))
        print("Finished with final event reach : " + str(len(critic_finished_graphs)))
        print ("Global timer : " + str(global_timer))

    
    except ValueError :
        print("Error: the program needs between 0 and 4 arguments, if 0 arguments the program will use values in the configuration file")
        print("1) The maximum length of a sequence (default = 10)")
        print("2) The maximum footprint (if 0 the footprint isn't taken into account)")
        print("3) The maximum number of iteration (default = 100 000)")
        print("4) If you want to see the results with graphs (default = 0, no) (1 = yes) ")
        print("Example : python3 light_weight_event_graphs_generator.py 10 3 100000")
        exit()
    
    
  

if __name__ == '__main__' :
    main(len(argv), argv)



