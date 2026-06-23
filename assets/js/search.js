(() => {
    const root = document.querySelector('[data-search-page]');

    if (!root) {
        return;
    }

    const form = root.querySelector('[data-search-form]');
    const input = root.querySelector('[data-search-input]');
    const status = root.querySelector('[data-search-status]');
    const results = root.querySelector('[data-search-results]');
    const empty = root.querySelector('[data-search-empty]');
    const indexUrl = root.dataset.indexUrl || '/search-index.json';
    const dateFormatter = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    let documents = [];

    const normalize = (value) => `${value || ''}`
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLocaleLowerCase('es-ES');

    const setStatus = (message) => {
        if (status) {
            status.textContent = message;
        }
    };

    const setEmpty = (message, visible = true) => {
        if (empty) {
            empty.textContent = message;
            empty.hidden = !visible;
        }
    };

    const clearResults = () => {
        results?.replaceChildren();
    };

    const createTermList = (terms, prefix = '') => {
        const list = document.createElement('div');
        list.className = 'search-result__terms';

        terms.forEach((term) => {
            const badge = document.createElement('span');
            badge.textContent = `${prefix}${term}`;
            list.appendChild(badge);
        });

        return list;
    };

    const renderResults = (matches, query) => {
        clearResults();

        if (!query) {
            setStatus(`${documents.length} artículos disponibles para buscar.`);
            setEmpty('Escribe una búsqueda para ver resultados.');
            return;
        }

        if (!matches.length) {
            setStatus('No se encontraron artículos para esa búsqueda.');
            setEmpty('No hay resultados. Prueba con otra palabra clave.');
            return;
        }

        setStatus(`${matches.length} resultado${matches.length === 1 ? '' : 's'} encontrado${matches.length === 1 ? '' : 's'}.`);
        setEmpty('', false);

        matches.forEach((item) => {
            const entry = document.createElement('li');
            entry.className = 'search-result';

            const article = document.createElement('article');
            const title = document.createElement('h3');
            const link = document.createElement('a');
            link.href = item.permalink;
            link.textContent = item.title;
            title.appendChild(link);

            const meta = document.createElement('p');
            meta.className = 'search-result__meta';
            meta.textContent = item.date ? dateFormatter.format(new Date(`${item.date}T00:00:00`)) : 'Artículo';

            const summary = document.createElement('p');
            summary.className = 'search-result__summary';
            summary.textContent = item.summary || 'Artículo de CODERTECTURA.';

            article.append(title, meta, summary);

            const terms = [
                ...item.categories,
                ...item.tags.map((tag) => `#${tag}`)
            ];

            if (terms.length) {
                article.appendChild(createTermList(terms));
            }

            entry.appendChild(article);
            results?.appendChild(entry);
        });
    };

    const search = (value) => {
        const query = value.trim();
        const terms = normalize(query).split(/\s+/).filter(Boolean);

        if (!terms.length) {
            renderResults([], '');
            return;
        }

        const matches = documents
            .map((item) => {
                const matched = terms.every((term) => item.searchText.includes(term));
                const score = terms.reduce((total, term) => {
                    if (item.titleText.includes(term)) {
                        return total + 4;
                    }

                    if (item.termText.includes(term)) {
                        return total + 3;
                    }

                    if (item.summaryText.includes(term)) {
                        return total + 2;
                    }

                    return item.contentText.includes(term) ? total + 1 : total;
                }, 0);

                return matched ? { ...item, score } : null;
            })
            .filter(Boolean)
            .sort((a, b) => b.score - a.score || new Date(b.date) - new Date(a.date));

        renderResults(matches, query);
    };

    const updateUrl = (value) => {
        const url = new URL(window.location.href);

        if (value.trim()) {
            url.searchParams.set('q', value.trim());
        } else {
            url.searchParams.delete('q');
        }

        window.history.replaceState({}, '', url);
    };

    const onSearch = () => {
        const value = input?.value || '';
        updateUrl(value);
        search(value);
    };

    form?.addEventListener('submit', (event) => {
        event.preventDefault();
        onSearch();
    });

    input?.addEventListener('input', onSearch);

    fetch(indexUrl, { headers: { Accept: 'application/json' } })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return response.json();
        })
        .then((items) => {
            documents = items.map((item) => {
                const categories = Array.isArray(item.categories) ? item.categories : [];
                const tags = Array.isArray(item.tags) ? item.tags : [];
                const titleText = normalize(item.title);
                const summaryText = normalize(item.summary);
                const contentText = normalize(item.content);
                const termText = normalize([...categories, ...tags].join(' '));

                return {
                    ...item,
                    categories,
                    tags,
                    titleText,
                    summaryText,
                    contentText,
                    termText,
                    searchText: `${titleText} ${summaryText} ${contentText} ${termText}`
                };
            });

            const initialQuery = new URLSearchParams(window.location.search).get('q') || '';
            if (input && initialQuery) {
                input.value = initialQuery;
            }

            search(input?.value || '');
        })
        .catch(() => {
            clearResults();
            setStatus('No se pudo cargar el índice de búsqueda. Inténtalo de nuevo más tarde.');
            setEmpty('La búsqueda no está disponible temporalmente.');
        });
})();