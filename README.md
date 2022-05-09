# BB Product / Popuplation
BB Product and Population is used for export and update data from CSV file to database and vice versa

I have already deployed with this link.
http://52.207.30.25:8000/login/

If DNS finished, you also can see here.
https://dbassesment.com/login

## Technology

[Script]
- Python (Django)
- Javascript (ajax)
- Html (Bootstrap)

[Database]
- MySQL

[Cloud hosting]
- AWS (EC2, Route53, RDS)

## Installation

I recommend to create venv.
- Create a project directory
- Change into the project directory
- Run venv and stay activate
```bash
python3 -m venv <name_of_virtualenv>
source <name_of_virtualenv>/bin/activate
```

execute requirements.txt
```bash
pip3 install -r requirements.txt 
```
## Migrations
Use migrate command to create database tables using 
```bash
python3 manage.py migrate
```
## Create database manager
This application has two different database (bb_product and population table).
To create database manager, you should create a db manager following below.
```bash
$ python3 manage.py createsuperuser

Username: [input user name]
0 for Super Admin User.
1 for BB Product User.
2 for Population User.
Enter your selection: [0 or 1 or 2]
Password: [input password]
```
## Run Project
Run the server on any port you want by default it can access using below
```bash
python3 manage.py runserver
```
## Usage
Login to the system with
```bash
http://127.0.0.1:8000/login/
```
