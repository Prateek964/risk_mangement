---
layout: default
title: d. Calculus
parent: 1. Maths
grand_parent: Primers
nav_order: 4
permalink: /primers/1_maths/d_calculus
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "c_functions"
next: "e_probability"
---

# Calculus

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

## Calculus

The word Calculus is derived from Latin meaning "small stone". This is so because Calculus helps us in understanding continuous changes by looking at smaller pieces.

Differential Calculus cuts something into small pieces to find how it changes.

For example, during a racing competition, a car's velocity is not constant throughout the race, it keeps on changing from time to time. Therefore, we can find the instantaneous velocity at any time by dividing the distance covered by the car in a very short time by the time duration.

Integral Calculus joins (integrates) the small pieces together to find how much there is. Consider a stick of varying density across its length. Then, we can use integral calculus to find the center of mass of the stick. The similar concept is also used to find the expected value, also known as mean, of a probability distribution.

<div class="subtheory" markdown="1">

### Curve

A curve is a continuous and smooth flowing line without any sharp turns. One way to recognize a curve is that it bends and changes its direction at least once.

For example, the graph of $y=x^2$ and $y=e^x$ represent curves.

</div>
<div class="subtheory" markdown="1">

### Slope

The slope is defined as the ratio of the vertical change between two points, the rise, to the horizontal change between the same two points, the run.

</div>
<div class="subtheory" markdown="1">
### Secant

A secant of a curve is a line that intersects the curve at a minimum of two distinct points.

</div>
<div class="subtheory" markdown="1">

### Tangent

A tangent to a curve at a given point is the straight line that "just touches" the curve at that point.

</div>
<div class="subtheory" markdown="1">

### Derivative

The derivative of a function at a point is the slope of the tangent line to the graph of the function at that point.

- Interpretation: Rate of Change
  Example: Velocity as the rate of change of displacement

- Calculation: Indicated by slope of the curve, given by $ \dfrac{dy}{dx} $

1) Example 1: Let $Y$ = Price of Option = $f(S)$, where $S$= price of Stock, then $\dfrac{dY}{dS}$ gives delta of the option, one of the 5 1st order Greeks

2) Example 2: Let $Y$ = Price of Future = $f(S)$, $S$= price of underlying Commodity, then $\dfrac{dY}{dS}$ gives delta of the Future contract.
</div>
<div class="subtheory" markdown="1">

### Taylor's Series

The Taylor series of a function is an infinite sum of terms that are expressed in terms of the function's derivatives at a single point.

For example, if $f(x)$ is diffrentiable at $x=a$, then we can write $f(x)$ as,

$$f(x) = f(a) + \dfrac{f^{'}(a)}{1!}(x-a) + \dfrac{f^{"}(a)}{2!}(x-a)^2 + ...$$

or,

$$f(x) = \sum_{n=0}^\infty \dfrac{f^{(n)}(a)}{n!}(x-a)^n $$

</div>
<div class="subtheory" markdown="1">

### Integral

Integral represents a numerical value equal to the area under the graph of a function for some interval (definite integral) or a new function the derivative of which is the original function (indefinite integral).

</div>
</div>