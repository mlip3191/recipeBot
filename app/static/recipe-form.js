const form = document.getElementById("recipe-form");
const recipeId = form.dataset.recipeId ? Number(form.dataset.recipeId) : null;

const nameInput = document.getElementById("field-name");
const proteinSelect = document.getElementById("field-protein");
const genreInput = document.getElementById("field-genre");
const genreOptionsList = document.getElementById("genre-options");
const cookTimeInput = document.getElementById("field-cook-time");
const totalTimeInput = document.getElementById("field-total-time");
const servingsInput = document.getElementById("field-servings");
const sourceInput = document.getElementById("field-source");
const notesInput = document.getElementById("field-notes");
const ingredientsRows = document.getElementById("ingredients-rows");
const instructionsRows = document.getElementById("instructions-rows");
const addIngredientBtn = document.getElementById("add-ingredient-btn");
const addInstructionBtn = document.getElementById("add-instruction-btn");
const deleteBtn = document.getElementById("delete-btn");
const formStatus = document.getElementById("form-status");

function el(tag, options = {}) {
    const node = document.createElement(tag);
    if (options.className) node.className = options.className;
    if (options.text !== undefined) node.textContent = options.text;
    return node;
}

async function fetchJSON(url) {
    const response = await fetch(url);
    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }
    return { ok: response.ok, status: response.status, data };
}

function field(placeholder, value, dataField, wide = false) {
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = placeholder;
    input.value = value || "";
    input.dataset.field = dataField;
    input.className = wide ? "row-input row-input-wide" : "row-input";
    return input;
}

function rowControls(getRow) {
    const wrap = el("div", { className: "row-controls" });

    const up = el("button", { className: "icon-btn", text: "↑" });
    up.type = "button";
    up.setAttribute("aria-label", "Move up");
    up.addEventListener("click", () => moveRow(getRow(), -1));

    const down = el("button", { className: "icon-btn", text: "↓" });
    down.type = "button";
    down.setAttribute("aria-label", "Move down");
    down.addEventListener("click", () => moveRow(getRow(), 1));

    const remove = el("button", { className: "icon-btn icon-btn-danger", text: "✕" });
    remove.type = "button";
    remove.setAttribute("aria-label", "Remove");
    remove.addEventListener("click", () => getRow().remove());

    wrap.append(up, down, remove);
    return wrap;
}

function moveRow(row, direction) {
    if (direction === -1 && row.previousElementSibling) {
        row.parentElement.insertBefore(row, row.previousElementSibling);
    } else if (direction === 1 && row.nextElementSibling) {
        row.parentElement.insertBefore(row.nextElementSibling, row);
    }
}

function createIngredientRow(data = {}) {
    const row = el("div", { className: "dynamic-row" });
    const itemInput = field("Item", data.item, "item");
    itemInput.required = true;

    row.appendChild(field("Qty", data.quantity, "quantity"));
    row.appendChild(field("Unit", data.unit, "unit"));
    row.appendChild(itemInput);
    row.appendChild(field("Prep note", data.prep_note, "prep_note"));
    row.appendChild(rowControls(() => row));
    return row;
}

function createInstructionRow(data = {}) {
    const row = el("div", { className: "dynamic-row dynamic-row-instruction" });
    const textInput = field("Step description", data.text, "text", true);
    textInput.required = true;

    row.appendChild(textInput);
    row.appendChild(rowControls(() => row));
    return row;
}

function populateProteinSelect(proteins) {
    proteinSelect.innerHTML = "";
    const placeholder = el("option", { text: "Select a protein" });
    placeholder.value = "";
    placeholder.disabled = true;
    placeholder.selected = true;
    proteinSelect.appendChild(placeholder);

    for (const protein of proteins) {
        const option = el("option", { text: protein.name });
        option.value = String(protein.id);
        proteinSelect.appendChild(option);
    }
}

function populateGenreOptions(genres) {
    genreOptionsList.innerHTML = "";
    for (const genre of genres) {
        const option = document.createElement("option");
        option.value = genre;
        genreOptionsList.appendChild(option);
    }
}

function showStatus(message, isError) {
    formStatus.textContent = message;
    formStatus.classList.remove("hidden");
    formStatus.classList.toggle("form-status-error", Boolean(isError));
}

function hideStatus() {
    formStatus.classList.add("hidden");
}

async function loadRecipeForEdit(id) {
    const { ok, data } = await fetchJSON(`/api/recipes/${id}`);
    if (!ok) {
        showStatus(`Could not load this recipe: ${(data && data.detail) || "not found."}`, true);
        form.classList.add("hidden");
        return;
    }

    nameInput.value = data.name;
    proteinSelect.value = String(data.protein.id);
    genreInput.value = data.genre;
    cookTimeInput.value = data.cook_time_min;
    totalTimeInput.value = data.total_time_min;
    servingsInput.value = data.servings;
    sourceInput.value = data.source || "";
    notesInput.value = data.notes || "";

    ingredientsRows.innerHTML = "";
    for (const ingredient of data.ingredients) {
        ingredientsRows.appendChild(createIngredientRow(ingredient));
    }

    instructionsRows.innerHTML = "";
    for (const instruction of data.instructions) {
        instructionsRows.appendChild(createInstructionRow(instruction));
    }

    deleteBtn.classList.remove("hidden");
}

function collectIngredients() {
    return Array.from(ingredientsRows.children)
        .map((row) => ({
            quantity: row.querySelector('[data-field="quantity"]').value.trim() || null,
            unit: row.querySelector('[data-field="unit"]').value.trim() || null,
            item: row.querySelector('[data-field="item"]').value.trim(),
            prep_note: row.querySelector('[data-field="prep_note"]').value.trim() || null,
        }))
        .filter((ingredient) => ingredient.item);
}

function collectInstructions() {
    return Array.from(instructionsRows.children)
        .map((row) => ({ text: row.querySelector('[data-field="text"]').value.trim() }))
        .filter((instruction) => instruction.text);
}

async function handleSubmit(event) {
    event.preventDefault();
    hideStatus();

    const payload = {
        name: nameInput.value.trim(),
        protein_id: Number(proteinSelect.value),
        genre: genreInput.value.trim(),
        cook_time_min: Number(cookTimeInput.value),
        total_time_min: Number(totalTimeInput.value),
        servings: Number(servingsInput.value),
        source: sourceInput.value.trim() || null,
        notes: notesInput.value.trim() || null,
        ingredients: collectIngredients(),
        instructions: collectInstructions(),
    };

    const url = recipeId ? `/api/recipes/${recipeId}` : "/api/recipes";
    const method = recipeId ? "PUT" : "POST";

    const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (response.ok) {
        window.location.href = "/recipes";
        return;
    }

    let detail = "Could not save the recipe. Please check the fields and try again.";
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
            detail = typeof errorData.detail === "string"
                ? errorData.detail
                : JSON.stringify(errorData.detail);
        }
    } catch (error) {
        // keep default detail message
    }
    showStatus(detail, true);
}

async function handleDelete() {
    if (!recipeId) return;
    if (!confirm("Delete this recipe? This cannot be undone.")) return;

    const response = await fetch(`/api/recipes/${recipeId}`, { method: "DELETE" });
    if (response.ok) {
        window.location.href = "/recipes";
    } else {
        showStatus("Could not delete this recipe. Please try again.", true);
    }
}

async function init() {
    const [proteinsResult, genresResult] = await Promise.all([
        fetchJSON("/api/proteins"),
        fetchJSON("/api/genres"),
    ]);

    populateProteinSelect(proteinsResult.ok ? proteinsResult.data : []);
    populateGenreOptions(genresResult.ok ? genresResult.data : []);

    if (recipeId) {
        await loadRecipeForEdit(recipeId);
    } else {
        ingredientsRows.appendChild(createIngredientRow());
        instructionsRows.appendChild(createInstructionRow());
    }

    addIngredientBtn.addEventListener("click", () => ingredientsRows.appendChild(createIngredientRow()));
    addInstructionBtn.addEventListener("click", () => instructionsRows.appendChild(createInstructionRow()));
    form.addEventListener("submit", handleSubmit);
    deleteBtn.addEventListener("click", handleDelete);
}

init();
