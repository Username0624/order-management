from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import os
import uuid
from email.mime.text import MIMEText

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# MongoDB
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
try:
    client.admin.command("ping")
    print("✅ MongoDB Atlas 連線成功")
except Exception as e:
    print("❌ MongoDB 連線失敗", e)

db = client["datasys114"]
users = db["users"]
forms = db["forms"]


# secret key（若已在 app.config['SECRET_KEY']，使用現有的）
app.config['SECRET_KEY'] = app.secret_key or "your_production_secret_here"

# 用來產生與驗證 token
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# SMTP 設定（可用環境變數或直接填入，若本機測試可略過）
SMTP_HOST = os.environ.get("SMTP_HOST")      # e.g. "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

# ---------------- Pages ----------------
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/create_form", methods=["GET"])
def create_form_page():
    return render_template("create_form.html")

@app.route("/form", methods=["GET"])
def form_page():
    return render_template("form.html")


# ---------------- Auth ----------------
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username") or ""
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"success": False, "message": "請輸入 email 與密碼"}), 400
    if users.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email 已被使用"}), 400
    # 在註冊處
    hashed = generate_password_hash(password)
    res = users.insert_one({"username": username, "email": email, "password": hashed})

    return jsonify({"success": True, "user_id": str(res.inserted_id), "username": username, "email": email})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    user = users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "帳號或密碼錯誤"}), 401
    return jsonify({"success": True, "user_id": str(user["_id"]), "username": user.get("username",""), "email": user["email"]})
def send_reset_email(email, token):
    reset_url = f"http://localhost:5000/reset_password/{token}"
    print("========== 密碼重設連結 ==========")
    print(f"寄給: {email}")
    print(f"重設連結: {reset_url}")
    print("=================================")

#重設密碼組
@app.route("/forgot_password", methods=["GET"])
def forgot_password_html():
    return render_template("forgot_password.html")

def forgot_password():
    data = request.get_json()
    email = data.get("email")

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "此 email 未註冊"})

    token = str(uuid.uuid4())

    users.update_one(
        {"email": email},
        {"$set": {"reset_token": token}}
    )

    send_reset_email(email, token)

    return jsonify({"success": True, "message": "重設密碼連結已寄出"})


@app.route("/api/reset_password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"success": False, "message": "缺少必要資料"})

    user = users.find_one({"reset_token": token})
    if not user:
        return jsonify({"success": False, "message": "無效或過期的重設連結"})

    # 更新密碼 + 移除 token
    users.update_one(
        {"reset_token": token},
        {
            "$set": {"password": new_password},
            "$unset": {"reset_token": ""}
        }
    )

    return jsonify({"success": True, "message": "密碼已成功更新，請重新登入"})


@app.route("/reset_password/<token>")
def reset_password_page(token):
    return render_template("reset_password.html", token=token)


@app.route("/api/update_username", methods=["POST"])
def api_update_username():
    data = request.get_json()
    user_id = data.get("user_id")
    username = data.get("username","")
    if not user_id:
        return jsonify({"success": False, "message":"缺少 user_id"}),400
    users.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": username}})
    user = users.find_one({"_id": ObjectId(user_id)})
    return jsonify({"success": True, "username": user.get("username","")})


# ---------------- Form management ----------------
@app.route("/api/create_form", methods=["POST"])
def api_create_form():
    data = request.get_json()
    owner_id = data.get("owner_id")
    owner_email = data.get("owner_email")
    title = data.get("title")
    description = data.get("description", "")   # 表單簡介

    # 前端傳來的 fields，包含 merge_shipping
    fields = data.get("fields", {})

    # 必填欄位，強制設為 True
    fields["buyer_name"] = True
    fields["buyer_email"] = True
    fields["item_name"] = True
    fields["item_qty"] = True
    fields["item_price"] = True
    fields["item_total"] = True

    # 這裡不要再覆蓋 merge_shipping
    # fields["merge_shipping"] = data.get("merge_shipping", False)

    doc = {
        "title": title,
        "description": description,
        "owner_id": owner_id,
        "owner_email": owner_email,
        "allowed_viewers": [],
        "fields": fields,
        "rows": [],
        "recent_buyers": []
    }

    res = forms.insert_one(doc)
    return jsonify({"success": True, "form_id": str(res.inserted_id)})


@app.route("/api/update_form_description", methods=["POST"])
def api_update_form_description():
    data = request.get_json()
    form_id = data.get("form_id")
    desc = data.get("description", "")

    forms.update_one(
        {"_id": ObjectId(form_id)},
        {"$set": {"description": desc}}
    )

    return jsonify({"success": True})


@app.route("/api/my_forms/<user_id>", methods=["GET"])
def api_my_forms(user_id):
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"owned": [], "viewable": []})
    email = user["email"]
    owned = list(forms.find({"owner_id": user_id}))
    viewable = list(forms.find({"allowed_viewers": email}))
    def conv(f):
        f["_id"] = str(f["_id"])
        return f
    owned = [conv(f) for f in owned]
    viewable = [conv(f) for f in viewable]
    return jsonify({"owned": owned, "viewable": viewable})


@app.route("/api/form/<form_id>/<user_id>", methods=["GET"])
def api_get_form(form_id, user_id):
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f:
        return jsonify({"success": False, "message": "找不到表單"}), 404
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"success": False, "message": "找不到使用者"}), 404
    email = user["email"]

    # 判斷身分：賣家或買家
    is_owner = (f.get("owner_id") == user_id)
    is_viewer = (email in f.get("allowed_viewers", []))
    if not (is_owner or is_viewer):
        return jsonify({"success": False, "message": "沒有權限檢視"}), 403

    # 建立回傳 rows（若 viewer 只回自己的 rows，且隱藏 buyer_social）
    rows = []
    for r in f.get("rows", []):
        if is_owner:
            rows.append(dict(r))
        else:
            if r.get("buyer_email") == email:
                row_copy = dict(r)
                row_copy.pop("buyer_social", None)
                rows.append(row_copy)

    # summary by buyer (owner 可見完整 summary；viewer 也算出所有 summary，但前端可只用自己的)
    summary = {}
    for r in f.get("rows", []):
        name = r.get("buyer_name","")
        total = float(r.get("item_total", 0) or 0)
        summary[name] = summary.get(name, 0) + total

    resp = {
        "success": True,
        "form": {
            "_id": str(f["_id"]),
            "title": f.get("title"),
             "description": f.get("description", ""),  
            "owner_id": f.get("owner_id"),
            "owner_email": f.get("owner_email"),
            "fields": f.get("fields", {}),
            "rows": rows,
            "allowed_viewers": f.get("allowed_viewers", []),
            "recent_buyers": f.get("recent_buyers", [])
        },
        "is_owner": is_owner,
        "is_viewer": is_viewer,
        "summary_by_buyer": summary
    }
    return jsonify(resp)


@app.route("/api/add_viewer", methods=["POST"])
def api_add_viewer():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    viewer_email = data.get("viewer_email")
    if not all([form_id, owner_id, viewer_email]):
        return jsonify({"success": False, "message": "缺少參數"}),400
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f:
        return jsonify({"success": False, "message": "找不到表單"}),404
    if f.get("owner_id") != owner_id:
        return jsonify({"success": False, "message": "只有表單擁有者可以新增檢視者"}),403
    viewer = users.find_one({"email": viewer_email})
    if not viewer:
        return jsonify({"success": False, "message": "此 email 尚未註冊"}),400
    forms.update_one({"_id": ObjectId(form_id)}, {"$addToSet": {"allowed_viewers": viewer_email}})
    return jsonify({"success": True})


@app.route("/api/remove_viewer", methods=["POST"])
def api_remove_viewer():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    viewer_email = data.get("viewer_email")
    if not all([form_id, owner_id, viewer_email]):
        return jsonify({"success": False, "message": "缺少參數"}),400
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f:
        return jsonify({"success": False, "message": "找不到表單"}),404
    if f.get("owner_id") != owner_id:
        return jsonify({"success": False, "message": "只有表單擁有者可以移除檢視者"}),403
    forms.update_one({"_id": ObjectId(form_id)}, {"$pull": {"allowed_viewers": viewer_email}})
    return jsonify({"success": True})


@app.route("/api/add_row", methods=["POST"])
def api_add_row():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "message":"找不到表單"}),404
    if f.get("owner_id") != owner_id: return jsonify({"success": False, "message":"沒有權限新增"}),403

    buyer_name = data.get("buyer_name")
    buyer_email = data.get("buyer_email")
    item_name = data.get("item_name")
    item_qty = float(data.get("item_qty") or 0)
    item_price = float(data.get("item_price") or 0)
    item_total = item_qty * item_price
    remittance = bool(data.get("remittance", False))
    shipped = data.get("shipped")  # ISO string or None
    shipping_fee = float(data.get("shipping_fee") or 0)
    buyer_social = data.get("buyer_social")
    merge_shipping = f.get("fields", {}).get("merge_shipping", False)

    item_total = item_qty * item_price
    if merge_shipping:
        item_total += shipping_fee 

    row = {
        "_id": str(ObjectId()),   # row id as string
        "buyer_name": buyer_name,
        "buyer_email": buyer_email,
        "item_name": item_name,
        "item_qty": item_qty,
        "item_price": item_price,
        "item_total": item_total,
        "remittance": remittance,
        "shipped": shipped,
        "shipping_fee": shipping_fee,
        "buyer_social": buyer_social
    }

    forms.update_one({"_id": ObjectId(form_id)}, {"$push": {"rows": row}})
    forms.update_one({"_id": ObjectId(form_id)}, {"$addToSet": {"recent_buyers": buyer_email}})
    return jsonify({"success": True, "row": row})


@app.route("/api/update_row", methods=["POST"])
def api_update_row():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    index = int(data.get("index"))
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "message":"找不到表單"}),404
    if f.get("owner_id") != owner_id: return jsonify({"success": False, "message":"沒有權限修改"}),403
    rows = f.get("rows", [])
    if index < 0 or index >= len(rows): return jsonify({"success": False, "message":"index 不合法"}),400

    item_qty = float(data.get("item_qty") or 0)
    item_price = float(data.get("item_price") or 0)
    shipping_fee = float(data.get("shipping_fee") or 0)

    # 後端依表單設定決定是否併入運費
    shipping_included = bool(f.get("fields", {}).get("shipping_fee_included", False))
    if shipping_included:
        item_total = item_qty * item_price + shipping_fee
    else:
        item_total = item_qty * item_price

    new_row = {
        "_id": rows[index].get("_id", str(ObjectId())),
        "buyer_name": data.get("buyer_name"),
        "buyer_email": data.get("buyer_email"),
        "item_name": data.get("item_name"),
        "item_qty": item_qty,
        "item_price": item_price,
        "item_total": item_total,
        "remittance": bool(data.get("remittance", False)),
        "shipped": data.get("shipped"),
        "shipping_fee": shipping_fee,
        "buyer_social": data.get("buyer_social")
    }

    rows[index] = new_row
    forms.update_one({"_id": ObjectId(form_id)}, {"$set": {"rows": rows}})
    forms.update_one({"_id": ObjectId(form_id)}, {"$addToSet": {"recent_buyers": new_row.get("buyer_email")}})
    return jsonify({"success": True, "row": new_row})


@app.route("/api/delete_row", methods=["POST"])
def api_delete_row():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    index = int(data.get("index"))
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "message":"找不到表單"}),404
    if f.get("owner_id") != owner_id: return jsonify({"success": False, "message":"沒有權限刪除"}),403
    rows = f.get("rows", [])
    if index < 0 or index >= len(rows): return jsonify({"success": False, "message":"index 不合法"}),400
    rows.pop(index)
    forms.update_one({"_id": ObjectId(form_id)}, {"$set": {"rows": rows}})
    return jsonify({"success": True})


@app.route("/api/clear_form", methods=["POST"])
def api_clear_form():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "message":"找不到表單"}),404
    if f.get("owner_id") != owner_id: return jsonify({"success": False, "message":"沒有權限清空"}),403
    forms.update_one({"_id": ObjectId(form_id)}, {"$set": {"rows": []}})
    return jsonify({"success": True})


@app.route("/api/recent_buyers/<form_id>", methods=["GET"])
def api_recent_buyers(form_id):
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "recent_buyers": []})
    return jsonify({"success": True, "recent_buyers": f.get("recent_buyers", [])})


@app.route("/api/delete_form", methods=["POST"])
def api_delete_form():
    data = request.get_json()
    form_id = data.get("form_id")
    owner_id = data.get("owner_id")
    f = forms.find_one({"_id": ObjectId(form_id)})
    if not f: return jsonify({"success": False, "message": "找不到表單"}), 404
    if f.get("owner_id") != owner_id:
        return jsonify({"success": False, "message": "沒有權限刪除"}), 403
    forms.delete_one({"_id": ObjectId(form_id)})
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run()
