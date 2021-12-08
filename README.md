# xtract-cli

## Steps for Configuring an Xtract Endpoint
An Xtract endpoint is a thin layer that sits atop a Globus and funcX endpoint. These directions will show how you can configure a Globus endpoint, 
configure a Python (Conda) environment capable of running funcX, and also installing Singularity so that we can run our extractors in containers. 
We assume that you are using a BASH shell on a standard 64-bit, x86 Linux OS. Additional architectures will require slightly different instructions,
so please let us know via git issue if you would be willing to help us write a guide!

### >> Step 1. Use a screen session
Having a screen session will enable us to run Globus Endpoints in perpetuity, even when connection to an instance is lost. 

#### To start your screen session
```
$ screen
```
#### To re-connect to your screen session if disconnected 
```
$ screen -RD
```

### >> Step 2. Configure a Globus Endpoint
Here we will show how to configure a Globus Endpoint entirely from the command line. Most of what is discussed in the following 
can also be found in the Globus Documentation (CITE). If you do not already have a Globus account, you should first go to Globus.org and create one. 

#### 2.01 Install Globus Endpoint Dependencies
```
$ sudo apt-get install tk tcllib
$ sudo apt-get update 
```

#### 2.02 Fetch, Unpack, and Setup the Globus Installer
```
$ wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
$ tar xzf globusconnectpersonal-latest.tgz
$ cd globusconnectperseonal-X.X.X # >>> USE TAB-COMPLETE TO FILL IN CORRECT VERSION NUMBER
$ ./globusconnectpersonal  
# >>> You will run through a Globus Authentication and endpoint setup from here. You can name it anything you'd like!
```

#### 2.03 Confirm Globus Endpoint Running
To confirm that your Globus Endpoint is functional, login at globus.org, click 'Endpoints > Administered By You' and confirm that the endpoint
you created and named in the last step is there with status 'ready'. If so, you've successfully configured your Globus endpoint! 

### >> Step 3. Install a Virtual Environment
We highly recommend installing a virtual environment to run funcX on your machine without interfering with your system's Python environment. 
In this walkthrough we will install miniconda-3 using only the command line. Feel free to read more [on their website](https://docs.conda.io/en/latest/index.html). 

#### 3.01 Install miniconda3
```
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
$ sudo chmod +x Miniconda3-latest-Linux-x86_64.sh
$ ./Miniconda3-latest-Linux-x86_64.sh
>> follow the instructions to install miniconda3 in the default location. 
>> exit ssh instance. SSH back into it! (this will automatically source the relevant BASH files to recognize the conda command
```
To confirm that miniconda3 is properly installed, please confirm by typing `conda`. If you see `conda: command not found`, try running the command in a new shell. 

#### 3.02 Create an environment
Here we will create a Python3.8 environment into which we can install funcX. I will name mine `q3_tests`, but feel free to name it whatever you want

```
$ conda create -n q3_tests python=3.8  # >>> click 'yes' to all options, and install in default directory. 
$ conda activate q3_tests
```
