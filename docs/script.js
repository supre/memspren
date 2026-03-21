document.addEventListener('DOMContentLoaded', function () {

    // --- Helpers ---
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    // --- Metadata ---
    function loadMetadata() {
        fetch('metadata.json?v=5')
            .then(function (res) { return res.json(); })
            .then(function (meta) {
                if (meta.version) {
                    // Populate by ID
                    var byId = document.querySelectorAll('#site-version');
                    byId.forEach(function (el) {
                        el.textContent = meta.version;
                    });
                    // Populate by class
                    var byClass = document.querySelectorAll('.site-version');
                    byClass.forEach(function (el) {
                        el.textContent = meta.version;
                    });
                }
            })
            .catch(function () {});
    }

    // --- Publications ---
    function loadPublications() {
        fetch('publications.json?v=5')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var publications = data || [];
                renderPublications(publications);
            })
            .catch(function () {});
    }

    function renderPublications(publications) {
        var list = document.getElementById('publications-list');
        if (!list) return;

        // Sort by date descending
        publications.sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });

        if (publications.length === 0) {
            list.innerHTML = '<p class="text-on-surface/40 text-sm">No publications yet.</p>';
            return;
        }

        var html = '';
        publications.forEach(function (pub) {
            var dateObj = new Date(pub.date);
            var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            var dateLabel = monthNames[dateObj.getMonth()] + ' ' + dateObj.getFullYear();

            html += '<a href="' + escapeHtml(pub.url) + '" target="_blank" class="glass-card glass-card-hover rounded-2xl p-8 transition-all duration-300 group no-underline block">' +
                '<div class="flex items-center gap-3 mb-4">' +
                '<span class="px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-[0.6rem] font-label uppercase tracking-widest text-primary/70">' + escapeHtml(pub.medium) + '</span>' +
                '<span class="text-on-surface/30 text-xs">' + escapeHtml(dateLabel) + '</span>' +
                '</div>' +
                '<h3 class="text-xl font-headline italic text-on-surface/80 group-hover:text-primary transition-colors mb-3">' + escapeHtml(pub.title) + '</h3>' +
                '<p class="text-on-surface/40 text-sm leading-relaxed font-light">' + escapeHtml(pub.context) + '</p>' +
                '</a>';
        });

        list.innerHTML = html;
    }

    // --- Progress Timeline ---
    function loadProgress() {
        fetch('progress-notes.json?v=5')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var notes = data || [];
                renderProgress(notes);
            })
            .catch(function () {});
    }

    function renderProgress(notes) {
        var timeline = document.getElementById('progress-timeline');
        if (!timeline) return;

        // Sort by date descending, take latest 4
        notes.sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });
        var latest = notes.slice(0, 6);

        if (latest.length === 0) return;

        var monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
        var html = '';

        latest.forEach(function (note, i) {
            var dateObj = new Date(note.date);
            var dateLabel = monthNames[dateObj.getMonth()] + ' ' + dateObj.getDate() + ', ' + dateObj.getFullYear();
            var isFirst = i === 0;
            var isRight = i % 2 === 0;

            // First entry is brighter
            var dotBorder = isFirst ? 'border-primary ring-4 ring-primary/20' : 'border-primary/40';
            var borderColor = isFirst ? 'border-l-primary' : 'border-l-primary/40';
            var dateColor = isFirst ? 'text-primary' : 'text-primary/70';
            var titleColor = isFirst ? 'text-primary' : 'text-primary/70';
            var justify = isRight ? 'md:justify-end' : 'md:justify-start';

            var summaryText = note.summary || note.content || '';

            html += '<div class="relative flex ' + justify + ' items-center group mb-10">' +
                '<div class="absolute left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-surface border-2 ' + dotBorder + ' hidden md:block z-10"></div>' +
                '<div class="glass-card p-8 rounded-2xl w-full md:w-[45%] border-l-4 ' + borderColor + ' relative overflow-hidden">' +
                '<div class="absolute inset-0 hud-scanline opacity-10 pointer-events-none"></div>' +
                '<span class="font-label text-[0.6rem] ' + dateColor + ' font-bold tracking-[0.3em] mb-3 block">' + escapeHtml(dateLabel) + '</span>' +
                '<h4 class="text-xl font-headline font-semibold ' + titleColor + ' mb-3 italic">' + escapeHtml(note.title) + '</h4>' +
                '<p class="text-on-surface/60 text-sm leading-relaxed">' + escapeHtml(summaryText) + '</p>' +
                '</div>' +
                '</div>';
        });

        // Keep the center line, append timeline entries after it
        var centerLine = timeline.querySelector('div');
        timeline.innerHTML = '';
        if (centerLine) timeline.appendChild(centerLine);
        timeline.insertAdjacentHTML('beforeend', html);
    }

    // --- Init ---
    loadMetadata();
    loadPublications();
    loadProgress();
});
