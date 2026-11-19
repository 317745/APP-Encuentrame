// Manejo de sesión en el front (usa lo que guarda auth.js en localStorage)
const Session = {
  getUser() {
    try {
      const u = JSON.parse(localStorage.getItem("user"));
      if (u && !u.role) u.role = "user";   // sesiones viejas
      return u;
    } catch { return null; }
  },
  getToken() {
    try { return localStorage.getItem("token"); } catch { return null; }
  },
  isLoggedIn() { return !!this.getUser(); },
  logout() {
    try { localStorage.removeItem("user"); localStorage.removeItem("token"); } catch {}
    location.href = "index.html";
  },
  // Úsalo al inicio de páginas privadas: Session.requireAuth("user") o ("fundation")
  requireAuth(role) {
    const u = this.getUser();
    if (!u || (role && u.role !== role)) {
      location.href = role === "fundation" ? "refugios.html" : "usuarios.html";
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const user = Session.getUser();
  if (!user) return;

  const homes = { user: "usuarios.html", fundation: "refugios.html" };
  const page = location.pathname.split("/").pop();

  // Con sesión activa no tiene sentido ver los registros
  if (page === "register.html" || page === "register-refugio.html") {
    location.replace(homes[user.role]);
    return;
  }

  const firstName = (user.name || user.email || "").split(" ")[0];

  // Header: saludo + cerrar sesión
  const nav = document.getElementById("nav");
  if (nav) {
    const box = document.createElement("div");
    box.className = "user-box";

    const hello = document.createElement("span");
    hello.className = "user-box__name";
    hello.textContent = "Hola, " + firstName;

    const out = document.createElement("button");
    out.type = "button";
    out.className = "btn btn--ghost";
    out.textContent = "Cerrar sesión";
    out.addEventListener("click", () => Session.logout());

    box.append(hello, out);
    nav.append(box);
  }

  // Página Usuarios: con sesión de usuario se muestra el dashboard (panel.js lo llena)
  const landing = document.getElementById("landing");
  const dashboard = document.getElementById("dashboard");
  if (landing && dashboard && landing.dataset.role === user.role) {
    landing.hidden = true;
    dashboard.hidden = false;
  }

  // Página Refugios: cambia el login por el panel si el rol coincide: cambia el login por el panel si el rol coincide
  const loginCard = document.getElementById("loginCard");
  const panel = document.getElementById("userPanel");
  if (loginCard && panel && loginCard.dataset.role === user.role) {
    loginCard.hidden = true;
    panel.hidden = false;
    document.getElementById("userGreeting").textContent = "Hola, " + firstName;
  }
});
