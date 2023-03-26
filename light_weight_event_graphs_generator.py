from os.path import join, dirname
from os import listdir, getcwd
import copy
import time
import json
from matplotlib import pyplot as plt

Vessel_initial_conditions_path = join(dirname(__file__), 'JSON_FILES/Vessel_initial_conditions.json')
Vessel_events_path = join(dirname(__file__), 'JSON_FILES/Vessel_attacks.json')

def read_json(path, field="" ):
        """ Read the json file and return the list of events """
        with open(path) as f:
            data = json.load(f)
        if field == "":
            return data
        else :
            return data[field]
        

""" Create and initialize all the states of the system """
initial_states = {}
initial_conditions = read_json(path=Vessel_initial_conditions_path)
for name, value in initial_conditions.items():
    initial_states[name] = value


""" According to the json file, create the events """
caracteristics_changed = {}
conditions = {} 
events_names = {}       
events_list = read_json(path=Vessel_events_path, field = 'atomic-attacks')
for item in events_list:
    caracteristics_changed[item["id"]] = item["results"]
    conditions[item["id"]] = item["conditions"]
    events_names[item["id"]] = item["name"]

events_names["0.0.0"] = "outside"

max_iterations = 1000



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





events_graphs = [] #list of graphs, a graph  is a couple : a list of nodes (events) and the global states of the system under this graph
events_graphs_minimality = []

finished_graphs = []
initial_event = "0.0.0"
events_graphs.append([[initial_event], initial_states])
counter = 0

efficiency_graph = []
#start the timer for the global function
start_time_global = time.time()

possible_events = []
old_possible_events = []
finished_graph_added= False

footprint = 0
for graph in events_graphs :
    # if counter > self.max_iterations :
    #     break
    
    #start the timer for each loop
    start_time = time.time()
    
    states = copy.deepcopy(graph[1])
    possible_events.clear()

    # gather all the possible events for this given states
    for  associated_event, event_conditions in conditions.items() :
        if associated_event not in graph[0] and  check_conditions(event_conditions, states):
            possible_events.append(associated_event)


    if len(possible_events) == 0 or graph[0][-1][0:4]=="3.1.": #    if there is no possible event or if a final state is reached, the graph is finish 
        
        if  graph not in  finished_graphs :
            finished_graphs.append(graph)
            events_graphs.remove(graph)
            finished_graph_added = True

        

    else  : # if there is possible events, we create a new graph for each possible event
        for new_event in possible_events :
            new_graph = copy.deepcopy(graph)
            new_states = copy.deepcopy(states)
            for caracteristic_name, value in caracteristics_changed[new_event].items():
                for index in range(len(value)) :
                    if value[index] != "-1" :
                        new_states[caracteristic_name][index] = value[index]

            new_graph[0].append(new_event)
            new_graph[1] = copy.deepcopy(new_states)
            events_graphs.append(new_graph)
        
        last_graph_length = len(events_graphs[-1][0])

        for grand_pa_graph in events_graphs : # remove the "grand-parents" graphs
            if len(grand_pa_graph[0]) == last_graph_length-1 : # the list is sorted by length, so if the length is not the same, we can exit the loop
                break
            if len(grand_pa_graph[0]) < last_graph_length-1 :
                events_graphs.remove(grand_pa_graph)
    
    #end the timer for each loop
    end_time = time.time()
    efficiency_graph.append([len(events_graphs), end_time-start_time])

    counter += 1

# if not finished_graph_added :
#     last_graph_length = len(events_graphs[-1][0])
#     for parent_graph in events_graphs : # remove the "parents" graphs
#                 if len(parent_graph[0]) == last_graph_length : # the list is sorted by length, so if the length is not the same, we can exit the loop
#                     break
#                 if len(parent_graph[0]) < last_graph_length :
#                     events_graphs.remove(parent_graph)
# else : finished_graph_added = False

#end the timer for the global function
end_time_global = time.time()



plt.xlabel('Time')
plt.ylabel('Nb of graphs')
plt.title('Nb of graphs vs time taken for generation')
plt.plot(efficiency_graph[0], efficiency_graph[1])
plt.show()

global_timer = end_time_global - start_time_global

print("Not finished : " + str(len(events_graphs)))
print("Finished : " + str(len(finished_graphs)))
print ("Global timer : " + str(global_timer))

count_files =0
original_file_name = "results"
file_name = original_file_name+ str(count_files)+".txt"
path_main = getcwd()
path_result_folder = join(path_main, "Results")
existing_files = listdir("Results") 
while file_name in existing_files:
    count_files += 1
    file_name = original_file_name + str(count_files)+".txt"
   

 


# write the results in a specific folder ::


with open(join(path_result_folder,file_name), "w") as f:
    #describe the configuration$
    f.write("Footprint: " + str(footprint) + "\nMax iterations : " + str(max_iterations) + "\nNumber of iterations : " + str(counter) ) 
    f.write("\nScenarios that lead to final state : " + str(len(finished_graphs)) + "\nScenarios that do not lead to final state : " + str(len(events_graphs)) + "\nGlobal timer : " + str(global_timer) + "s" )
    for graph in finished_graphs :
        f.write("\n"+ str(graph[0]) )
    
    f.write("\nWith events names :")
    for graph in finished_graphs :
        f.write("\n"+ str([events_names[event] for event in graph[0]]) )





