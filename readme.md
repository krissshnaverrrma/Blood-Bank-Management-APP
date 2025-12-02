# 🩸 LifeSaver: Blood Management System

A web application built using Python Flask to manage blood donation records, inventory, and transaction history for a blood bank.

---

## 🌟 Features

* **User Authentication:** Secure registration, login, logout, and password recovery.
* **Donor Management:** Record donor information and track last donation dates.
* **Blood Stock Tracking:** Real-time inventory of different blood groups (A+, O-, etc.).
* **Transaction Processing:** Issue blood units, calculate costs, and record payments (UTR).
* **Payment Integration:** QR code generation for streamlined payment collection.
* **Data Export:** Export transaction history to CSV format.

---

## 🚀 Setup and Run Locally

These instructions will get a copy of the project running on your local machine for development and testing.

### Prerequisites

You need **Python 3.10+** and `pip` installed.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/krissshnaverrrma/Blood-Bank-Management-APP](https://github.com/krissshnaverrrma/Blood-Bank-Management-APP)
    cd Blood-Management-APP
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # On Windows PowerShell/CMD
    # source venv/bin/activate # On Linux/macOS
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

You must create a file named **`.env`** in the project root to store sensitive credentials.

| Variable | Description |
| :--- | :--- |
| `SECRET_KEY` | Long, random string for session security. |
| `MAIL_USERNAME` | Your email address (for sending notifications). |
| `MAIL_PASSWORD` | Your **Gmail App Password** (if using Gmail). |
| `SQLALCHEMY_DATABASE_URI` | Path to the SQLite file (e.g., `sqlite:///instance/bloodbank.db`). |
| `UPI_ID` | Your UPI ID for payment QR code generation. |

### Running the Application

1.  **Set Flask Environment Variable:**
    ```bash
    $env:FLASK_APP = "app"  # For PowerShell
    # export FLASK_APP=app  # For Linux/macOS
    ```

2.  **Create Database Tables:**
    * **CRITICAL STEP:** If you encounter a database connection error (`unable to open database file`), you must ensure your project is **not** in a OneDrive/cloud-synced folder, or you must update the URI in your code to a safe local path (e.g., `sqlite:////C:/temp/bloodbank.db`).
    * The tables will be created when you run the application:
    
3.  **Start the Server:**
    ```bash
    flask run --debug
    ```
    The application will be accessible at `http://127.0.0.1:5000`.

---

## ⚙️ Deployment

For production deployment, you must use a WSGI server like Gunicorn and a persistent cloud database (e.g., PostgreSQL).

**Procfile Content:**
```text
web: gunicorn app:app