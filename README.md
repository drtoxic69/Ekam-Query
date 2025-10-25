# Ekam Query Engine 

A full-stack application that allows users to ingest documents and query both structured (SQL database) and unstructured (documents) data using natural language. Built with FastAPI, React, and local AI models.

---

##  Features

* **Dynamic Schema Discovery:** Automatically connects to and analyzes the structure (tables, columns, relationships) of a connected PostgreSQL database.
  
* **Document Ingestion:** Supports uploading PDF, DOCX, and TXT files. [cite: 83, 84, 144] [cite_start]Extracts text, performs intelligent chunking, generates embeddings locally, and stores them in a persistent vector database (ChromaDB).
* **Natural Language Query:** Accepts plain English queries via a web interface.
* **Hybrid Query Processing:**
    * **Classification:** Uses rules and a local transformer model to classify queries as SQL-focused, document-focused, or hybrid.
    * **Text-to-SQL:** Generates SQL queries using a local T5 model based on the user's query and the discovered database schema.
    * **Document Q&A:** Retrieves relevant document chunks using vector similarity search and extracts specific answers using a local QA model.
* **Caching:** Implements basic TTL caching for query results to improve performance.
* **Web Interface:** A React frontend providing UI for document upload and querying.

---

## Tech Stack

* **Backend:** Python 3.12+, FastAPI, SQLAlchemy (with asyncpg), Pydantic, Transformers, Sentence-Transformers, ChromaDB, `uv`
* **Frontend:** React, Vite, Axios, CSS Modules
* **Database:** PostgreSQL
* **Local Models:**
    * Text-to-SQL: `cssupport/t5-small-awesome-text-to-sql` (or similar T5)
    * Classification: `facebook/bart-large-mnli` (or similar zero-shot)
    * Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (via SentenceTransformers)
    * Question Answering: `distilbert-base-cased-distilled-squad` (or similar QA)

---

## Prerequisites

* **Python:** Version 3.12 recommended (due to package compatibility).
* **`uv`:** Python package manager (`pip install uv`).
* **Node.js & npm (or yarn):** For the frontend (LTS version recommended).
* **PostgreSQL:** A running instance of PostgreSQL server.

---

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd ekam-query
    ```

2.  **Backend Setup:**
    * Navigate to the project root.
    * Create and activate a Python 3.12 virtual environment using `uv`:
        ```bash
        # Create venv (if Python 3.12 is default or findable)
        uv venv
        # Or specify Python 3.12 if needed and installed
        # uv venv --python 3.12
        source .venv/bin/activate # Or `.venv\Scripts\activate` on Windows
        ```
    * Install backend dependencies:
        ```bash
        uv sync
        ```

3.  **Frontend Setup:**
    * Navigate to the frontend directory:
        ```bash
        cd frontend
        ```
    * Install frontend dependencies:
        ```bash
        npm install
        ```
    * Go back to the project root directory:
        ```bash
        cd ..
        ```

4.  **Database Setup:**
    * Access your PostgreSQL instance using `psql` (you might need `-U your_postgres_user`).
    * Create a user and database for the application (replace placeholders):
        ```sql
        CREATE ROLE your_app_user WITH LOGIN PASSWORD 'your_app_password';
        CREATE DATABASE ekam_db OWNER your_app_user;
        GRANT ALL PRIVILEGES ON DATABASE ekam_db TO your_app_user;
        \q
        ```
    * *(Optional but Recommended)* Connect to the new database (`psql -U your_app_user -d ekam_db`) and create the sample tables if you want to test Text-to-SQL immediately:
        ```sql
        CREATE TABLE departments (
          department_id SERIAL PRIMARY KEY,
          department_name VARCHAR(100) UNIQUE NOT NULL,
          manager_id INTEGER -- Optional
        );

        CREATE TABLE employees (
          employee_id SERIAL PRIMARY KEY,
          first_name VARCHAR(50) NOT NULL,
          last_name VARCHAR(50) NOT NULL,
          email VARCHAR(100) UNIQUE NOT NULL,
          phone_number VARCHAR(20),
          hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
          job_title VARCHAR(50),
          salary NUMERIC(10, 2) CHECK (salary >= 0),
          department_id INTEGER REFERENCES departments(department_id)
        );
        -- Insert sample data if needed
        INSERT INTO departments (department_name) VALUES ('Engineering'), ('Sales');
        INSERT INTO employees (first_name, last_name, email, department_id) VALUES ('Alice', 'Smith', 'alice@ekam.com', 1);
        ```

5.  **Environment Variables:**
    * Create a file named `.env` in the **project root directory**.
    * Add the following variables, replacing placeholders with your actual database credentials:
        ```env
        # --- Database Connection for Backend ---
        DATABASE_URL=postgresql+asyncpg://your_app_user:your_app_password@localhost:5432/ekam_db
        DATABASE_ECHO=false # Set to true for verbose SQL logs

        # --- Other Backend Settings (Optional Overrides) ---
        # CACHE_TTL_SECONDS=300
        # EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
        ```

---

## Running the Application

1.  **Start the Backend Server:**
    * Make sure your `uv` virtual environment is activated (`source .venv/bin/activate`).
    * Run from the **project root directory**:
        ```bash
        uv run uvicorn backend.main:app --reload
        ```
    * Wait for the server to start. It will take some time initially to download and load the ML models. You should see logs indicating the models are loaded and the server is running on `http://127.0.0.1:8000`.

2.  **Start the Frontend Server:**
    * Open a **new terminal window/tab**.
    * Navigate to the `frontend` directory:
        ```bash
        cd frontend
        ```
    * Start the Vite development server:
        ```bash
        npm run dev
        ```
    * The frontend will typically be available at `http://localhost:5173`.

---

## Usage

1.  Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2.  Use the "Ingest Documents" panel to upload PDF, DOCX, or TXT files. Wait for the success message.
3.  Use the "Submit Query" panel to ask natural language questions about your database (if you created tables/data) or the ingested documents.
4.  View the results displayed below the query panel.
