const API_BASE = "htAPI_BASEtp://127.0.0.1:5000";

// Auth
async function apiRegister(username, email, password) {
  const res = await fetch("/api/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, email, password })
  });
  return res.json();
}

async function apiLogin(email, password){
  const res = await fetch(`/api/login`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email, password})
  });
  return res.json();
}

async function apiUpdateUsername(user_id, username){
  const res = await fetch(`/api/update_username`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({user_id, username})
  });
  return res.json();
}

function logout(){
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  localStorage.removeItem("email");
  window.location.href = "/login";
}


// Forms
async function apiCreateForm(owner_id, owner_email, title, description, fields){
  const body = { owner_id, owner_email, title, description, fields };
  const res = await fetch(`/api/create_form`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}


async function apiGetMyForms(user_id){
  const res = await fetch(`/api/my_forms/${user_id}`);
  return res.json();
}

async function apiGetForm(formId, userId) {
    // 確保這裡的 URL 變數名是正確的： formId 和 userId
    const url = `/api/form/${formId}/${userId}`; 
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error fetching form data:', error);
        return { success: false, message: '連線錯誤，無法載入表單資料' };
    }
}
async function apiRequestPasswordReset(email){
  const res = await fetch(`/api/request_password_reset`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email})
  });
  return res.json();
}

async function apiForgotPassword(email){
  const res = await fetch(`/api/forgot_password`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ email })
  });
  return res.json();
}


async function apiAddViewer(form_id, owner_id, viewer_email){
  const res = await fetch(`/api/add_viewer`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({form_id, owner_id, viewer_email})
  });
  return res.json();
}

async function apiRemoveViewer(form_id, owner_id, viewer_email){
  const res = await fetch(`/api/remove_viewer`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({form_id, owner_id, viewer_email})
  });
  return res.json();
}

// Rows
async function apiAddRow(form_id, owner_id, row){
  const body = Object.assign({form_id, owner_id}, row);
  const res = await fetch(`/api/add_row`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}

async function apiUpdateRow(form_id, owner_id, index, row){
  const body = Object.assign({form_id, owner_id, index}, row);
  const res = await fetch(`/api/update_row`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}

async function apiDeleteRow(form_id, owner_id, index){
  const res = await fetch(`/api/delete_row`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({form_id, owner_id, index})
  });
  return res.json();
}

async function apiClearForm(form_id, owner_id){
  const res = await fetch(`/api/clear_form`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({form_id, owner_id})
  });
  return res.json();
}

// 👍 最終正確版本（沒有重複）
async function apiUpdateFormDescription(form_id, description){
  const res = await fetch(`/api/update_form_description`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({form_id, description})
  });
  return res.json();
}

async function apiRecentBuyers(form_id){
  const res = await fetch(`/api/recent_buyers/${form_id}`);
  return res.json();
}

async function apiGetFormRows(form_id, viewer_email){
  const res = await fetch(`/api/form_rows?form_id=${form_id}&viewer_email=${viewer_email}`);
  return res.json();

}
