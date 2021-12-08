# xtract-cli

## Steps for Configuring an Xtract Endpoint
An Xtract endpoint is a thin layer that sits atop a Globus and funcX endpoint. These directions will show how you can configure a Globus endpoint, 
configure a Python (Conda) environment capable of running funcX, and also installing Singularity so that we can run our extractors in containers. 
We assume that you are using a BASH shell on a Linux OS. 

### Step 1. Use a screen session
Having a screen session will enable us to run Globus Endpoints in perpetuity, even when connection to an instance is lost. 

#### To start your screen session
```
screen
```
#### To re-connect to your screen session if disconnected 
```
screen -RD
```

### Step 2. 
