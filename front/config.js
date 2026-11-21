// Cambia esto por la URL de tu API FastAPI
const API_BASE = "http://localhost:8000";

const ENDPOINTS = {
  user: {
    registerAuth:    "/users/register/auth/",
    registerProfile: "/users/register/profile/",
    login:           "/users/login/"
  },
  fundation: {
    registerAuth:    "/fundations/register/auth/",
    registerProfile: "/fundations/register/profile/",
    login:           "/fundations/login/"
  }
};

// A qué página va cada rol después de iniciar sesión
const HOME = { user: "usuarios.html", fundation: "refugios.html" };

// Endpoints de gatos
// Valor de actor_type que guarda el backend en cada gato
const ACTOR_TYPE = { user: "user", fundation: "foundation" };

const CATS = {
  byActor:     (actorId) => `/cats/${actorId}/cat_photos`,
  registerCat: "/cats/register/cat/",
  uploadPhoto: "/cats/register/photo/"
};

