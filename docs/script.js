document.addEventListener('DOMContentLoaded', function () {
    var navLinks = document.querySelectorAll('#side-nav a[data-route]');
    var pages = document.querySelectorAll('.page');

    // --- Router ---
    function navigate(route) {
        pages.forEach(function (page) {
            page.classList.remove('active');
        });

        var target = document.getElementById('page-' + route);
        if (target) {
            target.classList.add('active');
        }

        // Update nav active state
        navLinks.forEach(function (link) {
            var isActive = link.getAttribute('data-route') === route;
            if (isActive) {
                link.className = 'nav-item flex items-center px-4 py-3 bg-primary text-white rounded-full mx-2 cursor-pointer transition-transform hover:translate-x-1 no-underline';
            } else {
                link.className = 'nav-item flex items-center px-4 py-3 rounded-full mx-2 cursor-pointer transition-transform hover:translate-x-1 no-underline text-secondary hover:bg-surface-container-low';
            }
        });

        window.scrollTo(0, 0);
    }

    function getRouteFromHash() {
        var hash = window.location.hash;
        if (hash && hash.startsWith('#/')) {
            return hash.substring(2);
        }
        return 'story';
    }

    navLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            var route = this.getAttribute('data-route');
            window.location.hash = '#/' + route;
        });
    });

    window.addEventListener('hashchange', function () {
        navigate(getRouteFromHash());
    });

    // --- Filter active style helpers ---
    var FILTER_ACTIVE = 'filter-btn px-3 py-1 border border-primary bg-primary text-on-primary rounded-full text-xs font-body cursor-pointer transition-all';
    var FILTER_INACTIVE = 'filter-btn px-3 py-1 border border-outline-variant/30 bg-surface rounded-full text-xs font-body text-secondary cursor-pointer transition-all hover:border-primary hover:text-primary';

    function setFilterBtnState(btn, active) {
        btn.className = active ? FILTER_ACTIVE : FILTER_INACTIVE;
    }

    // --- Progress Notes ---
    var progressNotes = [];
    var activeTimeFilter = 0;
    var activeTags = [];

    function loadProgressNotes() {
        fetch('progress-notes.json?v=3')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                progressNotes = data;
                buildTagFilters();
                renderProgressNotes();
            })
            .catch(function () {
                document.getElementById('progress-empty').style.display = 'block';
            });
    }

    function buildTagFilters() {
        var tagSet = {};
        progressNotes.forEach(function (note) {
            (note.tags || []).forEach(function (tag) {
                tagSet[tag] = true;
            });
        });

        var container = document.getElementById('tag-filters');
        var allBtn = container.querySelector('[data-tag="all"]');
        container.innerHTML = '';
        container.appendChild(allBtn);
        setFilterBtnState(allBtn, true);

        Object.keys(tagSet).sort().forEach(function (tag) {
            var btn = document.createElement('button');
            btn.className = FILTER_INACTIVE;
            btn.setAttribute('data-tag', tag);
            btn.textContent = tag;
            btn.addEventListener('click', function () {
                toggleMultiFilter(activeTags, tag);
                updateMultiFilterUI('tag-filters', 'data-tag', activeTags);
                renderProgressNotes();
            });
            container.appendChild(btn);
        });

        allBtn.addEventListener('click', function () {
            activeTags = [];
            updateMultiFilterUI('tag-filters', 'data-tag', activeTags);
            renderProgressNotes();
        });
    }

    // Time filter clicks
    document.querySelectorAll('#time-filters .filter-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            activeTimeFilter = parseInt(this.getAttribute('data-hours'), 10);
            document.querySelectorAll('#time-filters .filter-btn').forEach(function (b) {
                setFilterBtnState(b, false);
            });
            setFilterBtnState(this, true);
            renderProgressNotes();
        });
    });

    function renderProgressNotes() {
        var now = new Date();
        var filtered = progressNotes.filter(function (note) {
            if (activeTimeFilter > 0) {
                var noteDate = new Date(note.date);
                var diffHours = (now - noteDate) / (1000 * 60 * 60);
                if (diffHours > activeTimeFilter) return false;
            }
            if (activeTags.length > 0) {
                if (!note.tags) return false;
                for (var i = 0; i < activeTags.length; i++) {
                    if (note.tags.indexOf(activeTags[i]) === -1) return false;
                }
            }
            return true;
        });

        var list = document.getElementById('progress-list');
        var empty = document.getElementById('progress-empty');

        if (filtered.length === 0) {
            list.innerHTML = '';
            empty.style.display = 'block';
            updateProgressBadge();
            return;
        }

        empty.style.display = 'none';

        filtered.sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });

        var html = '';
        filtered.forEach(function (note) {
            var dateObj = new Date(note.date);
            var monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
            var dateLabel = monthNames[dateObj.getMonth()] + ' ' + dateObj.getDate();

            var tagsHtml = (note.tags || []).map(function (tag) {
                return '<span class="text-[10px] uppercase tracking-tighter font-body bg-surface-container-high px-2 py-0.5 rounded text-on-surface-variant">' + escapeHtml(tag) + '</span>';
            }).join('');

            var scopeHtml = '';
            if (note.scope) {
                scopeHtml = '<span class="text-[10px] uppercase tracking-wider font-body font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded">' + escapeHtml(note.scope) + '</span>';
            }

            // Render details as bullet list
            var detailsHtml = '';
            if (note.details && note.details.length > 0) {
                detailsHtml = '<ul class="mt-2 space-y-1">';
                note.details.forEach(function (d) {
                    detailsHtml += '<li class="flex items-start gap-2 text-on-surface-variant text-sm leading-relaxed">' +
                        '<span class="text-primary/60 mt-1.5 text-[6px]">&#9679;</span>' +
                        '<span>' + escapeHtml(d) + '</span></li>';
                });
                detailsHtml += '</ul>';
            }

            // Render links — internal links open detail view, external links open in new tab
            var linksHtml = '';
            if (note.links && note.links.length > 0) {
                linksHtml = '<div class="mt-2 flex gap-4">';
                note.links.forEach(function (link) {
                    var detailId = toDetailId(link.url);
                    if (detailId) {
                        linksHtml += '<a href="javascript:void(0)" onclick="openDetail(\'' + detailId + '\')" class="text-primary text-xs font-medium hover:underline">' + escapeHtml(link.label) + ' →</a>';
                    } else {
                        linksHtml += '<a href="' + escapeAttr(link.url) + '" target="_blank" rel="noopener noreferrer" class="text-primary text-xs font-medium hover:underline">' + escapeHtml(link.label) + ' →</a>';
                    }
                });
                linksHtml += '</div>';
            }

            // Support both old format (content) and new format (summary + details)
            var summaryText = note.summary || note.content || '';

            html += '<div class="flex gap-8">' +
                '<span class="font-mono text-secondary-container bg-primary px-3 py-1 rounded h-fit text-xs font-bold whitespace-nowrap">' + dateLabel + '</span>' +
                '<div class="flex-1">' +
                '<div class="flex items-center gap-2 mb-1">' +
                '<h4 class="font-body font-bold text-on-surface">' + escapeHtml(note.title) + '</h4>' +
                scopeHtml +
                '</div>' +
                '<p class="text-on-surface-variant text-sm leading-relaxed">' + escapeHtml(summaryText) + '</p>' +
                detailsHtml +
                linksHtml +
                '<div class="flex flex-wrap gap-2 mt-3">' + tagsHtml + '</div>' +
                '</div>' +
                '</div>';
        });

        list.innerHTML = '<div class="bg-surface-container px-8 py-10 rounded-xl space-y-10">' + html + '</div>';
        updateProgressBadge();
    }

    // --- Publications ---
    var publications = [];
    var pubTimeFilter = 0;
    var pubTags = [];
    var pubTypes = [];
    var pubMediums = [];

    function loadPublications() {
        fetch('publications.json?v=2')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                publications = data || [];
                buildPubFilters();
                renderPublications();
            })
            .catch(function () {
                document.getElementById('publications-empty').style.display = 'block';
            });
    }

    function buildPubFilters() {
        var tagSet = {};
        var typeSet = {};
        var mediumSet = {};

        publications.forEach(function (pub) {
            (pub.tags || []).forEach(function (tag) { tagSet[tag] = true; });
            if (pub.type) typeSet[pub.type.toLowerCase()] = true;
            if (pub.medium) mediumSet[pub.medium] = true;
        });

        buildMultiFilterButtons('pub-tag-filters', 'data-tag', tagSet, pubTags, function () {
            renderPublications();
        });
        buildMultiFilterButtons('pub-type-filters', 'data-type', typeSet, pubTypes, function () {
            renderPublications();
        });
        buildMultiFilterButtons('pub-medium-filters', 'data-medium', mediumSet, pubMediums, function () {
            renderPublications();
        });
    }

    function buildMultiFilterButtons(containerId, dataAttr, valueSet, activeArr, onUpdate) {
        var container = document.getElementById(containerId);
        var allBtn = container.querySelector('[' + dataAttr + '="all"]');
        container.innerHTML = '';
        container.appendChild(allBtn);
        setFilterBtnState(allBtn, true);

        Object.keys(valueSet).sort().forEach(function (val) {
            var btn = document.createElement('button');
            btn.className = FILTER_INACTIVE;
            btn.setAttribute(dataAttr, val);
            btn.textContent = val;
            btn.addEventListener('click', function () {
                toggleMultiFilter(activeArr, val);
                updateMultiFilterUI(containerId, dataAttr, activeArr);
                onUpdate();
            });
            container.appendChild(btn);
        });

        allBtn.addEventListener('click', function () {
            activeArr.length = 0;
            updateMultiFilterUI(containerId, dataAttr, activeArr);
            onUpdate();
        });
    }

    // Publication time filter clicks
    document.querySelectorAll('#pub-time-filters .filter-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            pubTimeFilter = parseInt(this.getAttribute('data-hours'), 10);
            document.querySelectorAll('#pub-time-filters .filter-btn').forEach(function (b) {
                setFilterBtnState(b, false);
            });
            setFilterBtnState(this, true);
            renderPublications();
        });
    });

    function renderPublications() {
        var now = new Date();
        var filtered = publications.filter(function (pub) {
            if (pubTimeFilter > 0) {
                var pubDate = new Date(pub.date);
                var diffHours = (now - pubDate) / (1000 * 60 * 60);
                if (diffHours > pubTimeFilter) return false;
            }
            if (pubTags.length > 0) {
                if (!pub.tags) return false;
                for (var i = 0; i < pubTags.length; i++) {
                    if (pub.tags.indexOf(pubTags[i]) === -1) return false;
                }
            }
            if (pubTypes.length > 0) {
                if (pubTypes.indexOf((pub.type || '').toLowerCase()) === -1) return false;
            }
            if (pubMediums.length > 0) {
                if (pubMediums.indexOf(pub.medium) === -1) return false;
            }
            return true;
        });

        var list = document.getElementById('publications-list');
        var empty = document.getElementById('publications-empty');

        if (filtered.length === 0) {
            list.innerHTML = '';
            empty.style.display = 'block';
            updatePubBadge();
            return;
        }

        empty.style.display = 'none';

        filtered.sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });

        var html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-8">';
        filtered.forEach(function (pub) {
            var tagsHtml = (pub.tags || []).slice(0, 3).map(function (tag) {
                return '<span class="text-[10px] uppercase tracking-tighter font-body bg-surface-container-high px-2 py-0.5 rounded">' + escapeHtml(tag) + '</span>';
            }).join('');

            html += '<a href="' + escapeAttr(pub.url) + '" target="_blank" rel="noopener noreferrer" class="border-l-2 border-primary/20 pl-6 py-4 hover:border-primary transition-all cursor-pointer block no-underline">' +
                '<div class="flex items-center gap-2 mb-2">' +
                '<span class="text-[10px] uppercase tracking-tighter font-label bg-surface-container-high px-2 py-0.5 rounded text-on-surface-variant">' + escapeHtml(pub.medium) + '</span>' +
                '<span class="text-[10px] uppercase tracking-tighter font-label text-secondary">' + escapeHtml(pub.type) + '</span>' +
                '</div>' +
                '<h3 class="font-body font-bold text-lg leading-tight text-on-surface hover:text-primary transition-colors">' + escapeHtml(pub.title) + '</h3>' +
                '<p class="font-body text-on-surface-variant text-sm mt-2 leading-relaxed">' + escapeHtml(pub.context) + '</p>' +
                '<div class="flex flex-wrap gap-2 mt-3">' + tagsHtml + '</div>' +
                '</a>';
        });
        html += '</div>';

        list.innerHTML = html;
        updatePubBadge();
    }

    // --- Multi-select helpers ---
    function toggleMultiFilter(arr, val) {
        var idx = arr.indexOf(val);
        if (idx === -1) {
            arr.push(val);
        } else {
            arr.splice(idx, 1);
        }
    }

    function updateMultiFilterUI(containerId, dataAttr, activeArr) {
        var btns = document.querySelectorAll('#' + containerId + ' .filter-btn');
        btns.forEach(function (btn) {
            var val = btn.getAttribute(dataAttr);
            if (val === 'all') {
                setFilterBtnState(btn, activeArr.length === 0);
            } else {
                setFilterBtnState(btn, activeArr.indexOf(val) !== -1);
            }
        });
    }

    // --- Helpers ---
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return (str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // --- Filter Toggles ---
    function setupFilterToggle(toggleId, filterId) {
        var toggle = document.getElementById(toggleId);
        var panel = document.getElementById(filterId);
        if (!toggle || !panel) return;
        toggle.addEventListener('click', function () {
            var isOpen = panel.classList.toggle('open');
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    }

    setupFilterToggle('progress-filters-toggle', 'progress-filters');
    setupFilterToggle('pub-filters-toggle', 'pub-filters');

    function updateProgressBadge() {
        var count = 0;
        if (activeTimeFilter !== 0) count++;
        count += activeTags.length;
        var badge = document.getElementById('progress-filters-badge');
        if (count > 0) {
            badge.textContent = count;
            badge.classList.add('visible');
        } else {
            badge.classList.remove('visible');
        }
    }

    function updatePubBadge() {
        var count = 0;
        if (pubTimeFilter !== 0) count++;
        count += pubTags.length;
        count += pubTypes.length;
        count += pubMediums.length;
        var badge = document.getElementById('pub-filters-badge');
        if (count > 0) {
            badge.textContent = count;
            badge.classList.add('visible');
        } else {
            badge.classList.remove('visible');
        }
    }

    // --- Detail View (inline architecture pages) ---
    function toDetailId(url) {
        // Map internal .html links to detail div IDs
        if (!url || url.startsWith('http')) return null;
        var name = url.replace('.html', '').replace(/[^a-zA-Z0-9-]/g, '-');
        var el = document.getElementById('detail-' + name);
        return el ? 'detail-' + name : null;
    }

    window.openDetail = function (detailId) {
        // Hide log list + filters, show detail view
        var wrapper = document.getElementById('progress-list-wrapper');
        var filters = document.getElementById('progress-filters');
        var filterToggle = document.getElementById('progress-filters-toggle');
        var detail = document.getElementById(detailId);
        if (!detail) return;

        if (wrapper) wrapper.style.display = 'none';
        if (filters) filters.style.display = 'none';
        if (filterToggle) filterToggle.style.display = 'none';
        detail.style.display = 'block';
        window.scrollTo(0, 0);
    };

    window.closeDetail = function () {
        // Hide all detail views, restore log list
        var details = document.querySelectorAll('.detail-view');
        details.forEach(function (d) { d.style.display = 'none'; });

        var wrapper = document.getElementById('progress-list-wrapper');
        var filters = document.getElementById('progress-filters');
        var filterToggle = document.getElementById('progress-filters-toggle');
        if (wrapper) wrapper.style.display = '';
        if (filters) filters.style.display = '';
        if (filterToggle) filterToggle.style.display = '';
        window.scrollTo(0, 0);
    };

    // --- Metadata ---
    function loadMetadata() {
        fetch('metadata.json?v=3')
            .then(function (res) { return res.json(); })
            .then(function (meta) {
                var versionEl = document.getElementById('site-version');
                if (versionEl && meta.version) {
                    versionEl.textContent = meta.version;
                }
            })
            .catch(function () {});
    }

    // --- Init ---
    loadMetadata();
    loadProgressNotes();
    loadPublications();
    navigate(getRouteFromHash());
});
