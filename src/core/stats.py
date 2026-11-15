# network statistics and health score
# owner: person 2


# returns summary stats (counts, average/max latency, loss) for a device list
def summarize(devices):
    raise NotImplementedError


# returns a network health score from 0 to 100
def health_score(devices):
    raise NotImplementedError
