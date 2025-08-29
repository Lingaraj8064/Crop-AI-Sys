function displayResults(result) {
    const resultsDiv = document.getElementById("results");
    let html = `<div class="result-card">
        <h3>Plant: ${result.plant}</h3>
        <p>Status: ${result.status}</p>
        <p>Confidence: ${result.confidence}%</p>`;

    if (result.status === "Diseased") {
        html += `<p><b>Disease:</b> ${result.disease}</p>
                 <p><b>Symptoms:</b> ${result.symptoms}</p>
                 <p><b>Treatments:</b> ${result.treatments}</p>
                 <p><b>Prevention:</b> ${result.prevention}</p>`;
    } else {
        html += `<p><b>Care Tips:</b> ${result.care_tips}</p>`;
    }

    html += `</div>`;
    resultsDiv.innerHTML = html;
}
