const $ = (id) => document.getElementById(id);
let current = null;

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) { alert(data.error || "Request failed"); throw new Error(data.error); }
  return data;
}

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function loadProjects() {
  const projects = await api("/api/projects");
  $("projects").innerHTML = projects.map((p) =>
    `<li data-id="${p.id}" data-name="${esc(p.name)}" class="${current && current.id === p.id ? "active" : ""}">
       <span>${esc(p.name)}</span><span>${p.done}/${p.total}</span></li>`).join("");
}

async function loadTasks() {
  if (!current) return;
  const tasks = await api(`/api/projects/${current.id}/tasks`);
  const cols = { todo: "To do", doing: "In progress", done: "Done" };
  $("board").innerHTML = Object.entries(cols).map(([status, label]) => {
    const cards = tasks.filter((t) => t.status === status).map((t) => {
      const moves = Object.keys(cols).filter((s) => s !== status)
        .map((s) => `<button data-move="${s}" data-id="${t.id}">${cols[s]}</button>`).join("");
      const due = t.due_date ? `<span class="${t.overdue ? "overdue" : ""}">due ${t.due_date}</span>` : "";
      return `<div class="card p${t.priority}"><div>${esc(t.title)}</div>
        <div class="meta">${due}</div>${moves}<button data-del="${t.id}">Delete</button></div>`;
    }).join("");
    return `<div class="col"><h3>${label}</h3>${cards}</div>`;
  }).join("");
}

$("project-form").onsubmit = async (e) => {
  e.preventDefault();
  await api("/api/projects", "POST", { name: $("project-name").value });
  $("project-name").value = "";
  loadProjects();
};

$("projects").onclick = (e) => {
  const li = e.target.closest("li");
  if (!li) return;
  current = { id: Number(li.dataset.id), name: li.dataset.name };
  $("project-title").textContent = current.name;
  $("task-form").hidden = false;
  loadProjects(); loadTasks();
};

$("task-form").onsubmit = async (e) => {
  e.preventDefault();
  await api(`/api/projects/${current.id}/tasks`, "POST", {
    title: $("task-title").value,
    priority: Number($("task-priority").value),
    due_date: $("task-due").value || null,
  });
  $("task-title").value = "";
  loadProjects(); loadTasks();
};

$("board").onclick = async (e) => {
  const { move, id, del } = { ...e.target.dataset, del: e.target.dataset.del };
  if (move) await api(`/api/tasks/${id}`, "PATCH", { status: move });
  else if (del) await api(`/api/tasks/${del}`, "DELETE");
  else return;
  loadProjects(); loadTasks();
};

loadProjects();
