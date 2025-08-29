const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("fileElem");
const fileSelectBtn = document.getElementById("fileSelect");
const preview = document.getElementById("preview");
const analyzeBtn = document.getElementById("analyzeBtn");

let selectedFile = null;

fileSelectBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
    handleFiles(e.target.files);
});

dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropArea.classList.add("hover");
});

dropArea.addEventListener("dragleave", () => dropArea.classList.remove("hover"));

dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropArea.classList.remove("hover");
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(selectedFile);
        analyzeBtn.disabled = false;
    }
}

analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("file", selectedFile);

    const res = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    displayResults(data.result);
});
