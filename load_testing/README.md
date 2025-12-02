# Load Testing

This directory contains the necessary files to run a load test against the application using Locust.

## Prerequisites

-   Docker and Docker Compose
-   Python 3.x
-   `locust` package installed (`pip install locust`)

## Instructions

1.  **Start the application services:**

    Since `docker-compose` is not available in the environment, you will need to start the database and redis services manually. Make sure they are running on `localhost:5432` and `localhost:6379` respectively.

2.  **Create the test users:**

    Before running the load test, you need to create a pool of test users. Run the following command from the root of the repository:

    ```bash
    PYTHONPATH=. python load_testing/create_test_users.py
    ```

3.  **Run the load test:**

    ```bash
    locust -f load_testing/locustfile.py --host http://localhost:8000
    ```

4.  **Open the Locust web interface:**

    Open your web browser and go to `http://localhost:8089`.

5.  **Start the test:**

    -   Enter the number of users to simulate.
    -   Enter the spawn rate (users to add per second).
    -   Click "Start swarming".

6.  **Analyze the results:**

    The Locust web interface will show real-time statistics, including requests per second, response times, and failures.
