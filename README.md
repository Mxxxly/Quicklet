# Quicklet
QuickLet is a short-let and apartment booking platform built with Flask, featuring Admin, User and Agent dashboards, Google OAuth login, PayStack Api integration, and advanced search and filtering for verified listings.

## Key Features

### User Features
- Search and filter apartments by location, category, state, and LGA
- View apartment details and photos
- Book apartments and track booking status
- Google OAuth and email/password authentication
- Responsive UI for mobile and desktop

### Agent Features
- Create, edit, and manage apartment listings
- Upload apartment images
- View bookings related to their properties
- Agent dashboard for listing management

### Admin Features
- Admin dashboard with full platform control
- Delete or manage users, agents, and apartments
- Monitor platform activity and bookings

## 💻 Tech Stack
- Backend: Flask (Python 3.11)
- Database: MySQL
- Frontend: HTML, CSS, Bootstrap 5, Jinja2
- Authentication: Google OAuth2, JWT (JSON Web Tokens), secure password hashing
- Deployment: PythonAnywhere


### Installation
```bash
git clone https://github.com/YOUR_USERNAME/quicklet.git
cd quicklet
pip install -r requirements.txt
flask run


## 🔐 Security & Authentication

- Role-based authentication for **users, agents, and admins**
- **JWT (JSON Web Tokens)** used for secure API access
- Session-based authentication for web interactions
- Google OAuth2 integration
- Password hashing using industry best practices
