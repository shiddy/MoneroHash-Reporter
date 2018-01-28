# Monerohash-booper

This service exists to send information related to your current monerohash.com mining to you in the form of email or sms.

## Install.

pull the source:

    git clone https://github.com/shiddy/MoneroHash-Reporter.git

It's reccommended that you install this package with a virtual environment:

    pip install virtualenv
    virtualenv venv
    source venv/bin/activate

The python requirements for this are specified within the requirements.txt file.
Testing libraries included within the requirements file.

Installing requirements can be done through pip with the following:

    pip install -r requirements.txt


If you intend to run this program in AWS with lambda it's reccomended that you run the deploy with serverless
  this reuqires and install of node.js and npm which can be found here: https://nodejs.org/en/

  serverless can be installed with the following:
    npm install serverless -g

  and packaging the python libraries can be done with the serverless-python-requirements:
    sls plugin install -n serverless-python-requirements

  I also highly reccommend doing these builds with docker as the libraries pulled by your package manager are unlikey to function on aws lambda. Installing docker is reccommended through the doceker store for the most recent updates:
  https://store.docker.com/search?type=edition&offering=community

  Following this you should create api access for serverless as demonstrated in their documentation:
  https://serverless.com/framework/docs/providers/aws/guide/credentials#creating-aws-access-keys

  and ensure that those keys are accessable within your local box with:
  https://serverless.com/framework/docs/providers/aws/guide/credentials#quick-setup

## Setup

  Once installed, you shouldupdate the example_config.yaml file with your API and personalized information.

  If you want to send yourself and email you should set up a sendgrid account at https://app.sendgrid.com/signup
    * It's reccomended that you whitelabel your account, to prevent auto-spam filtering from your Inbox service provider.
    * It's also reccoemnded that you don't spoof your own inbox account i.e. @gmail for sends

  If you want to send yourself text messages you should set up a twilio account at https://www.twilio.com/try-twilio

  copy the example_config.yaml file to config.yaml:
    cp example_config.yaml config.yaml

  edit the contents of the config.yaml to contain your mining information

## Usage

  This code can be run manually with the following:

    python fetch.py

  If you intend to run this regularly, it can be pushed to AWS lambda and run serverless with the following:

    serverless deploy

  It's reccommended that you run the manual version first to ensure that everything is working as intended.

### NOTE
  Running this in aws labmda requires you to have the agg backend rendering setup to be headless. This requires the MPLBACKEND environment varaible to be set as 'agg'


## Testing

The tests for this package have been written with pytest and pytest-mock and can be invoked with the following:

    pytest -v Testfetch.py

