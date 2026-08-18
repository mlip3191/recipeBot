const searchInput = document.getElementById("search-input");
const proteinFilter = document.getElementById("protein-filter");
const recipesTable = document.getElementById("recipes-table");
const recipesTbody = document.getElementById("recipes-tbody");
const listEmptyState = document.getElementById("list-empty-state");

let allRecipes = [];
let searchDebounce = null;

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

async function loadProteinFilter() {
    const { ok, data } = await fetchJSON("/api/proteins");
    proteinFilter.innerHTML = "";
    proteinFilter.appendChild(el("option", { text: "Any protein" }));
    if (ok) {
        for (const protein of data) {
            const option = el("option", { text: protein.name });
            option.value = String(protein.id);
            proteinFilter.appendChild(option);
        }
    }
}

async function loadRecipes() {
    const params = new URLSearchParams();
    if (proteinFilter.value) params.set("protein", proteinFilter.value);
    const query = params.toString();

    const { ok, data } = await fetchJSON(`/api/recipes${query ? "?" + query : ""}`);
    allRecipes = ok ? data : [];
    renderTable();
}

function renderTable() {
    const search = searchInput.value.trim().toLowerCase();
    const filtered = search
        ? allRecipes.filter((recipe) => recipe.name.toLowerCase().includes(search))
        : allRecipes;

    recipesTbody.innerHTML = "";

    if (filtered.length === 0) {
        recipesTable.classList.add("hidden");
        listEmptyState.textContent = allRecipes.length === 0
            ? "No recipes yet. Add your first one!"
            : "No recipes match your search.";
        listEmptyState.classList.remove("hidden");
        return;
    }

    listEmptyState.classList.add("hidden");
    recipesTable.classList.remove("hidden");

    for (const recipe of filtered) {
        const row = el("tr");

        const nameCell = el("td");
        const nameLink = el("a", { text: recipe.name });
        nameLink.href = `/recipes/${recipe.id}/edit`;
        nameCell.appendChild(nameLink);
        row.appendChild(nameCell);

        row.appendChild(el("td", { text: recipe.protein }));
        row.appendChild(el("td", { text: recipe.genre }));
        row.appendChild(
            el("td", { text: `${recipe.cook_time_min} / ${recipe.total_time_min} min` })
        );

        const actionsCell = el("td");
        const deleteBtn = el("button", { className: "btn btn-danger btn-small", text: "Delete" });
        deleteBtn.addEventListener("click", () => deleteRecipe(recipe.id, recipe.name));
        actionsCell.appendChild(deleteBtn);
        row.appendChild(actionsCell);

        recipesTbody.appendChild(row);
    }
}

async function deleteRecipe(id, name) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;

    const response = await fetch(`/api/recipes/${id}`, { method: "DELETE" });
    if (response.ok) {
        allRecipes = allRecipes.filter((recipe) => recipe.id !== id);
        renderTable();
    } else {
        alert("Could not delete that recipe. Please try again.");
    }
}

function debouncedRenderTable() {
    if (searchDebounce) clearTimeout(searchDebounce);
    searchDebounce = setTimeout(renderTable, 150);
}

async function init() {
    await loadProteinFilter();
    await loadRecipes();

    searchInput.addEventListener("input", debouncedRenderTable);
    proteinFilter.addEventListener("change", loadRecipes);
}

init();
