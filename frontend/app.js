const API_URL =
    "https://transaction-validator-api.onrender.com";

window.onload = function () {

    const uploadBtn =
        document.getElementById("uploadBtn");

    uploadBtn.onclick = async function (event) {

        event.preventDefault();
        event.stopPropagation();

        const fileInput =
            document.getElementById("csvFile");

        if (fileInput.files.length === 0) {
            alert("Please select a CSV file.");
            return false;
        }

        const formData = new FormData();
        formData.append(
            "file",
            fileInput.files[0]
        );

        try {

            uploadBtn.disabled = true;
            uploadBtn.textContent =
                "Processing...";

            const response =
                await fetch(
                    `${API_URL}/upload`,
                    {
                        method: "POST",
                        body: formData
                    }
                );

            const data =
                await response.json();

            console.log(data);

            if (data.total_rows !== undefined) {

                document.getElementById(
                    "totalRows"
                ).textContent =
                    data.total_rows;

                document.getElementById(
                    "validRows"
                ).textContent =
                    data.valid_rows;

                document.getElementById(
                    "invalidRows"
                ).textContent =
                    data.invalid_rows;

                await loadUploadHistory();
                await loadChunks();
            }

        } catch (error) {

            console.error(error);

            alert(
                "Unable to connect to backend."
            );

        } finally {

            uploadBtn.disabled = false;
            uploadBtn.textContent =
                "Upload & Validate";
        }

        return false;
    };
};


async function loadUploadHistory() {

    try {

        const response =
            await fetch(
                `${API_URL}/uploads`
            );

        const data =
            await response.json();

        const historyBody =
            document.getElementById(
                "historyBody"
            );

        historyBody.innerHTML = "";

        data.forEach(upload => {

            historyBody.innerHTML += `
                <tr>
                    <td>${upload.id}</td>
                    <td>${upload.filename}</td>
                    <td>${upload.total_rows}</td>
                    <td>${upload.valid_rows}</td>
                    <td>${upload.invalid_rows}</td>
                    <td>${new Date(
                        upload.uploaded_at
                    ).toLocaleString()}</td>
                </tr>
            `;
        });

    } catch (error) {
        console.error(error);
    }
}

loadUploadHistory();

async function loadChunks() {

    try {

        const response =
            await fetch(
                `${API_URL}/chunks`
            );

        const chunks =
            await response.json();

        const container =
            document.getElementById(
                "chunkButtons"
            );

        container.innerHTML = "";

        chunks.forEach(chunk => {

            container.innerHTML += `
                <a
                    class="chunk-btn"
                    href="${API_URL}/download/chunk/${chunk}"
                    target="_blank"
                >
                    Download ${chunk}
                </a>
            `;
        });

    } catch (error) {

        console.error(
            "Chunk Error:",
            error
        );

    }
}

loadChunks();
