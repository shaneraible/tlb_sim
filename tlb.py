from collections import OrderedDict
from os import access
import time 

# The translation lookaside buffer class
class TLB: 
    def __init__(self, capacity=32):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.curr_ppn = 0
    
    def write(self, va, ppn):
        evicted = None
        vpn = self.get_tag(va)

        self.cache[vpn] = ppn
        self.cache.move_to_end(vpn, last=False)

        if len(self.cache) > self.capacity:
            evicted = self.cache.popitem(last = True)

        return evicted

    def get_tag(self, va): 
        # top 20 bits
        return va & (0b1111_1111_1111_1111_1111 << 12)

    def get_offset(self, va):
        # bottom 12 bits
        return va & 0b1111_1111_1111

    def read(self, va):
        vpn = self.get_tag(va)

        if vpn in self.cache:
            self.cache.move_to_end(vpn, last=False)
            return self.cache[vpn] & self.get_offset(va) 
        else:
            return None

# Global Variables
class GVars:
    d_tlb = TLB(32)
    i_tlb = TLB(32)
    curr_ppn = 0
    i_pw = 0
    i_accesses = 0
    i_hits = 0
    i_misses = 0
    d_pw = 0
    d_accesses = 0
    d_hits = 0
    d_misses = 0

# All of the instruction functions
class Instructions:
    def write(addr):
        pa =  GVars.d_tlb.read(addr)

        # miss
        if pa is None:
            GVars.d_pw +=1
            evicted = GVars.d_tlb.write(addr, GVars.curr_ppn)
            GVars.curr_ppn += 1
            GVars.d_misses += 1
        
        # hit
        else:
            GVars.d_hits += 1
        
        GVars.d_accesses += 1

    def read(addr):
        pa =  GVars.d_tlb.read(addr)

        # miss
        if pa is None:
            GVars.d_pw +=1
            evicted = GVars.d_tlb.write(addr, GVars.curr_ppn)
            GVars.curr_ppn += 1
            GVars.d_misses += 1
        
        # hit
        else:
            GVars.d_hits += 1
        GVars.d_accesses += 1

    def i_fetch(addr):
        pa =  GVars.i_tlb.read(addr)

        # miss
        if pa is None:
            GVars.i_pw +=1
            evicted = GVars.i_tlb.write(addr, GVars.curr_ppn)
            GVars.curr_ppn += 1
            GVars.i_misses += 1
        
        # hit
        else:
            GVars.i_hits += 1
        GVars.i_accesses += 1

    def misc(addr):
        pa =  GVars.d_tlb.read(addr)

        # miss
        if pa is None:
            GVars.d_pw +=1
            evicted = GVars.d_tlb.write(addr, GVars.curr_ppn)
            GVars.curr_ppn += 1
            GVars.d_misses += 1

        # hit
        else:
            GVars.d_hits += 1

        GVars.d_accesses += 1

instructions = {
    0: Instructions.read,
    1: Instructions.write,
    2: Instructions.i_fetch,
    3: Instructions.misc,
}

def execute_instruction(line):
    if len(line) > 2: instruction = line.split()[0:2]
    else: return
    instructions[int(instruction[0])](int(instruction[1], 16))


def main():
    tlb_size = 0
    valid_in = False
    while not valid_in:
        try:
            in_tlb_size = input("Enter TLB size (defualt 32): ")
            tlb_size = int(in_tlb_size)
        except:
            print('Error: please enter a positive integer.')
        else:
            if tlb_size>=0: valid_in = True
            else: print('Error: please enter a positive integer.')

    valid_in = False
    inp = ''
    while not valid_in:
        inp = input("Data and Instruction TLB together (t) or separate (s): ").lower()
    
        if inp == 't' or inp == 's': valid_in = True
        else: print('Error: please enter t or s.')
    
    together = inp == 't'

    if together:
        GVars.d_tlb = TLB(tlb_size)
        GVars.i_tlb = GVars.d_tlb
    else:
        GVars.d_tlb = TLB(tlb_size)
        GVars.i_tlb = TLB(tlb_size)

    start = time.time()
    with open('spice.din') as f:
        lines = f.readlines()
        i = 0
        for line in lines:
            execute_instruction(line)
            i+=1

    end = time.time()

    if not together:
        d_hit_rate = GVars.d_hits / GVars.d_accesses
        i_hit_rate = GVars.i_hits / GVars.i_accesses
        hit_rate = (GVars.i_hits + GVars.d_hits) / (GVars.i_accesses + GVars.d_accesses)

        print('\n-----------------------------------------')

        print('\t\tSUMMARY')
        print('-----------------------------------------')
        print(f'executed in {end-start} seconds')
        
        print(f'\nData accesses:\t {GVars.d_accesses}')
        print(f'Data hits:\t {GVars.d_hits}')
        print(f'Data misses:\t {GVars.d_misses}')
        print(f'Data hit rate:\t {d_hit_rate}')
        print(f'Data page walks: {GVars.d_pw}')

        print(f'\nInstruction accesses:\t {GVars.i_accesses}')
        print(f'Instruction hits:\t {GVars.i_hits}')
        print(f'Instruction misses:\t {GVars.i_misses}')
        print(f'Instruction hit rate:\t {i_hit_rate}')
        print(f'Instruction page walks:\t {GVars.i_pw}')

        print(f'\nTotal hit rate: {hit_rate}')
        print(f'\nTotal pages: {GVars.curr_ppn}')
        print('-----------------------------------------\n')

        print('Final instruction TLB')
        print('vpn     : ppn')
        i = 0
        for entry in GVars.i_tlb.cache:
            print(f'{hex(entry)}: {hex(GVars.i_tlb.cache[entry])}')  

        print('\nFinal data TLB')
        print('vpn       : ppn')
        for entry in GVars.d_tlb.cache:
            print(f'{hex(entry)}: {hex(GVars.d_tlb.cache[entry])}')
    
    else:
        hit_rate = (GVars.i_hits + GVars.d_hits) / (GVars.i_accesses + GVars.d_accesses)
        print('\n-----------------------------------------')

        print('\t\tSUMMARY')
        print('-----------------------------------------')
        print(f'executed in {end-start} seconds')
        
        print(f'\nAccesses:\t {GVars.d_accesses + GVars.i_accesses}')
        print(f'Hits:\t {GVars.d_hits + GVars.i_hits}')
        print(f'Misses:\t {GVars.d_misses + GVars.i_misses}')
        print(f'Hit rate:\t {hit_rate}')
        print(f'Page walks: {GVars.d_pw + GVars.i_pw}')
        print('-----------------------------------------\n') 

        print('\nFinal TLB')
        print('vpn       : ppn')
        for entry in GVars.d_tlb.cache:
            print(f'{hex(entry)}: {hex(GVars.d_tlb.cache[entry])}')

    print('-----------------------------------------\n')

if __name__ == "__main__":
    main()