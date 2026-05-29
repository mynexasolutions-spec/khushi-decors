// ---------- SHOP PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;

  // ---------- PRODUCT DATABASE ----------
  const mockProducts = {
    wallDecor: [
      { name: "Macrame Wall Hanging", price: 899, img: "/static/images/WD1.jpg" },
      { name: "Abstract Canvas", price: 1499, img: "/static/images/WD2.jpg" },
      { name: "Jute Wall Art", price: 2199, img: "/static/images/WD3.jpg" },
      { name: "Floating Set", price: 1299, img: "/static/images/WD4.jpg" },
      { name: "Boho Tapestry", price: 749, img: "/static/images/WD5.jpg" },
      { name: "Mirror Decor", price: 1899, img: "https://images.unsplash.com/photo-1618220179428-22790b461013?w=400&auto=format" }
    ],
    artificialPlants: [
      { name: "Fiddle lavender Leaf", price: 1599, img: "/static/images/AP.jpg" },
      { name: "Succulent Trio", price: 699, img: "/static/images/AP1.jpg" },
      { name: "Hanging Ivy", price: 849, img: "/static/images/AP2.jpg" },
      { name: "Monstera Plant", price: 1899, img: "/static/images/AP3.jpg" },
      { name: "Orchid Stem", price: 1199, img: "/static/images/AP4.jpg" },
      { name: "Pink Tree", price: 1349, img: "/static/images/APFIVE.jpg" }
    ],
    lamps: [
      { name: "Street Lamp", price: 1799, img: "/static/images/LAMP.jpg" },
      { name: "Table Lamp", price: 3299, img: "/static/images/LAMP1.jpg" },
      { name: "Rattan Lamp", price: 2499, img: "/static/images/LAMP2.jpg" },
      { name: "Wall Sconce Pair", price: 1399, img: "/static/images/LAMP3.jpg" },
      { name: "Arc Floor Lamp", price: 899, img: "/static/images/LAMP4.jpg" },
      { name: "Ceramic Table Lamp", price: 2099, img: "/static/images/LAMP5.jpg" }
    ],
    vases: [
      { name: "Terracotta Set", price: 1099, img: "/static/images/VASE1.jpg" },
      { name: "Ribbed Vase", price: 1899, img: "/static/images/VASE2.jpg" },
      { name: "Handcrafted Ceramic", price: 1649, img: "/static/images/VASE3.jpg" },
      { name: "Minimalist Marble", price: 1299, img: "/static/images/VASE4.jpg" },
      { name: "Bud Vase Duo", price: 2399, img: "/static/images/VASEFIVR.jpg" },
      { name: "Ceramic Vase", price: 799, img: "https://images.unsplash.com/photo-1612196808214-b8e1d6145a8c?w=400&auto=format" }
    ],
    clocks: [
      { name: "LongMountainic Clock", price: 2799, img: "/static/images/CLOCK1.jpg" },
      { name: "Vintage Wall Clock", price: 1499, img: "/static/images/CLCOK2.jpg" },
      { name: "Modern Minimalist", price: 1199, img: "/static/images/CLCOK3.jpg" },
      { name: "Digital Smart Clock", price: 2199, img: "/static/images/CLCOK4.jpg" }
    ]
  };

  const categoryMeta = {
    wallDecor: { label: 'Wall Decor', icon: 'fa-image' },
    artificialPlants: { label: 'Artificial Plants', icon: 'fa-seedling' },
    lamps: { label: 'Designer Lamps', icon: 'fa-lightbulb' },
    vases: { label: 'Vases & Vessels', icon: 'fa-flask' },
    clocks: { label: 'Statement Clocks', icon: 'fa-clock' }
  };

  // Build the list of all tagged products dynamically
  const allTagged = [];
  if (window.DB_PRODUCTS && window.DB_PRODUCTS.length > 0) {
    window.DB_PRODUCTS.forEach(p => {
      allTagged.push({
        id: p.id,
        name: p.name,
        price: p.price,
        img: p.image_url || "/static/images/placeholder.png",
        category: p.category_slug || "wallDecor"
      });
    });
    // Populate dynamic categories
    if (window.DB_CATEGORIES) {
      window.DB_CATEGORIES.forEach(c => {
        categoryMeta[c.slug] = { label: c.name, icon: 'fa-tag' };
      });
    }
  } else {
    Object.entries(mockProducts).forEach(([cat, items]) => {
      items.forEach(item => allTagged.push({ ...item, category: cat }));
    });
  }

  // Calculate pricing bounds
  const prices = allTagged.map(p => p.price);
  const globalMin = prices.length > 0 ? Math.min(...prices) : 100;
  const globalMax = prices.length > 0 ? Math.max(...prices) : 10000;

  // Check URL query parameters for initial filters
  const urlParams = new URLSearchParams(window.location.search);
  const initialCategory = urlParams.get('category') || 'all';

  // Filters State
  let state = {
    activeCategory: initialCategory,
    sort: 'default',
    priceMin: globalMin,
    priceMax: globalMax,
    search: ''
  };

  // DOM Elements
  const shopGrid = document.getElementById('shopGrid');
  const shopEmpty = document.getElementById('shopEmpty');
  const resultsCount = document.getElementById('resultsCount');
  const shopBreadcrumb = document.getElementById('shopBreadcrumb');
  
  // Filter sidebar controls
  const filterCatItems = document.querySelectorAll('.filter-cat-item');
  const priceMinSlider = document.getElementById('priceMinSlider');
  const priceMaxSlider = document.getElementById('priceMaxSlider');
  const priceMinInput = document.getElementById('priceMinInput');
  const priceMaxInput = document.getElementById('priceMaxInput');
  const priceMinLabel = document.getElementById('priceMinLabel');
  const priceMaxLabel = document.getElementById('priceMaxLabel');
  
  const shopSearchInput = document.getElementById('shopSearchInput');
  const shopSortSelect = document.getElementById('shopSortSelect');
  const mobileSortList = document.querySelectorAll('#mobileSortList .sort-item');
  const activeFilterChips = document.getElementById('activeFilterChips');
  
  // Mobile drawer controls
  const filterToggleBtn = document.getElementById('filterToggleBtn');
  const shopSidebar = document.getElementById('shopSidebar');
  const filterOverlay = document.getElementById('filterOverlay');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const applyFiltersBtn = document.getElementById('applyFiltersBtn');
  const clearAllFilters = document.getElementById('clearAllFilters');
  const shopEmptyReset = document.getElementById('shopEmptyReset');

  // ---------- FILTER FUNCTIONS ----------
  function getFiltered() {
    let list = state.activeCategory === 'all'
      ? allTagged
      : allTagged.filter(p => p.category === state.activeCategory);

    // Price Filter
    list = list.filter(p => p.price >= state.priceMin && p.price <= state.priceMax);

    // Search query match
    if (state.search) {
      const q = state.search.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(q));
    }

    // Sort order
    switch (state.sort) {
      case 'price-asc':
        list = [...list].sort((a, b) => a.price - b.price);
        break;
      case 'price-desc':
        list = [...list].sort((a, b) => b.price - a.price);
        break;
      case 'name-asc':
        list = [...list].sort((a, b) => a.name.localeCompare(b.name));
        break;
    }
    return list;
  }

  // Bind Add to Bag / Buy Now buttons in grid
  function attachCartEvents() {
    if (!shopGrid) return;
    
    shopGrid.querySelectorAll('.add-to-cart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = btn.dataset.name;
        const price = parseInt(btn.dataset.price);
        const cart = KD.getCart();
        cart.push({ name, price });
        KD.saveCart(cart);
        KD.showToast(`${name} added ✨`, "#C17A5A");
      });
    });

    shopGrid.querySelectorAll('.buy-now').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = btn.dataset.name;
        const price = parseInt(btn.dataset.price);
        const cart = KD.getCart();
        cart.push({ name, price });
        KD.saveCart(cart);
        window.location.href = '/cart';
      });
    });
  }

  // Render cards grid
  function renderCards() {
    if (!shopGrid) return;

    const items = getFiltered();
    shopGrid.innerHTML = '';

    if (items.length === 0) {
      shopGrid.style.display = 'none';
      if (shopEmpty) shopEmpty.style.display = 'flex';
      if (resultsCount) resultsCount.textContent = '';
      return;
    }

    shopGrid.style.display = '';
    if (shopEmpty) shopEmpty.style.display = 'none';
    if (resultsCount) {
      resultsCount.textContent = `${items.length} product${items.length !== 1 ? 's' : ''} found`;
    }

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'shop-product-card';
      const catLabel = categoryMeta[item.category]?.label || item.category;
      
      card.innerHTML = `
        <div class="shop-card-img-wrap" style="cursor: pointer;">
          <img src="${item.img}" alt="${item.name}" loading="lazy">
          <span class="shop-card-cat-tag">${catLabel}</span>
        </div>
        <div class="shop-card-body">
          <h4 class="shop-card-name" style="cursor: pointer;">${item.name}</h4>
          <p class="shop-card-price">₹${item.price.toLocaleString('en-IN')}</p>
          <div class="shop-card-actions">
            <button class="btn add-to-cart" data-name="${item.name}" data-price="${item.price}">
              <i class="fas fa-bag-shopping"></i> Add
            </button>
            <button class="btn btn-outline buy-now" data-name="${item.name}" data-price="${item.price}">
              Buy Now
            </button>
          </div>
        </div>
      `;

      // Click card details redirect
      card.querySelectorAll('.shop-card-img-wrap, .shop-card-name').forEach(el => {
        el.addEventListener('click', () => {
          window.location.href = `/product/${encodeURIComponent(item.name)}`;
        });
      });

      shopGrid.appendChild(card);
    });

    attachCartEvents();
  }

  // Sync UI state elements
  function updateBreadcrumb() {
    if (!shopBreadcrumb) return;
    if (state.activeCategory === 'all') {
      shopBreadcrumb.textContent = 'All Products';
    } else {
      shopBreadcrumb.textContent = categoryMeta[state.activeCategory]?.label || state.activeCategory;
    }
  }

  function updateActiveCatUI() {
    filterCatItems.forEach(li => {
      li.classList.toggle('active', li.dataset.cat === state.activeCategory);
    });
  }

  function updateSortUI() {
    mobileSortList.forEach(li => {
      li.classList.toggle('active', li.dataset.sort === state.sort);
    });
    if (shopSortSelect) {
      shopSortSelect.value = state.sort;
    }
  }

  function syncSliders() {
    if (priceMinSlider) priceMinSlider.value = state.priceMin;
    if (priceMaxSlider) priceMaxSlider.value = state.priceMax;
    if (priceMinInput) priceMinInput.value = state.priceMin;
    if (priceMaxInput) priceMaxInput.value = state.priceMax;
    if (priceMinLabel) priceMinLabel.textContent = `₹${state.priceMin}`;
    if (priceMaxLabel) priceMaxLabel.textContent = `₹${state.priceMax}`;
  }

  // Update active chips lists
  function updateChips() {
    if (!activeFilterChips) return;
    activeFilterChips.innerHTML = '';

    if (state.activeCategory !== 'all') {
      const label = categoryMeta[state.activeCategory]?.label || state.activeCategory;
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="cat">
          <i class="fas fa-tag"></i> ${label} <i class="fas fa-times"></i>
        </span>`;
    }

    if (state.priceMin !== globalMin || state.priceMax !== globalMax) {
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="price">
          <i class="fas fa-rupee-sign"></i> ₹${state.priceMin} – ₹${state.priceMax} <i class="fas fa-times"></i>
        </span>`;
    }

    if (state.search) {
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="search">
          <i class="fas fa-search"></i> "${state.search}" <i class="fas fa-times"></i>
        </span>`;
    }

    activeFilterChips.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const type = chip.dataset.clear;
        if (type === 'cat') {
          state.activeCategory = 'all';
          updateActiveCatUI();
        } else if (type === 'price') {
          state.priceMin = globalMin;
          state.priceMax = globalMax;
          syncSliders();
        } else if (type === 'search') {
          state.search = '';
          if (shopSearchInput) shopSearchInput.value = '';
        }
        updateChips();
        updateBreadcrumb();
        renderCards();
      });
    });
  }

  function closeMobileDrawer() {
    if (shopSidebar) shopSidebar.classList.remove('drawer-open');
    if (filterOverlay) filterOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Initialize display
  if (shopGrid) {
    updateBreadcrumb();
    updateActiveCatUI();
    updateSortUI();
    syncSliders();
    updateChips();
    renderCards();
  }

  // ---------- EVENT BINDINGS ----------
  
  // Mobile drawer trigger
  if (filterToggleBtn && shopSidebar && filterOverlay) {
    filterToggleBtn.addEventListener('click', () => {
      shopSidebar.classList.add('drawer-open');
      filterOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }

  if (filterOverlay) filterOverlay.addEventListener('click', closeMobileDrawer);
  if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeMobileDrawer);
  if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener('click', () => {
      updateChips();
      updateBreadcrumb();
      renderCards();
      closeMobileDrawer();
    });
  }

  // Category select filter items
  filterCatItems.forEach(li => {
    li.addEventListener('click', () => {
      state.activeCategory = li.dataset.cat;
      updateActiveCatUI();
      updateChips();
      updateBreadcrumb();
      renderCards();
    });
  });

  // Mobile list sort clicking
  mobileSortList.forEach(li => {
    li.addEventListener('click', () => {
      state.sort = li.dataset.sort;
      updateSortUI();
      renderCards();
    });
  });

  // Desktop select sort selector dropdown
  if (shopSortSelect) {
    shopSortSelect.addEventListener('change', (e) => {
      state.sort = e.target.value;
      updateSortUI();
      renderCards();
    });
  }

  // Price range dual sliders updates
  if (priceMinSlider) {
    priceMinSlider.addEventListener('input', (e) => {
      state.priceMin = Math.min(parseInt(e.target.value), state.priceMax - 50);
      syncSliders();
      renderCards();
      updateChips();
    });
  }

  if (priceMaxSlider) {
    priceMaxSlider.addEventListener('input', (e) => {
      state.priceMax = Math.max(parseInt(e.target.value), state.priceMin + 50);
      syncSliders();
      renderCards();
      updateChips();
    });
  }

  // Price text box inputs
  if (priceMinInput) {
    priceMinInput.addEventListener('change', (e) => {
      state.priceMin = Math.max(globalMin, Math.min(parseInt(e.target.value) || globalMin, state.priceMax - 50));
      syncSliders();
      renderCards();
      updateChips();
    });
  }

  if (priceMaxInput) {
    priceMaxInput.addEventListener('change', (e) => {
      state.priceMax = Math.min(globalMax, Math.max(parseInt(e.target.value) || globalMax, state.priceMin + 50));
      syncSliders();
      renderCards();
      updateChips();
    });
  }

  // Search filter matching
  let searchDebounce;
  if (shopSearchInput) {
    shopSearchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        state.search = e.target.value.trim();
        updateChips();
        renderCards();
      }, 280);
    });
  }

  // Reset Filters logic
  function resetAll() {
    state = {
      activeCategory: 'all',
      sort: 'default',
      priceMin: globalMin,
      priceMax: globalMax,
      search: ''
    };
    if (shopSearchInput) shopSearchInput.value = '';
    syncSliders();
    updateActiveCatUI();
    updateSortUI();
    updateChips();
    updateBreadcrumb();
    renderCards();
  }

  if (clearAllFilters) clearAllFilters.addEventListener('click', resetAll);
  if (shopEmptyReset) shopEmptyReset.addEventListener('click', resetAll);
});
