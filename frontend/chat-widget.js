const template = document.createElement("template");

template.innerHTML = `
  <link rel="stylesheet" href="./chat-widget.css" />
  <button class="chat-fab" type="button" aria-expanded="false">Chat</button>
  <section class="chat-modal" aria-label="Insurance Help" hidden>
    <div class="chat-header">Insurance Help</div>
    <div class="chat-body" role="log" aria-live="polite"></div>
    <form class="chat-input">
      <input
        type="text"
        autocomplete="off"
        placeholder="Type your question..."
        aria-label="Type your question"
      />
      <button type="submit">Send</button>
    </form>
  </section>
`;

class ChatWidget extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.appendChild(template.content.cloneNode(true));

    this.open = false;
    this.sending = false;
    this.messages = [
      { role: "bot", text: "Hi! Ask me anything about your policy or claims." },
    ];
  }

  connectedCallback() {
    this.fab = this.shadowRoot.querySelector(".chat-fab");
    this.modal = this.shadowRoot.querySelector(".chat-modal");
    this.body = this.shadowRoot.querySelector(".chat-body");
    this.form = this.shadowRoot.querySelector(".chat-input");
    this.input = this.shadowRoot.querySelector("input");
    this.sendButton = this.shadowRoot.querySelector(".chat-input button");

    this.fab.addEventListener("click", () => this.toggle());
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      this.send();
    });

    this.renderMessages();
    this.renderState();
  }

  get apiUrl() {
    return this.getAttribute("api-url") || "http://localhost:8000/api/chat";
  }

  toggle() {
    this.open = !this.open;
    this.renderState();

    if (this.open) {
      requestAnimationFrame(() => this.input.focus());
    }
  }

  async send() {
    const text = this.input.value.trim();
    if (!text || this.sending) return;

    this.addMessage("user", text);
    this.input.value = "";
    this.setSending(true);

    try {
      const response = await fetch(this.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Sorry, I could not get an answer.");
      }

      this.addMessage("bot", data.answer || "I do not have an answer yet.");
    } catch (error) {
      this.addMessage("bot", error.message || "Something went wrong.");
    } finally {
      this.setSending(false);
    }
  }

  addMessage(role, text) {
    this.messages = [...this.messages, { role, text }];
    this.renderMessages();
  }

  setSending(value) {
    this.sending = value;
    this.input.disabled = value;
    this.sendButton.disabled = value;
    this.sendButton.textContent = value ? "..." : "Send";
  }

  renderState() {
    this.modal.hidden = !this.open;
    this.fab.textContent = this.open ? "x" : "Chat";
    this.fab.setAttribute("aria-expanded", String(this.open));
  }

  renderMessages() {
    this.body.replaceChildren(
      ...this.messages.map((message) => {
        const bubble = document.createElement("div");
        bubble.className = `bubble ${message.role}`;
        bubble.textContent = message.text;
        return bubble;
      }),
    );
    this.body.scrollTop = this.body.scrollHeight;
  }
}

customElements.define("chat-widget", ChatWidget);
