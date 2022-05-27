<div align="center">

# VCMR: Video-Conditioned Music Representations
  
</div>

This repository is the official implementation of the project.

## Installation

Clone the repository and install the dependencies. We recommend using a conda environment with Python 3.9+.
```
git clone https://github.com/klean2050/VCMR
cd VCMR 
pip install -r requirements.txt
```

You will also need to install the ``libsndfile`` library:
```
conda install -c conda-forge libsndfile
```

## Project Structure

```
VCMR/
├─ config/              # configuration files for each train session
├─ tests/               # sample scripts to test functionalities
├─ vcmr/                # main project directory
│  ├─ loaders/             # pytorch dataset classes
│  ├─ models/              # backbone neural network models
│  ├─ scripts/             # preprocess, training and evaluation
│  ├─ trainers/            # lightning classes for each train session
│  ├─ utils/               # miscellaneous scripts and methods
├─ .gitignore           # ignore data/ and runs/ folders
├─ export.py            # script to export model to ONNX
├─ LICENSE              # MIT License
├─ main.py              # driver script to run
├─ README.md            # project introduction and description
├─ requirements.txt     # required packages
```

## Getting the Data

VCMR is trained on a large-scaled dataset of 4857 music video clips downloaded from YouTube.
