---
layout: default
title: j. Numpy Arrays
parent: 2. Python
grand_parent: Primers
nav_order: 10
permalink: /primers/3_python/j_numpy_arrays
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

## Numpy Arrays

Numpy arrays can be created using the `numpy` package are great alternatives to Python Lists. Some of the key advantages of Numpy arrays are that they are fast, easy to work with, and give users the opportunity to perform calculations across entire arrays.

- **_Element-wise Calculations_**: Numpy arrays can be used to perform element-wise
  calculations. These operations are very fast and computationally efficient.

- **_Subsetting_**: Another great feature of Numpy arrays is the ability to subset.

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
      # Create 2 new lists height and weight
      height = [1.87,  1.87, 1.82, 1.91, 1.90, 1.85]
      weight = [81.65, 97.52, 95.25, 92.98, 86.18, 88.45]

      # Import the numpy package as np
      import numpy as np

      # Create 2 numpy arrays from height and weight
      np_height = np.array(height)
      np_weight = np.array(weight)

      # Print type of numpy array
      print(type(np_height))

      # Element-wise calculation of BMI
      # Calculate bmi
      bmi = np_weight / np_height ** 2

      # Print the result
      print(bmi)

      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>
    </div>

</div>