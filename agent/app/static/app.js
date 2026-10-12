const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const frame = document.getElementById("artifact-frame");
const approvalBar = document.getElementById("approval-bar");

let threadId = null;

function appendMessage(text, role) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showApproval(interrupt) {
  if (!approvalBar) return;
  approvalBar.hidden = false;
  approvalBar.dataset.preview = interrupt.preview_html || "";
  const label = approvalBar.querySelector(".approval-text");
  if (label) {
    label.textContent =
      interrupt.message ||
      `Approve artifact "${interrupt.filename || "summary.html"}"?`;
  }
}

function hideApproval() {
  if (!approvalBar) return;
  approvalBar.hidden = true;
}

async function handleResponse(data) {
  threadId = data.thread_id;
  appendMessage(data.reply, "bot");

  if (data.status === "interrupt" && data.interrupt) {
    showApproval(data.interrupt);
    return;
  }

  if (data.artifact_url) {
    frame.removeAttribute("srcdoc");
    frame.src = data.artifact_url;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  appendMessage(message, "user");
  input.value = "";

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    appendMessage(
      err.detail || "Agent unavailable (check API keys and Docker services).",
      "bot",
    );
    return;
  }
  await handleResponse(await res.json());
});

document.querySelectorAll("[data-approve]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!threadId) return;
    const approved = btn.dataset.approve === "true";
    const res = await fetch("/api/chat/resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId, approved }),
    });
    if (!res.ok) {
      appendMessage("Could not resume thread.", "bot");
      return;
    }
    hideApproval();
    await handleResponse(await res.json());
  });
});

appendMessage(
  "Drop files into the host ingest folder, then ask questions or request an HTML summary.",
  "bot",
);
