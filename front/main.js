// Menú móvil
const menuBtn = document.getElementById("menuBtn");
const nav = document.getElementById("nav");

menuBtn.addEventListener("click", () => {
  const open = nav.classList.toggle("is-open");
  menuBtn.setAttribute("aria-expanded", open);
});

// Marca como activo el link de la página actual
const current = location.pathname.split("/").pop() || "index.html";
const activeMap = { "register.html": "usuarios.html", "register-refugio.html": "refugios.html" };
const activePage = activeMap[current] || current;
document.querySelectorAll(".nav__link").forEach(link => {
  link.classList.toggle("is-active", link.getAttribute("href") === activePage);
});
