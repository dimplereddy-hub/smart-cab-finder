# 🚕 Smart Cab Finder - Project Specification

## Project Information

### Project Name
Smart Cab Finder

### Project Type
Web Application

### Domain
Transportation / Fare Comparison

### Architecture
Client-Server Web Application

### Development Approach
Spec-Driven Development (SpecKit)

---

# 1. Project Overview

Smart Cab Finder is a web-based cab fare comparison platform that allows users to compare fares from multiple ride providers including Uber, Ola, and Rapido.

The platform enables users to:

- Login securely
- Select pickup and destination locations
- Calculate route distance
- Estimate travel duration
- Compare cab fares
- View routes on an interactive map
- Identify the cheapest ride option

The objective is to eliminate the need to manually compare prices across multiple ride-hailing applications.

---

# 2. Problem Statement

Users often switch between multiple cab booking applications to compare prices before booking a ride.

This process is:

- Time-consuming
- Inconvenient
- Inefficient

Smart Cab Finder provides a centralized solution for comparing ride fares and selecting the best option.

---

# 3. Objectives

### Primary Objectives

- Compare cab fares from multiple providers
- Calculate route distance
- Estimate travel duration
- Display route visually
- Highlight the cheapest ride

### Secondary Objectives

- Deliver a premium user experience
- Support responsive layouts
- Provide theme customization
- Demonstrate Flask web development concepts

---

# 4. Functional Requirements

## FR-01 User Login

Users shall be able to authenticate using:

- Username
- Password

Current Demo Credentials:

Username: admin

Password: 1234

System shall validate credentials before granting access.

---

## FR-02 Location Selection

Users shall be able to select:

- Pickup Location
- Destination Location

Supported Locations:

- Gachibowli
- Airport
- Hitech City
- Kukatpally
- Secunderabad
- Manikonda

System shall reject invalid locations.

---

## FR-03 Distance Calculation

System shall:

- Retrieve coordinates
- Calculate route distance

Formula:

Haversine Distance Formula

Output:

Distance in kilometers

---

## FR-04 Travel Time Estimation

System shall estimate trip duration.

Formula:

Travel Time = Distance × 3

Output:

Travel duration in minutes

---

## FR-05 Fare Generation

System shall generate estimated fares for:

### Uber

- Uber Go
- Uber Non-AC
- Uber Premium

### Ola

- Ola Mini
- Ola Auto
- Ola Sedan

### Rapido

- Rapido Bike
- Rapido Auto
- Rapido Cab

Each fare shall include:

- Ride Type
- Estimated Fare
- Waiting Time

---

## FR-06 Cheapest Ride Detection

System shall:

- Compare all available fares
- Identify lowest fare

Output:

Best Value Badge

---

## FR-07 Route Visualization

System shall display:

- Pickup Marker
- Destination Marker
- Route Polyline

Technology:

- Leaflet.js
- OpenStreetMap

---

## FR-08 Theme Toggle

System shall support:

### Dark Theme

Default theme.

### Light Theme

Optional theme.

User can switch between themes.

---

# 5. Non-Functional Requirements

## Performance

- Page load under 3 seconds
- Responsive interactions

## Usability

- Simple navigation
- Clear UI hierarchy
- Minimal user actions

## Compatibility

Supported Browsers:

- Chrome
- Edge
- Firefox

## Maintainability

- Modular code structure
- Separated templates and styles

---

# 6. Technology Stack

## Backend

Python

Framework:

Flask

Responsibilities:

- Route handling
- Authentication
- Distance calculation
- Fare generation
- Template rendering

---

## Frontend

HTML5

CSS3

JavaScript

Responsibilities:

- User Interface
- Form Handling
- Theme Switching
- Dynamic Rendering

---

## Mapping

Leaflet.js

Map Provider:

OpenStreetMap

---

# 7. File Specifications

## app.py

Purpose:

Main backend application.

Responsibilities:

- Configure Flask
- Manage routes
- Authenticate users
- Calculate distances
- Generate fare data
- Render templates

Routes:

- /
- /login
- /home
- /compare

---

## login.html

Purpose:

Authentication interface.

Features:

- Username field
- Password field
- Login button
- Animated loader
- Glassmorphism design

---

## index.html

Purpose:

Route search interface.

Features:

- Pickup selection
- Destination selection
- Location suggestions
- Search submission

---

## result.html

Purpose:

Display comparison results.

Features:

- Route summary
- Interactive map
- Fare comparison cards
- Cheapest ride highlighting
- Theme switching

---

## style.css

Purpose:

Global styling system.

Features:

- Dark mode
- Light mode
- Glassmorphism effects
- Responsive grid
- Card animations
- Brand-specific ride cards

---

# 8. UI Design Specification

Design Language:

Apple-Inspired Interface

Visual Features:

- Glassmorphism
- Blur Effects
- Glow Backgrounds
- Smooth Animations
- Rounded Corners
- Responsive Layout

Color Palette:

Dark Mode

Background:
#0f172a

Text:
#ffffff

Light Mode

Background:
#f5f7fa

Text:
#111111

---

# 9. Application Workflow

Step 1

User opens Login Page

↓

Step 2

User enters credentials

↓

Step 3

System validates login

↓

Step 4

User accesses Home Page

↓

Step 5

User selects pickup location

↓

Step 6

User selects destination

↓

Step 7

System calculates distance

↓

Step 8

System generates fare estimates

↓

Step 9

System identifies cheapest ride

↓

Step 10

System displays route and comparison results

---

# 10. Project Structure

SmartCabFinder/

├── app.py

├── README.md

├── SPECKIT.md

├── templates/
│   ├── login.html
│   ├── index.html
│   └── result.html

├── static/
│   └── style.css

└── requirements.txt

---

# 11. Future Enhancements

Authentication

- User Registration
- Password Recovery
- Session Management

Fare Services

- Uber API Integration
- Ola API Integration
- Rapido API Integration

User Features

- Search History
- Saved Routes
- User Profiles

Analytics

- Fare Trends
- Price Prediction
- Ride Recommendations

AI Features

- Dynamic Fare Prediction
- Traffic Analysis
- Smart Suggestions

---

# 12. Success Criteria

The project shall be considered successful if:

✓ Users can login

✓ Users can search routes

✓ Distance is calculated correctly

✓ Travel time is estimated

✓ Cab fares are generated

✓ Cheapest ride is highlighted

✓ Route map is displayed

✓ Theme switching works

✓ Application is responsive

✓ UI provides a modern user experience