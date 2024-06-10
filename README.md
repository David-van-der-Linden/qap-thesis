# QAP Thesis: A Disjunctive Programming Approach to the Quadratic Assignment Problem Using Benders' Decomposition

This repository contains the code for my master thesis on the quadratic assignment problem. 

The quadratic assignment problem was first posed by [Koopmans and Beckmann](10.2307/1907742) in 1957. They presented the problem as a problem of placing $n$ facilities to $n$ locations while minimizing a quadratic function of their flow and distance. Since then, the quadratic assignment problem has gained a lot of attention, with over $75000$ articles published, see [OpenAlex.org](https://openalex.org/works?page=1\&filter=default.search\%3AQuadratic\%20Assignment\%20Problem).

During my thesis together with Matthias Walter, I have developed a method for solving the quadratic assignment problem. At its core, it introduces one new variable per node and combines Disjunctive Programming with Benders' decomposition.

See `docs/report.pdf` for more detail.

## Quick Start
1. If not installed install Gurobi [here](https://www.gurobi.com/downloads/older-versions-gurobi-software/) (recommended version 9.5.0)
2. Set up the QAPLIB data
    1. Download from [here](https://coral.ise.lehigh.edu/data-sets/qaplib/qaplib-problem-instances-and-solutions/)
    2. Unzip the data
    3. Organize data like this:
        * `data/QAPLIB/qapdata`
        * `data/QAPLIB/qapsoln`
3. Specify `my_path` in `src/my_secrets.py`
    * Create `src/my_secrets.py`
    * Add line `my_path = 'C:/example/path/qap-thesis/'`, make sure to end with `/`
    * Using full path is recommended. However,
        * you can use `my_path = './'` when running from the `qap-thesis/` directory, and
        * you can use `my_path = '../'` when running from the `qap-thesis/src/` directory
4. Adjust `main.py` as indicated by comments in `main.py`
5. Run `main.py`
    1. If not installed pip install poetry
    2. While in the `qap-thesis` directory in your terminal: 
        1. Execute  `poetry install`
        2. Execute `poetry run python src/main.py`

## Contact
For questions or bug reports, please contact david.van.der.linden.nl@gmail.com
