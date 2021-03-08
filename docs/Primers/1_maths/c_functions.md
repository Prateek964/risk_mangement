---
layout: default
title: c. Functions
parent: 1. Maths
grand_parent: Primers
nav_order: 3
permalink: /primers/1_maths/c_functions
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "b_series"
next: "d_calculus"
---

# Functions

![Maths](/assets/images/primers/maths.svg)

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

## Functions

In simple terms, a function maps some input to an output. For example, there can be a function _areaCircle_ which maps radius of a circle to its area. Similarly, there can be another function _circumferenceCircle_ which maps the radius of a circle to its circumference.

Note: Functions have many other interesting properties as well but these are not required for this course so we will skip these.

Next, we will discuss briefly about the two most commonly used functions in Quantitative Finance, the exponential function and logarithmic function. Both these funcitons are inverse of each other.

<div class="subtheory" markdown="1">

### Exponential Function

The general exponential function is given by:

$$ f(x) = a^x, $$

where $a$ is a constant.

Note that:

1) When $a=1$, $f(x)$ has a constant value of 1.  
2) When $0<a<1$, $f(x)$ decreases exponentially as $x$ increases.   
3) When $0<a<1$, $f(x)$ increases exponentially as $x$ decreases.   

The natural exponential function is given by:

$$ f(x) = e^x $$

where $e$ is "Euler's Number", given by 2.72.

</div>

<div class="subtheory" markdown="1">

### Logarithmic Function

To understand the logarithms, let us ask ourselves the question that how many times do we have to multiply 2 to itself to get 8?

Well, since $2 \times 2 \times 2 = 8 $, so the asnswer is 3.

We write this as $log_2(8) = 3$

Therefore, $ log_b(x) =y $ implies that $b^y=x$

Some properties of Logarithms:

1) $ log_b(xy) = log_b x + log_b y $    
2) $ log_b \left( \dfrac{x}{y} \right) = log_b x - log_b y $  
3) $ log_b (x^p) = p log_b x $  
</div>
</div>