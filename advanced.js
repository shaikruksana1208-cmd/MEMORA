(() => {
    const fileInput = document.querySelector("#advancedFile");
    const indexButton = document.querySelector("#advancedIndex");
    const askButton = document.querySelector("#advancedAsk");
    const questionInput = document.querySelector("#advancedQuestion");
    const healthStatus = document.querySelector("#advancedHealth");
    const indexStatus = document.querySelector("#advancedIndexStatus");
    const answerStatus = document.querySelector("#advancedAnswerStatus");
    const answerPanel = document.querySelector("#advancedAnswer");
    const sourcesPanel = document.querySelector("#advancedSources");
    let indexedFileSignature = null;

    const fileSignature = (file) => `${file.name}:${file.size}:${file.lastModified}`;

    const setStatus = (element, message, state) => {
        element.textContent = message;
        element.dataset.state = state;
    };

    const apiRequest = async (url, options = {}, timeout = 125000) => {
        let response;
        try {
            response = await fetch(url, { ...options, signal: AbortSignal.timeout(timeout) });
        } catch (error) {
            if (error.name === "TimeoutError") {
                throw new Error("The request took too long. Please try again.");
            }
            throw new Error("The MEMORA API is unavailable. Check your connection and try again.");
        }

        let payload;
        try {
            payload = await response.json();
        } catch {
            throw new Error("The MEMORA API returned an unreadable response.");
        }
        if (!response.ok) {
            throw new Error(payload.error || "The request could not be completed.");
        }
        return payload;
    };

    const checkHealth = async () => {
        try {
            const health = await apiRequest("/health", {}, 7000);
            setStatus(healthStatus, `${health.service || "MEMORA API"} connected`, "success");
        } catch (error) {
            setStatus(healthStatus, error.message, "error");
        }
    };

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        askButton.disabled = !file || fileSignature(file) !== indexedFileSignature;
        if (!file) {
            setStatus(indexStatus, "No Advanced document indexed yet.", "info");
            return;
        }
        if (!/\.(pdf|txt|md)$/i.test(file.name)) {
            fileInput.value = "";
            askButton.disabled = true;
            setStatus(indexStatus, "Choose a PDF, TXT, or Markdown file.", "error");
            return;
        }
        if (file.size > 25 * 1024 * 1024) {
            fileInput.value = "";
            askButton.disabled = true;
            setStatus(indexStatus, "The selected document exceeds the 25 MB limit.", "error");
            return;
        }
        setStatus(indexStatus, `${file.name} selected. Ready to index.`, "info");
    });

    indexButton.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) {
            setStatus(indexStatus, "Choose a document before indexing.", "error");
            return;
        }

        indexButton.disabled = true;
        askButton.disabled = true;
        setStatus(indexStatus, "Uploading and indexing document…", "loading");
        try {
            const form = new FormData();
            form.append("file", file);
            const result = await apiRequest("/api/advanced/index-document", {
                method: "POST",
                body: form,
            });
            indexedFileSignature = fileSignature(file);
            askButton.disabled = false;
            questionInput.dataset.indexed = "true";
            setStatus(
                indexStatus,
                `${result.filename || file.name} indexed · ${result.pages} pages · ${result.chunks} chunks.`,
                "success",
            );
            answerPanel.replaceChildren();
            const title = document.createElement("h3");
            title.textContent = "Document ready for questions";
            answerPanel.append(title);
            sourcesPanel.innerHTML = "<h3>Sources</h3><p>Sources will appear with your answer.</p>";
        } catch (error) {
            setStatus(indexStatus, error.message, "error");
        } finally {
            indexButton.disabled = false;
        }
    });

    askButton.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file || fileSignature(file) !== indexedFileSignature) {
            askButton.disabled = true;
            setStatus(answerStatus, "Index the currently selected document before asking.", "error");
            return;
        }
        const question = questionInput.value.trim();
        if (!question) {
            setStatus(answerStatus, "Enter a question before asking.", "error");
            return;
        }
        if (question.length > 2000) {
            setStatus(answerStatus, "Keep your question to 2000 characters or fewer.", "error");
            return;
        }
        askButton.disabled = true;
        setStatus(answerStatus, "Retrieving evidence and preparing an answer…", "loading");
        try {
            const result = await apiRequest("/api/advanced/document-question", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question }),
            });
            const answer = document.createElement("p");
            answer.textContent = result.answer || "No answer was returned.";
            answerPanel.replaceChildren(answer);
            sourcesPanel.innerHTML = "<h3>Sources</h3>";
            const sources = Array.isArray(result.sources) ? result.sources : [];
            if (!sources.length) {
                const empty = document.createElement("p");
                empty.textContent = "No sources returned.";
                sourcesPanel.append(empty);
            } else {
                const list = document.createElement("ul");
                sources.forEach((source) => {
                    const item = document.createElement("li");
                    item.textContent = `${source.filename || "Document"}${source.page ? ` · page ${source.page}` : ""}`;
                    list.append(item);
                });
                sourcesPanel.append(list);
            }
            setStatus(answerStatus, "Answer ready.", "success");
        } catch (error) {
            setStatus(answerStatus, error.message, "error");
        } finally {
            askButton.disabled = false;
        }
    });

    checkHealth();
})();
