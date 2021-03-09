---
layout: default
title: g. Loops
parent: 3. Python
grand_parent: Primers
nav_order: 7
permalink: /primers/3_python/a_intro
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "/primers/2_finance/"
next: ""
---

# Money

![Finance](/assets/images/primers/finance.svg)

{: .no_toc }

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
2. TOC
{:toc}
</details>

---

<div class="theory" markdown="1">

<div class="subtheory" markdown="1">

## Loops

For loops iterate over a given sequence. For loops can iterate over a sequence of numbers using the range function

Break statement: break is used to exit a for loop or a while loop
Continue Statement: continue is used to skip the current block, and return to the for statement



<div class="exercise">
    
    <div data-datacamp-exercise data-lang="python" data-height="auto">
     primes = [2, 3, 5, 7]
    for prime in primes:
    print(prime)

    # Prints out the numbers 0,1,2,3,4
    for x in range(5):
      print(x)

# Prints out 3,4,5
for x in range(3, 6):
  print(x)

# Prints out 3,5,7
for x in range(3, 8, 2):
  print(x)


# Prints out only odd numbers - 1,3,5,7,9
for x in range(10):
  # Check if x is even
  if x % 2 == 0:
    continue
  print(x)

# Prints out only odd numbers less than 5- 1,3
for x in range(10):
  # Exit the loop at x = 5
  if x == 5:
    break

  # Check if x is even
  if x % 2 == 0:
    continue
  print(x)
  
    </div>

  </div>

</div>
</div>