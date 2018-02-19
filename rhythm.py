# osu! rhythm analyzer
# Based on Toussaint's Metrical Complexity (see README for more info)

# Rhythms are given in the form of indices, like (0, 3, 6, 10, 12)
# Every single note is considered instantaneous and an onset, so pulses == onsets

from itertools import permutations

def prime_factorization(n):
    # lazy code
    assert n > 1

    m = n
    factors = []
    while m > 1:
        for i in range(2, m+1):
            if m % i == 0:
                factors.append(i)
                m //= i
                break

    return factors


def metrical_hierarchies(n):
    # Get all permutations without repeats
    unique_factorizations = set(permutations(prime_factorization(n)))

    hierarchies = []
    for factorization in unique_factorizations:
        w = [1] * n
        l = 1
        for factor in factorization:
            for i in range(0, n, n//l):
                w[i] += 1
            l *= factor  # l = n is never used

        # For our purposes, invert hierarchy so that stronger beats have less weight
        #max_weight = max(w)
        #for i in range(n):
        #    w[i] = max_weight - w[i] + 1

        hierarchies.append(w)

    return hierarchies


def metrical(rhythm, n):
    hierarchies = metrical_hierarchies(n)
    complexities = []
    for hierarchy in hierarchies:
        complexity = 0
        for pulse in rhythm:
            complexity += hierarchy[pulse]
        complexities.append(complexity)

    # Final metrical complexity is the average of complexities for all hierarchies
    metrical = sum(complexities) / len(complexities)
    return metrical


def onsets(rhythm):
    pass

def onorm():
    pass

def test_functions():
    clave = (0, 3, 6, 10, 12)
    print(metrical(clave, 16))

test_functions()
