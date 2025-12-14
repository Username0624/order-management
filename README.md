# 📦 Personal Shopping WMS: Warehouse & Logistics Management System

## 🌟 Project Overview

[cite_start]This system is a lightweight Warehouse and Logistics Management Solution specifically engineered for **Personal Shopping Sellers**[cite: 2, 3].

[cite_start]Traditional enterprise WMS/Logistics systems are often complex, expensive, and over-engineered, making them unsuitable for small, individual personal shoppers[cite: 5]. [cite_start]This project aims to provide a transparent, efficient, and specialized platform to resolve core pain points in personal shopping workflows [cite: 1][cite_start]: communication chaos, difficulty in order tracking, and high buyer-seller support costs[cite: 17, 19, 21].

### [cite_start]🎯 Target Users [cite: 31, 32]

| Category | User Group | Core Problem Solved |
| :--- | :--- | :--- |
| **Primary** | [cite_start]**Personal Shoppers** [cite: 33] | [cite_start]Provides a centralized, low-cost system to manage orders, items, and logistics statuses[cite: 27]. |
| **Stakeholder** | [cite_start]**Buyers** [cite: 34] | [cite_start]Enables buyers to track their order status autonomously, improving transparency and reducing friction[cite: 29, 34]. |

-----

## ✨ Features and Usage Flow

The system is designed around two main user scenarios: the Seller (Personal Shopper) for management, and the Buyer for tracking.

### 1\. Seller Usage Flow (Management)

The seller uses the system to manage the entire lifecycle of an order:

1.  [cite_start]**Customer Management:** Maintain records of customers (name, phone, address, social media)[cite: 25, 38, 39, 40, 41].
2.  [cite_start]**Order Creation:** Input new orders, including buyer email, item name, quantity, and price[cite: 51, 52, 53]. [cite_start]The system automatically calculates the `total_amount`[cite: 48].
3.  [cite_start]**Status Updates:** Use the detailed order table to update logistics and payment status[cite: 27]:
      * Mark payment as **Remitted (已匯款)**.
      * [cite_start]Mark fulfillment as **Shipped (已出貨)**, automatically recording the `shipped_date`[cite: 47].
4.  [cite_start]**Reporting:** View automated reports, specifically the **Summary by Buyer**, to quickly reconcile total payments[cite: 28].

### 2\. Buyer Usage Flow (Tracking)

[cite_start]The buyer only needs to track their purchased items[cite: 34]:

1.  **Access:** Buyers receive a unique link or log in with their email.
2.  **Order View:** The system automatically filters the order data, showing *only* the rows associated with the buyer's email address (as seen in the debug logs).
3.  [cite_start]**Progress Check:** Buyers view the real-time status of their item (Remittance, Shipped Date) without needing to contact the seller[cite: 17].

-----

## 💻 Technical Stack

The project is built on the following robust technologies:

| Category | Technology | Description | Source |
| :--- | :--- | :--- | :--- |
| **Backend** | Flask (Python) | [cite_start]Lightweight framework handling CRUD operations and API endpoints[cite: 58]. |
| **Database** | MongoDB | [cite_start]NoSQL database for flexible and scalable data management[cite: 60]. |
| **Frontend** | HTML, Bootstrap | [cite_start]Responsible for the User Interface (UI) and buyer-side tracking interface[cite: 59]. |

-----

## 📚 Database Schema (MongoDB Collections)

[cite_start]The database design utilizes three primary collections[cite: 60]:

| Collection | Key Fields | Relationships |
| :--- | :--- | :--- |
| [cite_start]`customers` [cite: 37] | [cite_start]`_id` (PK) [cite: 38][cite_start], `name` [cite: 39][cite_start], `email`, `address` [cite: 41] | Stores buyer contact and social information. |
| [cite_start]`items` [cite: 49] | [cite_start]`_id` (PK) [cite: 50][cite_start], `item_name` [cite: 51][cite_start], `price` [cite: 52][cite_start], `stock` [cite: 53] | Stores product details. |
| [cite_start]`orders` [cite: 42] | [cite_start]`_id` (PK) [cite: 43][cite_start], `customer_id` (FK → `customers._id`) [cite: 44, 45][cite_start], `status` [cite: 47][cite_start], `total_amount` [cite: 48] | Stores transaction and logistics status. |

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
