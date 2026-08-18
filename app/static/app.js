const STORAGE_KEY_PROTEIN = "recipeVault.protein";
const STORAGE_KEY_GENRE = "recipeVault.genre";
const STORAGE_KEY_TAGS = "recipeVault.tags";

const proteinSelect = document.getElementById("protein-select");
const genreSelect = document.getElementById("genre-select");
const tagCheckboxes = document.getElementById("tag-checkboxes");
const randomBtn = document.getElementById("random-btn");
const anotherBtn = document.getElementById("another-btn");
const recipeCard = document.getElementById("recipe-card");
const emptyState = document.getElementById("empty-state");

function el(tag, options = {}) {
    const node = document.createElement(tag);
    if (options.className) node.className = options.className;
    if (options.text !== undefined) node.textContent = options.text;
    return node;
}

function populateSelect(select, items, defaultLabel) {
    select.innerHTML = "";
    const defaultOption = el("option", { text: defaultLabel });
    defaultOption.value = "";
    select.appendChild(defaultOption);
    for (const item of items) {
        const option = el("option", { text: item.label });
        option.value = item.value;
        select.appendChild(option);
    }
}

function restoreSelection(select, storageKey) {
    const saved = localStorage.getItem(storageKey);
    if (saved && Array.from(select.options).some((option) => option.value === saved)) {
        select.value = saved;
    }
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

function populateTagCheckboxes(tags, selectedNames) {
    tagCheckboxes.innerHTML = "";
    for (const tag of tags) {
        const label = el("label", { className: "tag-checkbox" });
        const input = document.createElement("input");
        input.type = "checkbox";
        input.value = tag.name;
        input.checked = selectedNames.includes(tag.name);
        label.appendChild(input);
        label.appendChild(document.createTextNode(tag.name));
        tagCheckboxes.appendChild(label);
    }
}

function getSelectedTags() {
    return Array.from(tagCheckboxes.querySelectorAll('input[type="checkbox"]:checked')).map(
        (input) => input.value
    );
}

async function loadFilters() {
    const [proteinsResult, genresResult, tagsResult] = await Promise.all([
        fetchJSON("/api/proteins"),
        fetchJSON("/api/genres"),
        fetchJSON("/api/tags"),
    ]);

    const proteinItems = proteinsResult.ok
        ? proteinsResult.data.map((protein) => ({ value: String(protein.id), label: protein.name }))
        : [];
    const genreItems = genresResult.ok
        ? genresResult.data.map((genre) => ({ value: genre, label: genre }))
        : [];
    const tagItems = tagsResult.ok ? tagsResult.data : [];

    populateSelect(proteinSelect, proteinItems, "Any protein");
    populateSelect(genreSelect, genreItems, "Any genre");

    restoreSelection(proteinSelect, STORAGE_KEY_PROTEIN);
    restoreSelection(genreSelect, STORAGE_KEY_GENRE);

    let savedTags = [];
    try {
        savedTags = JSON.parse(localStorage.getItem(STORAGE_KEY_TAGS) || "[]");
    } catch (error) {
        savedTags = [];
    }
    populateTagCheckboxes(tagItems, savedTags);
}

function buildQuery() {
    const params = new URLSearchParams();
    if (proteinSelect.value) params.set("protein", proteinSelect.value);
    if (genreSelect.value) params.set("genre", genreSelect.value);
    for (const tag of getSelectedTags()) {
        params.append("tags", tag);
    }
    const query = params.toString();
    return query ? `?${query}` : "";
}

function formatIngredient(ingredient) {
    const parts = [ingredient.quantity, ingredient.unit, ingredient.item]
        .filter((part) => part !== null && part !== undefined && part !== "")
        .join(" ");
    return ingredient.prep_note ? `${parts} — ${ingredient.prep_note}` : parts;
}

function renderRecipe(recipe) {
    recipeCard.innerHTML = "";

    const titleRow = el("div", { className: "recipe-title-row" });
    titleRow.appendChild(el("h2", { text: recipe.name }));
    const editLink = el("a", { className: "btn btn-secondary btn-small", text: "Edit" });
    editLink.href = `/recipes/${recipe.id}/edit`;
    titleRow.appendChild(editLink);
    recipeCard.appendChild(titleRow);

    const badges = el("div", { className: "badges" });
    badges.appendChild(el("span", { className: "badge", text: recipe.protein.name }));
    badges.appendChild(el("span", { className: "badge", text: recipe.genre }));
    for (const tag of recipe.tags) {
        badges.appendChild(el("span", { className: "badge badge-tag", text: tag.name }));
    }
    recipeCard.appendChild(badges);

    const meta = el("p", {
        className: "meta",
        text: `Cook: ${recipe.cook_time_min} min · Total: ${recipe.total_time_min} min · Serves ${recipe.servings}`,
    });
    recipeCard.appendChild(meta);

    recipeCard.appendChild(el("h3", { text: "Ingredients" }));
    const ingredientsList = el("ul", { className: "ingredients" });
    for (const ingredient of recipe.ingredients) {
        ingredientsList.appendChild(el("li", { text: formatIngredient(ingredient) }));
    }
    recipeCard.appendChild(ingredientsList);

    recipeCard.appendChild(el("h3", { text: "Instructions" }));
    const instructionsList = el("ol", { className: "instructions" });
    for (const instruction of recipe.instructions) {
        instructionsList.appendChild(el("li", { text: instruction.text }));
    }
    recipeCard.appendChild(instructionsList);

    if (recipe.source || recipe.notes) {
        const footer = el("div", { className: "recipe-footer" });
        if (recipe.source) footer.appendChild(el("p", { text: `Source: ${recipe.source}` }));
        if (recipe.notes) footer.appendChild(el("p", { text: recipe.notes }));
        recipeCard.appendChild(footer);
    }
}

function showCard() {
    emptyState.classList.add("hidden");
    recipeCard.classList.remove("hidden");
}

function showEmptyState(message) {
    recipeCard.classList.add("hidden");
    emptyState.textContent = message;
    emptyState.classList.remove("hidden");
}

function setLoading(isLoading) {
    randomBtn.disabled = isLoading;
    anotherBtn.disabled = isLoading;
    randomBtn.textContent = isLoading ? "Rolling…" : "Random recipe";
}

async function rollRandom() {
    setLoading(true);
    const { ok, status, data } = await fetchJSON(`/api/recipes/random${buildQuery()}`);
    setLoading(false);

    if (ok) {
        renderRecipe(data);
        showCard();
        anotherBtn.classList.remove("hidden");
    } else if (status === 404) {
        showEmptyState((data && data.detail) || "No recipes match those filters.");
    } else {
        showEmptyState("Something went wrong loading a recipe. Please try again.");
    }
}

function persistSelections() {
    localStorage.setItem(STORAGE_KEY_PROTEIN, proteinSelect.value);
    localStorage.setItem(STORAGE_KEY_GENRE, genreSelect.value);
    localStorage.setItem(STORAGE_KEY_TAGS, JSON.stringify(getSelectedTags()));
}

async function init() {
    await loadFilters();

    proteinSelect.addEventListener("change", persistSelections);
    genreSelect.addEventListener("change", persistSelections);
    tagCheckboxes.addEventListener("change", persistSelections);
    randomBtn.addEventListener("click", rollRandom);
    anotherBtn.addEventListener("click", rollRandom);
}

init();
