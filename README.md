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

#### 2.01 -- Install Globus Endpoint Dependencies
```
$ sudo apt-get update
$ sudo apt-get install tk tcllib
$ sudo apt-get update 
```

#### 2.02 -- Fetch, Unpack, and Setup the Globus Installer
```
$ wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
$ tar xzf globusconnectpersonal-latest.tgz
$ cd globusconnectperseonal-X.X.X # >>> USE TAB-COMPLETE TO FILL IN CORRECT VERSION NUMBER
$ ./globusconnectpersonal
$ ./globusconnectpersonal -start &  # the '&' starts it in terminal (non-GUI) mode. 
# >>> You will run through a Globus Authentication and endpoint setup from here. You can name it anything you'd like!
```

#### 2.03 -- Confirm Globus Endpoint Running
To confirm that your Globus Endpoint is functional, login at globus.org, click 'Endpoints > Administered By You' and confirm that the endpoint
you created and named in the last step is there with status 'ready'. If so, you've successfully configured your Globus endpoint! 

### >> Step 3. Install a Virtual Environment
We highly recommend installing a virtual environment to run funcX on your machine without interfering with your system's Python environment. 
In this walkthrough we will install miniconda-3 using only the command line. Feel free to read more [on their website](https://docs.conda.io/en/latest/index.html). 

#### 3.01 -- Install miniconda3
```
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
$ sudo chmod +x Miniconda3-latest-Linux-x86_64.sh
$ ./Miniconda3-latest-Linux-x86_64.sh
>> follow the instructions to install miniconda3 in the default location. 
>> exit ssh instance. SSH back into it! (this will automatically source the relevant BASH files to recognize the conda command
```
To confirm that miniconda3 is properly installed, please confirm by typing `conda`. If you see `conda: command not found`, try running the command in a new shell. 

#### 3.02 -- Create an environment
Here we will create a Python3.8 environment into which we can install funcX. I will name mine `q3_tests`, but feel free to name it whatever you want

```
$ conda create -n q3_tests python=3.8  # >>> click 'yes' to all options, and install in default directory. 
$ conda activate q3_tests
```

### >>> Step 4. Install Singularity
Singularity is the compute fabric used by Xtract (and funcX) for running extractors on the endpoint. In the following, 
we install Singularity 3.8. For this, I highly recommend using the singularity documentation. 

#### 4.01 -- Confirm Singularity installed
```
$ singularity --version
```
You should see Singularity 3.8.x appear. If you see `singularity: command not found`, you should try restarting your shell OR 
attempt to reinstall [from these instructions](https://sylabs.io/guides/3.8/admin-guide/installation.html#installation-on-linux).

### >>> Step 5. Install and configure funcX
From inside of your conda environment, we are going to install and configure funcX! To accomplish this, we simply run: 
```
$ pip install funcx funcx_endpoint
```
#### Step 5.01 -- Configure the funcX endpoint
```
$ cd ~/.funcx
$ funcx-endpoint configure q3_tests
$ cd ~/q3_tests
```
Next, we want to copy the configuration into `~/.funcx/q3_tests/config.py`. At this point, I will defer you to [the funcX documentation](https://funcx.readthedocs.io/en/latest/endpoints.html?highlight=containers#container-behaviors-and-routing) to figure out what
most lines in this configuration file do.
```
from funcx_endpoint.endpoint.utils.config import Config
from funcx_endpoint.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from funcx_endpoint.strategies import SimpleStrategy

config = Config(
        executors=[HighThroughputExecutor(
        scheduler_mode="soft",
        worker_mode="singularity_reuse",
        container_type="singularity",
        max_workers_per_node=2,
        strategy=SimpleStrategy(max_idletime=1799),
        container_cmd_options="-H /home/tskluzac",
        provider=LocalProvider(
        init_blocks=1,
        worker_init='conda q3_tests',
        min_blocks=0,
        max_blocks=1,
        ),
        )],
        funcx_service_address='https://api2.funcx.org/v2'
        )
```
Now we will start our funcX endpoint, and confirm that it is working. 
```
$ funcx-endpoint start q3_tests
$ funcx-endpoint list
```
Now you should see a list containing your named endpoint, the status `active`, and a funcX endpoint ID. 

Now you have all of the prerequisites installed to your Linux machine to use Xtract! 
