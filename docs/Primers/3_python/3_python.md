---
layout: default
title: 
parent: Primers
has_children: true
nav_order: 3
permalink: /primers/3_python
nav_img: "/assets/images/lesson.svg"
nav_alt: "Study"
previous: "finance"
next: "/foundations_of_risk_management"
---

# Python

![Python](/assets/images/primers/python.svg)

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
## Introduction

Python is an interpreted, high-level and general-purpose programming language. It was created by Guido van Rossum and first released in 1991.

In this unit, we will cover Python and see how we can use it to write programs for building quantitative models such as those for CAPM, Regression Analysis, Options Pricing and VaR Calculation. 

Although Python is not part of FRM I syllabus, we have still incorporated it as an essential component in our course so that students can understand the applications of various topics that we study and how these are used in industry. Here, we present a very simple implementation which may not be an exact representation of how things actually work in Financial firms, but it will give you an idea of the same.

</div>

<div class="theory" markdown="1">

## First Program

To print a string in Python 3, simply write the string in quotes inside the `print()` statement:

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # We are going to print Hello World! This is a comment indicating the same 
        print("Hello World!")
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>

<div class="theory" markdown="1">

## Variables

Python is completely object oriented, and not "statically typed". Therefore, we You need not declare variables or their types before using them. Every variable in Python is an object.

</div>

<div class="theory" markdown="1">

## DataTypes

<div class="subtheory" markdown="1">
### Numbers

Python supports two types of numbers - integers and floating point numbers. (It also supports complex numbers, which are out of scope for this course).

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # Declaring and printing an int
        myint = 7
        print(myint)

        # Declaring and printing a float
        myfloat = 7.0
        print(myfloat)

        # Converting an int to float and printing it
        myfloat = float(7)
        print(myfloat)
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>

<div class="subtheory" markdown="1">

### Strings

Strings are defined either with a single quote or a double quotes.

  <div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # Creating a string using single quotes
        mystring = 'hello'
        print(mystring)

        # Creating a string using double quotes
        mystring = "hello"
        print(mystring)

        # Strings can be concatenated using + operator
        helloworld = "hello" + " " + "world"
        print(helloworld)

        # Length of strings can be found using len() function
        print(len(helloworld))
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>
<div class="subtheory" markdown="1">

### Lists

Lists are very similar to arrays. They can contain any type of variable, and they can contain as many variables as we wish. Lists can also be iterated over in a very simple manner. Here is an example of how to build a list.

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        mylist = []
        mylist.append(1)
        mylist.append(2)
        mylist.append(3)
        print(mylist[0]) # prints 1
        print(mylist[1]) # prints 2
        print(mylist[2]) # prints 3

        # prints out 1,2,3
        for x in mylist:
          print(x)

        # Lists can be concatenated using + operator, similar to strings
        my_numbers = [1,3,5,7]+ [2,4,6,8]
        print(my_numbers)

        # Length of lists can be found using len() function, similar to strings
        print(len(my_numbers))

      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>

<div class="subtheory" markdown="1">

### Dictionaries

A dictionary is a data type similar to lists, but works with keys and values instead of indexes. Each value stored in a dictionary can be accessed using a key, which is any type of object (a string, a number, a list, etc.) instead of using its index to address it.

Dictionaries can be iterated over using the key value pairs. Unlike a list, does not keep the order of the values stored in it.

  <div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # Creating a phonebook dictionary 
        phonebook = {}
        phonebook["John"] = 938477566
        phonebook["Jack"] = 938377264
        phonebook["Jill"] = 947662781
        print(phonebook)

        # Creating the same dictionary using a different syntax
        phonebook = {
        "John" : 938477566,
        "Jack" : 938377264,
        "Jill" : 947662781
        }
        print(phonebook)

        # Iterating over the phonebook dictionary
        for name, number in phonebook.items():
          print("Phone number of %s is %d" % (name, number))

      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>

</div>

<div class="theory" markdown="1">
## Arithmetic Operations

Python achieves arithmetic operations using below operators:

| Opearation         | Operator | Example | Result |
| :----------------- | :------- | ------- | ------ |
| Addition           | +        | 7+5     | 12     |
| Subtraction        | -        | 7-5     | 2      |
| Multiplication     | X        | 7 X 5   | 35     |
| Division           | /        | 7/5     | 1      |
| Modulo (Remainder) | %        | 7%5     | 2      |

</div>
<div class="theory" markdown="1">

## Conditional Statements

Python uses boolean variables to evaluate conditions. The boolean values True and False are returned when an expression is compared or evaluated.

_Note_:

- Variable assignment is done using a single equals operator `=`
- Comparison between two variables is done using the double equals operator `==`
- The "not equals" operator is marked as `!=`

- **_Boolean Operators_**: The `and` and `or` boolean operators allow building complex boolean expressions.

| Opearator | Synatax                       | Results                                              |
| :-------- | :---------------------------- | ---------------------------------------------------- |
| `and`     | expression1 `and` expression2 | True if both expression1 `and` expression2 are true  |
| `or`      | expression1 `or` expression2  | True if either expression1 `or` expression2 are True |

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        x = 42
        print(x == 42) # prints out True
        print(x == 43) # prints out False
        print(x < 45) # prints out True

        # Boolean Opearators
        if x%7 ==0 and x%3==0:
          print(str(x) + " is divisible by 21")

        if str(x)[-1]==0 or str(x)[-1]==5:
          sprint(str(x) + " is divisible by 5")
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>
<div class="theory" markdown="1">
## Loops

<div class="subtheory" markdown="1">
### For Loop

For loops iterate over a given sequence. For loops can iterate over a sequence of numbers using the `range` function

- **_Break statement_**: `break` is used to exit a for loop or a while loop
- **_Continue Statement_**: `continue` is used to skip the current block, and return to the `for` statement

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
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
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>
</div>
<div class="theory" markdown="1">

## Functions

Functions are a convenient way to divide your code into useful blocks, allowing us to order our code, make it more readable, reuse it and save some time. Also functions are a key way to define interfaces so programmers can share their code.

Functions in python are defined using the keyword `def`, followed with the function's name. Functions may also receive arguments (variables passed from the caller to the function).

Functions may return a value using the keyword `return`.

Functions can be called by simply writing the function's name followed by `()`, placing any required arguments within the brackets.

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # Define our 3 functions
        def my_function():
          print("Hello From My Function!")

        def my_function_with_args(username, greeting):
          print("Hello, %s , From My Function!, I wish you %s"%(username, greeting))

        def sum_two_numbers(a, b):
          return a + b

        #rint(a simple greeting)
        my_function()

        # Prints - "Hello, John Doe, From My Function!, I wish you a great year!"
        my_function_with_args("John Doe", "a great year!")

        # After this line x will hold the value 3!
        x = sum_two_numbers(1,2)
      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>

</div>

<div class="theory" markdown="1">

## Modules and Packages

<div class="subtheory" markdown="1">
### Module 

A module is a piece of software that has a specific functionality. Modules in Python are simply Python files with a .py extension. The name of the module will be the name of the file. A Python module can have a set of functions, classes or variables defined and implemented. Modules are imported from other modules using the `import` command. We may also use the `import *` command to import all objects from a specific module. We can provide a custom name to the imported module in our workspace using the `as` keyword.

</div>

---

<div class="subtheory" markdown="1">
### Packages

Packages are namespaces which contain multiple packages and modules themselves.They are simply directories, but with a twist. Each package in Python is a directory which MUST contain a special file called `__init__.py`.

</div>

<div class="exercise">
    <div data-datacamp-exercise data-lang="python" data-height="auto">
      <code data-type="pre-exercise-code"></code>
      <code id= "foo" data-type="sample-code" >
        # import the built-in math module
        import math

        # Import the constant variable pi from math module
        from math import pi

        # Importing all objects from math module
        from math import *

        # Imprtnig math module as mth
        import math as mth

      </code>
      <code data-type="solution"></code>
      <code data-type="sct"></code>
      <div data-type="hint">Just press 'Run'.</div>
    </div>

  </div>
</div>

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
<div class="theory" markdown="1">

## Conclusion

We have discussed some fundamental concepts assocuiate with Python Programming language in this Primer Chapter. These tutorials augmented by some Googling will be enough for us to build quantitative models for various topics covered in the FRM I exam.

</div>

<!-- If Want to add a Copy Program segment
<div id="foo1"  class="code-example" markdown="1">
```js
// Javascript code with syntax highlighting.
var fun = function lang(l) {
  dateformat.i18n = require('./lang/' + l)
  return true;
}

```
<button class="btn" data-clipboard-target="#foo">
  <img src="https://img.icons8.com/nolan/16/copy.png" alt="Copy to Clipboard" /> Copy Program
</button>
</div>
-->
