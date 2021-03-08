---
layout: default
title: c. Interest Rates
parent: 2. Finance
grand_parent: Primers
nav_order: 3
permalink: /primers/2_finance/c_interest_rates
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "b_risk_vs_reward"
next: "d_time_value_of_money"
---

# Interest Rates

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
     
## Interest Rates

The interest rate is the percent of principal charged by the lender for the use of its money.

Interest Rate can be of the type Simple Interest or Compound Interest.

- Simple Interest is calculated based on the principal amount (Consider it as an Arithmetic Progression like growth)
- Compound Interest is calculated based on the principal amount and the interest (Consider it as a Geometric Progression bsed growth)

<div class="subtheory" markdown="1">

### Simple Interest

Simple interest is calculated by multiplying the daily interest rate by the principal by the number of days that elapse between payments.

$Simple \text{ } Interest  =  P \times r \times t$

where:
$P$: Principle,  
$r$: Daily interest rate, and  
$t$: Number of days between payments

</div>
<div class="subtheory" markdown="1">

### Compound Interest

The amount earned using compounding can be calculated as:

$$ A = P \left(1+ \dfrac{r}{n} \right)^{nt} $$

where,

$A$: The amount you’ll end up with,  
$P$: Your initial deposit, known as the principal,  
$r$: the annual interest rate, written in decimal format,  
$n$: the number of compounding periods per year (for example, monthly is 12 and weekly is 52), and  
$t$: the amount of time (in years) that your money compounds

The compound interest (CI) can be calculated by subtracting the the initial deposit $P$ from the total amount earned $A$.

<!--
https://www.thebalance.com/compound-interest-4061154#:~:text=Compound%20interest%20is%20interest%20earned,sometimes%20known%20as%20exponential%20growth.
-->

<div class="subtheory" markdown="1">

- **_Continuous Compounding_**: In continuous compounding, the account balance continually earns interest, and that interest gets added to the balance, which then also earns interest and it continues to grow.

Using continuous compounding,

$$ A = P e^{rt} $$

- **_Discrete Compounding_**: Discrete compounding refers to the method by which interest is calculated and added to the principal at certain set points in time.
  For discrete compounding,

  $$ A = P \left(1+ \dfrac{r}{m} \right)^{mt} $$

  Here, $m$ refers to numbner of compounding periods per year.

</div>
</div>
</div>