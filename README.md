# Apartment Bill Management System

This project is an **Apartment Bill Management System** built using Django, designed to help managers handle various aspects of apartment billing and payments. The system allows for the generation and management of utility bills, tracking of payments, and more. The manager enters the total bills(electricity, elevator, cleaning etc.) for the entrance and the system automatically distributes them equally between the apartments.

## Features

- **User Authentication**: Secure login system with role-based access control (Manager, Owner).
- **Billing Management**: Automated generation of bills for apartments based on total utility usage and maintenance costs for the building entrance.
- **Payment Tracking**: Record and track payments made by apartment owners, including the balance(if any).
- **Monthly Reports**: View and manage bills by month, with easy navigation between different months.
- **Balance Transfer**: Automatically transfer any balance (change) from previous bills to the current month's bill.

## Getting Started

### Prerequisites

- Python 3.11.2+
- Django 5.0.8+
- PostgreSQL (or any other database supported by Django)
- Celery 5.4.0+
- Redis 5.0.8+

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/dinocom33/BuildingBillsManagement.git
   cd BuildingBillsManagement
2. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Setup the Database:**
   Ensure that your database is set up and update the DATABASES settings in your ```.env``` file. A ```.env.sample``` file is provided.
   Run the following commands to apply migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **Create a Superuser:**
   ```bash
   python manage.py createsuperuser
   ```
6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   celery -A BuildingBillsManagement worker --pool=solo -l info
   ```
Now, open your browser and go to http://127.0.0.1:8000/ to access the application.
First you need to create a ```superuser```. With it you create the first user (who will be a manager) and add a ```manager``` group to him.

### Usage
 - **Admin Panel:** Accessible at /admin, where managers can manage users, apartments, and billing information.
 - **Manager Dashboard:** A dedicated interface for managers to generate bills, view and manage payments, and handle various apartment-related operations.
 - **Dashboard:** A dashboard interface for regular users(residents) to see the bills of all apartments from the building entrance to which they belong by months.
 - **My bills:** A dashboard interface for regular users(residents) to see all the bills of his own apartment by month.(to do)
 - **My account:** A dashboard interface for changing user information.(to do)

### Project Structure
 - **accounts/:** Contains user authentication, management and dashboards logic.
 - **building/:** Contains the logic related to buildings, entrances, apartments, bills, and other building-related operations.
 - **pages/:** Common pages(index, about etc.).
 - **templates/:** Contains HTML templates used by the application.
 - **partials/:** Partial templates(like navbar).
 - **static/:** Contains static files (CSS, JavaScript, images).
 - **media/:** (If used) Contains uploaded files and media.
 - **manage.py:** Django's command-line utility for administrative tasks.

### Key Functionality
 - **User Creation:** Managers can create a users(residents).
 - **Building Creation:** Managers can create buildings with number and address.
 - **Apartment Creation:** Managers can create apartments, assignh them to building and entrance and assignh an apartment owner from created users(residents)
 - **Bill Creation:** Managers can create monthly bills for all apartments, including transferring any remaining balance from previous months.
 - **Payment Processing:** Owners can pay their bills, and managers can track payments and update records.
 - **Monthly Navigation:** Easily navigate between different months to view and manage past and current bills.

### License
 - This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgements
 - Thanks to the Django community for providing such an excellent framework.

### Screenshots
 - soon...
