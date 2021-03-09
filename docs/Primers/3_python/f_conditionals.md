---
layout: default
title: f. Conditionals
parent: 2. Python
grand_parent: Primers
nav_order: 6
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