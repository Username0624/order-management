# 📦 Personal Shopping WMS: Warehouse & Logistics Management System

* [youtube](https://youtu.be/FvuIHIclPz0z)

* [System website link](https://order-management-803v.onrender.com)

---
## 🌟 Project Overview

This system is a lightweight Warehouse and Logistics Management Solution specifically engineered for **Personal Shopping Sellers**.

Traditional enterprise WMS/Logistics systems are often complex, expensive, and over-engineered, making them unsuitable for small, individual personal shoppers. This project aims to provide a transparent, efficient, and specialized platform to resolve core pain points in personal shopping workflows: communication chaos, difficulty in order tracking, and high buyer-seller support costs.

### 🎯 Target Users

| Category | User Group | Core Problem Solved |
| :--- | :--- | :--- |
| **Primary** | **Personal Shoppers**|Provides a centralized, low-cost system to manage orders, items, and logistics statuses. |
| **Stakeholder** | **Buyers** |Enables buyers to track their order status autonomously, improving transparency and reducing friction. |

-----

## ✨ Features and Usage Flow

The system is designed around two main user scenarios: the Seller (Personal Shopper) for management, and the Buyer for tracking.

### 1\. Seller Usage Flow (Management)

The seller uses the system to manage the entire lifecycle of an order:

1.  **Customer Management:** Maintain records of customers (name, phone, address, social media).
2.  **Order Creation:** Input new orders, including buyer email, item name, quantity, and price. The system automatically calculates the `total_amount`.
3.  **Status Updates:** Use the detailed order table to update logistics and payment status:
      * Mark payment as **Remitted (已匯款)**.
      * Mark fulfillment as **Shipped (已出貨)**, automatically recording the `shipped_date`.
4.  **Reporting:** View automated reports, specifically the **Summary by Buyer**, to quickly reconcile total payments.

### 2\. Buyer Usage Flow (Tracking)

The buyer only needs to track their purchased items:

1.  **Access:** Buyers receive a unique link or log in with their email.
2.  **Order View:** The system automatically filters the order data, showing *only* the rows associated with the buyer's email address (as seen in the debug logs).
3.  **Progress Check:** Buyers view the real-time status of their item (Remittance, Shipped Date) without needing to contact the seller.

-----

## 💻 Technical Stack

The project is built on the following robust technologies:

| Category | Technology | Description | Source |
| :--- | :--- | :--- | :--- |
| **Backend** | Flask (Python) | Lightweight framework handling CRUD operations and API endpoints. |
| **Database** | MongoDB | NoSQL database for flexible and scalable data management. |
| **Frontend** | HTML, Bootstrap | Responsible for the User Interface (UI) and buyer-side tracking interface. |

-----

## 📚 Database Schema (MongoDB Collections)

The database design utilizes three primary collections:

| Collection | Key Fields | Relationships |
| :--- | :--- | :--- |
| `customers` | `_id` (PK) , `name` , `email`, `address` | Stores buyer contact and social information. |
| `items` | `_id` (PK), `item_name`, `price` , `stock`  | Stores product details. |
| `orders`  | `_id` (PK) , `customer_id` (FK → `customers._id`, `status` , `total_amount`  | Stores transaction and logistics status. |

-----

## ⚙️ Installation and Execution

### 1\. Prerequisites

  * Python 3.x
  * MongoDB service running locally or accessible via a remote URI.

### 2\. Setup (Local Execution)

```bash
# 1. Clone the repository
git clone [Your Repository URL]
cd personal-shopping-wms

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate 

# 3. Install dependencies
pip install Flask pymongo python-dotenv

# 4. Configure MongoDB URI
# Create a .env file in the root directory and add your connection string.
# Example: MONGO_URI=mongodb://localhost:27017/personal_shopping_db
```

### 3\. Run the Application

```bash
flask run
```

The application will be accessible at `http://127.0.0.1:5000`.

-----
