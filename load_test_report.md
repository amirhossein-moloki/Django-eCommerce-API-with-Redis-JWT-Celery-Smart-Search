# Load Test Report

## Overview

This report documents the results of the load test performed on the e-commerce application. The test was executed using Locust, simulating various user behaviors to identify performance bottlenecks.

## Test Environment

-   **Application Host:** [e.g., Local machine, Staging server]
-   **CPU:** [e.g., 4-core]
-   **Memory:** [e.g., 8GB RAM]
-   **Locust Version:** [e.g., 2.15.1]

## Test Scenarios

-   **User Authentication:** Requesting and verifying OTP.
-   **Product Search:** Searching for products.
-   **Add to Cart:** Adding a product to the shopping cart.
-   **Order Creation:** Placing an order.

## Test Configuration

-   **Number of Users:** [e.g., 100]
-   **Spawn Rate:** [e.g., 10 users/second]
-   **Test Duration:** [e.g., 10 minutes]

## Results

| Request Type        | # Requests | # Fails | Median (ms) | 95%ile (ms) | 99%ile (ms) | Req/s  |
| ------------------- | ---------- | ------- | ----------- | ----------- | ----------- | ------ |
| GET /api/v1/products/ |            |         |             |             |             |        |
| POST /api/v1/cart/add/ |           |         |             |             |             |        |
| POST /api/v1/orders/  |            |         |             |             |             |        |
| POST /auth/request-otp/ |          |         |             |             |             |        |
| POST /auth/verify-otp/  |          |         |             |             |             |        |
| **Total**           |            |         |             |             |             |        |

## Analysis

[Provide a summary of the test results and any notable observations. For example, mention any endpoints with high latency, a high number of failures, or unexpected resource usage.]

### CPU and Memory Usage

-   **CPU Usage:** [e.g., Average 60%, peak 85%]
-   **Memory Usage:** [e.g., Average 1.2GB, peak 1.5GB]

## Recommendations

[Based on the analysis, provide recommendations for performance improvements. For example, suggest optimizing specific database queries, caching frequently accessed data, or scaling up resources.]
