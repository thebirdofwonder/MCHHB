/** フロントエンド — アップロードと Excel/PDF ダウンロード */

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const previewGrid = document.getElementById("preview-grid");
const processBtn = document.getElementById("process-btn");
const clearBtn = document.getElementById("clear-btn");
const statusEl = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const backendStatus = document.getElementById("backend-status");
const backendFooter = document.getElementById("backend-footer");

let selectedFiles = [];
let previewObjectUrls = [];

const lightbox = document.getElementById("image-lightbox");
const lightboxImage = document.getElementById("lightbox-image");
const lightboxCaption = document.getElementById("lightbox-caption");
const lightboxClose = document.getElementById("lightbox-close");
const lightboxBackdrop = document.querySelector(".image-lightbox-backdrop");

function setBackendStatus(message, bgColor) {
  if (backendStatus) backendStatus.textContent = message;
  if (backendFooter) backendFooter.style.background = bgColor;
  const systemStatus = document.getElementById("system-status");
  if (systemStatus) {
    systemStatus.textContent = message;
    systemStatus.style.background = bgColor;
  }
}

const FOOTER_BG = { ok: "#2e7d32", warn: "#e65100", error: "#c62828", info: "#2c3e50" };

fetch("/api/status")
  .then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then((s) => {
    setBackendStatus(s.message, FOOTER_BG[s.level] || FOOTER_BG.info);
    if (!s.can_process) processBtn.disabled = true;
  })
  .catch((err) => {
    setBackendStatus(`サーバーに接続できません（${err.message}）`, FOOTER_BG.error);
  });

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  addFiles(e.dataTransfer.files);
});

fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
  fileInput.value = "";
});

function addFiles(fileList) {
  for (const f of fileList) {
    if (!f.type.startsWith("image/")) continue;
    selectedFiles.push(f);
  }
  renderPreviews();
  processBtn.disabled = selectedFiles.length === 0;
  clearBtn.disabled = selectedFiles.length === 0;
}

function revokePreviewUrls() {
  previewObjectUrls.forEach((url) => URL.revokeObjectURL(url));
  previewObjectUrls = [];
}

function openLightbox(file) {
  const url = URL.createObjectURL(file);
  lightboxImage.src = url;
  lightboxCaption.textContent = file.name;
  lightbox.classList.remove("hidden");
  lightbox._tempUrl = url;
}

function closeLightbox() {
  lightbox.classList.add("hidden");
  lightboxImage.src = "";
  if (lightbox._tempUrl) {
    URL.revokeObjectURL(lightbox._tempUrl);
    lightbox._tempUrl = null;
  }
}

lightboxClose.addEventListener("click", closeLightbox);
lightboxBackdrop.addEventListener("click", closeLightbox);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeLightbox();
});

function renderPreviews() {
  revokePreviewUrls();
  previewGrid.innerHTML = "";
  selectedFiles.forEach((f, i) => {
    const wrap = document.createElement("div");
    wrap.className = "preview-item";

    const img = document.createElement("img");
    const url = URL.createObjectURL(f);
    previewObjectUrls.push(url);
    img.src = url;
    img.title = `${f.name}（クリックで拡大）`;
    img.addEventListener("click", (e) => {
      e.stopPropagation();
      openLightbox(f);
    });

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "preview-remove";
    removeBtn.title = "削除";
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      selectedFiles.splice(i, 1);
      renderPreviews();
      processBtn.disabled = selectedFiles.length === 0;
      clearBtn.disabled = selectedFiles.length === 0;
    });

    wrap.appendChild(img);
    wrap.appendChild(removeBtn);
    previewGrid.appendChild(wrap);
  });
}

clearBtn.addEventListener("click", () => {
  selectedFiles = [];
  closeLightbox();
  renderPreviews();
  processBtn.disabled = true;
  clearBtn.disabled = true;
  resultCard.classList.add("hidden");
  hideStatus();
});

processBtn.addEventListener("click", async () => {
  if (!selectedFiles.length) return;

  processBtn.disabled = true;
  resultCard.classList.add("hidden");
  showStatus("Claude API で読み取り中...", "loading");

  const formData = new FormData();
  selectedFiles.forEach((f) => formData.append("files", f));

  try {
    const res = await fetch("/api/process", { method: "POST", body: formData });
    if (!res.ok) {
      let detail = "処理に失敗しました";
      try {
        const err = await res.json();
        detail = err.detail || detail;
      } catch {
        /* zip 以外のエラー応答でない場合 */
      }
      throw new Error(detail);
    }

    const count = res.headers.get("X-Vaccination-Count") || "?";
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "vaccination_record.zip";
    a.click();
    URL.revokeObjectURL(a.href);

    resultCard.innerHTML = `
      <h3>出力完了</h3>
      <p>接種記録 <strong>${count}</strong> 件を読み取りました。</p>
      <p>ZIP ファイル（<code>vaccination_record.xlsx</code> と <code>vaccination_record.pdf</code>）をダウンロードしました。</p>
    `;
    resultCard.classList.remove("hidden");
    showStatus(`完了（${count} 件）— Excel / PDF をダウンロードしました`, "success");
  } catch (err) {
    showStatus(err.message, "error");
  } finally {
    processBtn.disabled = false;
  }
});

function showStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function hideStatus() {
  statusEl.classList.add("hidden");
}
