import os
import sumolib

net_path = os.path.join('SUMO_xml', 'HelloWorld.net.xml')
net = sumolib.net.readNet(net_path)

edge = next(ed for ed in net.getEdges() if not ed.getID().startswith(':'))
out = edge.getOutgoing()

print('edge type:', type(edge))
print('getOutgoing type:', type(out))

# getOutgoing may be list-like already
sample = list(out) if not isinstance(out, dict) else list(out.values())
print('sample length:', len(sample))
if sample:
    s0 = sample[0]
    print('sample[0] type:', type(s0))
    print('has getID:', hasattr(s0, 'getID'))
    print('has getTo:', hasattr(s0, 'getTo'))
    if hasattr(s0, 'getID'):
        print('sample[0] id:', s0.getID())

# node outgoing/incoming
node = edge.getFromNode()
node_out = list(node.getOutgoing())
print('node outgoing[0] type:', type(node_out[0]) if node_out else None)
