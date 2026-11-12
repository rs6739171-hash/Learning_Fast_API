import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from passlib.context import CryptContext

import app.main
from app.api.dependencies import get_product_service, get_seller_service, get_session
from app.api.schema.schemas_fields import ProductStatus, ProductRead
from app.database.models import Product, Seller
from app.api.schema.product import SellerCreate
from app.utils import generate_access_token, decode_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class MockProductService:
    def __init__(self):
        self.products = {}
        self.counter = 1

    async def get(self, id: int):
        return self.products.get(id)

    async def add(self, product_create):
        prod = Product(
            id=self.counter,
            name=product_create.name,
            price=product_create.price,
            stock=product_create.stock,
            status=ProductStatus.active,
            warranty_until=datetime.now(timezone.utc) + timedelta(days=365),
        )
        self.products[self.counter] = prod
        self.counter += 1
        return prod

    async def update(self, id: int, product_update: dict):
        prod = self.products.get(id)
        if not prod:
            return None
        for k, v in product_update.items():
            setattr(prod, k, v)
        return prod

    async def delete(self, id: int) -> bool:
        if id in self.products:
            del self.products[id]
            return True
        return False


class MockSellerService:
    def __init__(self):
        self.sellers = {}
        self.counter = 1

    async def get(self, val):
        if isinstance(val, int):
            return self.sellers.get(val)
        if isinstance(val, str):
            for s in self.sellers.values():
                if s.email == val:
                    return s
        return None

    async def add(self, credentials: SellerCreate):
        seller = Seller(
            id=self.counter,
            name=credentials.name,
            email=credentials.email,
            password_hash=pwd_context.hash(credentials.password),
        )
        self.sellers[self.counter] = seller
        self.counter += 1
        return seller

    async def login(self, email: str, password: str) -> str:
        seller = None
        for s in self.sellers.values():
            if s.email == email:
                seller = s
                break
        if seller is None or not pwd_context.verify(password, seller.password_hash):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Email is not correct")

        return generate_access_token({"user": {"id": seller.id, "email": seller.email}})


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Disable lifespan database connection during testing
        app.main.app.router.lifespan_context = None

        cls.mock_product_service = MockProductService()
        cls.mock_seller_service = MockSellerService()
        cls.blacklist = set()

        # Wire dependency overrides
        app.main.app.dependency_overrides[get_product_service] = lambda: cls.mock_product_service
        app.main.app.dependency_overrides[get_seller_service] = lambda: cls.mock_seller_service

        cls.client = TestClient(app.main.app)

        # Patch redis blacklist functions with in-memory set
        async def mock_add_blacklist(jti: str):
            cls.blacklist.add(jti)

        async def mock_is_blacklisted(jti: str) -> bool:
            return jti in cls.blacklist

        cls.patch_add = patch("app.api.routers.sellers.add_jti_to_blacklist", side_effect=mock_add_blacklist)
        cls.patch_is = patch("app.api.dependencies.is_jti_blacklisted", side_effect=mock_is_blacklisted)
        cls.patch_add.start()
        cls.patch_is.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch_add.stop()
        cls.patch_is.stop()
        app.main.app.dependency_overrides.clear()

    # ==================== SELLER ENDPOINTS ====================

    def test_01_seller_signup(self):
        payload = {
            "name": "Alice Developer",
            "email": "alice@test.com",
            "password": "Password123!",
        }
        res = self.client.post("/seller/signup", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Alice Developer")
        self.assertEqual(data["email"], "alice@test.com")
        self.assertIn("id", data)
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_02_seller_signup_validation_error(self):
        payload = {
            "name": "Alice",
            "email": "invalid-email-format",
            "password": "123",
        }
        res = self.client.post("/seller/signup", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_03_seller_login_success(self):
        res = self.client.post(
            "/seller/login",
            data={"username": "alice@test.com", "password": "Password123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_04_seller_login_invalid_password(self):
        res = self.client.post(
            "/seller/login",
            data={"username": "alice@test.com", "password": "WrongPassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(res.status_code, 401)

    def test_05_seller_login_invalid_email(self):
        res = self.client.post(
            "/seller/login",
            data={"username": "nonexistent@test.com", "password": "Password123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(res.status_code, 401)

    def test_06_seller_dashboard_authenticated(self):
        # Login to obtain token
        login_res = self.client.post(
            "/seller/login",
            data={"username": "alice@test.com", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]

        # Call /seller/dashboard with token
        res = self.client.get("/seller/dashboard", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], "alice@test.com")

        # Call /seller/me with token
        res_me = self.client.get("/seller/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_me.status_code, 200)

    def test_07_seller_dashboard_unauthenticated(self):
        res = self.client.get("/seller/dashboard")
        self.assertEqual(res.status_code, 401)

    def test_08_seller_logout_and_token_blacklist(self):
        # Login to obtain token
        login_res = self.client.post(
            "/seller/login",
            data={"username": "alice@test.com", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]

        # Token is initially valid
        check_before = self.client.get("/seller/dashboard", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(check_before.status_code, 200)

        # Logout
        logout_res = self.client.get("/seller/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn("Successfully Logged Out", logout_res.json().get("details", ""))

        # Token should now be rejected as blacklisted
        check_after = self.client.get("/seller/dashboard", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(check_after.status_code, 401)

    # ==================== PRODUCT ENDPOINTS ====================

    def test_09_create_product_success(self):
        payload = {
            "name": "Wireless Gaming Mouse",
            "price": 59.99,
            "stock": 25,
        }
        res = self.client.post("/product/", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Wireless Gaming Mouse")
        self.assertEqual(data["price"], 59.99)
        self.assertEqual(data["stock"], 25)
        self.assertEqual(data["status"], "active")
        self.assertIn("id", data)

    def test_10_create_product_validation_failure(self):
        # Invalid price (<= 0)
        res = self.client.post("/product/", json={"name": "Bad", "price": -5, "stock": 10})
        self.assertEqual(res.status_code, 422)

        # Invalid stock (< 0)
        res = self.client.post("/product/", json={"name": "Bad", "price": 10, "stock": -1})
        self.assertEqual(res.status_code, 422)

        # Name too short (< 3 chars)
        res = self.client.post("/product/", json={"name": "X", "price": 10, "stock": 5})
        self.assertEqual(res.status_code, 422)

    def test_11_get_product_by_id(self):
        # Product #1 was created in test_09
        res = self.client.get("/product/?id=1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["name"], "Wireless Gaming Mouse")

    def test_12_get_product_not_found(self):
        res = self.client.get("/product/?id=99999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("doesn't exist", res.json().get("detail", ""))

    def test_13_get_product_missing_id_query_param(self):
        res = self.client.get("/product/")
        self.assertEqual(res.status_code, 422)

    def test_14_update_product_success(self):
        update_payload = {"price": 49.99, "stock": 15}
        res = self.client.patch("/product/?id=1", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["price"], 49.99)
        self.assertEqual(data["stock"], 15)

    def test_15_update_product_empty_body(self):
        res = self.client.patch("/product/?id=1", json={})
        self.assertEqual(res.status_code, 400)
        self.assertIn("No data provided to update", res.json().get("detail", ""))

    def test_16_update_product_not_found(self):
        res = self.client.patch("/product/?id=99999", json={"price": 10.0})
        self.assertEqual(res.status_code, 404)

    def test_17_delete_product_success(self):
        res = self.client.delete("/product/?id=1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("deleted", res.json().get("detail", ""))

        # Verify it no longer exists
        check_res = self.client.get("/product/?id=1")
        self.assertEqual(check_res.status_code, 404)

    def test_18_delete_product_not_found(self):
        res = self.client.delete("/product/?id=99999")
        self.assertEqual(res.status_code, 404)

    # ==================== FRONTEND STATIC SERVING ====================

    def test_19_frontend_root_served(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("StockFlow", res.text)


if __name__ == "__main__":
    unittest.main()
