import numpy as np
import random 

def rand_key(p): 
    key1 = []
    for i in range(p): 
        temp = random.randint(0, 1)
        key1.append(temp) 
          
    return(np.array(key1))
