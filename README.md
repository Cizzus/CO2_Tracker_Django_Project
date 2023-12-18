## Overview

CO2 Tracker is a project designed to monitor and track carbon dioxide emissions. This README provides essential
information for setting up and using the CO2 Tracker application.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contacts](#contacts)

## Installation<a name="installation"></a>

### Prerequisites

Before you begin, ensure that you have the following installed:

- [Python](https://www.python.org/) (version 3.6 or higher)
- [Pip](https://pip.pypa.io/en/stable/installation/)

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Cizzus/CO2_Tracker_Django_Project.git
   ```
2. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   ```
   After successfully venv installation activate your virtual environment
   ```bash
   your_project_direcotry/venv/Scripts/activate.bat
   ```
3. **Install requirements file:**

   Write packages in your virtual environment
   ```bash
   pip install -r requirements.txt
   ```

## Configuration<a name="configuration"></a>

Before running Django project we neeed to make some conifgurations.

### Steps

1. **Delete old migrations:**

   In `co2_tracker_app/migrations` directory delete all old migrations .py files, except `__init__.py` file (this file
   is important to run migrations).

2. **Generate Secret Key:**

   In `co2_tracker_project/settings.py` find `SECRET_KEY` variable and generate your
   own [secret key](https://djecrety.ir/?source=post_page-----53d5939b7e9e--------------------------------).

3. **Add media:**

   In your project base directory add `media` directory and `profile_pics` direcotry in it. In `media\profile_pics`
   directory add `default.png` that will be shown next to the user as the default profile picture.

4. **Create Rapid API Key:**

   This project uses differrent API's from [Rapid API](https://rapidapi.com/hub). You need to register to this site to
   get API key which you will use for all API connections. After you get you API key, you need to subscribe these API's:

    - [Daily atmosphere carbon dioxide concentration](https://rapidapi.com/rene-mdd/api/daily-atmosphere-carbon-dioxide-concentration/)
    - [CarbonFootprint](https://rapidapi.com/carbonandmore-carbonandmore-default/api/carbonfootprint1/pricing)
    - [CarbonSutra](https://rapidapi.com/carbonsutra/api/carbonsutra1/pricing)
    - [Tracker For Carbon Footprint API](https://rapidapi.com/zyla-labs-zyla-labs-default/api/tracker-for-carbon-footprint-api/)
    - [Foodprint](https://rapidapi.com/benarapovic/api/foodprint/)

   P.S. All of these API subscriptions are totally free for minimum of 100 requests. Add you API key
   into `co2_tracker_app\views.py` at the top (not secure) or add it as your environment variable
   called `RAPID_API_KEY`.

5. **Configure SMTP:**

   To enable Django password return we need to configure our main email in `co2_tracker_project\settings.py`.

6. **Make migrations:**

   Now in our command line we activate virtual environment and make migrations. This is done in `manage.py` file
   directory:
   ```bash
   (venv) C:\project_root_directory_path> python manage.py makemigrations
   (venv) C:\project_root_directory_path> python manage.py migrate
   ```

7. **Create superuser:**

   To create admin profile we create super user that can reach, make changes, add records in Django framework project
   database:
   ```bash
   python manage.py createsuperuser
   ```
8. **Run server:**

   Finally, we run our project by calling `runserver` in our terminal:
   ```bash
   (venv) C:\project_root_directory_path> python manage.py runserver
   ```

## Usage<a name="usage"> </a>

This website can register user which will track CO2 emission of every user. User can add his CO2 emission in kg by
adding - travel, food or energy consumption. Inputs by user is sent into API and API returns CO2 emission in kg
that is added into database. For every user there is a week limit taht we can change in `co2_tracker_app\views.py` file,
variable named `week_limit` which is bu default 800 kg. Also we can track CO2 kg emission by user for different
categories mentioned before - travel, food, energy. We can compare CO2 kg emission between user in `Footprint Highscore`
page.

## Contacts<a name="contacts"></a>

If you have any questions or need further assistance, contact Ernestas Čižus at ernestas.cizus@gmail.com.

    
