/* ============================================================
   NEXORA front-end application
   ============================================================ */
(function () {
  "use strict";

  // ---- State ----
  const state = {
    currency: "INR",          // "INR" | "USD"
    filters: { accessibility: new Set(), stars: new Set(), maxPrice: 15000, sort: "featured" },
    hotels: [],
    activeHotel: null,
    selectedRoom: null,
    meta: null,
    usdPerInr: 83.5,
  };

  // ---- DOM refs ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const el = {
    results: $("#results"),
    resultsSection: $("#results-section"),
    resultsCount: $("#results-count"),
    resultsTitle: $("#results-title"),
    noResults: $("#no-results"),
    detailSection: $("#detail"),
    filtersPanel: $("#filters-panel"),
    toggleFilters: $("#toggle-filters"),
    filterCount: $("#filter-count"),
    accChips: $("#acc-chips"),
    maxPrice: $("#max-price"),
    priceVal: $("#price-val"),
    sort: $("#sort"),
    modal: $("#modal"),
    modalContent: $("#modal-content"),
    toast: $("#toast"),
    cityList: $("#city-list"),
    menuToggle: $("#menu-toggle"),
    mobileNav: $("#main-nav"),
  };

  // ---- Utilities ----
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  function inr(n) { return "₹" + Number(n).toLocaleString("en-IN"); }
  function usd(n) { return "$" + Number(n).toFixed(2); }
  function money(n) { return state.currency === "USD" ? usd(n / state.usdPerInr) : inr(n); }
  function moneyNote(n) {
    // shows secondary currency on next line
    return state.currency === "USD"
      ? '<small class="usd">' + inr(n) + "</small>"
      : '<small class="usd">≈ ' + usd(n / state.usdPerInr) + "</small>";
  }
  function starStr(n) { return "★".repeat(Math.min(n, 5)) + "☆".repeat(Math.max(0, 5 - n)); }

  function showToast(msg, ms) {
    el.toast.textContent = msg;
    el.toast.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => { el.toast.hidden = true; }, ms || 3500);
  }

  // ---- API helpers ----
  async function api(path, opts) {
    const r = await fetch(path, opts);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || "Request failed");
    return data;
  }
  const GET = (p) => api(p);
  const POST = (p, body) =>
    api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  // ---- Currency toggle ----
  function setCurrency(cur) {
    state.currency = cur;
    $("#cur-inr").classList.toggle("active", cur === "INR");
    $("#cur-usd").classList.toggle("active", cur === "USD");
    $("#cur-inr").setAttribute("aria-pressed", cur === "INR");
    $("#cur-usd").setAttribute("aria-pressed", cur === "USD");
    // Re-render current view
    if (state.activeHotel) renderDetail(state.activeHotel);
    else renderResults();
    // update price display on range label
    el.priceVal.textContent = inr(Number(el.maxPrice.value));
  }

  // ---- Load meta + cities ----
  async function loadMeta() {
    try {
      const [m, c] = await Promise.all([GET("/api/meta"), GET("/api/cities")]);
      state.meta = m;
      state.usdPerInr = m.usd_per_inr;
      // populate city datalist
      el.cityList.innerHTML = c.cities
        .map((x) => `<option value="${esc(x.city)}">${esc(x.city)}, ${esc(x.state)}</option>`).join("");
      // accessibility chips
      const keys = m.accessibility_keys;
      el.accChips.innerHTML = Object.keys(keys).map((k) =>
        `<button type="button" class="chip" data-acc="${k}" aria-pressed="false">${esc(keys[k])}</button>`
      ).join("");
      // wire chips
      $$("#acc-chips .chip").forEach((b) =>
        b.addEventListener("click", () => {
          const k = b.dataset.acc;
          if (state.filters.accessibility.has(k)) { state.filters.accessibility.delete(k); b.setAttribute("aria-pressed", "false"); }
          else { state.filters.accessibility.add(k); b.setAttribute("aria-pressed", "true"); }
          updateFilterCount();
          renderResults();
        })
      );
    } catch (e) {
      console.error(e);
      el.resultsCount.textContent = "Could not load data.";
    }
  }

  function updateFilterCount() {
    const n = state.filters.accessibility.size + state.filters.stars.size;
    el.filterCount.hidden = n === 0;
    el.filterCount.textContent = n;
  }

  // ---- Build search query ----
  function buildQuery() {
    const q = $("#q").value.trim();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (state.filters.accessibility.size) params.set("accessibility", [...state.filters.accessibility].join(","));
    if (state.filters.stars.size) params.set("stars", [...state.filters.stars].sort().join(","));
    if (state.filters.maxPrice < 15000) params.set("max_price", state.filters.maxPrice);
    params.set("sort", state.filters.sort);
    return params.toString();
  }

  async function renderResults() {
    try {
      const qs = buildQuery();
      const data = await GET("/api/hotels?" + qs);
      state.hotels = data.hotels;
      state.usdPerInr = data.usd_per_inr;
      el.resultsCount.textContent = `${data.count} hotel${data.count === 1 ? "" : "s"} available`;
      el.noResults.hidden = data.count > 0;
      if (!data.count) { el.results.innerHTML = ""; return; }
      el.results.innerHTML = data.hotels.map(cardHTML).join("");
      wireCards();
    } catch (e) {
      console.error(e);
      el.resultsCount.textContent = "Error loading hotels.";
    }
  }

  function cardHTML(h) {
    const accChips = (h.access_summary || [])
      .filter((a) => ["wheelchair_accessible", "elevator", "lifts_ramps", "accessible_bathrooms", "accessible_rooms", "staff_assistance"]
        .includes(a.key))
      .map((a) => `<span class="acc-tag strong">${esc(a.label)}</span>`).join("");
    const more = (h.amenities || []).slice(0, 3).map((a) => `<span class="acc-tag">${esc(a)}</span>`).join("");
    return `
      <article class="hotel-card" aria-label="${esc(h.name)}">
        <figure class="img"><img src="${esc(h.photo)}" alt="Photo of ${esc(h.name)} in ${esc(h.city)}" loading="lazy" /></figure>
        <div class="card-body">
          <div class="card-top">
            <span class="stars" aria-label="${h.stars} star hotel">${starStr(h.stars)}</span>
            <span class="rating-badge">${esc(h.badge)} · ${h.rating.toFixed(1)}</span>
          </div>
          <p class="card-title">${esc(h.name)}</p>
          <p class="card-loc">${esc(h.city)}, ${esc(h.state)} · ${esc(h.type)}</p>
          <span class="type-tag">${esc(h.type)}</span>
          <div class="acc-tags">${accChips}${more}</div>
          <div class="card-foot">
            <div class="price">${money(h.price_inr)} ${moneyNote(h.price_inr)}</div>
            <button class="btn btn-primary" data-view="${h.id}" type="button">View</button>
          </div>
        </div>
      </article>`;
  }

  function wireCards() {
    $$('[data-view]').forEach((b) =>
      b.addEventListener("click", () => { location.hash = "#/hotel/" + b.dataset.view; })
    );
  }

  // ---- Detail page ----
  async function openHotel(id) {
    el.resultsSection.hidden = true;
    el.detailSection.hidden = false;
    try {
      const data = await GET("/api/hotels/" + id);
      state.activeHotel = data;
      renderDetail(data);
      window.scrollTo({ top: 0 });
    } catch (e) {
      el.resultsSection.hidden = false;
      el.detailSection.hidden = true;
      showToast(e.message);
    }
  }

  function renderDetail(h) {
    el.detailSection.setAttribute("aria-label", "Details for " + h.name);

    const accKeys = state.meta ? state.meta.accessibility_keys : {};
    const accOnes = h.accessibility || {};
    const accSummary = Object.keys(accKeys).map((k) => {
      const on = accOnes[k] === true;
      return `<div class="cell"><span>${esc(accKeys[k])}</span><span class="${on ? "acc-chip" : "acc-chip no"}">${on ? "Yes" : "No"}</span></div>`;
    }).join("");

    const rooms = (h.rooms || []).map((r) => `
      <div class="room-card">
        <span class="rname">${esc(r.type)}</span>
        <span class="rdesc">${esc(r.beds)} · up to ${r.guests} guests</span>
        <span class="rprice">${money(r.price_inr)} <span class="usd">${moneyNote(r.price_inr)}</span></span>
        <span class="detail">${(r.amenities || []).map((a) => esc(a)).join(" · ")}</span>
        <button class="btn btn-primary btn-block" data-bookroom="${esc(r.type)}" type="button">Book this room</button>
      </div>`).join("");

    const menu = (h.food_menu || []).map((cat) => `
      <section>
        <h3>${esc(cat.category)}</h3>
        <table class="menu-table"><thead><tr><th>Item</th><th>Price</th></tr></thead><tbody>
          ${(cat.items || []).map((it) => `
            <tr><td><span class="${it.veg ? "veg" : "nonveg"}">●</span> ${esc(it.name)}</td>
            <td>${money(it.price_inr)} <span class="usd">(${state.currency === "USD" ? inr(it.price_inr) : usd(it.price_inr / state.usdPerInr)})</span></td></tr>`).join("")}
        </tbody></table>
      </section>`).join("");

    const nearby = (list, extra) => (list || []).map((n) =>
      `<div class="nearby-item"><span>${esc(n.name)}</span><span class="d">${n.distance_km} km${extra ? " · " + esc(extra(n)) : ""}</span></div>`
    ).join("");

    // ---- Need Help? Contact Hotel ---- (contact fields from backend; never invent data)
    const cPhone = (h.phone || "").toString();
    const cEmail = (h.email || "").toString();
    const cWeb = (h.website || "").toString();
    const helpBlock = `
      <div class="panel nx-help" role="region" aria-label="Need help? Contact the hotel">
        <h2>🆘 Need Help? Contact Hotel</h2>
        <p style="color:var(--muted);font-size:.9rem">For urgent assistance or accessibility questions, reach the hotel directly. Fields marked "not available" mean this hotel has not provided verified contact details.</p>
        <div class="nx-help-rows">
          <div class="nx-help-row"><span class="nx-help-label">📞 Phone</span><span class="nx-help-val">${cPhone ? esc(cPhone) : "Contact details not available"}</span></div>
          <div class="nx-help-row"><span class="nx-help-label">✉️ Email</span><span class="nx-help-val">${cEmail ? esc(cEmail) : "Contact details not available"}</span></div>
          <div class="nx-help-row"><span class="nx-help-label">🌐 Website</span><span class="nx-help-val">${cWeb ? esc(cWeb) : "Contact details not available"}</span></div>
          <div class="nx-help-row"><span class="nx-help-label">📍 Address</span><span class="nx-help-val">${esc(h.address)}</span></div>
        </div>
        <div class="nx-help-btns">
          ${cPhone ? `<a class="nx-help-btn" href="tel:${esc(cPhone)}" aria-label="Call ${esc(h.name)}">📞 Call Hotel</a>` : `<span class="nx-help-btn disabled" role="button" aria-disabled="true" tabindex="-1">📞 Call Hotel</span>`}
          ${cEmail ? `<a class="nx-help-btn" href="mailto:${esc(cEmail)}" aria-label="Email ${esc(h.name)}">✉️ Email Hotel</a>` : `<span class="nx-help-btn disabled" role="button" aria-disabled="true" tabindex="-1">✉️ Email Hotel</span>`}
          ${cWeb ? `<a class="nx-help-btn" href="${esc(cWeb)}" target="_blank" rel="noopener noreferrer" aria-label="Open ${esc(h.name)} website">🌐 Visit Website</a>` : `<span class="nx-help-btn disabled" role="button" aria-disabled="true" tabindex="-1">🌐 Visit Website</span>`}
          <a class="nx-help-btn secondary" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&destination=${typeof h.latitude === "number" && typeof h.longitude === "number" ? h.latitude + "," + h.longitude : encodeURIComponent(h.name + ", " + h.city)}" aria-label="Get directions to ${esc(h.name)}">🗺️ Get Directions</a>
        </div>
        <p style="color:var(--muted);font-size:.8rem;margin-top:.6rem">🗺️ Directions open Google Maps using this hotel's exact location.</p>
      </div>`;

    el.detailSection.innerHTML = `
      <a class="back-link" href="#/home">← Back to results</a>
      <div class="detail-hero">
        <figure class="photo" style="margin:0">
          <img src="${esc(h.photo)}" alt="Photo of ${esc(h.name)}" />
        </figure>
        <div class="detail-info">
          <div class="detail-meta">
            <span class="stars" aria-label="${h.stars} star">${starStr(h.stars)}</span>
            <span class="rating-badge">${esc(h.badge)} · ${h.rating.toFixed(1)}</span>
            <span class="tag">${esc(h.type)}</span>
          </div>
          <h1>${esc(h.name)}</h1>
          <p class="card-loc">${esc(h.address)}</p>
          <p>${esc(h.description)}</p>
          <div class="section-label">Accessibility summary</div>
          <div class="amenity-wrap">${(h.access_summary || []).slice(0, 10).map((a) => `<span class="acc-chip">${esc(a.label)}</span>`).join("")}</div>
          <div class="section-label">Amenities</div>
          <div class="amenity-wrap">${(h.amenities || []).map((a) => `<span class="amenity">${esc(a)}</span>`).join("")}</div>
          <div class="price-box">
            <div><span class="big">${money(h.price_inr)}</span><span class="usd">${state.currency === "USD" ? inr(h.price_inr) : usd(h.price_inr / state.usdPerInr)} / night</span></div>
            <button class="btn btn-primary" data-scrollrooms type="button">View rooms</button>
          </div>
        </div>
      </div>

      <div class="detail-sections">
        ${helpBlock}

        <div class="panel" id="rooms-section">
          <h2>Rooms &amp; prices</h2>
          <p style="color:var(--muted);font-size:.9rem">Check-in ${esc(h.check_in)} · Check-out ${esc(h.check_out)}</p>
          <div class="room-grid">${rooms}</div>
        </div>

        <div class="panel">
          <h2>Accessibility features</h2>
          <div class="acc-table">${accSummary}</div>
        </div>

        <div class="panel">
          <h2>Food menu</h2>
          <p style="color:var(--muted);font-size:.9rem">Sample menu from the hotel restaurant.</p>
          ${menu}
        </div>

        <div class="panel">
          <h2>Nearby — what's around you</h2>
          <div class="section-label">🏛️ Famous places</div>
          <div class="nearby">${nearby(h.nearby_places, (n) => n.category)}</div>
          <div class="section-label">🏥 Hospitals</div>
          <div class="nearby">${nearby(h.nearby_hospitals)}</div>
          <div class="section-label">🍽️ Restaurants</div>
          <div class="nearby">${nearby(h.nearby_restaurants, (n) => n.cuisine + " · " + n.price)}</div>
          <div class="section-label">🚆 Transport</div>
          <div class="nearby">${nearby(h.nearby_transport, (n) => n.type)}</div>
        </div>
      </div>

      <div class="detail-sections" style="grid-template-columns:1fr">
        <div class="panel book-card-sticky">
          <h2>Book your stay</h2>
          <p style="color:var(--muted);font-size:.9rem">Select a room above, complete your details, and get your accessibility blueprint instantly after confirmation.</p>
          <div id="quick-room"></div>
          <button class="btn btn-primary btn-block" data-bookguest type="button">Select a room to book</button>
        </div>
      </div>`;

    // wire detail actions
    $$('[data-scrollrooms]').forEach((b) => b.addEventListener("click", () =>
      document.querySelector("#rooms-section").scrollIntoView({ behavior: "smooth" })));
    $$('[data-bookroom]').forEach((b) => b.addEventListener("click", () => {
      state.selectedRoom = b.dataset.bookroom;
      openBooking(h, b.dataset.bookroom);
    }));
    $$('[data-bookguest]').forEach((b) => b.addEventListener("click", () => {
      // default to Accessible Room if present
      const defaultRoom = (h.rooms && h.rooms[0]) ? h.rooms[0].type : null;
      if (defaultRoom) {
        state.selectedRoom = defaultRoom;
        openBooking(h, defaultRoom);
      }
    }));
  }

  // ---- Booking modal ----
  function roomPrice(h, roomType) {
    const r = (h.rooms || []).find((x) => x.type === roomType) || h.rooms[0];
    return r ? r.price_inr : h.price_inr;
  }

  function openBooking(h, roomType) {
    const room = (h.rooms || []).find((x) => x.type === roomType) || h.rooms[0];
    const ci = $("#check-in").value;
    const co = $("#check-out").value;
    const nightPrice = room ? room.price_inr : h.price_inr;
    let nights = 1;
    if (ci && co) {
      const d1 = new Date(ci), d2 = new Date(co);
      if (d2 > d1) nights = Math.max(1, Math.round((d2 - d1) / 86400000));
    }
    const total = nightPrice * nights;

    el.modalContent.innerHTML = `
      <h2 id="modal-title">Book ${esc(h.name)}</h2>
      <div class="summary-box">
        <div class="summary-line"><span>Room</span><strong>${esc(room ? room.type : "Standard")}</strong></div>
        <div class="summary-line"><span>Location</span><span>${esc(h.city)}, ${esc(h.state)}</span></div>
        <div class="summary-line"><span>Nights</span><span>${nights}</span></div>
        <div class="summary-line"><span>Price / night</span><span>${money(nightPrice)}</span></div>
        <div class="summary-line total"><span>Total</span><span>${money(total)} <small>(${state.currency === "USD" ? inr(total) : usd(total / state.usdPerInr)})</small></span></div>
      </div>
      <form id="booking-form" class="form-grid" novalidate>
        <div class="form-field full"><label for="bk-name">Full name *</label><input id="bk-name" name="name" autocomplete="name" required /></div>
        <div class="form-field full"><label for="bk-email">Email *</label><input id="bk-email" name="email" type="email" autocomplete="email" required /></div>
        <div class="form-field full"><label for="bk-phone">Phone</label><input id="bk-phone" name="phone" type="tel" autocomplete="tel" /></div>
        <div class="form-field"><label for="bk-in">Check-in</label><input id="bk-in" type="date" value="${esc(ci)}" /></div>
        <div class="form-field"><label for="bk-out">Check-out</label><input id="bk-out" type="date" value="${esc(co)}" /></div>
        <div class="form-field full"><label for="bk-guests">Guests</label><select id="bk-guests">${[1,2,3,4,5,6].map(g=>`<option value="${g}" ${g===$("#guests").value?"selected":""}>${g} guest${g>1?"s":""}</option>`).join("")}</select></div>
        <div class="form-field full"><button class="btn btn-primary btn-block" type="submit">Confirm booking</button></div>
      </form>
      <p style="color:var(--muted);font-size:.85rem;margin-top:.6rem">After confirming, you'll receive a booking reference and an accessibility blueprint for this hotel.</p>`;

    showModal();
    setTimeout(() => $("#bk-name").focus(), 50);

    $("#booking-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = $("#bk-name").value.trim();
      const email = $("#bk-email").value.trim();
      if (!name || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        showToast("Please enter your name and a valid email.");
        return;
      }
      const btn = e.target.querySelector('button[type="submit"]');
      btn.disabled = true; btn.textContent = "Booking…";
      try {
        const res = await POST("/api/bookings", {
          hotel_id: h.id, room_type: roomType,
          guest_name: name, guest_email: email,
          guest_phone: $("#bk-phone").value.trim(),
          check_in: $("#bk-in").value, check_out: $("#bk-out").value,
          guests: Number($("#bk-guests").value),
        });
        showConfirmation(res);
      } catch (err) {
        showToast(err.message);
        btn.disabled = false; btn.textContent = "Confirm booking";
      }
    });
  }

  function showConfirmation(res) {
    const b = res.booking;
    const bp = res.blueprint_url;
    el.modalContent.innerHTML = `
      <div class="confirm">
        <span class="tick">✓</span>
        <h2 id="modal-title">Booking confirmed!</h2>
        <p>Thank you, ${esc(b.guest_name)}. Your accessible stay at <strong>${esc(b.hotel_name)}</strong> (${esc(b.city)}) is booked.</p>
        <div class="summary-box">
          <div class="summary-line"><span>Booking reference</span><span class="ref-code">${esc(b.ref)}</span></div>
          <div class="summary-line"><span>Room</span><span>${esc(b.room_type)}</span></div>
          <div class="summary-line"><span>Check-in → Check-out</span><span>${esc(b.check_in || "—")} → ${esc(b.check_out || "—")}</span></div>
          <div class="summary-line"><span>Guests</span><span>${b.guests}</span></div>
          <div class="summary-line total"><span>Total (${b.nights} night${b.nights>1?"s":""})</span><span>${money(b.price_inr)} (≈ ${usd(b.price_usd)})</span></div>
        </div>
        <div class="section-label">🗺️ Your accessibility blueprint</div>
        <div class="blueprint">
          <img src="${esc(bp)}" alt="Accessibility blueprint of ${esc(b.hotel_name)}" />
          <p><a href="${esc(bp)}" target="_blank" rel="noopener">Download blueprint (SVG)</a></p>
        </div>
        <button class="btn btn-primary" data-close type="button">Done</button>
      </div>`;
    showModal();
  }

  // ---- Modal helpers ----
  let lastFocus = null;
  function showModal() {
    lastFocus = document.activeElement;
    el.modal.hidden = false;
    document.body.style.overflow = "hidden";
    const panel = el.modal.querySelector(".modal-panel");
    if (panel) panel.focus();
  }
  function hideModal() {
    el.modal.hidden = true;
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }
  $$("[data-close]").forEach((b) => b.addEventListener("click", () => {
    // close button and backdrop both carry data-close
    hideModal();
  }));
  el.modal.querySelector(".modal-backdrop").addEventListener("click", hideModal);
  el.modal.querySelector(".modal-close").addEventListener("click", hideModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !el.modal.hidden) hideModal();
  });
  // re-wire dynamically injected [data-close] inside modal content
  el.modalContent.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]")) hideModal();
  });

  // ---- Filters wiring ----
  el.toggleFilters.addEventListener("click", () => {
    const open = el.filtersPanel.hidden;
    el.filtersPanel.hidden = !open;
    el.toggleFilters.setAttribute("aria-expanded", open);
  });

  // star chips (delegated)
  $("#stars-chips").addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (!b) return;
    const s = b.dataset.stars;
    const pressed = b.getAttribute("aria-pressed") === "true";
    if (pressed) { state.filters.stars.delete(s); b.setAttribute("aria-pressed", "false"); }
    else { state.filters.stars.add(s); b.setAttribute("aria-pressed", "true"); }
    updateFilterCount();
    renderResults();
  });

  el.maxPrice.addEventListener("input", () => {
    state.filters.maxPrice = Number(el.maxPrice.value);
    el.priceVal.textContent = inr(el.maxPrice.value);
  });
  el.maxPrice.addEventListener("change", renderResults);

  el.sort.addEventListener("change", () => { state.filters.sort = el.sort.value; renderResults(); });

  // ---- Search ----
  $("#search-form").addEventListener("submit", (e) => {
    e.preventDefault();
    renderResults();
  });

  // ---- Currency buttons ----
  $("#cur-inr").addEventListener("click", () => setCurrency("INR"));
  $("#cur-usd").addEventListener("click", () => setCurrency("USD"));

  // ---- Mobile nav ----
  el.menuToggle.addEventListener("click", () => {
    const open = el.mobileNav.classList.toggle("open");
    el.menuToggle.setAttribute("aria-expanded", open);
    el.mobileNav.hidden = !open;
  });

  // ---- Router (basic hash routing) ----
  function route() {
    const hash = location.hash || "#/home";
    const m = hash.match(/^#\/hotel\/(\d+)/);
    if (m) {
      openHotel(m[1]);
    } else {
      // show results
      el.resultsSection.hidden = false;
      el.detailSection.hidden = true;
      state.activeHotel = null;
      renderResults();
    }
  }
  window.addEventListener("hashchange", route);

  // ---- Init ----
  async function init() {
    await loadMeta();
    // set default dates (today → +2 days)
    const today = new Date();
    const fmt = (d) => d.toISOString().slice(0, 10);
    $("#check-in").value = fmt(today);
    const co = new Date(today); co.setDate(co.getDate() + 2);
    $("#check-out").value = fmt(co);
    route();
  }
  init();
})();
