const form = document.querySelector("#comic-form");
const button = document.querySelector("#generate-button");
const statusBox = document.querySelector("#status");
const preview = document.querySelector("#preview");
let currentComicId = null;

function showStatus(message, isError = false) {
  statusBox.hidden = false;
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  preview.hidden = true;
  showStatus("Creating your comic…");
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.panel_count = Number(payload.panel_count);
  try {
    const response = await fetch("/api/comics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Comic generation failed.");
    currentComicId = result.id;
    document.querySelector("#comic-title").textContent = result.title;
    const isDemo = result.generation_mode === "demo";
    document.querySelector("#preview-mode").textContent = isDemo
      ? "LOCAL DEMO · TEMPLATE STORY · PLACEHOLDER ART"
      : "FRESH OFF THE PRESS";
    const grid = document.querySelector("#panel-grid");
    grid.replaceChildren(...result.panels.map((panel, index) => {
      const card = document.createElement("article");
      card.className = "panel-card";
      const image = document.createElement("img");
      image.src = `/api/comics/${result.id}/images/${index + 1}`;
      image.alt = panel.image_prompt;
      const heading = document.createElement("h3");
      heading.textContent = panel.title;
      const narration = document.createElement("p");
      narration.textContent = panel.narration;
      const number = document.createElement("span");
      number.className = "panel-number";
      number.textContent = String(index + 1).padStart(2, "0");
      card.append(image, number, heading, narration);
      return card;
    }));
    preview.hidden = false;
    showStatus(isDemo
      ? "Your local demo comic is ready. Add a Gemini API key to enable AI-generated stories and Stable Diffusion illustrations."
      : "Your comic is ready. Change the tone or art style and generate again to explore another take.");
    preview.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#download-button").addEventListener("click", async () => {
  if (!currentComicId) return;
  const downloadButton = document.querySelector("#download-button");
  downloadButton.disabled = true;
  try {
    const response = await fetch(`/api/comics/${currentComicId}/pdf`);
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.detail || "PDF export failed.");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    const contentDisposition = response.headers.get("Content-Disposition") || "";
    const filename = contentDisposition.match(/filename="?([^";]+)"?/i)?.[1];
    anchor.download = filename || `comiccraft-${new Date().toISOString().slice(0, 10)}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
    window.location.assign(`/export-success/${currentComicId}`);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    downloadButton.disabled = false;
  }
});
