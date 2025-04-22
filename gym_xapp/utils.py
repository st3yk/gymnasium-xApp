def decode_state(state):
    splitted = state.split(';')
    throughput = splitted[:3]
    prbs = splitted[3:6]
    mcs = splitted[6:9]
    nok = splitted[9:]

def normalize(value, min_v, max_v):
    return 2 * (value - min_v) / (max_v - min_v) - 1 # min max scaling [-1;1]