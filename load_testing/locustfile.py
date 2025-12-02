import random
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        """ on_start is called when a Locust start before they start-up """
        self.login()

    def login(self):
        """Login a test user and get a JWT token."""
        user_id = random.randint(0, 99)
        phone_number = f'555555{user_id:04d}'

        response = self.client.post("/auth/token/test/", json={"phone_number": phone_number})
        if response.status_code == 200:
            self.token = response.json().get('access')
        else:
            self.token = None

    @task
    def search_products(self):
        self.client.get("/api/v1/products/?search=test")

    @task
    def add_to_cart_and_order(self):
        """A task that simulates adding a product to the cart and then ordering."""
        if not self.token:
            return

        headers = {'Authorization': f'Bearer {self.token}'}

        # First, get a list of products to choose from
        response = self.client.get("/api/v1/products/", headers=headers)
        products = response.json().get('results', [])
        if not products:
            return

        product_id = random.choice(products)['id']

        # Add the product to the cart
        self.client.post(f"/api/v1/cart/add/{product_id}/", headers=headers)

        # Create an order
        # This is a simplified payload. A real-world scenario might need more data.
        order_payload = {
            "address": "123 Test St",
            "postal_code": "12345"
        }
        self.client.post("/api/v1/orders/", headers=headers, json=order_payload)
