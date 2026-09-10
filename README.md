# 🌿 ShopEasy Garden

A full-stack **Django-based e-commerce website** for browsing and purchasing plants and gardening products.

ShopEasy Garden provides a complete online shopping experience with product categories, cart management, checkout, Razorpay payment integration, order tracking, customer email notifications, and Django Admin management.

---

## 📌 Project Overview

**ShopEasy Garden** is an online gardening store built using Django.

Customers can:

* Browse gardening products
* View product details
* Filter products by category
* Add products to cart
* Update cart quantities
* Proceed to checkout
* Make online payments using Razorpay
* Receive order confirmation emails
* View their previous orders
* Track order status
* Cancel eligible orders

Administrators can:

* Add, edit, and delete products
* Manage product categories
* Manage product stock
* Restore product stock manually
* Manage customer orders
* Update payment status
* Update order status
* Automatically send customer status-update emails

---

# ✨ Features

## 🛍️ Customer Features

### Product Browsing

* Featured products on the home page
* Product categories
* Product search
* Product detail pages
* Product availability display
* Product pricing
* Product images
* Stock information

### Shopping Cart

* Add products to cart
* Increase/decrease quantity
* Remove products
* Automatic subtotal calculation
* Shipping calculation
* Grand total calculation
* Checkout button with loading indicator

### User Account

* Customer registration
* Customer login
* Customer logout
* Profile page
* Customer information
* Order history

### Checkout

* Customer name
* Email address
* Phone number
* Delivery address
* City
* State
* Pincode
* Payment method
* Order summary

### Online Payment

The project supports online payment using:

**Razorpay**

Payment verification is performed on the server before the order is confirmed.

### Orders

Customers can:

* View order number
* View ordered products
* View quantities
* View prices
* View total amount
* View payment status
* View order status
* Cancel eligible orders

Orders that are already:

* Shipped
* Delivered
* Cancelled

cannot be cancelled by the customer.

---

# 📧 Email Notifications

ShopEasy Garden sends email notifications for important order events.

### Order Confirmation

After successful payment, the customer receives an order confirmation email.

### Order Status Updates

When an administrator changes the order status, the customer receives an email notification.

Examples:

* Pending
* Confirmed
* Processing
* Shipped
* Delivered
* Cancelled

### Cancellation Email

When a customer cancels an eligible order, cancellation notification emails can be sent to the customer and administrator.

---

# 📦 Stock Management

Product stock is automatically checked before an order is processed.

After successful payment:

* Ordered quantity is deducted from product stock.
* Product availability can be controlled through the admin panel.

## Manual Stock Restoration

Administrators can manually restore stock using Django Admin.

Go to:

**Admin → Products**

Select one or more products.

Choose:

**Restore stock**

Enter the quantity and apply the action.

Example:

```text
Current stock: 10
Restore quantity: 5

New stock: 15
```

### Important

Customer order cancellation does **not** automatically restore product stock.

Stock restoration is handled manually by the administrator.

---

# 🛠️ Admin Panel

Django Admin is used for managing the store.

Administrators can manage:

## Categories

* Add category
* Edit category
* Delete category
* Manage category slug
* Manage category image

## Products

* Add product
* Edit product
* Delete selected products
* Search products
* Filter products
* Update price
* Update stock
* Update availability
* Restore stock manually

## Orders

Administrators can:

* View orders
* Search orders
* Filter orders
* Update payment status
* Update order status
* View customer details
* View ordered products
* View order totals

Order status changes trigger customer email notifications.

---

# 💻 Technology Stack

## Backend

* Python
* Django

## Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Bootstrap Icons

## Database

The project can use:

* SQLite for local development
* PostgreSQL for production

## Payment Gateway

* Razorpay

## Email

SMTP-based email service

## Deployment

The application can be deployed on platforms such as:

* Render
* Railway
* PythonAnywhere
* VPS / Cloud server

---

# 📁 Project Structure

A typical project structure is:

```text
garden-ecommerce-django/
│
├── manage.py
│
├── requirements.txt
│
├── README.md
│
├── .gitignore
│
├── project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── store/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── email_service.py
│   ├── migrations/
│   │
│   ├── templates/
│   │   └── store/
│   │       ├── home.html
│   │       ├── cart.html
│   │       ├── checkout.html
│   │       ├── my_orders.html
│   │       ├── order_success.html
│   │       └── ...
│   │
│   └── static/
│
├── media/
│
└── static/
```

> Folder names may vary depending on the project configuration.

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/sharmariteshkumar/garden-ecommerce-django
```

Move into the project directory:

```bash
cd garden-ecommerce-django
```

---

# 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

---

# 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not exist, install Django first:

```bash
pip install django
```

Install Razorpay:

```bash
pip install razorpay
```

---

# 4. Configure Environment Variables

Create a `.env` file in the project root if your project uses environment variables.

Example:

```env
SECRET_KEY=your-secret-key

DEBUG=True

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password
EMAIL_USE_TLS=True

DEFAULT_FROM_EMAIL=your-email@gmail.com
ADMIN_EMAIL=your-admin-email@gmail.com
```

### ⚠️ Security

Never commit the following to GitHub:

```text
.env
SECRET_KEY
RAZORPAY_KEY_SECRET
EMAIL_HOST_PASSWORD
API keys
SMTP passwords
```

Add `.env` to `.gitignore`.

---

# 5. Run Database Migrations

Run:

```bash
python manage.py makemigrations
```

Then:

```bash
python manage.py migrate
```

---

# 6. Create Django Admin User

Create a superuser:

```bash
python manage.py createsuperuser
```

Enter:

```text
Username
Email
Password
```

---

# 7. Run the Development Server

Start Django:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

---

# 💳 Razorpay Configuration

The project uses Razorpay for online payments.

Create Razorpay API credentials from your Razorpay dashboard.

Configure:

```env
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret
```

The secret key must remain private.

## Payment Flow

The general payment flow is:

```text
Customer
   ↓
Add Products
   ↓
Cart
   ↓
Checkout
   ↓
Create Razorpay Order
   ↓
Razorpay Payment
   ↓
Payment Verification
   ↓
Confirm Order
   ↓
Deduct Stock
   ↓
Send Confirmation Email
   ↓
Order Success
```

Payment verification should always happen on the backend.

---

# 📧 Email Configuration

The project uses SMTP to send customer emails.

For Gmail, an **App Password** should be used instead of the normal Gmail password when required by the account configuration.

Example:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

Email functionality is used for:

* Order confirmation
* Order cancellation
* Order status updates

---

# 🧑‍💼 Order Status Flow

Orders support the following statuses:

```text
Pending
   ↓
Confirmed
   ↓
Processing
   ↓
Shipped
   ↓
Delivered
```

An order may also become:

```text
Cancelled
```

depending on the order state.

Customers cannot cancel orders after they have been shipped or delivered.

---

# 💰 Payment Status

Supported payment statuses include:

```text
Pending
Paid
Failed
Refunded
```

The payment status and order status are managed separately.

For example:

```text
Payment Status: Paid
Order Status: Processing
```

is a valid state.

---

# 🔐 Authentication

Django's built-in authentication system is used for customer accounts.

Typical authentication flow:

```text
Register
   ↓
Login
   ↓
Browse Products
   ↓
Add to Cart
   ↓
Checkout
   ↓
View Orders
```

---

# 🖼️ Media Files

Product and category images are stored using Django's media configuration.

Typical locations:

```text
media/
├── products/
└── categories/
```

During development, Django can serve media files using the configured development settings.

For production, configure proper media storage according to the hosting platform.

---

# 📦 Static Files

Django static files include:

* CSS
* JavaScript
* Bootstrap assets
* Django Admin assets
* Images/icons

For production, run:

```bash
python manage.py collectstatic
```

Make sure your production configuration has a proper `STATIC_ROOT`.

---

# 🌍 Production Deployment

Before deploying the application:

## Set DEBUG to False

```env
DEBUG=False
```

## Configure ALLOWED_HOSTS

Example:

```python
ALLOWED_HOSTS = [
    "your-domain.com",
]
```

For Render, configure the appropriate Render hostname as well.

## Configure Database

Production should preferably use PostgreSQL or another production-ready database instead of SQLite.

## Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Apply Migrations

```bash
python manage.py migrate
```

## Configure Environment Variables

Production secrets should be added through the hosting provider's environment-variable settings.

Do not store production secrets directly in source code.

---

# ☁️ Render Deployment

For Render deployment, the project generally requires:

### Build Command

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Start Command

A typical Django/Gunicorn start command is:

```bash
gunicorn project.wsgi:application
```

Replace `project` with the actual Django project package name if different.

---

# 🔄 Typical Deployment Workflow

After making changes:

```bash
git add .
```

Commit:

```bash
git commit -m "Update e-commerce functionality"
```

Push:

```bash
git push
```

The hosting provider can then build and deploy the latest version.

---

# 🧪 Testing

Before production deployment, test the following.

## Customer

* [ ] Registration works
* [ ] Login works
* [ ] Logout works
* [ ] Products display correctly
* [ ] Product details work
* [ ] Search works
* [ ] Category filtering works
* [ ] Add to cart works
* [ ] Cart quantity update works
* [ ] Product removal works
* [ ] Checkout works
* [ ] Payment works
* [ ] Payment verification works
* [ ] Order success page works
* [ ] Confirmation email is received
* [ ] Order history works
* [ ] Order cancellation works
* [ ] Status updates are displayed correctly

## Admin

* [ ] Admin login works
* [ ] Categories can be created
* [ ] Products can be created
* [ ] Products can be edited
* [ ] Products can be deleted
* [ ] Delete selected action works
* [ ] Restore stock action works
* [ ] Orders are visible
* [ ] Payment status can be updated
* [ ] Order status can be updated
* [ ] Status email is sent after status change

---

# 🛡️ Security Checklist

Before production:

* [ ] `DEBUG=False`
* [ ] Secret key stored in environment variables
* [ ] Razorpay secret stored securely
* [ ] SMTP password stored securely
* [ ] `.env` is included in `.gitignore`
* [ ] Production `ALLOWED_HOSTS` configured
* [ ] CSRF protection enabled
* [ ] HTTPS enabled
* [ ] Database credentials secured
* [ ] Admin account uses a strong password
* [ ] Sensitive credentials are not committed to GitHub

---

# 📝 Important Business Logic

## Stock Deduction

Stock is deducted after successful payment verification.

Example:

```text
Product stock = 20
Customer buys = 3

Remaining stock = 17
```

## Customer Cancellation

Customer cancellation changes the order status to:

```text
cancelled
```

Customer cancellation does **not** automatically restore product stock.

Administrators can manually restore stock through the Product Admin action.

## Order Status Email

When an administrator changes an order status, an email is sent to the customer's registered email address.

Example:

```text
Old Status: Processing
New Status: Shipped
```

The customer receives a status update email.

---

# 🧹 Git Ignore

A `.gitignore` should include sensitive and generated files such as:

```gitignore
venv/
.env
__pycache__/
*.pyc
db.sqlite3

media/
staticfiles/

.DS_Store
.idea/
.vscode/
```

If production media files need to be versioned or stored separately, adjust the configuration accordingly.

---

# 📄 License

This project is intended for educational, personal, or commercial use according to the license selected by the project owner.

If this project is distributed publicly, add an appropriate license such as:

```text
MIT License
```

or another license suitable for the project.

---

# 👨‍💻 Development

The project follows a Django-based MVC/MVT architecture.

Main application responsibilities:

```text
Models
   ↓
Database structure

Views
   ↓
Business logic

Templates
   ↓
User interface

URLs
   ↓
Request routing

Admin
   ↓
Store management
```

---

# 🚀 Future Improvements

Possible future improvements include:

* Product reviews and ratings
* Wishlist
* Coupon system
* Discount management
* Advanced product search
* Product sorting
* Pagination
* Automated stock restoration after approved refunds
* Order invoice generation
* PDF invoices
* WhatsApp order notifications
* Advanced admin dashboard
* Sales analytics
* Customer notifications
* Multiple payment methods
* Cloud image storage
* PostgreSQL production optimization

---

# 🌱 ShopEasy Garden

**ShopEasy Garden — Grow More. Shop Better. 🌿**

Built with:

**Python + Django + Bootstrap + JavaScript + Razorpay**
