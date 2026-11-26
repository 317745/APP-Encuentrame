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
  },
  collaborator: {
    registerAuth:    "/collaborator/register/auth/",
    registerProfile: "/collaborator/register/profile/",
    login:           "/collaborator/login/"
  }
};

// A qué página va cada rol después de iniciar sesión
const HOME = { user: "usuarios.html", fundation: "refugios.html", collaborator: "colaboradores.html" };

// Endpoints de gatos
// Valor de actor_type que guarda el backend en cada gato
const ACTOR_TYPE = { user: "user", fundation: "foundation", collaborator: "collaborator" };

const CATS = {
  byActor:     (actorId) => `/cats/${actorId}/cat_photos`,
  registerCat: "/cats/register/cat/",
  matches:     (catId) => `/cats/matches/cat/${catId}`,
  // Fotos de UN gato. Si lo pones en null se usa GET /cats/photos/ (todas) y se filtra por cat_id en el front.
  photosByCat: (catId) => `/cats/${catId}/photos/`,
  allPhotos:   "/cats/photos/",
  uploadPhoto: "/cats/register/photo/",
  deletePhoto: (photoId) => `/cats/delete_photo/${photoId}`,
  deleteCat:   (catId) => `/cats/delete_cat/${catId}`
};

