---
layout: default
title: a. Sequence
parent: 1. Maths
grand_parent: Primers
nav_order: 1
permalink: /primers/1_maths/a_sequence
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "/primers/1_maths/"
next: "b_series"
---

# Sequence

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

## Sequence

A sequence is a list of numbers in a "special order". These numbers are known as terms of the sequence and we can use the special order to write a general expression for $n^{th}$ term of the sequence.

Most common examples of sequence are Arithmetic Progressions and Geometric Progressions.

<div class="subtheory" markdown="1">

### Arithmetic Progression

An Arithmetic Progression is a sequence of numbers in which the difference of any two consecutive terms is a constant, which is known as the common difference of the sequence.

Therefore, the "special order" in an AP is characterized by the common difference $d$ and we can write a general expression for the $n^{th}$ term if we know the common difference $d$ and the first term $a$.

It can be easily proved that:

- The $n{th}$ term of an AP is given by:

$$ a_n = a + (n-1)d $$

- The sum of first $n$ terms of an AP is given by:

$$ S_n = \dfrac{n}{2}[2a+ (n-1)d ] $$

- If the number of terms in the AP is finite and equal to $n$, then we can $S_n$ in terms of $n$, $a$ and $l$, where $l$ represents the last term and is given by $a + (n-1)d $, as below:

$$ S_n = \dfrac{n}{2} (a+l) $$

</div>

---

<div class="subtheory" markdown="1">

### Geometric Progression

A Geometric Progression is a sequence of numbers in which the ratio of any two consecutive terms is a constant, which is known as the common ratio of the sequence.

Therefore, the "special order" in a GP is characterized by the common ratio $r$ and we can write a general expression for the $n^{th}$ term if we know the common ratio $r$ and the first term $a$.

It can be easily proved that:

- The $n^{th}$ term of a GP is given by:
  $$ a_n = ar^{(n-1)} $$

- The sum of first $n$ terms of a GP is given by:

$$ S_n = a \left( \dfrac{r^n-1}{r-1} \right) $$

- If the number of terms in the GP is infinite and common ratio $r$ is less than 1, then $S_n$ can be written as:

$$ S_n = \dfrac{a}{1-r} $$

</div>
</div>

