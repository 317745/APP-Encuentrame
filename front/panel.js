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

      await load();
      showMsg(data.message || "Foto registrada con éxito.");
    } catch (err) {
      console.error(err);
      statusEl.textContent = err instanceof TypeError
        ? "No se pudo conectar con el servidor."
        : err.message;
    }
  }

  /* ---------- guía para tomar fotos (ventana emergente) ---------- */
  const guide = document.getElementById("guideModal");
  if (guide) {
    document.getElementById("guideClose").addEventListener("click", () => guide.close());
    guide.addEventListener("click", (e) => { if (e.target === guide) guide.close(); });
  }
  const openGuide = () => { if (guide && !guide.open) guide.showModal(); };
  document.querySelectorAll("[data-open-guide]").forEach(b => b.addEventListener("click", openGuide));

  /* ---------- eliminar foto ---------- */
  async function deletePhoto(cat, photo, btn, statusEl) {
    if (!photo || !photo.id) return;
    if (!confirm("¿Eliminar esta foto de " + (cat.name || "este gato") + "? Esta acción no se puede deshacer.")) return;

    btn.disabled = true;
    statusEl.textContent = "Eliminando foto…";
    try {
      const res = await fetch(API_BASE + CATS.deletePhoto(photo.id), { method: "DELETE" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data, res));

      await load();
      showMsg(data.msg || "Foto eliminada.");
    } catch (err) {
      console.error(err);
      btn.disabled = false;
      statusEl.textContent = err instanceof TypeError
        ? "No se pudo conectar con el servidor."
        : err.message;
    }
  }

  /* ---------- eliminar gato (con todas sus fotos) ---------- */
  async function deleteCat(cat, btn, statusEl) {
    const name = cat.name || "este gato";
    if (!confirm("¿Eliminar a " + name + " y todas sus fotos? Esta acción no se puede deshacer.")) return;

    btn.disabled = true;
    statusEl.textContent = "Eliminando gato…";
    try {
      const res = await fetch(API_BASE + CATS.deleteCat(cat.id), { method: "DELETE" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data, res));

      await load();
      showMsg(name + " fue eliminado.");
    } catch (err) {
      console.error(err);
      btn.disabled = false;
      statusEl.textContent = err instanceof TypeError
        ? "No se pudo conectar con el servidor."
        : err.message;
    }
  }

  /* ---------- coincidencias en ventana emergente (solo usuarios) ---------- */
  const modal = document.getElementById("matchesModal");
  const modalTitle = document.getElementById("matchesTitle");
  const modalBody = document.getElementById("matchesBody");
  if (modal) {
    document.getElementById("matchesClose").addEventListener("click", () => modal.close());
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.close(); });   // clic en el fondo
  }

  const note = (text) => h("p", { class: "matches__note" }, text);
  const ORG_LABEL = { foundation: "Fundación", collaborator: "Colaborador" };
  const isEmail = (s) => typeof s === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

  function longDate(iso) {
    const d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" });
  }

  // Tiempo transcurrido desde iso hasta hoy: "2 años, 3 meses y 5 días"
  function elapsed(iso) {
    const start = new Date(iso);
    if (isNaN(start)) return null;
    const now = new Date();
    let y = now.getFullYear() - start.getFullYear();
    let m = now.getMonth() - start.getMonth();
    let d = now.getDate() - start.getDate();
    if (d < 0) { m--; d += new Date(now.getFullYear(), now.getMonth(), 0).getDate(); }
    if (m < 0) { y--; m += 12; }
    if (y < 0) return null;
    const parts = [];
    if (y) parts.push(y + (y === 1 ? " año" : " años"));
    if (m) parts.push(m + (m === 1 ? " mes" : " meses"));
    if (d) parts.push(d + (d === 1 ? " día" : " días"));
    return parts.join(", ").replace(/, ([^,]*)$/, " y $1");   // "" si es de hoy
  }

  function orgBlock(m, cat) {
    const label = ORG_LABEL[m.actor_type] || "Quien lo reportó";
    const box = h("div", { class: "match__org" },
      h("p", {}, h("strong", {}, m.actor_name ? label + ": " + m.actor_name : label)));

    const since = m.created_at ? longDate(m.created_at) : "";
    if (since) {
      const t = elapsed(m.created_at);
      box.append(h("p", {}, "Activa desde " + since + " (" + (t ? "hace " + t : "hoy") + ")"));
    }

    if (isEmail(m.email)) {
      const subject = encodeURIComponent("Posible coincidencia: " + m.name);
      const body = encodeURIComponent("Hola, creo que su gato «" + m.name + "» podría ser mi gato «" + (cat.name || "") + "». ¿Podemos hablar?");
      box.append(
        h("p", {}, "Correo: " + m.email),
        h("a", { class: "btn btn--small", href: "mailto:" + m.email + "?subject=" + subject + "&body=" + body }, "Contactar")
      );
    } else {
      box.append(h("p", {}, "Contacto no disponible."));
    }
    return box;
  }

  function matchItem(m, cat) {
    const pct = Math.max(0, Math.min(100, Number(m.similitud) || 0));
    const photo = m.image_url
      ? h("img", { class: "match__img", src: m.image_url, alt: "Foto de " + m.name, loading: "lazy" })
      : h("div", { class: "match__img match__img--empty" }, "Sin foto");
    return h("li", { class: "match" },
      h("div", { class: "match__top" },
        photo,
        h("div", { class: "match__info" },
          h("strong", {}, m.name),
          h("div", { class: "match__bar" }, h("span", { style: "width:" + pct + "%" }))),
        h("span", { class: "match__pct" }, Math.round(pct) + "%")),
      orgBlock(m, cat));
  }

  function renderMatches(cat, matches) {
    const list = h("ul", { class: "matches__list" });
    matches.forEach(m => list.append(matchItem(m, cat)));
    modalBody.replaceChildren(list, note("Es una sugerencia automática: confirma comparando las fotos antes de contactar."));
  }

  async function openMatches(cat, count) {
    if (!modal) return;
    modalTitle.textContent = "Posibles coincidencias para " + (cat.name || "tu gato");
    modalBody.replaceChildren(note(count ? "Buscando coincidencias…" : "Sube al menos una foto de este gato para buscar coincidencias."));
    if (!modal.open) modal.showModal();
    if (!count) return;

    try {
      const res = await fetch(API_BASE + CATS.matches(cat.id));
      const data = await res.json().catch(() => ({}));

      if (res.status === 404) {
        modalBody.replaceChildren(note("Todavía estamos procesando las fotos de este gato. Intenta de nuevo en unos segundos."));
        return;
      }
      if (!res.ok) throw new Error(errorText(data, res));

      const matches = data.matches || [];
      if (!matches.length) {
        modalBody.replaceChildren(note("No encontramos coincidencias por ahora."));
        return;
      }
      renderMatches(cat, matches);
    } catch (err) {
      console.error(err);
      modalBody.replaceChildren(note(err instanceof TypeError
        ? "No se pudo conectar con el servidor."
        : "No pudimos buscar coincidencias: " + err.message));
    }
  }

  /* ---------- tarjeta de gato ---------- */
  function renderCat(cat) {
    const name = cat.name || "Gato sin nombre";
    // Acepta ["url", ...] o [{ id, image_url }, ...]; solo con id se puede eliminar
    const photos = (cat.photos || []).map(ph =>
      typeof ph === "string" ? { id: null, url: ph } : { id: ph.id || null, url: ph.image_url || ph.url });
    const count = cat.photos_count ?? photos.length;

    // foto principal + miniaturas + eliminar
    let gallery;
    if (photos.length) {
      let current = 0;
      const main = h("img", { class: "cat__main", src: photos[0].url, alt: "Foto de " + name, loading: "lazy" });
      const thumbs = h("div", { class: "cat__thumbs" });
      const delBtn = h("button", { type: "button", class: "btn btn--ghost btn--small btn--danger" }, "Eliminar esta foto");

      photos.forEach((ph, i) => {
        const btn = h("button", { type: "button", class: "cat__thumb" + (i === 0 ? " is-active" : ""), "aria-label": "Ver foto " + (i + 1) },
          h("img", { src: ph.url, alt: "", loading: "lazy" }));
        btn.addEventListener("click", () => {
          current = i;
          main.src = ph.url;
          thumbs.querySelectorAll(".cat__thumb").forEach(b => b.classList.remove("is-active"));
          btn.classList.add("is-active");
          delBtn.hidden = !photos[current].id;
        });
        thumbs.append(btn);
      });

      delBtn.hidden = !photos[0].id;
      delBtn.addEventListener("click", () => deletePhoto(cat, photos[current], delBtn, statusEl));
      gallery = h("div", {}, main, thumbs, delBtn);
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

    // botón de coincidencias: solo para usuarios
    let matchesBtn = null;
    if (user.role === "user" && modal) {
      matchesBtn = h("button", { type: "button", class: "btn btn--ghost btn--small" }, "Ver coincidencias");
      matchesBtn.addEventListener("click", () => openMatches(cat, count));
    }

    const guideBtn = guide ? h("button", { type: "button", class: "link-btn" }, "Guía para tomar fotos") : null;
    if (guideBtn) guideBtn.addEventListener("click", openGuide);

    const delCatBtn = h("button", { type: "button", class: "btn btn--ghost btn--small btn--danger" }, "Eliminar gato");
    delCatBtn.addEventListener("click", () => deleteCat(cat, delCatBtn, statusEl));

    return h("article", { class: "card cat" },
      h("div", { class: "cat__head" },
        h("h2", { class: "card__title" }, name),
        h("span", { class: "cat__count" }, count + "/" + MAX_PHOTOS + " fotos")),
      gallery, dl,
      h("div", { class: "cat__actions" }, upload, matchesBtn, delCatBtn),
      guideBtn,
      statusEl);
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
      const comuna = Number(document.getElementById("catComuna").value);
      if (!name) return showMsg("Escribe el nombre del gato.", "error");
      if (!Number.isInteger(comuna) || comuna < 1 || comuna > 22) return showMsg("Selecciona una comuna del 1 al 22.", "error");

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
