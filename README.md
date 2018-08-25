# Catalog Application

## About
This project was created as an assignment in the Full Stack Nanodegree program at Udacity.

This project makes use of the python "Flask" web framework to build a basic
cataloging web application. It also uses the SQLAlchemy ORM for database 
support. Bootstrap is used as the CSS, HTML, and basic JS framework.


## Set Up
The linux based virtual machine used in this application was provided by Udcacity.

1. Download and install [Vagrant](https://www.vagrantup.com/)
2. Download and install Oracle's [Virtual Box](https://www.virtualbox.org/)
3. Download this git repository.
4. Download the database dump from [here](https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip).
5. In a terminal, navigate to the repository's directory.
6. Execute `$ vagrant up`
    * The default Udacity configuration file is provided.
7. Execute `$ vagrant ssh` to connect to the VM
8. Navigate to the `/vagrant` directory.

## Execution
To compile the code and start the server, follow the following steps in the VM 
ssh.

1. `cd` into the project repository.
2. Execute: `$ python app.py`
3. Open your webbrowser and navigate to `localhost:8000`

## API
`/api/json`

There is a basic API provided at the endpoint `/api/json`. This route returns a
JSON object containing all categories and their attached items. All database 
items and categories are public via this API.