const chatHistory = document.getElementById("chatHistory");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const quickRepliesDiv = document.getElementById("quickReplies");
const sessionId = localStorage.getItem("crop_chat_session");

function addMessage(who, text) {
    const el = document.createElement("div");
    el.className = "msg " + (who === "bot" ? "bot" : "user");
    el.innerText = text;
    chatHistory.appendChild(el);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage(text) {
    addMessage("user", text);
    chatInput.value = "";
    const res = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId, message: text})
    });
    const data = await res.json();
    addMessage("bot", data.reply);
    renderQuickReplies(data.quick_replies || []);
}

function renderQuickReplies(list) {
    quickRepliesDiv.innerHTML = "";
    if (!list || list.length === 0) return;
    list.forEach(q => {
        const b = document.createElement("button");
        b.className = "quick-btn";
        b.innerText = q;
        b.onclick = () => sendMessage(q);
        quickRepliesDiv.appendChild(b);
    });
}

sendBtn.addEventListener("click", () => {
    const t = chatInput.value.trim();
    if (!t) return;
    sendMessage(t);
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendBtn.click();
    }
});

// welcome message on load
window.addEventListener("load", () => {
    addMessage("bot", "Hello — I can help with crop care, uploading, or disease symptoms. Try a quick suggestion.");
    renderQuickReplies(["How to upload a photo?", "Tomato care tips"]);
});
