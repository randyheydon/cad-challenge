Paperless Parts CAD Challenge
=============================

Paperless Parts is a manufacturing intelligence startup, creating algorithms and statistical models for analyzing 3D geometries. We're looking for your help to create algorithms in Python and FreeCAD for identifying ten common design issues with uniform thickness parts that makes them hard or impossible to manufacture using processes like laser cutting, water jetting, and wire EDM.

If you have experience with **Python and FreeCAD**, take a shot at completing this challenge. The first person or company to submit a working solution (before June 1, 2017) will receive a **$400 award**. See details below.

*(In order for us to pay you, it has to be legal for us to do so. Therefore, the award is restricted to a person or entity that can legally receive funds from a US business. If you are unsure, please contact us PRIOR to completing the challenge. You may have to pay taxes on this award; consult your tax professional.)*

Get Email Updates
-----------------

[Subscribe for email updates here!](https://form.jotform.us/71215677192156) We'll let you know when the prize has been awarded, when we're launching the next CAD Challenge, and if anything else changes. Otherwise, check back at this page for updates.

How to Participate
------------------

### Review the design issues you need to detect

The design issues to be detected are listed in this PDF: [http://bit.ly/2pykH8B](http://bit.ly/2pykH8B)

### Clone this repository

`git clone git@github.com:paperlessPARTS/cad-challenge.git`

A `cad-challenge/` folder will be created. Do your work in here.

### Create an algorithm

Create any files, classes and functions you need to complete the challenge. Your solution must be run by calling the `dfm_check` function in `solution.py`. See the code comments for more information. If you introduce dependencies (other than FreeCAD), be sure to list them in `requirements.txt`.

### Test your solution

To test your solution, run the unit tests contained in `test.py`, which will check your algorithm using the test STEP files included in the `step_files/` folder. On Unix/Linux/Mac systems, you can run these tests using the included `test_solution.sh` script. We will evaluate your solution by running these tests in addition to running the algorithm on a "hold out" set of different parts with the same kinds of design issues.

### Submit your solution

Once you have a solution that works, **submit it via Pull Request on Github or by emailing your solution to code@paperlessparts.com**. By accepting an award for your solution, you are granting Paperless Parts, Inc. unlimited and perpetual rights to use and extend your solution commercially. All submissions will be assumed to be licensed under [The Unlicense](http://unlicense.org/UNLICENSE) unless other licensing terms are explicitly provided.

You can also email us questions prior to solving the problem. We will try our best to respond in a timely manner.