# Train Station API

A RESTful API built with Django REST Framework (DRF) for managing train station operations, routes, journeys, crews, and ticket reservations.

## Features

* **Authentication & Authorization**: Token-based authentication with role-based access control (Admin vs. User).
* **Train & Station Management**: Models and endpoints for managing Stations, Routes, Trains, Train Types, and Crews.
* **Journey Scheduling**: View and manage train journeys with custom query filtering.
* **Order & Ticket Reservations**: Book tickets for journeys with automated validation.
* **Interactive API Documentation**: Fully documented endpoints with Swagger UI powered by `drf-spectacular`.
* **Database Support**: Configured for PostgreSQL with local fallbacks.

---

## Tech Stack

* **Language**: Python
* **Framework**: Django, Django REST Framework
* **Database**: PostgreSQL (SQLite for local development)
* **Documentation**: `drf-spectacular` (OpenAPI / Swagger UI)
* **Containerization**: Docker & Docker Compose

---

### Installation & Setup

1. **Clone the repository:**

* **git clone https://github.com/chizenkosofia-creator/API_TrainStation.git**
* **cd API_TrainStation**
* **python -m venv .venv**
* **.venv\Scripts\activate**
* **pip install -r requirements.txt**

* **set POSTGRES_HOST=<your db hostname>**
* **set POSTGRES_DB=<your db name>**
* **set POSTGRES_USER=<your db username>**
* **set POSTGRES_PASSWORD=<your db user password>**
* **set POSTGRES_PORT=5432**
* **set SECRET_KEY=<your secret key>**

* **python manage.py migrate**
* **python manage.py runserver**