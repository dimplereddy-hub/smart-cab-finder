# 🚕 Smart Cab Finder

Smart Cab Finder is a Flask-based web application that helps users compare cab fares across multiple ride providers such as Uber, Ola, and Rapido. The platform calculates route distance, estimates travel time, visualizes routes on an interactive map, and recommends the most economical ride option.

---

## 📖 Overview

Finding the cheapest ride often requires checking multiple ride-hailing applications separately. Smart Cab Finder simplifies this process by providing a single platform where users can compare fares and make informed travel decisions.

The application offers:

- Secure login system
- Route-based fare comparison
- Distance and travel time estimation
- Interactive map visualization
- Cheapest ride recommendation
- Modern responsive UI
- Dark/Light theme support

---

## ✨ Features

### 🔐 Authentication

- Login page with validation
- Loading animation during authentication
- Glassmorphism-inspired design

Demo Credentials:

```text
Username: admin
Password: 1234
```

---

### 📍 Route Selection

Supported Locations:

- Gachibowli
- Airport
- Hitech City
- Kukatpally
- Secunderabad
- Manikonda

Users can select:

- Pickup Location
- Destination Location

---

### 🚗 Fare Comparison

Compare ride fares from:

#### Uber
- Uber Go
- Uber Non-AC
- Uber Premium

#### Ola
- Ola Mini
- Ola Auto
- Ola Sedan

#### Rapido
- Rapido Bike
- Rapido Auto
- Rapido Cab

Each ride displays:

- Ride Type
- Estimated Fare
- Waiting Time

---

### 💰 Cheapest Ride Detection

The system automatically:

- Compares all available rides
- Identifies the lowest fare
- Highlights the cheapest option

Badge Display:

```text
Best Value
```

---

### 🗺 Interactive Route Visualization

Built using:

- Leaflet.js
- OpenStreetMap

Features:

- Pickup Marker
- Destination Marker
- Route Path
- Interactive Map Controls

---

### 🌗 Theme Support

Available Themes:

- Dark Mode
- Light Mode

Users can switch themes using the theme toggle button.

---

### 🎨 User Interface

Design Characteristics:

- Apple-inspired layout
- Glassmorphism cards
- Gradient backgrounds
- Hover animations
- Responsive design
- Modern typography

---

## 🏗 Technology Stack

### Backend

- Python
- Flask

### Frontend

- HTML5
- CSS3
- JavaScript

### Mapping

- Leaflet.js
- OpenStreetMap

### Styling

- Custom CSS
- Glassmorphism Effects
- Responsive Grid Layout

---

## 📂 Project Structure

```text
SmartCabFinder/
│
├── app.py
├── README.md
├── SPECKIT.md
├── requirements.txt
│
├── templates/
│   ├── login.html
│   ├── index.html
│   └── result.html
│
├── static/
│   └── style.css
│
└── specs/
    ├── app.spec.md
    ├── login.spec.md
    ├── index.spec.md
    ├── result.spec.md
    └── style.spec.md
```

---

## ⚙ Installation

### Clone Repository

```bash
git clone https://gitlab.com/<username>/smart-cab-finder.git
cd smart-cab-finder
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux / Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install flask
```

Or:

```bash
pip install -r requirements.txt
```

---

## ▶ Running the Application

Start the Flask application:

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🔄 Application Workflow

1. User opens Login Page
2. User enters credentials
3. User is redirected to Home Page
4. User selects pickup location
5. User selects destination
6. User clicks **Find Ride**
7. System calculates route distance
8. System estimates travel duration
9. System generates fares
10. System identifies cheapest ride
11. Results are displayed with route map and fare comparison cards

---

## 📈 Future Enhancements

### Authentication

- User Registration
- Password Recovery
- Session Management

### Fare Services

- Uber API Integration
- Ola API Integration
- Rapido API Integration

### User Features

- Search History
- Favorite Routes
- User Profiles

### Analytics

- Fare Trend Analysis
- Ride Statistics Dashboard
- Historical Fare Tracking

### AI Features

- Fare Prediction
- Traffic-Based Recommendations
- Smart Route Suggestions

---

## 🎯 Learning Outcomes

This project demonstrates:

- Flask Web Development
- Route-Based Calculations
- Interactive Mapping
- Template Rendering
- Frontend UI Design
- Responsive Web Development
- Software Documentation
- Spec-Driven Development

---

## 👨‍💻 Author

**Dimple Reddy**  
Computer Science Engineering Student

---

## 📄 License

This project is developed for educational and academic purposes.

---

## 🙏 Acknowledgements

- Flask Framework
- OpenStreetMap
- Leaflet.js
- Python Community
- Open Source Contributors