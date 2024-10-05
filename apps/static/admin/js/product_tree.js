document.addEventListener('DOMContentLoaded', function() {
    console.log("Script loaded");

    function renderProductAreas() {
        var elements = document.querySelectorAll('.product-area-data');
        console.log("Product area elements found:", elements.length);

        var treeContainer = document.getElementById('product-areas-tree');
        if (!treeContainer) {
            console.error("Tree container not found");
            return;
        }

        treeContainer.innerHTML = ''; // Clear existing content

        elements.forEach(function(el) {
            var item = document.createElement('div');
            item.className = 'tree-item';
            item.style.marginLeft = (parseInt(el.getAttribute('data-depth')) * 20) + 'px';

            var name = document.createElement('a');
            name.href = el.getAttribute('data-url');
            name.textContent = el.getAttribute('data-name');

            item.appendChild(name);

            var videoLink = el.getAttribute('data-video-link');
            if (videoLink) {
                var video = document.createElement('a');
                video.href = videoLink;
                video.target = '_blank';
                video.textContent = ' (Video)';
                item.appendChild(video);
            }

            treeContainer.appendChild(item);
        });
    }

    renderProductAreas();
});