// Manejo de sesión en el front (usa lo que guarda auth.js en localStorage)
const HOMES = { user: "usuarios.html", fundation: "refugios.html", collaborator: "colaboradores.html" };

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
  // Úsalo al inicio de páginas privadas: Session.requireAuth("user" | "fundation" | "collaborator")
  requireAuth(role) {
    const u = this.getUser();
    if (!u || (role && u.role !== role)) {
      location.href = HOMES[role] || "usuarios.html";
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const user = Session.getUser();
  if (!user) return;

  const page = location.pathname.split("/").pop();

  // Con sesión activa no tiene sentido ver los registros
  if (["register.html", "register-refugio.html", "register-colaborador.html"].includes(page)) {
    location.replace(HOMES[user.role] || "index.html");
    return;
  }

  const firstName = (user.name || user.email || "").split(" ")[0];

  // Menú: solo el botón de cerrar sesión
  const nav = document.getElementById("nav");
  if (nav) {
    const out = document.createElement("button");
    out.type = "button";
    out.className = "btn btn--ghost nav__cta";
    out.textContent = "Cerrar sesión";
    out.addEventListener("click", () => Session.logout());
    nav.append(out);
  }

  // Con sesión del rol de la página: se cambia la bienvenida por el dashboard (panel.js lo llena)
  const landing = document.getElementById("landing");
  const dashboard = document.getElementById("dashboard");
  if (landing && dashboard && landing.dataset.role === user.role) {
    landing.hidden = true;
    dashboard.hidden = false;
  }
});
