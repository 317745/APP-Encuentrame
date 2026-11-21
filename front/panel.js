// Panel del usuario: muestra sus gatos con fotos (GET /cats/{actor_id}/cat_photos)
(function () {
  const dash = document.getElementById("dashboard");
  if (!dash) return;

  const user = Session.getUser();
  if (!user || user.role !== dash.dataset.role) return;

  const MAX_PHOTOS = 5;               // el backend también lo valida
  const HIDDEN_FIELDS = ["id", "actor_id", "actor_type", "photos", "photos_count", "name", "created_at"];

  const grid = document.getElementById("catGrid");
  const dashMsg = document.getElementById("dashMsg");
  const summary = document.getElementById("dashSummary");

  document.getElementById("dashName").textContent = "Hola, " + (user.name || "bienvenido");
  document.getElementById("dashEmail").textContent = user.email || "";
  const meta = document.getElementById("dashMeta");

  // "Miembro desde": viene en lo que devuelve el login (created_at), sin endpoint extra
  if (user.created_at && meta) {
    meta.textContent = "Miembro desde " + new Date(user.created_at)
      .toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" });
  }

  /* ---------- helpers ---------- */
  function h(tag, attrs = {}, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v);
    }
    el.append(...kids.filter(Boolean));
    return el;
  }
  const label = (k) => { const t = k.replace(/_/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };
  const fmt = (v) => (typeof v === "boolean" ? (v ? "Sí" : "No") : String(v));

  function showMsg(text, type = "ok") {
    dashMsg.textContent = text;
    dashMsg.className = "form-msg form-msg--" + type;
  }

  function errorText(data, res) {
    return typeof data.detail === "string" ? data.detail : "Error " + res.status;
  }

  /* ---------- subir foto ---------- */
  async function uploadPhoto(cat, file, statusEl) {
    if (file.type !== "image/jpeg") {
      statusEl.textContent = "Solo se aceptan fotos JPG o JPEG.";
      return;
    }
    const fd = new FormData();
    fd.append("cat_id", cat.id);
    fd.append("file", file);

    statusEl.textContent = "Subiendo y analizando la foto…";
    try {
      const res = await fetch(API_BASE + CATS.uploadPhoto, { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data, res));

      const tip = typeof data.info === "string" ? data.info.replace(/\s+/g, " ").trim() : "";
      await load();
      showMsg([data.message, tip].filter(Boolean).join(" "));
    } catch (err) {
      console.error(err);
      statusEl.textContent = err instanceof TypeError
        ? "No se pudo conectar con el servidor."
        : err.message;
    }
  }

  /* ---------- tarjeta de gato ---------- */
  function renderCat(cat) {
    const name = cat.name || "Gato sin nombre";
    const photos = cat.photos || [];
    const count = cat.photos_count ?? photos.length;

    // foto principal + miniaturas
    let gallery;
    if (photos.length) {
      const main = h("img", { class: "cat__main", src: photos[0], alt: "Foto de " + name, loading: "lazy" });
      const thumbs = h("div", { class: "cat__thumbs" });
      photos.forEach((url, i) => {
        const btn = h("button", { type: "button", class: "cat__thumb" + (i === 0 ? " is-active" : ""), "aria-label": "Ver foto " + (i + 1) },
          h("img", { src: url, alt: "", loading: "lazy" }));
        btn.addEventListener("click", () => {
          main.src = url;
          thumbs.querySelectorAll(".cat__thumb").forEach(b => b.classList.remove("is-active"));
          btn.classList.add("is-active");
        });
        thumbs.append(btn);
      });
      gallery = h("div", {}, main, thumbs);
    } else {
      gallery = h("div", { class: "cat__empty" }, "Aún sin fotos");
    }

    // datos del gato (todo lo que traiga el backend, menos lo técnico)
    const dl = h("dl", { class: "cat__fields" });
    for (const [k, v] of Object.entries(cat)) {
      if (HIDDEN_FIELDS.includes(k) || v === null || v === "") continue;
      dl.append(h("dt", {}, label(k)), h("dd", {}, fmt(v)));
    }
    if (cat.created_at) {
      dl.append(h("dt", {}, "Registrado"), h("dd", {}, new Date(cat.created_at).toLocaleDateString("es-CO")));
    }

    // subir foto (se oculta al llegar al máximo)
    const statusEl = h("p", { class: "cat__status", role: "status" });
    let upload;
    if (count < MAX_PHOTOS) {
      const input = h("input", { type: "file", accept: "image/jpeg", class: "cat__file" });
      input.addEventListener("change", () => { if (input.files[0]) uploadPhoto(cat, input.files[0], statusEl); });
      upload = h("label", { class: "btn btn--small" }, "Subir foto", input);
    } else {
      upload = h("p", { class: "cat__max" }, "Llegaste al máximo de " + MAX_PHOTOS + " fotos");
    }

    return h("article", { class: "card cat" },
      h("div", { class: "cat__head" },
        h("h2", { class: "card__title" }, name),
        h("span", { class: "cat__count" }, count + "/" + MAX_PHOTOS + " fotos")),
      gallery, dl, upload, statusEl);
  }

  /* ---------- cargar ---------- */
  async function load() {
    grid.replaceChildren(h("p", { class: "dash__state" }, "Cargando gatos…"));
    try {
      const res = await fetch(API_BASE + CATS.byActor(user.id));
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data, res));

      const cats = (data.info && data.info.cats) || [];
      const totalPhotos = cats.reduce((n, c) => n + (c.photos_count ?? (c.photos || []).length), 0);
      summary.textContent = (cats.length === 1 ? "1 gato registrado" : cats.length + " gatos registrados")
        + " · " + totalPhotos + (totalPhotos === 1 ? " foto" : " fotos");

      if (!cats.length) {
        grid.replaceChildren(h("p", { class: "dash__state" }, "Aún no hay gatos registrados."));
        return;
      }
      grid.replaceChildren(...cats.map(renderCat));
    } catch (err) {
      console.error(err);
      summary.textContent = "";
      grid.replaceChildren(h("p", { class: "dash__state dash__state--error" },
        err instanceof TypeError
          ? "No se pudo conectar con el servidor. Revisa que la API esté encendida."
          : "No pudimos cargar los gatos: " + err.message));
    }
  }

  /* ---------- registrar gato ---------- */
  const catForm = document.getElementById("catForm");
  if (catForm) {
    const btn = catForm.querySelector("button");
    catForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("catName").value.trim();
      const comuna = document.getElementById("catComuna").value.trim();
      if (!name || !comuna) return showMsg("Escribe el nombre y la comuna.", "error");

      btn.disabled = true;
      btn.textContent = "Registrando…";
      try {
        const res = await fetch(API_BASE + CATS.registerCat, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ actor_id: user.id, actor_type: ACTOR_TYPE[user.role], name, comuna })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = errorText(data, res);
          throw new Error(/duplicate|unique|idx_actor_cat_name/i.test(detail)
            ? "Ya hay un gato registrado con ese nombre."
            : detail);
        }
        catForm.reset();
        await load();
        showMsg("¡Gato registrado! Ahora sube sus fotos desde su tarjeta.");
      } catch (err) {
        console.error(err);
        showMsg(err instanceof TypeError ? "No se pudo conectar con el servidor." : err.message, "error");
      } finally {
        btn.disabled = false;
        btn.textContent = "Registrar gato";
      }
    });
  }

  load();
})();
