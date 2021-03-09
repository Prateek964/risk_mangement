---
layout: default
title: d. Datatypes
parent: 3. Python
grand_parent: Primers
nav_order: 4
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
