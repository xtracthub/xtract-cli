# xtract-cli

## Steps for Configuring an Xtract Endpoint
An Xtract endpoint is a thin layer that sits atop a Globus and funcX endpoint. These directions will show how you can configure a Globus endpoint, 
configure a Python (Conda) environment capable of running funcX, and also installing Singularity so that we can run our extractors in containers. 
We assume that you are using a BASH shell on a Linux OS. 

### >> Step 1. Use a screen session
Having a screen session will enable us to run Globus Endpoints in perpetuity, even when connection to an instance is lost. 

#### To start your screen session
```
screen
```
#### To re-connect to your screen session if disconnected 
```
screen -RD
```

### >> Step 2. Configure a Globus Endpoint
Here we will show how to configure a Globus Endpoint entirely from the command line. Most of what is discussed in the following 
can also be found in the Globus Documentation (CITE). 

#### 2.01 Install Globus Endpoint Dependencies
```
sudo apt-get install tk tcllib
sudo apt-get update 
```

#### 2.02 Fetch, Unpack, and Setup the Globus Installer
```
wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
tar xzf globusconnectpersonal-latest.tgz
cd globusconnectperseonal-X.X.X # >>> USE TAB-COMPLETE TO FILL IN CORRECT VERSION NUMBER
./globusconnectpersonal
```
