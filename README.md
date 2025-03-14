# ucu.motions.search
## Set Up
1. Download or clone repository onto your device.
2. In the console navigate to the project directory.
3. (Optional) Create and activate a virtual environment.
   Use commands:
   python -m venv env
   env\Scripts\activate
5. Install required packages:
   pip install -r requirements.txt
7. Once all packages are installed, activate localhost:
   python .\flask_app.py
9. Once message "Running on http://127.0.0.1:5000" is printed to the console, go to link http://127.0.0.1:5000
10. Login using:
    Username: Admin
    Password: password
11. Go to "Register User" and create a new user with a strong password.
12. Open "Motions.db" (may require installing DB Browser for SQLite) go to the user table and change the admin column of this new user from 0 to 1.
13. Delete "Admin" user.
    **WARNING! Not deleting the default Admin user may allow others to access the website with adming privileges using the default Admin profile**
## How to use
- Only admins can register new users or use the "Survey" or "Scrape Motions" page.
- All new users are set as not admins by default. You have to change Admin status manually in the database if you want to change admin privileges.
- The "Survey" page is very similar to the "Submit Relevant" button on the "Home" page but instead the searches are created automatically using splits from the 2023-2024 session as the search query and limiting results to any other session.
- The "Scrape Motions" page allows admins to extract motions from the UCU website. Enter the start and end ID (they can be the same) of pages you would like to search. The ID should match the number in the URL link for that motion.

![URL for motion on UCU website](UCU_motion_URL.png)
- For details on how to use "Home" page see the "Help" page.
## What does it do?
This website allows you to extract motions from the UCU website and to search them using a varitiy of search methods.
