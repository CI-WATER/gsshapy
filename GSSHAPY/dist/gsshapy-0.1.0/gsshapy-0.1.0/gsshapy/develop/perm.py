'''
Created on Aug 9, 2013

@author: swainn
'''
import itertools

names = ('TRAP', 'ERODE', 'SUBSURFACE')

x = itertools.permutations(names, 2)

for i in x:
    print "'%s'," % '_'.join(i)