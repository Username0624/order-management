from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
# 引入 itsdangerous 的特定模組
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
import os
import uuid
from urllib.parse import urlparse

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
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "your_production_secret_here")
# 🚨 新增：用於密碼重設的額外安全鹽值
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", "a_unique_salt_for_password_reset")

# 用來產生與驗證 token (使用 SECRET_KEY 和 額外的 SALT)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=app.config['SECURITY_PASSWORD_SALT'])

# SMTP 設定（可用環境變數或直接填入）
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")      # e.g. "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

# ---------------- 郵件發送函式 ----------------
def send_reset_email(email, token):
    """使用 smtplib 發送密碼重設郵件，包含一個帶有時間限制的連結。"""
    
    # 使用 url_for 根據路由名稱生成完整連結
    # _external=True 會根據 request 建立完整的 URL，但這裡我們強制使用 localhost:5000
    reset_url = url_for('reset_password_page', token=token, _external=True)
    
    # 如果部署在伺服器上，建議確保 reset_url 使用您的實際域名
    if "127.0.0.1:5000" in reset_url or "localhost:5000" in reset_url:
        reset_url = f"http://127.0.0.1:5000/reset_password/{token}"
    
    print("========== 密碼重設連結 ==========")
    print(f"寄給: {email}")
    print(f"重設連結: {reset_url}")
    print("=================================")

    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        print("⚠️ 警告：SMTP 環境變數未設定，重設郵件無法發送。請檢查 .env 或環境設定。")
        return False

    msg = MIMEText(f"""
        您好，
        
        我們收到了您要求重設密碼的請求。請點擊以下連結重設您的密碼：
        {reset_url}
        
        此連結將在 1 小時後過期。
        
        如果不是您本人操作，請忽略此郵件。
        
        謝謝。
    """, 'plain', 'utf-8')
    msg['Subject'] = '【重要】密碼重設請求 - 訂單管理系統'
    msg['From'] = FROM_EMAIL
    msg['To'] = email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # 使用 TLS 加密
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        print("✅ 重設郵件發送成功")
        return True
    except Exception as e:
        print(f"❌ 郵件發送失敗: {e}")
        return False

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

@app.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>")
def reset_password_page(token):
    """
    接收重設連結的 token，並在前端渲染重設密碼表單。
    在此處預先驗證 token 有效性，避免前端提交時才發現過期。
    """
    try:
        # 驗證 token 是否有效及是否過期 (1 小時 = 3600 秒)
        email = serializer.loads(token, max_age=3600)
        
        # 再次檢查資料庫，確保使用者存在
        if users.find_one({"email": email}):
             return render_template("reset_password.html", token=token)
        else:
             return "無效的重設連結：使用者不存在。", 404
             
    except SignatureExpired:
        return "密碼重設連結已過期，請重新發送忘記密碼請求。", 400
    except BadTimeSignature:
        return "無效的密碼重設連結或格式錯誤。", 400
    except Exception as e:
        print(f"重設頁面載入錯誤: {e}")
        return "無效的密碼重設連結。", 400


# ---------------- Auth ----------------
@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.json
        print("收到註冊資料:", data)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        print("解析後:", username, email)

        if not username or not email or not password:
            return jsonify({"error": "缺少欄位"}), 400
        
        # ⚠️ 修正重點：使用 generate_password_hash 雜湊密碼
        hashed_password = generate_password_hash(password)

        # 檢查 Email 是否已存在（建議新增，防止重複註冊）
        if users.find_one({"email": email}):
            return jsonify({"error": "該電子郵件已被註冊"}), 409 # Conflict

        result = users.insert_one({
            "username": username,
            "email": email,
            # ✅ 存入雜湊後的密碼
            "password": hashed_password 
        })

        print("insert result:", result.inserted_id)

        return jsonify({"success": True, "message": "註冊成功"})

    except Exception as e:
        print("註冊錯誤:", str(e))
        return jsonify({"error": "伺服器錯誤"}), 500
        
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    print("\n--- 收到登入請求 ---")
    print(f"1. 接收到的 Email: {email}")
    print(f"2. 接收到的 密碼 (明文): {password}")
    
    # 步驟 1: 查找用戶
    user = users.find_one({"email": email})
    
    # 步驟 2: 檢查用戶是否存在
    if not user:
        print("3. 檢查結果: 用戶不存在 (Email 錯誤或未註冊)")
        return jsonify({"success": False, "message": "帳號或密碼錯誤"}), 401
    
    print("3. 檢查結果: 成功找到用戶")
    
    # 步驟 3: 提取資料庫中的雜湊密碼
    hashed_password_in_db = user.get("password")
    
    print(f"4. 資料庫中儲存的雜湊值: {hashed_password_in_db}")

    # 步驟 4: 驗證密碼
    try:
        password_verified = check_password_hash(hashed_password_in_db, password)
    except ValueError as e:
        print(f"5. 密碼比對錯誤: ValueError - 可能是資料庫中的密碼格式錯誤。錯誤訊息: {e}")
        password_verified = False
    except Exception as e:
        print(f"5. 密碼比對發生其他錯誤: {e}")
        password_verified = False


    if not password_verified:
        print("6. 最終驗證結果: 密碼比對失敗")
        return jsonify({"success": False, "message": "帳號或密碼錯誤"}), 401
    
    # 步驟 5: 登入成功
    print("6. 最終驗證結果: 登入成功！")
    print("----------------------\n")
    
    return jsonify({
        "success": True, 
        "user_id": str(user["_id"]), 
        "username": user.get("username",""), 
        "email": user["email"]
    })

# ---------------- 忘記/重設密碼 API ----------------

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password_api():
    """處理前端提交的 Email，生成 **帶時間限制** 的 Token 並發送重設郵件。"""
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "請提供電子郵件。"})

    user = users.find_one({"email": email})
    
    # 安全策略：不論使用者是否存在，都回傳成功訊息，防止被猜測 Email
    if not user:
        print(f"找不到使用者: {email}，但仍回傳成功訊息。")
        return jsonify({"success": True, "message": "如果該信箱存在，我們已發送重設密碼連結。"})

    # 1. 產生帶有 Email 資訊和時間限制的 Token
    try:
        # Token 包含 email，並只在後端進行驗證
        token = serializer.dumps(email)
    except Exception as e:
        print(f"Token 生成失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤，請稍後再試。'}), 500

    # 2. 發送郵件
    email_sent = send_reset_email(email, token)

    if email_sent:
        return jsonify({"success": True, "message": "密碼重設連結已寄出。請檢查您的信箱 (包含垃圾郵件)。"})
    else:
        # 郵件發送失敗，但前端仍應顯示成功，以避免洩露 SMTP 狀態
        return jsonify({"success": True, "message": "重設請求已受理。但郵件發送失敗，請稍後重試或聯繫管理員。"}), 202


@app.route("/api/reset-password", methods=["POST"])
def reset_password_api():
    """接收 Token 和新密碼，驗證 Token 有效性並更新密碼。"""
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"success": False, "message": "缺少必要資料"}), 400

    # 1. 驗證 Token 並提取 Email
    try:
        email = serializer.loads(token, max_age=3600)  # 1 小時過期驗證
    except SignatureExpired:
        return jsonify({'success': False, 'message': '密碼重設連結已過期，請重新發送請求。'}), 400
    except (BadTimeSignature, Exception):
        return jsonify({'success': False, 'message': '無效的密碼重設連結。'}), 400

    # 2. 查找使用者
    user = users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "使用者不存在。"})

    # 3. 雜湊新密碼
    hashed_password = generate_password_hash(new_password)
    
    # 4. 更新密碼
    # 由於我們使用 itsdangerous 的時間驗證，不需要在資料庫中儲存 token
    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hashed_password}, # ✅ 存入雜湊後的密碼
        }
    )

    return jsonify({"success": True, "message": "密碼已成功更新，請重新登入"})


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
    description = data.get("description", "")    # 表單簡介

    # 前端傳來的 fields，包含 merge_shipping
    fields = data.get("fields", {})

    # 必填欄位，強制設為 True
    fields["buyer_name"] = True
    fields["buyer_email"] = True
    fields["item_name"] = True
    fields["item_qty"] = True
    fields["item_price"] = True
    fields["item_total"] = True

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
    
    # 權限檢查：必須是擁有者，或者被允許的檢視者 (且已登入)
    if not (is_owner or is_viewer):
        return jsonify({"success": False, "message": "沒有權限檢視"}), 403

    # 建立回傳 rows
    rows = []
    for r in f.get("rows", []):
        row_copy = dict(r) # 複製訂單資料
        
        if is_owner:
            # 擁有者：回傳所有訂單，包含買家社群資訊
            rows.append(row_copy)
        
        elif is_viewer:
            # 檢視者/買家：只回傳該買家自己 Email 匹配的訂單
            if row_copy.get("buyer_email") == email:
                # 為了保護隱私，隱藏買家社群資訊
                row_copy.pop("buyer_social", None) 
                rows.append(row_copy)

    # ---------------- 統計資料 (summary) ----------------
    summary = {}
    for r in f.get("rows", []):
        name = r.get("buyer_name","")
        total = float(r.get("item_total", 0) or 0)
        
        # 為了簡化，讓擁有者可以看到完整的 summary，檢視者可以自己計算
        # 如果要讓檢視者只能看到自己的總額，則這裡需增加 is_viewer 判斷
        summary[name] = summary.get(name, 0) + total
    
    # ---------------- 回傳結果 ----------------
    resp = {
        "success": True,
        "form": {
            "_id": str(f["_id"]),
            "title": f.get("title"),
            "description": f.get("description", ""),  
            "owner_id": f.get("owner_id"),
            "owner_email": f.get("owner_email"),
            "fields": f.get("fields", {}),
            "rows": rows, # 這裡包含了篩選後的 rows
            "allowed_viewers": f.get("allowed_viewers", []),
            "recent_buyers": f.get("recent_buyers", [])
        },
        "is_owner": is_owner,
        "is_viewer": is_viewer,
        "summary_by_buyer": summary # summary 這裡沒有特別篩選，通常前端會自行處理
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
    if not f: return jsonify({"success": False, "message": "找不到表單"}),404
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
    if not f: return jsonify({"success": False, "message": "找不到表單"}),404
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
    shipped = data.get("shipped")    # ISO string or None
    shipping_fee = float(data.get("shipping_fee") or 0)
    buyer_social = data.get("buyer_social")
    merge_shipping = f.get("fields", {}).get("merge_shipping", False)

    item_total = item_qty * item_price
    if merge_shipping:
        item_total += shipping_fee 

    row = {
        "_id": str(ObjectId()),    # row id as string
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
    # 注意：這裡的 key 應該是 fields.merge_shipping，但為了保持與您程式碼的邏輯一致，
    # 我使用 shipping_fee_included，如果您的 fields 裡是 merge_shipping，請調整
    shipping_included = bool(f.get("fields", {}).get("merge_shipping", False)) 
    
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
    app.run(debug=True)