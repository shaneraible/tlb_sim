# tlb_sim
This project simulates a Translation Lookaside Buffer given the address trace file spice.din. 

To run
```
python3 tlb.py
```

The ouput is a breakdown of the hit rate and the resulting translation lookaside buffer for each data and instruction accesses. The replacement policy used is LRU and is implemented used an OrderedDict. The backbone of this is a hashmap that contains references to nodes in a doublely linked list. Every time the memory is accessed we move it to the top of the dict.