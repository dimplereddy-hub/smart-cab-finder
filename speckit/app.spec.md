# File Specification: app.py

## Purpose

Acts as the main Flask backend application.

## Responsibilities

- Initialize Flask application
- Manage routes
- Handle login authentication
- Calculate route distance
- Generate fare estimates
- Select cheapest cab
- Render templates

## Routes

### /

Displays login page.

Template:
login.html

---

### /login

Method: POST

Inputs:

- username
- password

Validation:

username = admin
password = 1234

Output:

Redirect to /home

---

### /home

Displays ride search page.

Template:

index.html

---

### /compare

Method: POST

Inputs:

- pickup
- drop

Process:

- Validate locations
- Calculate distance
- Calculate travel time
- Generate cab fares
- Identify cheapest cab

Output:

result.html

---

## Data Sources

Location coordinates stored internally.

Supported locations:

- Gachibowli
- Airport
- Hitech City
- Kukatpally
- Secunderabad
- Manikonda

---

## Dependencies

- Flask
- math

---

## Future Enhancements

- Database Integration
- Real Cab APIs
- User Accounts