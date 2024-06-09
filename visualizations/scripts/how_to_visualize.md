# How to visualize
## Quick Start
1. Run `process_results.py`
    1. Ensure you specify
        * the path to the directory from where to take results, and
        * the output .pkl file for processed results.
        * If you want to visualize my experiments you need to unzip `experiment_1.zip`.
    2. run using command `poetry run python visualizations/scripts/process_results.py`.
2. Run `prepare_results.ipynb`
    1. Ensure you specify
        * the input .pkl file of processed results, and
        * the output .pkl file.
        * The above two points can be done by setting the booleans
            * `do_test_out`,
            * `do_preliminary_tests`, and 
            * `do_experiment_1`.
    2. run using command `poetry run jupyter notebook`.
3. Run `visualize_exp_1.ipynb` or `visualize_preliminary_tests.ipynb`
    1. Ensure you specify
        * the input .pkl of prepared results, and
        * the output image names.
    2. run using command `poetry run jupyter notebook`.