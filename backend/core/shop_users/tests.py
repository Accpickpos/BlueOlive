from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import Client, TestCase, override_settings
from tenancy.models import Tenant

User = get_user_model()


# Disable tenant database creation for all tests
def disable_tenant_signals():
    """Decorator to disable tenant database creation signals during tests"""
    from tenancy.signals import create_tenant_database

    post_save.disconnect(create_tenant_database, sender=Tenant)


def enable_tenant_signals():
    """Re-enable tenant database creation signals after tests"""
    from tenancy.signals import create_tenant_database

    post_save.connect(create_tenant_database, sender=Tenant)


class ShopUserModelTest(TestCase):
    """Tests for ShopUser model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disable_tenant_signals()

    @classmethod
    def tearDownClass(cls):
        enable_tenant_signals()
        super().tearDownClass()

    def setUp(self):
        """Create test tenants with all required fields"""
        default_db = settings.DATABASES["default"]

        self.tenant1 = Tenant.objects.create(
            name="Tenant 1",
            slug="tenant1",
            subdomain="tenant1",
            db_name="test_tenant1_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )
        self.tenant2 = Tenant.objects.create(
            name="Tenant 2",
            slug="tenant2",
            subdomain="tenant2",
            db_name="test_tenant2_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )

    def test_create_user_with_tenant(self):
        """Test creating a user with a tenant"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
            role=User.Role.STAFF,
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.tenant, self.tenant1)
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertTrue(user.check_password("testpass123"))

    def test_create_superuser_without_tenant(self):
        """Test that superusers are created without tenant"""
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",  # nosec B105 B106 - test fixture password
        )
        self.assertIsNone(superuser.tenant)
        self.assertTrue(superuser.is_superuser)

    def test_unique_username_per_tenant(self):
        """Test that same username can exist in different tenants"""
        user1 = User.objects.create_user(
            username="john",
            email="john1@example.com",
            password="pass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
        )
        user2 = User.objects.create_user(
            username="john",
            email="john2@example.com",
            password="pass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant2,
        )
        self.assertEqual(user1.username, user2.username)
        self.assertNotEqual(user1.tenant, user2.tenant)
        self.assertNotEqual(user1.id, user2.id)

    def test_user_role_methods(self):
        """Test role checking methods"""
        admin = User.objects.create_user(
            username="admin",
            password="pass",
            tenant=self.tenant1,
            role=User.Role.ADMIN,  # nosec B105 B106 - test fixture password
        )
        staff = User.objects.create_user(
            username="staff",
            password="pass",
            tenant=self.tenant1,
            role=User.Role.STAFF,  # nosec B105 B106 - test fixture password
        )
        manager = User.objects.create_user(
            username="manager",
            password="pass",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
            role=User.Role.MANAGER,
        )
        customer = User.objects.create_user(
            username="customer",
            password="pass",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
            role=User.Role.CUSTOMER,
        )

        # Test ADMIN role
        self.assertTrue(admin.is_admin_user())
        self.assertTrue(admin.is_staff_user())
        self.assertTrue(admin.has_role(User.Role.ADMIN))

        # Test STAFF role
        self.assertFalse(staff.is_admin_user())
        self.assertTrue(staff.is_staff_user())
        self.assertTrue(staff.has_role(User.Role.STAFF))

        # Test MANAGER role
        self.assertFalse(manager.is_admin_user())
        self.assertTrue(manager.is_staff_user())
        self.assertTrue(manager.has_role(User.Role.MANAGER))

        # Test CUSTOMER role
        self.assertFalse(customer.is_admin_user())
        self.assertFalse(customer.is_staff_user())
        self.assertTrue(customer.has_role(User.Role.CUSTOMER))

    def test_user_cannot_be_created_without_tenant(self):
        """Test that regular users must have a tenant"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="notenantuser",
                password="pass",
                tenant=None,  # nosec B105 B106 - test fixture password
            )

    def test_default_role_is_customer(self):
        """Test that default role is CUSTOMER"""
        user = User.objects.create_user(
            username="defaultrole",
            password="pass",
            tenant=self.tenant1,  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(user.role, User.Role.CUSTOMER)


class TenantUserManagerTest(TestCase):
    """Tests for TenantUserManager"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disable_tenant_signals()

    @classmethod
    def tearDownClass(cls):
        enable_tenant_signals()
        super().tearDownClass()

    def setUp(self):
        default_db = settings.DATABASES["default"]

        self.tenant1 = Tenant.objects.create(
            name="Tenant 1",
            slug="tenant1",
            subdomain="tenant1",
            db_name="test_tenant1_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )
        self.tenant2 = Tenant.objects.create(
            name="Tenant 2",
            slug="tenant2",
            subdomain="tenant2",
            db_name="test_tenant2_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )

        self.user1 = User.objects.create_user(
            username="user1",
            password="pass",
            tenant=self.tenant1,  # nosec B105 B106 - test fixture password
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="pass",
            tenant=self.tenant2,  # nosec B105 B106 - test fixture password
        )

    @patch("shop_users.managers.get_current_tenant")
    def test_queryset_filters_by_tenant(self, mock_tenant):
        """Test that queryset automatically filters by current tenant"""
        mock_tenant.return_value = self.tenant1

        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.user1)

    @patch("shop_users.managers.get_current_tenant")
    def test_queryset_different_tenant(self, mock_tenant):
        """Test that switching tenant context filters correctly"""
        mock_tenant.return_value = self.tenant2

        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.user2)

    @patch("shop_users.managers.get_current_tenant")
    def test_queryset_no_tenant_shows_all(self, mock_tenant):
        """Test that no tenant context shows all users"""
        mock_tenant.return_value = None

        users = User.objects.all()
        self.assertEqual(users.count(), 2)


class ShopUserAuthenticationTest(TestCase):
    """Tests for authentication backend"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disable_tenant_signals()

    @classmethod
    def tearDownClass(cls):
        enable_tenant_signals()
        super().tearDownClass()

    def setUp(self):
        default_db = settings.DATABASES["default"]

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test",
            subdomain="testsub",
            db_name="test_tenant_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant,
            role=User.Role.ADMIN,
        )

    @patch("shop_users.auth_backends.get_current_tenant")
    def test_authenticate_with_correct_tenant(self, mock_tenant):
        """Test authentication succeeds with correct tenant"""
        from shop_users.auth_backends import ShopUserBackend

        mock_tenant.return_value = self.tenant
        backend = ShopUserBackend()

        authenticated_user = backend.authenticate(
            None,
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, self.user)

    @patch("shop_users.auth_backends.get_current_tenant")
    def test_authenticate_with_wrong_tenant(self, mock_tenant):
        """Test authentication fails with wrong tenant"""
        from shop_users.auth_backends import ShopUserBackend

        default_db = settings.DATABASES["default"]

        # Create another tenant
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other",
            subdomain="other",
            db_name="test_other_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )

        mock_tenant.return_value = other_tenant
        backend = ShopUserBackend()

        authenticated_user = backend.authenticate(
            None,
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

        self.assertIsNone(authenticated_user)

    @patch("shop_users.auth_backends.get_current_tenant")
    def test_authenticate_inactive_user(self, mock_tenant):
        """Test that inactive users cannot authenticate"""
        from shop_users.auth_backends import ShopUserBackend

        self.user.is_active = False
        self.user.save()

        mock_tenant.return_value = self.tenant
        backend = ShopUserBackend()

        authenticated_user = backend.authenticate(
            None,
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

        self.assertIsNone(authenticated_user)

    @patch("shop_users.auth_backends.get_current_tenant")
    def test_authenticate_wrong_password(self, mock_tenant):
        """Test that wrong password fails authentication"""
        from shop_users.auth_backends import ShopUserBackend

        mock_tenant.return_value = self.tenant
        backend = ShopUserBackend()

        authenticated_user = backend.authenticate(
            None,
            username="testuser",
            password="wrongpassword",  # nosec B105 B106 - test fixture password
        )

        self.assertIsNone(authenticated_user)

    @patch("shop_users.auth_backends.get_current_tenant")
    def test_authenticate_nonexistent_user(self, mock_tenant):
        """Test that nonexistent user fails authentication"""
        from shop_users.auth_backends import ShopUserBackend

        mock_tenant.return_value = self.tenant
        backend = ShopUserBackend()

        authenticated_user = backend.authenticate(
            None,
            username="nonexistent",
            password="anypassword",  # nosec B105 B106 - test fixture password
        )

        self.assertIsNone(authenticated_user)


class SubdomainIsolationIntegrationTest(TestCase):
    """Integration tests for tenant isolation via subdomains"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disable_tenant_signals()

    @classmethod
    def tearDownClass(cls):
        enable_tenant_signals()
        super().tearDownClass()

    def setUp(self):
        default_db = settings.DATABASES["default"]

        # Create two tenants with different subdomains
        self.tenant1 = Tenant.objects.create(
            name="Tenant One",
            slug="tenantone",
            subdomain="tenant1",
            db_name="test_tenant1_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )
        self.tenant2 = Tenant.objects.create(
            name="Tenant Two",
            slug="tenanttwo",
            subdomain="tenant2",
            db_name="test_tenant2_db",
            db_user=default_db.get("USER", "postgres"),
            db_password=default_db.get("PASSWORD", ""),
            db_host=default_db.get("HOST", "localhost"),
            db_port=default_db.get("PORT", 5432),
        )
        # Register connections
        from tenancy.utils import register_tenant_connection

        register_tenant_connection(self.tenant1)
        register_tenant_connection(self.tenant2)

        # Create users for each tenant
        self.user1 = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
            role=User.Role.ADMIN,
        )
        self.user2 = User.objects.create_user(
            username="testuser",  # Same username, different tenant
            password="testpass123",  # nosec B105 B106 - test fixture password
            tenant=self.tenant2,
            role=User.Role.ADMIN,
        )

        # Additional users as per task
        self.user1_extra = User.objects.create_user(
            username="extrauser1",
            password="extrapass1",  # nosec B105 B106 - test fixture password
            tenant=self.tenant1,
            role=User.Role.STAFF,
        )
        self.user2_extra = User.objects.create_user(
            username="extrauser2",
            password="extrapass2",  # nosec B105 B106 - test fixture password
            tenant=self.tenant2,
            role=User.Role.STAFF,
        )

    def test_successful_login_own_subdomain(self):
        """Test that user can login to their own subdomain"""
        client = Client(SERVER_NAME="tenant1.localhost")
        response = client.post(
            "/api/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.json().get("message", ""))

    def test_login_blocked_wrong_subdomain(self):
        """Test that user is blocked from logging in to wrong subdomain"""
        client = Client(SERVER_NAME="tenant2.localhost")
        response = client.post(
            "/api/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },  # user1's username  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials", response.json().get("error", ""))

    def test_additional_user_own_subdomain(self):
        """Test additional user can login to own subdomain"""
        client = Client(SERVER_NAME="tenant1.localhost")
        response = client.post(
            "/api/login/",
            {
                "username": "extrauser1",
                "password": "extrapass1",
            },  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(response.status_code, 200)

    def test_additional_user_blocked_other_subdomain(self):
        """Test additional user blocked from other subdomain"""
        client = Client(SERVER_NAME="tenant2.localhost")
        response = client.post(
            "/api/login/",
            {
                "username": "extrauser1",
                "password": "extrapass1",
            },  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(response.status_code, 400)

    def test_data_isolation_users_view(self):
        """Test that users can only see users from their tenant"""
        # Login as user1
        client = Client(SERVER_NAME="tenant1.localhost")
        client.post(
            "/api/login/",
            {"username": "testuser", "password": "testpass123"},  # nosec
        )
        # Access users API
        response = client.get("/api/users/")
        self.assertEqual(response.status_code, 200)
        users = response.json()
        # Should only see users from tenant1
        usernames = [u["username"] for u in users]
        self.assertIn("testuser", usernames)
        self.assertIn("extrauser1", usernames)
        self.assertNotIn("extrauser2", usernames)

    def test_invalid_subdomain_blocks_access(self):
        """Test that invalid subdomain returns forbidden"""
        client = Client(SERVER_NAME="invalid.localhost")
        response = client.post(
            "/api/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },  # nosec B105 B106 - test fixture password
        )
        self.assertEqual(response.status_code, 403)
