document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('.toc a[data-route]');
    const pages = document.querySelectorAll('.page');

    // --- Router ---
    function navigate(route) {
        // Hide all pages
        pages.forEach(function (page) {
            page.classList.remove('active');
        });

        // Show target page
        var target = document.getElementById('page-' + route);
        if (target) {
            target.classList.add('active');
        }

        // Update nav active state
        navLinks.forEach(function (link) {
            link.classList.remove('active');
            if (link.getAttribute('data-route') === route) {
                link.classList.add('active');
            }
        });

        // Scroll to top of main content
        window.scrollTo(0, 0);
    }

    function getRouteFromHash() {
        var hash = window.location.hash;
        if (hash && hash.startsWith('#/')) {
            return hash.substring(2);
        }
        return 'overview';
    }

    // Handle nav clicks
    navLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            var route = this.getAttribute('data-route');
            window.location.hash = '#/' + route;
        });
    });

    // Handle hash changes
    window.addEventListener('hashchange', function () {
        navigate(getRouteFromHash());
    });

    // --- Progress Notes ---
    var progressNotes = [];
    var activeTimeFilter = 0;
    var activeTags = [];

    function loadProgressNotes() {
        fetch('progress-notes.json')
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

        Object.keys(tagSet).sort().forEach(function (tag) {
            var btn = document.createElement('button');
            btn.className = 'filter-btn';
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
                b.classList.remove('active');
            });
            this.classList.add('active');
            renderProgressNotes();
        });
    });

    function renderProgressNotes() {
        var now = new Date();
        var filtered = progressNotes.filter(function (note) {
            // Time filter
            if (activeTimeFilter > 0) {
                var noteDate = new Date(note.date);
                var diffHours = (now - noteDate) / (1000 * 60 * 60);
                if (diffHours > activeTimeFilter) return false;
            }
            // Tag filter (multi-select: note must have ALL selected tags)
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

        // Sort by date descending
        filtered.sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });

        var html = '';
        filtered.forEach(function (note) {
            var tagsHtml = (note.tags || []).map(function (tag) {
                return '<span class="tag">' + escapeHtml(tag) + '</span>';
            }).join('');

            html += '<article class="progress-card">' +
                '<div class="progress-card-header">' +
                '<time>' + formatDate(note.date) + '</time>' +
                '<div class="tags">' + tagsHtml + '</div>' +
                '</div>' +
                '<h3>' + escapeHtml(note.title) + '</h3>' +
                '<p>' + escapeHtml(note.content) + '</p>' +
                '</article>';
        });

        list.innerHTML = html;
        updateProgressBadge();
    }

    // --- Publications ---
    var publications = [];
    var pubTimeFilter = 0;
    var pubTags = [];
    var pubTypes = [];
    var pubMediums = [];

    function loadPublications() {
        fetch('publications.json')
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

        Object.keys(valueSet).sort().forEach(function (val) {
            var btn = document.createElement('button');
            btn.className = 'filter-btn';
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
                b.classList.remove('active');
            });
            this.classList.add('active');
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

        var html = '';
        filtered.forEach(function (pub) {
            var typeIcon = getTypeIcon(pub.type);
            var tagsHtml = (pub.tags || []).map(function (tag) {
                return '<span class="tag">' + escapeHtml(tag) + '</span>';
            }).join('');

            html += '<article class="publication-card">' +
                '<div class="publication-card-header">' +
                '<span class="publication-type"><i class="' + typeIcon + '"></i> ' + escapeHtml(pub.type) + '</span>' +
                '<span class="publication-medium">' + escapeHtml(pub.medium) + '</span>' +
                '<time>' + formatDate(pub.date) + '</time>' +
                '</div>' +
                '<h3>' + escapeHtml(pub.title) + '</h3>' +
                '<p>' + escapeHtml(pub.context) + '</p>' +
                '<div class="publication-footer">' +
                '<div class="tags">' + tagsHtml + '</div>' +
                '<a href="' + escapeAttr(pub.url) + '" class="publication-link" target="_blank" rel="noopener noreferrer">Read on ' + escapeHtml(pub.medium) + ' <i class="fas fa-arrow-up-right-from-square"></i></a>' +
                '</div>' +
                '</article>';
        });

        list.innerHTML = html;
        updatePubBadge();
    }

    function getTypeIcon(type) {
        switch ((type || '').toLowerCase()) {
            case 'video': return 'fas fa-video';
            case 'podcast': return 'fas fa-podcast';
            default: return 'fas fa-newspaper';
        }
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
                if (activeArr.length === 0) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            } else {
                if (activeArr.indexOf(val) !== -1) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            }
        });
    }

    // --- Helpers ---
    function formatDate(dateStr) {
        var d = new Date(dateStr);
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
    }

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

    // --- Init ---
    loadProgressNotes();
    loadPublications();
    navigate(getRouteFromHash());
});
