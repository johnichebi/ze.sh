const token = localStorage.getItem("token");
if (!token) window.location.href = "/login.html";

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}), Authorization: "Bearer " + token };
  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login.html";
  }
  return res;
}

async function getMe() {
  const res = await api("/account/me");
  return res.ok ? res.json() : null;
}

async function getLiked() {
  const res = await api("/likes/me");
  return new Set(res.ok ? await res.json() : []);
}

async function renderNav() {
  const me = await getMe();
  const nav = document.createElement("nav");

  const home = document.createElement("a");
  home.href = "/index.html";
  home.textContent = "Home";

  const profile = document.createElement("a");
  profile.href = "/profile.html" + (me ? "?u=" + encodeURIComponent(me.user_name) : "");
  profile.textContent = "Profile";

  const search = document.createElement("form");
  const input = document.createElement("input");
  input.placeholder = "Go to username";
  const go = document.createElement("button");
  go.textContent = "Go";
  search.append(input, go);
  search.addEventListener("submit", (e) => {
    e.preventDefault();
    const u = input.value.trim().replace(/^@/, "");
    if (u) window.location.href = "/profile.html?u=" + encodeURIComponent(u);
  });

  const logout = document.createElement("button");
  logout.textContent = "Log out";
  logout.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/login.html";
  });

  nav.append(home, " | ", profile, " | ", search, logout);
  document.body.prepend(nav);
}

function renderPost(p, liked) {
  const div = document.createElement("div");

  const name = document.createElement("a");
  name.href = "/profile.html?u=" + encodeURIComponent(p.user_name);
  name.textContent = "@" + p.user_name;

  const content = document.createElement("p");
  const link = document.createElement("a");
  link.href = "/post.html?id=" + encodeURIComponent(p.post_id);
  link.textContent = p.content;
  content.appendChild(link);

  const media = [];
  for (const url of p.media_urls || []) {
    const isVideo = /\.(mp4|webm|mov)$/i.test(url);
    const el = document.createElement(isVideo ? "video" : "img");
    el.src = url;
    if (isVideo) el.controls = true;
    el.style.maxWidth = "300px";
    media.push(el);
  }

  const likeBtn = document.createElement("button");
  const paint = () => {
    likeBtn.textContent = (liked.has(p.post_id) ? "♥ " : "♡ ") + p.like_count;
  };
  paint();
  likeBtn.addEventListener("click", async () => {
    const r = await api("/like_post", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ post_id: p.post_id })
    });
    if (!r.ok) return;
    const data = await r.json();
    if (data.message === "Post liked") {
      liked.add(p.post_id);
      p.like_count += 1;
    } else {
      liked.delete(p.post_id);
      p.like_count -= 1;
    }
    paint();
  });

  const when = document.createElement("small");
  when.textContent = " " + new Date(p.created_at).toLocaleString();

  div.append(name, content, ...media, likeBtn, when, document.createElement("hr"));
  return div;
}

document.addEventListener("DOMContentLoaded", renderNav);
