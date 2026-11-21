const msgBox = document.getElementById("formMsg");
const submitBtn = document.getElementById("submitBtn");

function showMsg(text, type = "error") {
  msgBox.textContent = text;
  msgBox.className = "form-msg form-msg--" + type;
}

function setLoading(loading, label) {
  submitBtn.disabled = loading;
  submitBtn.textContent = loading ? "Un momento…" : label;
}

async function request(path, body) {
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  } catch (err) {
    console.error("Fallo de red hacia", API_BASE + path, err);
    throw new Error("No se pudo conectar con el servidor. Revisa que la API esté encendida y que API_BASE (config.js) sea correcto.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    console.error(res.status, API_BASE + path, data);
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    throw new Error(detail || "Error " + res.status + " en " + path);
  }
  return data;
}

/* ---------- REGISTRO (2 pasos: credenciales -> perfil) ---------- */
const registerForm = document.getElementById("registerForm");
if (registerForm) {
  const role = registerForm.dataset.role;      // "user" o "fundation"
  const ep = ENDPOINTS[role];
  const label = submitBtn.textContent;

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = registerForm.name.value.trim();
    const email = registerForm.email.value.trim();
    const password = registerForm.password.value;
    const confirm = registerForm.confirm.value;

    if (!name) return showMsg("Escribe un nombre.");
    if (registerForm.consent && !registerForm.consent.checked) return showMsg("Debes autorizar que se muestre el correo de la fundación.");
    if (password.length < 8) return showMsg("La contraseña debe tener al menos 8 caracteres.");
    if (password !== confirm) return showMsg("Las contraseñas no coinciden.");

    setLoading(true);
    try {
      const auth = await request(ep.registerAuth, { email, password });
      const id = auth.data.id;
      await request(ep.registerProfile, { id, email, name });

      showMsg("¡Cuenta creada! Te llevamos al inicio de sesión…", "ok");
      setTimeout(() => (location.href = HOME[role]), 1500);
    } catch (err) {
      showMsg(err.message);
      setLoading(false, label);
    }
  });
}

/* ---------- LOGIN ---------- */
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  const role = loginForm.dataset.role;
  const ep = ENDPOINTS[role];
  const label = submitBtn.textContent;

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = loginForm.email.value.trim();
    const password = loginForm.password.value;

    setLoading(true);
    try {
      const res = await request(ep.login, { email, password });
      try {
        localStorage.setItem("user", JSON.stringify({ ...res.data, role, actor_type: ACTOR_TYPE[role] }));
        if (res.token) localStorage.setItem("token", res.token);
      } catch (_) {}
      location.href = HOME[role];
    } catch (err) {
      showMsg(err.message);
      setLoading(false, label);
    }
  });
}
