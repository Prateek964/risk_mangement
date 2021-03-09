---
layout: default
title: k. Pandas
parent: 2. Python
grand_parent: Primers
nav_order: 11
permalink: /primers/3_python/k_pandas
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

## Pandas

- **_Pandas Dataframes_**: Pandas is a high-level data manipulation tool built on the Numpy package and its key data structure is called the DataFrame. DataFrames allow us to store and manipulate tabular data in rows of observations and columns of variables. There are several ways to create a DataFrame. One way way is to use a dictionary

- **_Indexing Dataframe_**: There are several ways to index a Pandas DataFrame. One of the easiest ways to do this is by using square bracket notation. We also use `loc` and `iloc` to perform just about any data selection operation. `loc` is label-based, which means that we have to specify rows and columns based on their row and column labels. `iloc` is integer index based, so we have to specify rows and columns by their integer index

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
      # Creating a Dataframe by using a dictionary
      dict = {"country": ["Brazil", "Russia", "India", "China", "South Africa"],
       "capital": ["Brasilia", "Moscow", "New Dehli", "Beijing", "Pretoria"],
       "area": [8.516, 17.10, 3.286, 9.597, 1.221],
       "population": [200.4, 143.5, 1252, 1357, 52.98] }

      import pandas as pd
      brics = pd.DataFrame(dict)
      print(brics)

      # Indexing Dataframes
      # Print out country column as Pandas Series
      print(brics['country'])

      # Print out country column as Pandas DataFrame
      print(brics[['country']])

      # Print out brics DataFrame with country and population columns
      print(brics[['country', 'population']])

      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>
    </div>

</div>