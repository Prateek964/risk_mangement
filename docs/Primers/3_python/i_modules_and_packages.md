---
layout: default
title: i. Modules and Packages
parent: 3. Python
grand_parent: Primers
nav_order: 9
permalink: /primers/3_python/i_modules_and_packages
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
