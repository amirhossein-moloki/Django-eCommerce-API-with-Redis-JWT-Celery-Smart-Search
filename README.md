# Hypex E-commerce API

Welcome to the Hypex E-commerce API, a scalable and feature-rich backend solution built with Django and Django REST Framework.

## Core Features

-   **Clean & Modular Architecture**: Organized into logical Django apps for maintainability.
-   **Complete E-commerce Functionality**: Covers products, carts, orders, payments, coupons, and more.
-   **JWT Authentication**: Secure, token-based authentication powered by `djoser` and `simple_jwt`.
-   **Interactive API Documentation**: Auto-generated, interactive API docs using `drf-spectacular` (OpenAPI 3).
-   **Asynchronous Task Processing**: Uses `Celery` with a `Redis` broker for handling background tasks.
-   **Performance Optimized**: Implements caching with `Redis` and rate limiting.
-   **Containerized with Docker**: Comes with a complete Docker and Docker Compose setup for easy development and deployment.

## Advanced Documentation

For a deeper understanding of the project's design and workflows, please refer to the following documents:

-   **[High-Level Architecture](./docs/ARCHITECTURE.md)**: A diagram and description of the system's architecture.
-   **[Database ERD](./docs/DATABASE.md)**: An Entity-Relationship Diagram of the core database models.
-   **[Order Creation Sequence](./docs/ORDER_SEQUENCE.md)**: A sequence diagram detailing the order creation process.

## Getting Started (Development)

This project is fully containerized. All you need is Docker and Docker Compose.

### Prerequisites

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/m-h-s/E-commerce-api.git
    cd E-commerce-api
    ```

2.  **Create Environment File**
    Copy the example environment file and customize it if needed. The defaults are configured to work with the Docker setup.
    ```bash
    cp .env.example .env
    ```

3.  **Build and Run with Docker Compose**
    This command builds the images and starts all services in detached mode.
    ```bash
    docker-compose up -d --build
    ```

## Usage

-   **API**: `http://localhost:80/api/v1/`
-   **Interactive API Docs (Swagger UI)**: `http://localhost:80/api/v1/docs/`
-   **Celery Monitoring (Flower)**: `http://localhost:5555/`

## Running Tests

To run the test suite, execute the following command:
```bash
docker-compose exec web pytest
```

## How to Debug

-   **View Logs**: Check the logs of a specific service.
    ```bash
    docker-compose logs -f <service_name>  # e.g., web, celery_worker
    ```
-   **Attach to a Running Container**: Access a shell inside a running container for interactive debugging.
    ```bash
    docker-compose exec <service_name> sh # e.g., web
    ```
-   **Use Django's `shell_plus`**: `shell_plus` (from `django-extensions`) is a powerful tool that auto-imports all your models.
    ```bash
    docker-compose exec web python manage.py shell_plus
    ```

## Production Deployment

While the provided `docker-compose.yml` is suitable for development, a production setup requires additional considerations for security, scalability, and observability. Key steps include:

1.  **Secure Configuration**:
    -   Set `DEBUG = False` and `DJANGO_SETTINGS_MODULE = ecommerce_api.settings.prod` in your production `.env` file.
    -   Use a strong, randomly generated `SECRET_KEY`.
    -   Configure `ALLOWED_HOSTS` to your domain.
2.  **Database & Cache**: Use managed services (e.g., AWS RDS, ElastiCache) for your PostgreSQL database and Redis cache for better reliability and scalability.
3.  **Static & Media Files**: Serve static and media files from a cloud storage solution like AWS S3, and use a CDN (e.g., CloudFront) for better performance.
4.  **Container Orchestration**: Use a container orchestrator like Kubernetes (a basic Helm chart is included in the `/helm` directory) or AWS ECS to manage your containers.
5.  **CI/CD**: Implement a CI/CD pipeline to automate testing, building, and deploying your application.

## Project Structure

The project follows a modular architecture, with business logic separated into distinct Django apps.

```
├── account/         # User accounts, profiles, addresses
├── cart/            # Shopping cart logic
├── shop/            # Products, categories, reviews
├── orders/          # Order management and processing
├── payment/         # Payment gateway integration
├── coupons/         # Coupon and discount logic
├── chat/            # Real-time chat functionality
├── sms/             # SMS/OTP services
├── ecommerce_api/   # Core project settings and configuration
│   ├── settings/    # Environment-specific settings (base, local, prod)
│   └── ...
├── docs/            # Project documentation and diagrams
├── helm/            # Kubernetes Helm chart for deployment
├── nginx/           # Nginx configuration
├── docker-compose.yml # Defines development services
├── Dockerfile       # Defines the application's Docker image
└── manage.py        # Django's command-line utility
```
