# read the config file
from configparser import ConfigParser

parser =ConfigParser()
parser.read('configuration.ini')
final_states = []
final_states_strings = parser.get('Algorithm_settings', 'final_states').split('],[')
for final_states_combination in final_states_strings :
    states_combination = []
    final_states_separated = final_states_combination.split(',')
    for state in final_states_separated :
        state = state.replace('[','').replace(']','')
        states_combination.append(state)
    final_states.append(states_combination)

print(final_states)