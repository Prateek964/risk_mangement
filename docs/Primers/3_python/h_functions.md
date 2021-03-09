---
layout: default
title: h. Functions
parent: 2. Python
grand_parent: Primers
nav_order: 8
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