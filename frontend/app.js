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

function makeAvatar(url, name) {
  if (url) {
    const img = document.createElement("img");
    img.className = "avatar";
    img.src = url;
    img.alt = "";
    return img;
  }
  const ph = document.createElement("span");
  ph.className = "avatar avatar-empty";
  ph.textContent = ((name || "?")[0] || "?").toUpperCase();
  return ph;
}

let mePromise;
function getMe() {
  if (!mePromise) mePromise = api("/account/me").then((r) => (r.ok ? r.json() : null));
  return mePromise;
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
	profile.className = "nav-profile";
	profile.title = "Profile";
	profile.href = "/profile.html" + (me ? "?u=" + encodeURIComponent(me.user_name) : "");
	profile.appendChild(me ? makeAvatar(me.pfp_url, me.user_name) : document.createTextNode("Profile"));

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

function renderPost(p, liked, me) {
  const div = document.createElement("div");
  div.className = "post";

  const name = document.createElement("a");
  name.href = "/profile.html?u=" + encodeURIComponent(p.user_name);
  name.textContent = "@" + p.user_name;

	const header = document.createElement("div");
	header.className = "post-header";
	header.append(makeAvatar(p.pfp_url, p.user_name), name);

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
    media.push(el);
  }

  const likeBtn = document.createElement("button");
	likeBtn.className = "like-btn";
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
	when.className = "post-time";
  when.textContent = " " + new Date(p.created_at).toLocaleString();

div.append(header, content, ...media, likeBtn, when);

if (me && me.user_id === p.user_id) {
  const del = document.createElement("button");
	del.className = "delete-btn";
  del.textContent = "Delete";
  del.addEventListener("click", async () => {
    if (!confirm("Delete this post?")) return;
    const r = await api("/posts/" + encodeURIComponent(p.post_id), { method: "DELETE" });
    if (r.ok) div.remove();
  });
  div.append(" ", del);
}


document.addEventListener("DOMContentLoaded", renderNav);
