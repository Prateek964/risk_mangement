---
layout: default
title: a. Options Pricing using BSM
parent: 4. Articles
grand_parent: Market Risk
nav_order: 1
permalink: /market_risk/4_articles_/a_options_pricing_using_BSM
nav_img: "/assets/images/paper.svg"
nav_alt: "Study"
previous: "/market_risk/4_articles/"
next: "/"
---

# Options Pricing using BSM

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

## What is the BSM Model?

Black Scholes Merton’s (BSM) model is one of the most important results in Quantitative Finance and serves as the starting point of pricing of Equity Derivatives. It establishes the link between the price of Options on an asset and the price of the asset. The result was obtained in the 1970’s by the Trio of Black, Scholes & Merton.

</div>

<div class="theory" markdown="1">

## How is the BSM model derived ?

Like most of the quantitative finance models, the BSM model is derived from a physics model which was originaly used for studying the movement of particles called as Geometric Brownian Motion. GBM has a partial derivative equation with constant drift term and a constant volatility term. However the most important part of the BSM model is the result or equation that is obtained which relates the price of the option with the price of the underlying stock.

</div>

<div class="theory" markdown="1">

## So What exactly is the BSM model and the derived equation?

The model gives the theoretical price of the derivatives under several assumptions. 

The model primarily has 5 inputs including: 
- Spot Price, 
- Strike Price, 
- Time left to maturity, 
- Volatility of the underlying Stock, 
- Risk free rate of returns.

<div class="subtheory" markdown="1">

### Pricing of Call Option using the BSM model 

The price of a call options is given by: 
s
$C=S_{t} N\left(d_{1}\right)-K e^{-r t} N\left(d_{2}\right)$  
where:  
$d_{1}=\frac{\ln \frac{S_{t}}{K}+\left(r+\frac{\sigma_{z}^{2}}{2}\right) t}{\sigma_{s} \sqrt{t}}$  
and  
$d_{2}=d_{1}-\sigma_{s} \sqrt{t}$  
where:  
$C=$ Call option price   
$S=$ Current stock (or other underlying) price   
$K=$ Strike price    
$r=$ Risk-free interest rate  
$t=$ Time to maturity  
$N=$ A normal distribution  

</div>

<div class="subtheory" markdown="1">

### Pricing of Put Option using the BSM model 

The price of a put option is given by:

$$
\mathrm{P}_{0}=\mathrm{Ke}^{\mathrm{rT}} \times \mathrm{N}\left(-\mathrm{d}_{2}\right)-\mathrm{S}_{0} \times \mathrm{N}\left(-\mathrm{d}_{1}\right)
$$
Where:
$$
\begin{array}{l}
\mathrm{d}_{1}=\frac{\ln \left(\frac{\mathrm{S}_{0}}{\mathrm{~K}}\right)+\left[\mathrm{r}+\left(\frac{\sigma^{2}}{2}\right)\right] \mathrm{T}}{\sigma \sqrt{\mathrm{T}}} \\
\mathrm{d}_{2}=\mathrm{d}_{1}-(\sigma \sqrt{\mathrm{T}})
\end{array}
$$

$\mathrm{T}$ =time to maturity, assuming 365 days per year  
$\mathrm{S}_{0}=$ asset price    
$\mathrm{K}$ =exercise price    
$\mathrm{R}_{\mathrm{f}}^{\mathrm{c}}=$ continuously compounded risk-free rate  
$\sigma=$ volatility of continuously compounded returns on the stock   
$\mathrm{N}\left(\mathrm{d}_{\mathrm{i}}\right)=$ cumulative distribution function for a standardized normal  distribution variable

</div>

</div>

<div class="theory" markdown="1">

## Assumptions used to arrive at Black Scholes Merton Equation

- The option is European and can only be exercised at expiration.  
- No dividends are paid out during the life of the option.  
- Markets are efficient (i.e., market movements cannot be predicted).  
- There are no transaction costs in buying the option.  
- The risk-free rate and volatility of the underlying are known and constant.  
- The returns on the underlying asset are normally distributed.  

</div>

<div class="theory" markdown="1">

## Handling of Dividends

As can be seen from the above 2 simple models, the dividend payments made by stocks are assumed to not cause a major impact on the price of the options. However if we want to take into account the changes in option price, due to dividend payments it can be done in 2 ways.

<div class="subtheory" markdown="1">

### Continuous Dividend Rate is estimated

When continuous Dividend rate is given, In the model we create an adjusted risk free rate by subtracting continuous dividend rate (q) from risk free rate(r) to be used in the calculation of $d_1$ and by extension $d_2$.

</div>

<div class="subtheory" markdown="1">

### Dividend payment details are estimated 

When Dividend Payment details are given we calculate the Present value of all dividend payments and create an adjusted stock price by subtracting PV of dividend payments from Current Stock Price and use this adjusted stock price in calculating $d_1$ and hence $d_2$.

![Dividend](https://cdn.mathpix.com/snip/images/Dbv6coruU0ZiMbWTXug_RnFTfdOFUg3mcz1uVy9H6Gs.original.fullsize.png)

In the created google sheets model of BSM options pricing, I have accounted for dividend effects in pricing of the options as can be seen above.
</div>

</div>

<div class="theory" markdown="1">

## Python Implementation of BSM Model


```python
# Packages Used
import math

#import norm for normal distribution
from scipy.stats import norm 

# Input Variables
print('Enter Risk free rate in decimals, i.e., /100')
r=float(input())

print('Enter Spot Price')
s=float(input())

print('Enter Strike Price')
k=float(input())

print('Enter time till maturity in years')
t=float(input())

print('Enter Annualised Volatility')
v=float(input())

print('Enter 0 for Call Price, 1 for Put Price')
typ=float(input())

```

The above are the inputs that we will be requiring from the user they can be entered in the command line.  

The 5 inputs in the basic BSM models are: 
- Risk Free Rate
- Spot Price
- Strike Price
- Time till exercise
- Volatility - Annualised

The additional 6th input that we will be passing to the function is used to determine if the price that needs to be estimated is that of a Call option / Put Option.  


```python

model_inputs = list([r,s,k,t,v,typ])

# Function to create BSM Price based on model inputs

def BSM_option_price(x):
  # Intermediate Values Calculation
  num = math.log(x[1]/x[2])+x[4]/2)*x[3] 
  den=x[4]*math.sqrt(x[3]) 
  d1=float(num/den)
  d2=float(d1-x[4]*math.sqrt(x[3])) 
  pv_multiplier=math.exp(-1*x[0]*x[3])
  Nd1= float(norm.cdf(d1))
  Nd2= float(norm.cdf(d2))
  NNd1=float(1-Nd1)
  NNd2=float(1-Nd2)

  # Option Price Calculation and Output
  call_option_price = x[1]*Nd1-x[2]*PV_multiplier*Nd2
  put_option_price = x[2]*PV_multiplier*NNd2-x[1]*NNd1 

  if x[5]==0:
    return (call_option_price) 

  if x[5]==1:
    return (put_option_price) 

print('Option price is',  BSM_option_price(model_inputs))

```

We are creating a list variable so that we pass one single variable as input to the function and not six separate variables. Note that the order of inputs needs to be perserved while passing them as input arguments to the function.

The calculation is split into 2 variables called nume & deno for the sake of simplicity and understanding.
Norm.cdf function is used to get the cumulative normal distribution value needed for N(d1) & N(d2).


***Console Output:***

![Console Output](https://cdn.mathpix.com/snip/images/UmNcPyetJesSu3aXyCHmFRwsWUqaDXXkBpfxHJmjkJY.original.fullsize.png)


The same has been implemented in the Google Sheets as well and here’s a link to use the pricing model developed in Google Sheets. 

[Google Sheets Implementation of BSM Options Pricing Model](https://docs.google.com/spreadsheets/d/1qoM3euK7awUCyY07rTmHSuKKsoD3WxgDzVDLDhK4Us8/edit?usp=sharing)

</div>