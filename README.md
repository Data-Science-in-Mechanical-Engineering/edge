# On exploration requirements for learning safety constraints

Source code for the article "On exploration requirements for learning safety constraints" presented at the [3rd L4DC conference](https://l4dc.ethz.ch).

This code was developed in __python 3.7.9__.

## Installation

Clone the repository. Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html) with a Python 3.7.9 interpreter. Then run in the project folder:
```
pip3 install -r requirements.txt
```
This may take some time. After that, run the following command to install the `edge` module:
```
pip3 install -e .
```

## Usage

To reproduce the results in the article, first follow the installation instructions. Then, execute the following commands from the project folder:
```
python experiments/on_policy_hovership/on_policy_hovership.py [CONTROLLER]
```
where `[CONTROLLER]` should be either `affine` or `random`, depending on what results you want to reproduce. Do not `cd` in the `experiments/on_policy_hovership/` folder to execute the script, as this breaks relative paths in the code. Depending on your machine, this command may take some time to complete.
Note that you can further customize parameters by directly editing the file `on_policy_hovership.py`. The main parameters can be changed between lines 314 and 347.

## Results

The previous command will create the directory `./experiments/on_policy_hovership/[CONTROLLER]_[SEED]/`, where `[SEED]` is the random number generator seed. It contains the following:
* `data/`: the training and testing data generated during learning
* `figs/`: the figures that were used to create Figures 3 and 4 in the article
* `logs/`: the logs. In particular, the main parameters are saved here, and the performance of the agent
* `models/`: contains the GPs of the safety measure learned during training with their datasets. The model is checkpointed at the end of each train-test phase
* `samples/`: unused