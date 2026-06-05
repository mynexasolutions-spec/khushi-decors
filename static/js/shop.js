// ---------- SHOP PAGE FRONTEND AJAX & HISTORY CONTROLLER ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  if (!KD) return;

  // Initialize absolute bounds from script variables
  const globalMin = window.GLOBAL_MIN || 100;
  const globalMax = window.GLOBAL_MAX || 10000;

  // 1. Centralized Filter State (sourced initially from URL query parameters)
  const urlParams = new URLSearchParams(window.location.search);
  let state = {
    category: urlParams.get('category') || 'all',
    sort: urlParams.get('sort') || 'default',
    min_price: parseInt(urlParams.get('min_price')) || globalMin,
    max_price: parseInt(urlParams.get('max_price')) || globalMax,
    search: urlParams.get('search') || '',
    page: parseInt(urlParams.get('page')) || 1
  };

  // DOM Elements Selector Cache
  const shopGridContainer = document.getElementById('shopGridContainer');
  const priceMinSlider = document.getElementById('priceMinSlider');
  const priceMaxSlider = document.getElementById('priceMaxSlider');
  const priceMinInput = document.getElementById('priceMinInput');
  const priceMaxInput = document.getElementById('priceMaxInput');
  const priceMinLabel = document.getElementById('priceMinLabel');
  const priceMaxLabel = document.getElementById('priceMaxLabel');
  
  const shopSearchInput = document.getElementById('searchInput');
  const shopSortSelect = document.getElementById('shopSortSelect');
  const mobileSortList = document.querySelectorAll('#mobileSortList .sort-item');
  const filterCatItems = document.querySelectorAll('.filter-cat-list .filter-cat-item');
  
  // Mobile Drawer elements
  const filterToggleBtn = document.getElementById('filterToggleBtn');
  const shopSidebar = document.getElementById('shopSidebar');
  const filterOverlay = document.getElementById('filterOverlay');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const applyFiltersBtn = document.getElementById('applyFiltersBtn');
  const clearAllFilters = document.getElementById('clearAllFilters');

  // ---------- SIDEBAR ACCORDION CONTROLLER ----------
  function initAccordionUI() {
    // Automatically expand the parent folder display if one of its children subcategory items is active
    document.querySelectorAll('.filter-subcat-list').forEach(list => {
      const activeItem = list.querySelector('.filter-cat-item.active');
      if (activeItem) {
        list.style.display = 'flex';
        const parentToggle = list.previousElementSibling.querySelector('.accordion-toggle');
        if (parentToggle) parentToggle.style.transform = 'rotate(180deg)';
      }
    });

    // Wire up expand/collapse accordion chevron toggle actions
    document.querySelectorAll('.accordion-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const targetId = btn.dataset.toggle;
        const list = document.getElementById(targetId);
        if (list) {
          const isOpen = list.style.display === 'flex';
          list.style.display = isOpen ? 'none' : 'flex';
          btn.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
        }
      });
    });
  }

  // ---------- AJAX QUERY & DATA OVER-THE-WIRE ENGINE ----------
  let fetchController = null;

  function applyFilters(resetPage = true) {
    if (resetPage) {
      state.page = 1;
    }

    // Cancel any active in-flight fetches to prevent race conditions
    if (fetchController) {
      fetchController.abort();
    }
    fetchController = new AbortController();

    // 1. Compile search parameters
    const params = new URLSearchParams();
    if (state.category && state.category !== 'all') {
      params.set('category', state.category);
    }
    if (state.sort && state.sort !== 'default') {
      params.set('sort', state.sort);
    }
    if (state.min_price !== globalMin) {
      params.set('min_price', state.min_price);
    }
    if (state.max_price !== globalMax) {
      params.set('max_price', state.max_price);
    }
    if (state.search) {
      params.set('search', state.search);
    }
    if (state.page && state.page > 1) {
      params.set('page', state.page);
    }

    // 2. Sync parameters cleanly to browser Address Bar history
    const queryStr = params.toString();
    const newUrl = queryStr ? `/shop?${queryStr}` : '/shop';
    history.pushState(null, '', newUrl);

    // 3. Render premium Shimmer overlay loaders on grid swapping
    if (shopGridContainer) {
      shopGridContainer.style.opacity = '0.55';
      shopGridContainer.style.pointerEvents = 'none';
    }

    // 4. Fetch HTML Partial from route
    params.set('ajax', '1');
    fetch(`/shop?${params.toString()}`, { signal: fetchController.signal })
      .then(response => {
        if (!response.ok) throw new Error('Query error');
        return response.text();
      })
      .then(htmlPartial => {
        if (shopGridContainer) {
          shopGridContainer.innerHTML = htmlPartial;
          shopGridContainer.style.opacity = '1';
          shopGridContainer.style.pointerEvents = '';
          
          // Re-initialize interactive list triggers inside new partial
          attachGridCartCTAEvents();
          attachPaginationEvents();
          initAccordionUI();
          initActiveChips();
          syncSortUI();
          initCardSlideshows();
        }
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          console.error('AJAX Load Failed:', err);
          if (shopGridContainer) {
            shopGridContainer.style.opacity = '1';
            shopGridContainer.style.pointerEvents = '';
          }
        }
      });
  }

  // Debouncing timer for price range sliders & keyups
  let filterDebounceTimer;
  function triggerDebouncedApplyFilters(resetPage = true) {
    clearTimeout(filterDebounceTimer);
    filterDebounceTimer = setTimeout(() => {
      applyFilters(resetPage);
    }, 280);
  }

  // ---------- INTERACTIVE EVENT BINDINGS & HANDLERS ----------

  // Intercept category link clicks to provide seamless AJAX swaps
  function attachCategoryClickListeners() {
    document.querySelectorAll('.filter-cat-list .cat-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const parentLi = link.closest('.filter-cat-item');
        const catSlug = parentLi.dataset.cat;
        
        state.category = catSlug;

        // Visual active selector highlight adjustment
        document.querySelectorAll('.filter-cat-list .filter-cat-item').forEach(li => {
          li.classList.remove('active');
        });
        parentLi.classList.add('active');

        // Automatically expand its subcategory accordion if it has one
        const accordionList = parentLi.querySelector('.filter-subcat-list');
        if (accordionList) {
          accordionList.style.display = 'flex';
          const toggleChevron = parentLi.querySelector('.accordion-toggle');
          if (toggleChevron) toggleChevron.style.transform = 'rotate(180deg)';
        }

        applyFilters(true);
        closeMobileDrawer();
      });
    });
  }

  // Intercept pagination buttons clicks
  function attachPaginationEvents() {
    document.querySelectorAll('.shop-pagination .pagination-btn').forEach(btn => {
      if (btn.classList.contains('active') || btn.classList.contains('disabled')) return;
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = parseInt(btn.dataset.page);
        if (targetPage) {
          state.page = targetPage;
          applyFilters(false); // Do NOT reset active page index!
          
          // Smooth scroll results to top
          const topbar = document.querySelector('.shop-topbar');
          if (topbar) {
            topbar.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      });
    });
  }

  // Bind Cart CTA actions (Add to Bag / Buy Now)
  function attachGridCartCTAEvents() {
    if (!shopGridContainer) return;

    // Add to Bag CTA
    shopGridContainer.querySelectorAll('.add-to-cart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = btn.dataset.name;
        const price = parseInt(btn.dataset.price);
        const sku = btn.dataset.sku || '';
        const cart = KD.getCart();

        cart.push({ name, price, sku });
        KD.saveCart(cart);
        KD.showToast(`${name} added to Bag ✨`, "#C17A5A");
      });
    });

    // Buy Now CTA
    shopGridContainer.querySelectorAll('.buy-now').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = btn.dataset.name;
        const price = parseInt(btn.dataset.price);
        const sku = btn.dataset.sku || '';
        const cart = KD.getCart();

        cart.push({ name, price, sku });
        KD.saveCart(cart);
        window.location.href = '/cart';
      });
    });

    // Reset button in empty state partial block
    const shopEmptyReset = document.getElementById('shopEmptyReset');
    if (shopEmptyReset) {
      shopEmptyReset.addEventListener('click', resetAllFilters);
    }
  }

  // Sync dual slider visual tracks and value elements
  function syncSlidersUI() {
    if (priceMinSlider) priceMinSlider.value = state.min_price;
    if (priceMaxSlider) priceMaxSlider.value = state.max_price;
    if (priceMinInput) priceMinInput.value = state.min_price;
    if (priceMaxInput) priceMaxInput.value = state.max_price;
    if (priceMinLabel) priceMinLabel.textContent = `₹${state.min_price}`;
    if (priceMaxLabel) priceMaxLabel.textContent = `₹${state.max_price}`;

    // Compute range percentage tracks for dynamic dual styling fills
    const minPercent = ((state.min_price - globalMin) / (globalMax - globalMin)) * 100;
    const maxPercent = ((state.max_price - globalMin) / (globalMax - globalMin)) * 100;
    const track = document.querySelector('.slider-track');
    if (track) {
      track.style.background = `linear-gradient(to right, #EAE6DF ${minPercent}%, var(--primary) ${minPercent}%, var(--primary) ${maxPercent}%, #EAE6DF ${maxPercent}%)`;
    }
  }

  // Sync and update active search, categorization and pagination parameters sort dropdown elements
  function syncSortUI() {
    if (shopSortSelect) {
      shopSortSelect.value = state.sort;
    }
    mobileSortList.forEach(li => {
      li.classList.toggle('active', li.dataset.sort === state.sort);
    });
  }

  // Draw active filter chips
  function initActiveChips() {
    const activeFilterChips = document.getElementById('activeFilterChips');
    if (!activeFilterChips) return;
    activeFilterChips.innerHTML = '';

    // Active Category chip
    if (state.category && state.category !== 'all') {
      // Find category title from sidebar li links
      const matchedCatLi = document.querySelector(`.filter-cat-item[data-cat="${state.category}"]`);
      const catLabel = matchedCatLi ? matchedCatLi.querySelector('.cat-link').innerText.trim() : state.category;
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="cat">
          <i class="fas fa-tag"></i> ${catLabel} <i class="fas fa-times"></i>
        </span>`;
    }

    // Active Price Boundary chip
    if (state.min_price !== globalMin || state.max_price !== globalMax) {
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="price">
          <i class="fas fa-rupee-sign"></i> ₹${state.min_price} – ₹${state.max_price} <i class="fas fa-times"></i>
        </span>`;
    }

    // Active Search Keyword chip
    if (state.search) {
      activeFilterChips.innerHTML += `
        <span class="filter-chip" data-clear="search">
          <i class="fas fa-search"></i> "${state.search}" <i class="fas fa-times"></i>
        </span>`;
    }

    // Handle Chip click clears
    activeFilterChips.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const type = chip.dataset.clear;
        if (type === 'cat') {
          state.category = 'all';
          // Revert visual highlights
          document.querySelectorAll('.filter-cat-list .filter-cat-item').forEach(li => {
            li.classList.toggle('active', li.dataset.cat === 'all');
          });
        } else if (type === 'price') {
          state.min_price = globalMin;
          state.max_price = globalMax;
          syncSlidersUI();
        } else if (type === 'search') {
          state.search = '';
          if (shopSearchInput) shopSearchInput.value = '';
        }
        applyFilters(true);
      });
    });
  }

  // ---------- DUAL SLIDER INPUT BINDINGS ----------
  if (priceMinSlider && priceMaxSlider) {
    priceMinSlider.addEventListener('input', (e) => {
      // Prevent handles from overlapping (enforcing minimum 50 difference)
      const val = Math.min(parseInt(e.target.value), state.max_price - 50);
      priceMinSlider.value = val;
      state.min_price = val;
      syncSlidersUI();
      triggerDebouncedApplyFilters(true);
    });

    priceMaxSlider.addEventListener('input', (e) => {
      const val = Math.max(parseInt(e.target.value), state.min_price + 50);
      priceMaxSlider.value = val;
      state.max_price = val;
      syncSlidersUI();
      triggerDebouncedApplyFilters(true);
    });
  }

  // Text inputs bindings
  if (priceMinInput) {
    priceMinInput.addEventListener('change', (e) => {
      const val = Math.max(globalMin, Math.min(parseInt(e.target.value) || globalMin, state.max_price - 50));
      state.min_price = val;
      syncSlidersUI();
      applyFilters(true);
    });
  }

  if (priceMaxInput) {
    priceMaxInput.addEventListener('change', (e) => {
      const val = Math.min(globalMax, Math.max(parseInt(e.target.value) || globalMax, state.min_price + 50));
      state.max_price = val;
      syncSlidersUI();
      applyFilters(true);
    });
  }

  // Sort Dropdown binding (desktop)
  if (shopSortSelect) {
    shopSortSelect.addEventListener('change', (e) => {
      state.sort = e.target.value;
      applyFilters(true);
    });
  }

  // Sort clicking binding (mobile list)
  mobileSortList.forEach(li => {
    li.addEventListener('click', () => {
      state.sort = li.dataset.sort;
      syncSortUI();
      applyFilters(true);
      closeMobileDrawer();
    });
  });

  // Search input change debouncing bindings
  let searchDebounce;
  if (shopSearchInput) {
    // Sourced search on load
    shopSearchInput.value = state.search;
    
    shopSearchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        state.search = e.target.value.trim();
        applyFilters(true);
      }, 350);
    });

    // Prevent navbar form submission on shop page to keep it dynamic/AJAX
    const searchForm = shopSearchInput.closest('form');
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        clearTimeout(searchDebounce);
        state.search = shopSearchInput.value.trim();
        applyFilters(true);
      });
    }
  }

  // ---------- MOBILE DRAWER SLIDER CONTROLLER ----------
  function closeMobileDrawer() {
    if (shopSidebar) shopSidebar.classList.remove('drawer-open');
    if (filterOverlay) filterOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

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
      applyFilters(true);
      closeMobileDrawer();
    });
  }

  // Reset Filters logic
  function resetAllFilters() {
    state = {
      category: 'all',
      sort: 'default',
      min_price: globalMin,
      max_price: globalMax,
      search: '',
      page: 1
    };

    if (shopSearchInput) shopSearchInput.value = '';
    
    // Highlight category All in sidebar
    document.querySelectorAll('.filter-cat-list .filter-cat-item').forEach(li => {
      li.classList.toggle('active', li.dataset.cat === 'all');
    });

    // Close all open subcategory lists
    document.querySelectorAll('.filter-subcat-list').forEach(list => {
      list.style.display = 'none';
      const toggler = list.previousElementSibling.querySelector('.accordion-toggle');
      if (toggler) toggler.style.transform = 'rotate(0deg)';
    });

    syncSlidersUI();
    syncSortUI();
    applyFilters(true);
  }

  if (clearAllFilters) {
    clearAllFilters.addEventListener('click', resetAllFilters);
  }

  // ---------- MODERN PRODUCT CARD HOVER IMAGES SLIDESHOW ----------
  function initCardSlideshows() {
    const cards = document.querySelectorAll('.shop-product-card');
    cards.forEach(card => {
      const imgWrap = card.querySelector('.shop-card-img-wrap');
      if (!imgWrap) return;

      const track = imgWrap.querySelector('.card-images-slider-track');
      const dotsContainer = card.querySelector('.card-slideshow-dots');
      if (!track) return;

      let images = [];
      try {
        images = JSON.parse(imgWrap.dataset.images || '[]');
      } catch (e) {
        images = [];
      }

      if (images.length <= 1) return;

      let intervalId = null;
      let hoverTimeout = null;
      let currentIndex = 0;

      function updateSliderPosition() {
        track.style.transform = `translateX(-${currentIndex * 100}%)`;

        if (dotsContainer) {
          const dots = dotsContainer.querySelectorAll('.slideshow-dot');
          dots.forEach((dot, idx) => {
            dot.classList.toggle('active', idx === currentIndex);
          });
        }
      }

      card.addEventListener('mouseenter', () => {
        if (dotsContainer) dotsContainer.style.opacity = '1';

        // Clear any old interval/timeout just in case
        if (intervalId) clearInterval(intervalId);
        if (hoverTimeout) clearTimeout(hoverTimeout);

        // Start cycling images after a short initial delay of 400ms
        hoverTimeout = setTimeout(() => {
          // Slide to the next image immediately
          currentIndex = (currentIndex + 1) % images.length;
          updateSliderPosition();

          // Then keep sliding every 1500ms
          intervalId = setInterval(() => {
            currentIndex = (currentIndex + 1) % images.length;
            updateSliderPosition();
          }, 1500);
        }, 400);
      });

      card.addEventListener('mouseleave', () => {
        if (hoverTimeout) {
          clearTimeout(hoverTimeout);
          hoverTimeout = null;
        }
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }

        if (dotsContainer) dotsContainer.style.opacity = '0';

        currentIndex = 0;
        updateSliderPosition();
      });
    });
  }

  // Initialize and run on initial page load
  attachCategoryClickListeners();
  attachGridCartCTAEvents();
  attachPaginationEvents();
  initAccordionUI();
  initActiveChips();
  syncSlidersUI();
  syncSortUI();
  initCardSlideshows();
});
