(function() {
      // ---------- STATE ----------
      let cart = JSON.parse(localStorage.getItem('vividCart_pro')) || [];
      let userDetails = JSON.parse(localStorage.getItem('vividUser_pro')) || null;

      // ---------- PRODUCT DATA ----------
      const products = {
        wallDecor: [
          {name:"Macrame Wall Hanging", price:899, img:"IMAGES/WD1.jpg"},
          {name:"Abstract Canvas", price:1499, img:"IMAGES/WD2.jpg"},
          {name:"Jute Wall Art", price:2199, img:"IMAGES/WD3.jpg"},
          {name:"Floating Set", price:1299, img:"IMAGES/WD4.jpg"},
          {name:"Boho Tapestry", price:749, img:"IMAGES/WD5.jpg"},
          {name:"Mirror Decor", price:1899, img:"https://images.unsplash.com/photo-1618220179428-22790b461013?w=400&auto=format"}
        ],
        artificialPlants: [
          {name:"Fiddle lavender Leaf", price:1599, img:"IMAGES/AP.jpg"},
          {name:"Succulent Trio", price:699, img:"IMAGES/AP1.jpg"},
          {name:"Hanging Ivy", price:849, img:"IMAGES/AP2.jpg"},
          {name:"Monstera Plant", price:1899, img:"IMAGES/AP3.jpg"},
          {name:"Orchid Stem", price:1199, img:"IMAGES/AP4.jpg"},
          {name:"Pink Tree", price:1349, img:"IMAGES/APFIVE.jpg"}
        ],
        lamps: [
          {name:"Street Lamp", price:1799, img:"IMAGES/LAMP.jpg"},
          {name:"Table Lamp", price:3299, img:"IMAGES/LAMP1.jpg"},
          {name:"Rattan Lamp", price:2499, img:"IMAGES/LAMP2.jpg"},
          {name:"Wall Sconce Pair", price:1399, img:"IMAGES/LAMP3.jpg"},
          {name:"Arc Floor Lamp", price:899, img:"IMAGES/LAMP4.jpg"},
          {name:"Ceramic Table Lamp", price:2099, img:"IMAGES/LAMP5.jpg"}
        ],
        vases: [
          {name:"Terracotta Set", price:1099, img:"IMAGES/VASE1.jpg"},
          {name:"Ribbed Vase", price:1899, img:"IMAGES/VASE2.jpg"},
          {name:"Handcrafted Ceramic", price:1649, img:"IMAGES/VASE3.jpg"},
          {name:"Minimalist Marble", price:1299, img:"IMAGES/VASE4.jpg"},
          {name:"Bud Vase Duo", price:2399, img:"IMAGES/VASEFIVR.jpg"},
          {name:"Ceramic Vase", price:799, img:"https://images.unsplash.com/photo-1612196808214-b8e1d6145a8c?w=400&auto=format"}
        ],
        clocks: [
          {name:"LongMountainic Clock", price:2799, img:"IMAGES/CLOCK1.jpg"},
          {name:"Vintage Wall Clock", price:1499, img:"IMAGES/CLCOK2.jpg"},
          {name:"Modern Minimalist", price:1199, img:"IMAGES/CLCOK3.jpg"},
          {name:"Digital Smart Clock", price:2199, img:"IMAGES/CLCOK4.jpg"}
        ]
      };

      // ---------- CORE FUNCTIONS ----------
      function saveCart() { 
        localStorage.setItem('vividCart_pro', JSON.stringify(cart)); 
        updateCartCount(); 
      }
      
      function updateCartCount() { 
        const countEl = document.getElementById('cartCount');
        if (countEl) countEl.innerText = cart.length; 
      }

      function closeSidebar() {
        document.getElementById('sidebar').classList.remove('active');
        document.getElementById('overlay').classList.remove('active');
      }

      function showPage(pageId, extraParam) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active-page'));
        if (pageId === 'mainPage') {
          document.getElementById('mainPage').classList.add('active-page');
          document.getElementById('dynamicPage').classList.remove('active-page');
        } else {
          document.getElementById('mainPage').classList.remove('active-page');
          document.getElementById('dynamicPage').classList.add('active-page');
          renderDynamicPage(pageId, extraParam);
        }
        // Manage active states on desktop navigation
        document.querySelectorAll('.desktop-nav-link').forEach(link => {
          link.classList.toggle('active', link.dataset.page === pageId);
        });
        closeSidebar();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }

      function showToast(msg, bg) {
        let toast = document.createElement('div'); 
        toast.innerText = msg; 
        toast.style.position='fixed'; 
        toast.style.bottom='30px'; 
        toast.style.left='50%'; 
        toast.style.transform='translateX(-50%)'; 
        toast.style.backgroundColor=bg; 
        toast.style.color='white'; 
        toast.style.padding='12px 24px'; 
        toast.style.borderRadius='60px'; 
        toast.style.zIndex='9999'; 
        toast.style.fontWeight='500'; 
        toast.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)';
        document.body.appendChild(toast); 
        setTimeout(()=> toast.remove(), 1800);
      }

      function showSuccessModal() {
        document.getElementById('successModal').classList.add('active');
      }

      // ---------- RENDER DYNAMIC PAGES ----------
      function renderDynamicPage(pageId, extraParam) {
        const container = document.getElementById('dynamicPage');
        if (pageId === 'account') renderAccountPage(container);
        else if (pageId === 'cart') renderCartPage(container);
        else if (pageId === 'allProducts') renderAllProducts(container);
        else if (pageId === 'about') renderAboutPage(container);
        else if (pageId === 'contact') renderContactPage(container);
        else if (pageId === 'productDetail') renderProductDetail(container, extraParam);
        else if (products[pageId]) renderProductGrid(container, pageId, products[pageId]);
        else showPage('mainPage');
      }

      // ======================================================
      // SHOP PAGE — unified renderer (category grid + filters)
      // ======================================================
      const categoryMeta = {
        wallDecor:       { label: 'Wall Decor',         icon: 'fa-image' },
        artificialPlants:{ label: 'Artificial Plants',  icon: 'fa-seedling' },
        lamps:           { label: 'Designer Lamps',     icon: 'fa-lightbulb' },
        vases:           { label: 'Vases & Vessels',    icon: 'fa-flask' },
        clocks:          { label: 'Statement Clocks',   icon: 'fa-clock' }
      };

      function renderShopPage(container, initialCategory) {
        // Flatten all products, tag each with category
        const allTagged = [];
        Object.entries(products).forEach(([cat, items]) => {
          items.forEach(item => allTagged.push({ ...item, category: cat }));
        });

        // Price extremes
        const prices = allTagged.map(p => p.price);
        const globalMin = Math.min(...prices);
        const globalMax = Math.max(...prices);

        // Reactive state
        let state = {
          activeCategory: initialCategory || 'all',
          sort: 'default',
          priceMin: globalMin,
          priceMax: globalMax,
          search: ''
        };

        // ---- Build skeleton ----
        container.innerHTML = `
          <div class="shop-page-wrapper">

            <!-- Sleek Compact Banner -->
            <div class="page-banner" style="background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.55)), url('https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=1600&auto=format');">
              <div class="banner-content">
                <h1>Shop Our Collections</h1>
                <p>Handpicked artisan crafts for premium living</p>
              </div>
            </div>

            <!-- Mobile header bar -->
            <div class="shop-mobile-bar">
              <button class="back-home-shop" id="shopBackBtn"><i class="fas fa-arrow-left"></i></button>
              <h1 class="shop-mobile-title">Our Collections</h1>
              <button class="shop-filter-toggle" id="filterToggleBtn">
                <i class="fas fa-sliders-h"></i> Filters
              </button>
            </div>

            <!-- Filter drawer overlay (mobile) -->
            <div class="filter-drawer-overlay" id="filterOverlay"></div>

            <div class="shop-layout">

              <!-- ===== SIDEBAR FILTERS ===== -->
              <aside class="shop-sidebar" id="shopSidebar">
                <div class="sidebar-inner">
                  <div class="sidebar-header">
                    <h3><i class="fas fa-sliders-h"></i> Filters</h3>
                    <button class="sidebar-close-btn" id="sidebarCloseBtn"><i class="fas fa-times"></i></button>
                    <button class="clear-all-btn" id="clearAllFilters">Clear All</button>
                  </div>

                  <!-- Category Filter -->
                  <div class="filter-group">
                    <h4 class="filter-group-title">Category</h4>
                    <ul class="filter-cat-list">
                      <li class="filter-cat-item ${state.activeCategory === 'all' ? 'active' : ''}" data-cat="all">
                        <i class="fas fa-th-large"></i> All Products
                        <span class="cat-count">${allTagged.length}</span>
                      </li>
                      ${Object.entries(categoryMeta).map(([key, meta]) => `
                      <li class="filter-cat-item ${state.activeCategory === key ? 'active' : ''}" data-cat="${key}">
                        <i class="fas ${meta.icon}"></i> ${meta.label}
                        <span class="cat-count">${products[key].length}</span>
                      </li>`).join('')}
                    </ul>
                  </div>

                  <!-- Price Range Filter -->
                  <div class="filter-group">
                    <h4 class="filter-group-title">Price Range</h4>
                    <div class="price-range-display">
                      <span id="priceMinLabel">₹${globalMin}</span>
                      <span id="priceMaxLabel">₹${globalMax}</span>
                    </div>
                    <div class="price-sliders">
                      <input type="range" class="price-range-input" id="priceMinSlider"
                        min="${globalMin}" max="${globalMax}" value="${globalMin}" step="50">
                      <input type="range" class="price-range-input" id="priceMaxSlider"
                        min="${globalMin}" max="${globalMax}" value="${globalMax}" step="50">
                    </div>
                    <div class="price-inputs-row">
                      <div class="price-input-box">
                        <label>Min</label>
                        <input type="number" id="priceMinInput" value="${globalMin}" min="${globalMin}" max="${globalMax}">
                      </div>
                      <div class="price-range-sep">—</div>
                      <div class="price-input-box">
                        <label>Max</label>
                        <input type="number" id="priceMaxInput" value="${globalMax}" min="${globalMin}" max="${globalMax}">
                      </div>
                    </div>
                  </div>

                  <!-- Sort (duplicate for mobile convenience) -->
                  <div class="filter-group">
                    <h4 class="filter-group-title">Sort By</h4>
                    <ul class="sort-list" id="mobileSortList">
                      <li class="sort-item active" data-sort="default">Recommended</li>
                      <li class="sort-item" data-sort="price-asc">Price: Low → High</li>
                      <li class="sort-item" data-sort="price-desc">Price: High → Low</li>
                      <li class="sort-item" data-sort="name-asc">Name: A → Z</li>
                    </ul>
                  </div>

                  <button class="apply-filters-btn" id="applyFiltersBtn">Apply Filters</button>
                </div>
              </aside>

              <!-- ===== MAIN CONTENT ===== -->
              <main class="shop-main">

                <!-- Desktop top-bar -->
                <div class="shop-topbar">
                  <div class="shop-breadcrumb">
                    <span id="shopBreadcrumb">All Products</span>
                  </div>
                  <div class="shop-topbar-right">
                    <div class="shop-search-box">
                      <i class="fas fa-search"></i>
                      <input type="text" id="shopSearchInput" placeholder="Search products…">
                    </div>
                    <div class="shop-sort-select-wrap">
                      <select id="shopSortSelect">
                        <option value="default">Recommended</option>
                        <option value="price-asc">Price: Low → High</option>
                        <option value="price-desc">Price: High → Low</option>
                        <option value="name-asc">Name: A → Z</option>
                      </select>
                    </div>
                  </div>
                </div>

                <!-- Active filter chips -->
                <div class="active-filter-chips" id="activeFilterChips"></div>

                <!-- Results summary -->
                <p class="results-count" id="resultsCount"></p>

                <!-- Product grid -->
                <div class="shop-grid" id="shopGrid"></div>

                <!-- Empty state -->
                <div class="shop-empty" id="shopEmpty" style="display:none;">
                  <i class="fas fa-search"></i>
                  <h3>No products found</h3>
                  <p>Try adjusting your filters or search term.</p>
                  <button class="btn" id="shopEmptyReset">Reset Filters</button>
                </div>
              </main>
            </div>
          </div>
        `;

        // ---- Helpers ----
        function getFiltered() {
          let list = state.activeCategory === 'all'
            ? allTagged
            : allTagged.filter(p => p.category === state.activeCategory);
          list = list.filter(p => p.price >= state.priceMin && p.price <= state.priceMax);
          if (state.search) {
            const q = state.search.toLowerCase();
            list = list.filter(p => p.name.toLowerCase().includes(q));
          }
          switch (state.sort) {
            case 'price-asc':  list = [...list].sort((a,b) => a.price - b.price); break;
            case 'price-desc': list = [...list].sort((a,b) => b.price - a.price); break;
            case 'name-asc':   list = [...list].sort((a,b) => a.name.localeCompare(b.name)); break;
          }
          return list;
        }

        function renderCards() {
          const grid = container.querySelector('#shopGrid');
          const empty = container.querySelector('#shopEmpty');
          const countEl = container.querySelector('#resultsCount');
          const items = getFiltered();

          grid.innerHTML = '';
          if (items.length === 0) {
            grid.style.display = 'none';
            empty.style.display = 'flex';
            countEl.textContent = '';
            return;
          }
          grid.style.display = '';
          empty.style.display = 'none';
          countEl.textContent = `${items.length} product${items.length !== 1 ? 's' : ''} found`;

          items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'shop-product-card';
            const catLabel = categoryMeta[item.category]?.label || item.category;
            card.innerHTML = `
              <div class="shop-card-img-wrap">
                <img src="${item.img}" alt="${item.name}" loading="lazy">
                <span class="shop-card-cat-tag">${catLabel}</span>
              </div>
              <div class="shop-card-body">
                <h4 class="shop-card-name">${item.name}</h4>
                <p class="shop-card-price">₹${item.price.toLocaleString('en-IN')}</p>
                <div class="shop-card-actions">
                  <button class="btn add-to-cart" data-name="${item.name}" data-price="${item.price}">
                    <i class="fas fa-bag-shopping"></i> Add to Bag
                  </button>
                  <button class="btn btn-outline buy-now" data-name="${item.name}" data-price="${item.price}">
                    Buy Now
                  </button>
                </div>
              </div>
            `;
            
            card.querySelectorAll('.shop-card-img-wrap, .shop-card-name').forEach(el => {
              el.style.cursor = 'pointer';
              el.addEventListener('click', () => {
                showPage('productDetail', item.name);
              });
            });

            grid.appendChild(card);
          });
          attachCartEvents(container);
        }

        function updateBreadcrumb() {
          const bc = container.querySelector('#shopBreadcrumb');
          if (bc) bc.textContent = state.activeCategory === 'all' ? 'All Products' : categoryMeta[state.activeCategory]?.label || state.activeCategory;
        }

        function updateActiveCatUI() {
          container.querySelectorAll('.filter-cat-item').forEach(li => {
            li.classList.toggle('active', li.dataset.cat === state.activeCategory);
          });
        }

        function updateSortUI() {
          container.querySelectorAll('.sort-item').forEach(li => {
            li.classList.toggle('active', li.dataset.sort === state.sort);
          });
          const sel = container.querySelector('#shopSortSelect');
          if (sel) sel.value = state.sort;
        }

        function updateChips() {
          const chips = container.querySelector('#activeFilterChips');
          if (!chips) return;
          chips.innerHTML = '';
          if (state.activeCategory !== 'all') {
            chips.innerHTML += `<span class="filter-chip" data-clear="cat"><i class="fas fa-tag"></i> ${categoryMeta[state.activeCategory]?.label} <i class="fas fa-times"></i></span>`;
          }
          if (state.priceMin !== globalMin || state.priceMax !== globalMax) {
            chips.innerHTML += `<span class="filter-chip" data-clear="price"><i class="fas fa-rupee-sign"></i> ₹${state.priceMin} – ₹${state.priceMax} <i class="fas fa-times"></i></span>`;
          }
          if (state.search) {
            chips.innerHTML += `<span class="filter-chip" data-clear="search"><i class="fas fa-search"></i> "${state.search}" <i class="fas fa-times"></i></span>`;
          }
          chips.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
              const t = chip.dataset.clear;
              if (t === 'cat') { state.activeCategory = 'all'; updateActiveCatUI(); }
              if (t === 'price') {
                state.priceMin = globalMin; state.priceMax = globalMax;
                syncSliders();
              }
              if (t === 'search') {
                state.search = '';
                const si = container.querySelector('#shopSearchInput');
                if (si) si.value = '';
              }
              updateChips(); updateBreadcrumb(); renderCards();
            });
          });
        }

        function syncSliders() {
          const minS = container.querySelector('#priceMinSlider');
          const maxS = container.querySelector('#priceMaxSlider');
          const minI = container.querySelector('#priceMinInput');
          const maxI = container.querySelector('#priceMaxInput');
          const minL = container.querySelector('#priceMinLabel');
          const maxL = container.querySelector('#priceMaxLabel');
          if (minS) minS.value = state.priceMin;
          if (maxS) maxS.value = state.priceMax;
          if (minI) minI.value = state.priceMin;
          if (maxI) maxI.value = state.priceMax;
          if (minL) minL.textContent = `₹${state.priceMin}`;
          if (maxL) maxL.textContent = `₹${state.priceMax}`;
        }

        function closeMobileDrawer() {
          container.querySelector('#shopSidebar')?.classList.remove('drawer-open');
          container.querySelector('#filterOverlay')?.classList.remove('active');
          document.body.style.overflow = '';
        }

        // ---- Initial render ----
        updateBreadcrumb(); updateActiveCatUI(); updateSortUI(); updateChips(); renderCards();

        // ---- Events ----
        // Back
        container.querySelector('#shopBackBtn')?.addEventListener('click', () => showPage('mainPage'));

        // Mobile drawer
        container.querySelector('#filterToggleBtn')?.addEventListener('click', () => {
          container.querySelector('#shopSidebar')?.classList.add('drawer-open');
          container.querySelector('#filterOverlay')?.classList.add('active');
          document.body.style.overflow = 'hidden';
        });
        container.querySelector('#filterOverlay')?.addEventListener('click', closeMobileDrawer);
        container.querySelector('#sidebarCloseBtn')?.addEventListener('click', closeMobileDrawer);
        container.querySelector('#applyFiltersBtn')?.addEventListener('click', () => {
          updateChips(); updateBreadcrumb(); renderCards(); closeMobileDrawer();
        });

        // Category items
        container.querySelectorAll('.filter-cat-item').forEach(li => {
          li.addEventListener('click', () => {
            state.activeCategory = li.dataset.cat;
            updateActiveCatUI(); updateChips(); updateBreadcrumb(); renderCards();
          });
        });

        // Sort (mobile list)
        container.querySelectorAll('.sort-item').forEach(li => {
          li.addEventListener('click', () => {
            state.sort = li.dataset.sort;
            updateSortUI(); renderCards();
          });
        });

        // Sort (desktop select)
        container.querySelector('#shopSortSelect')?.addEventListener('change', (e) => {
          state.sort = e.target.value;
          updateSortUI(); renderCards();
        });

        // Search
        let searchDebounce;
        container.querySelector('#shopSearchInput')?.addEventListener('input', (e) => {
          clearTimeout(searchDebounce);
          searchDebounce = setTimeout(() => {
            state.search = e.target.value.trim();
            updateChips(); renderCards();
          }, 280);
        });

        // Price sliders
        container.querySelector('#priceMinSlider')?.addEventListener('input', (e) => {
          state.priceMin = Math.min(parseInt(e.target.value), state.priceMax - 50);
          syncSliders(); renderCards(); updateChips();
        });
        container.querySelector('#priceMaxSlider')?.addEventListener('input', (e) => {
          state.priceMax = Math.max(parseInt(e.target.value), state.priceMin + 50);
          syncSliders(); renderCards(); updateChips();
        });

        // Price text inputs
        container.querySelector('#priceMinInput')?.addEventListener('change', (e) => {
          state.priceMin = Math.max(globalMin, Math.min(parseInt(e.target.value)||globalMin, state.priceMax - 50));
          syncSliders(); renderCards(); updateChips();
        });
        container.querySelector('#priceMaxInput')?.addEventListener('change', (e) => {
          state.priceMax = Math.min(globalMax, Math.max(parseInt(e.target.value)||globalMax, state.priceMin + 50));
          syncSliders(); renderCards(); updateChips();
        });

        // Clear all
        function doReset() {
          state = { activeCategory: 'all', sort: 'default', priceMin: globalMin, priceMax: globalMax, search: '' };
          const si = container.querySelector('#shopSearchInput'); if (si) si.value = '';
          syncSliders(); updateActiveCatUI(); updateSortUI(); updateChips(); updateBreadcrumb(); renderCards();
        }
        container.querySelector('#clearAllFilters')?.addEventListener('click', doReset);
        container.querySelector('#shopEmptyReset')?.addEventListener('click', doReset);
      }

      // Redirect old individual-category & all-products calls → new unified shop page
      function renderProductGrid(container, category, items) {
        renderShopPage(container, category);
      }
      function renderAllProducts(container) {
        renderShopPage(container, 'all');
      }


      function attachCartEvents(container) {
        container.querySelectorAll('.add-to-cart').forEach(btn => {
          btn.addEventListener('click', () => {
            const name = btn.dataset.name, price = parseInt(btn.dataset.price);
            cart.push({name, price});
            saveCart();
            showToast(`${name} added ✨`, "#C17A5A");
          });
        });
        container.querySelectorAll('.buy-now').forEach(btn => {
          btn.addEventListener('click', () => {
            const name = btn.dataset.name, price = parseInt(btn.dataset.price);
            cart.push({name, price});
            saveCart();
            showPage('cart');
          });
        });
      }

      // ---------- HELPERS ----------
      function getProductImage(name) {
        for (const cat in products) {
          const found = products[cat].find(p => p.name === name);
          if (found) return found.img;
        }
        if (name === "Macrame Wall Hanging") return "IMAGES/WD1.jpg";
        if (name === "Rattan Lamp") return "IMAGES/LAMP2.jpg";
        if (name === "Monstera Plant") return "IMAGES/AP3.jpg";
        if (name === "Ribbed Vase") return "IMAGES/VASE2.jpg";
        return "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=300&auto=format";
      }

      // ---------- CART PAGE ----------
      function renderCartPage(container) {
        const total = cart.reduce((s, i) => s + i.price, 0);
        const delivery = total >= 2000 ? 0 : 80;
        const finalTotal = total + delivery;
        container.innerHTML = `
          <!-- Sleek Compact Banner -->
          <div class="page-banner" style="background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.55)), url('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=1600&auto=format');">
            <div class="banner-content">
              <h1>Your Shopping Bag</h1>
              <p>Review your selected designer items</p>
            </div>
          </div>

          <div class="cart-wrapper">
            <!-- Stepper -->
            <div class="checkout-stepper">
              <div class="step-item active">
                <div class="step-dot">1</div>
                <div class="step-label">Bag</div>
              </div>
              <div class="step-item">
                <div class="step-dot">2</div>
                <div class="step-label">Checkout</div>
              </div>
              <div class="step-item">
                <div class="step-dot">3</div>
                <div class="step-label">Success</div>
              </div>
            </div>

            <h1 style="margin-bottom:1.5rem;"><i class="fas fa-shopping-bag"></i> Your Shopping Bag (${cart.length})</h1>
            ${cart.length === 0 ? `<p style="text-align:center; padding: 4rem 1rem; color:#8a857a; font-size:1.1rem;">Your bag is empty.<br><br><button class="btn btn-primary" id="startShopping" style="padding:0.9rem 2.2rem; font-size:0.9rem;">Start Shopping</button></p>` : `
            <div class="cart-layout">
              <div class="cart-items-section">
                ${cart.map((item, idx) => {
                  const img = getProductImage(item.name);
                  return `
                    <div class="cart-item-card">
                      <img src="${img}" alt="${item.name}" class="cart-item-img">
                      <div class="cart-item-info">
                        <div class="cart-item-title">${item.name}</div>
                        <div class="cart-item-price">₹${item.price}</div>
                      </div>
                      <div class="cart-item-controls">
                        <div class="quantity-selector">
                          <button class="qty-dec" data-idx="${idx}">-</button>
                          <span id="qty-${idx}">1</span>
                          <button class="qty-inc" data-idx="${idx}">+</button>
                        </div>
                      </div>
                      <div class="cart-item-total" id="item-total-${idx}">₹${item.price}</div>
                      <button class="cart-item-remove remove-item" data-idx="${idx}"><i class="fas fa-trash"></i></button>
                    </div>
                  `;
                }).join('')}
              </div>
              <div class="summary-card">
                <h3 style="margin-bottom:1.25rem; font-family:'Playfair Display', serif; font-size:1.4rem;">Order Summary</h3>
                <p style="display:flex; justify-content:space-between; margin-bottom: 0.8rem; font-size:0.95rem;"><span>Subtotal:</span> <span>₹<span id="summarySubtotal">${total}</span></span></p>
                <p style="display:flex; justify-content:space-between; margin-bottom: 1.2rem; border-bottom: 1px solid #f0ede8; padding-bottom: 0.8rem; font-size:0.95rem;"><span>Shipping:</span> <span>${delivery === 0 ? '<strong style="color:var(--secondary)">FREE</strong>' : '₹'+delivery}</span></p>
                <h4 style="display:flex; justify-content:space-between; font-size:1.25rem; margin-bottom: 1.5rem; font-weight:800; color:var(--dark-charcoal);"><span>Total:</span> <span>₹<span id="summaryTotal">${finalTotal}</span></span></h4>
                <button class="checkout-btn" id="proceedCheckout" style="margin-bottom:0.8rem; padding:1rem; font-size:0.95rem;">Proceed to Checkout</button>
                <button class="btn btn-outline" id="continueShopping" style="width:100%; padding:0.9rem; font-size:0.85rem;">Continue Shopping</button>
              </div>
            </div>`}
          </div>`;
        
        if (cart.length === 0) {
          container.querySelector('#startShopping')?.addEventListener('click', ()=> showPage('mainPage'));
          return;
        }
        
        let quantities = cart.map(() => 1);
        
        function updateTotals() {
          let newTotal = cart.reduce((s, item, i) => s + (item.price * quantities[i]), 0);
          let newDelivery = newTotal >= 2000 ? 0 : 80;
          document.getElementById('summarySubtotal').innerText = newTotal;
          document.getElementById('summaryTotal').innerText = newTotal + newDelivery;
        }
        
        container.querySelectorAll('.qty-inc').forEach(b => b.addEventListener('click', (e) => {
          const idx = e.target.dataset.idx; quantities[idx]++; 
          document.getElementById('qty-'+idx).innerText = quantities[idx];
          document.getElementById('item-total-'+idx).innerText = '₹' + (cart[idx].price * quantities[idx]);
          updateTotals();
        }));
        
        container.querySelectorAll('.qty-dec').forEach(b => b.addEventListener('click', (e) => {
          const idx = e.target.dataset.idx; if(quantities[idx]>1) quantities[idx]--;
          document.getElementById('qty-'+idx).innerText = quantities[idx];
          document.getElementById('item-total-'+idx).innerText = '₹' + (cart[idx].price * quantities[idx]);
          updateTotals();
        }));
        
        container.querySelectorAll('.remove-item').forEach(b => b.addEventListener('click', (e) => {
          const idx = e.target.closest('button').dataset.idx; cart.splice(idx,1); quantities.splice(idx,1);
          saveCart(); renderCartPage(container);
        }));
        
        container.querySelector('#proceedCheckout').addEventListener('click', ()=> {
          if (!userDetails?.address) { 
            showToast("Please complete your profile to continue", "#c7362b"); 
            showPage('account'); 
          }
          else renderOrderConfirm(container, cart.reduce((s,item,i)=> s+(item.price*quantities[i]),0));
        });
        
        container.querySelector('#continueShopping').addEventListener('click', ()=> showPage('mainPage'));
      }

      // ---------- ORDER CONFIRM ----------
      function renderOrderConfirm(container, total) {
        const delivery = total >= 2000 ? 0 : 80;
        const orderId = "DEC" + Math.floor(Math.random() * 1000000);
        container.innerHTML = `
          <!-- Sleek Compact Banner -->
          <div class="page-banner" style="background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.55)), url('https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?q=80&w=1600&auto=format');">
            <div class="banner-content">
              <h1>Secure Checkout</h1>
              <p>Provide delivery details to place order</p>
            </div>
          </div>

          <div class="confirm-order-wrapper">
            <!-- Stepper -->
            <div class="checkout-stepper">
              <div class="step-item completed">
                <div class="step-dot"><i class="fas fa-check"></i></div>
                <div class="step-label">Bag</div>
              </div>
              <div class="step-item active">
                <div class="step-dot">2</div>
                <div class="step-label">Checkout</div>
              </div>
              <div class="step-item">
                <div class="step-dot">3</div>
                <div class="step-label">Success</div>
              </div>
            </div>

            <h2 style="margin-bottom:1.5rem; font-family:'Playfair Display', serif; font-size:1.8rem;">Confirm Order #${orderId}</h2>
            <div class="order-layout">
              <div class="order-card">
                <div class="card-header"><i class="fas fa-bag-shopping"></i><h3>Items in Order</h3></div>
                <div class="checkout-summary-list">
                  ${cart.map(item => `
                    <div class="checkout-summary-item">
                      <img src="${getProductImage(item.name)}" alt="${item.name}" class="checkout-item-img">
                      <div class="checkout-item-name">${item.name}</div>
                      <div class="checkout-item-price">₹${item.price}</div>
                    </div>
                  `).join('')}
                </div>

                <div class="card-header" style="margin-top:2rem;"><i class="fas fa-map-marker-alt"></i><h3>Delivery Address</h3></div>
                <div class="address-card-premium">
                  <p style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--dark-charcoal);">${userDetails.firstName} ${userDetails.lastName}</p>
                  <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6; margin-bottom: 0.3rem;"><i class="fas fa-building" style="color: var(--primary); margin-right: 8px;"></i>${userDetails.address}</p>
                  <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6; margin-bottom: 0.3rem;"><i class="fas fa-city" style="color: var(--primary); margin-right: 8px;"></i>${userDetails.city}, ${userDetails.pincode}</p>
                  <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6;"><i class="fas fa-phone-alt" style="color: var(--primary); margin-right: 8px;"></i>Phone: ${userDetails.phone}</p>
                </div>
              </div>
              <div class="order-card">
                <div class="card-header"><i class="fas fa-credit-card"></i><h3>Payment</h3></div>
                <div class="payment-option-card selected"><i class="fas fa-money-bill-wave"></i> Cash on Delivery</div>
                <div style="margin: 1.5rem 0; border-top: 1px solid #f0ede8; padding-top: 1rem;">
                  <p style="display:flex; justify-content:space-between; margin-bottom:0.5rem; font-size:0.95rem; color:#6E695F;"><span>Subtotal:</span> <span>₹${total}</span></p>
                  <p style="display:flex; justify-content:space-between; margin-bottom:1rem; font-size:0.95rem; color:#6E695F;"><span>Shipping:</span> <span>${delivery === 0 ? 'FREE' : '₹'+delivery}</span></p>
                  <p style="display:flex; justify-content:space-between; font-size:1.2rem; font-weight:800; color:var(--dark-charcoal);"><span>Total:</span> <span>₹${total + delivery}</span></p>
                </div>
                <button class="place-order-btn-enhanced" id="finalOrderBtn" style="margin-bottom:0.8rem; padding:1rem; font-size:0.95rem;">Place Order · ₹${total+delivery}</button>
                <button class="btn btn-outline" id="backToCartFromConfirm" style="width:100%; padding:0.9rem; font-size:0.85rem;">Back to Cart</button>
              </div>
            </div>
          </div>`;
        container.querySelector('#finalOrderBtn').addEventListener('click', ()=> {
          cart = []; saveCart(); showSuccessModal();
        });
        container.querySelector('#backToCartFromConfirm').addEventListener('click', ()=> renderCartPage(container));
      }

      // ---------- ACCOUNT PAGE ----------
      function renderAccountPage(container) {
            if (userDetails && userDetails.firstName && userDetails.address) {
    // ========== LOGGED IN - =========
    const memberSince = new Date().getFullYear();
    const orderCount = JSON.parse(localStorage.getItem('vividOrderCount') || '0');
    
    container.innerHTML = `
      <div class="account-dashboard">
        <!-- Hero Section -->
        <div class="account-hero">
          <div class="account-avatar-large">
            <i class="fas fa-user-circle"></i>
          </div>
          <div class="account-info">
            <h2>Welcome back, ${userDetails.firstName}! 👋</h2>
            <p>Member since ${memberSince} · ${userDetails.email || 'Email not set'}</p>
            <div class="account-stats-row">
              <div class="stat-badge">
                <div class="stat-num">${cart.length}</div>
                <div class="stat-lbl">Cart Items</div>
              </div>
              <div class="stat-badge">
                <div class="stat-num">${orderCount}</div>
                <div class="stat-lbl">Orders</div>
              </div>
              <div class="stat-badge">
                <div class="stat-num">0</div>
                <div class="stat-lbl">Wishlist</div>
              </div>
              <div class="stat-badge">
                <div class="stat-num">₹0</div>
                <div class="stat-lbl">Saved</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions-grid">
          <div class="quick-action-card" onclick="document.getElementById('cartIcon').click()">
            <i class="fas fa-shopping-bag"></i>
            <span>My Cart</span>
          </div>
          <div class="quick-action-card" id="quickOrders">
            <i class="fas fa-box"></i>
            <span>My Orders</span>
          </div>
          <div class="quick-action-card" id="quickWishlist">
            <i class="fas fa-heart"></i>
            <span>Wishlist</span>
          </div>
          <div class="quick-action-card" id="quickSupport">
            <i class="fas fa-headset"></i>
            <span>Support</span>
          </div>
        </div>

        <!-- Main Grid -->
        <div class="account-grid-enhanced">
          <!-- Profile Card -->
          <div class="enhanced-card" id="profileCard">
            <div class="card-header-enhanced">
              <h3><i class="fas fa-id-card"></i> Personal Information</h3>
              <button class="edit-btn-icon" id="editProfileBtnEnhanced" title="Edit Profile">
                <i class="fas fa-pen"></i>
              </button>
            </div>
            <div class="info-grid" id="profileInfoDisplay">
              <div class="info-item">
                <span class="info-label">Full Name</span>
                <span class="info-value">${userDetails.firstName} ${userDetails.lastName}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Email</span>
                <span class="info-value">${userDetails.email || 'Not provided'}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Phone</span>
                <span class="info-value">${userDetails.phone || 'Not provided'}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Member Since</span>
                <span class="info-value">${memberSince}</span>
              </div>
            </div>
          </div>

          <!-- Address Card -->
          <div class="enhanced-card" id="addressCard">
            <div class="card-header-enhanced">
              <h3><i class="fas fa-map-marker-alt"></i> Delivery Address</h3>
              <button class="edit-btn-icon" id="editAddressBtnEnhanced" title="Edit Address">
                <i class="fas fa-pen"></i>
              </button>
            </div>
            <div class="address-display" id="addressInfoDisplay">
              <div class="address-line">
                <i class="fas fa-building"></i>
                <span>${userDetails.address}</span>
              </div>
              <div class="address-line">
                <i class="fas fa-city"></i>
                <span>${userDetails.city}, ${userDetails.pincode}</span>
              </div>
              <div class="address-line">
                <i class="fas fa-map"></i>
                <span>${userDetails.state || 'Maharashtra'}, India</span>
              </div>
              <div class="address-line">
                <i class="fas fa-phone-alt"></i>
                <span>${userDetails.phone}</span>
              </div>
            </div>
          </div>

          <!-- Preferences Card -->
          <div class="enhanced-card">
            <div class="card-header-enhanced">
              <h3><i class="fas fa-sliders-h"></i> Preferences</h3>
            </div>
            <div class="preference-list">
              <div class="preference-row">
                <span><i class="fas fa-envelope" style="margin-right: 8px; color: #C17A5A;"></i> Email Notifications</span>
                <label class="switch">
                  <input type="checkbox" checked id="prefEmail">
                  <span class="slider"></span>
                </label>
              </div>
              <div class="preference-row">
                <span><i class="fas fa-sms" style="margin-right: 8px; color: #C17A5A;"></i> SMS Alerts</span>
                <label class="switch">
                  <input type="checkbox" id="prefSMS">
                  <span class="slider"></span>
                </label>
              </div>
              <div class="preference-row">
                <span><i class="fas fa-newspaper" style="margin-right: 8px; color: #C17A5A;"></i> Newsletter</span>
                <label class="switch">
                  <input type="checkbox" checked id="prefNewsletter">
                  <span class="slider"></span>
                </label>
              </div>
              <div class="preference-row">
                <span><i class="fas fa-tag" style="margin-right: 8px; color: #C17A5A;"></i> Promo Offers</span>
                <label class="switch">
                  <input type="checkbox" checked id="prefPromo">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="account-actions-row">
          <button class="btn-logout" id="logoutAccEnhanced">
            <i class="fas fa-sign-out-alt"></i> Logout
          </button>
          <button class="btn-shopping" id="backHomeAccEnhanced">
            <i class="fas fa-shopping-bag"></i> Continue Shopping
          </button>
        </div>
      </div>
    `;

    // ========== EVENT LISTENERS ==========
    
    // Edit Profile
    container.querySelector('#editProfileBtnEnhanced').addEventListener('click', () => {
      const profileInfoDisplay = container.querySelector('#profileInfoDisplay');
      profileInfoDisplay.innerHTML = `
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">First Name</label>
          <input type="text" id="editFirstName" value="${userDetails.firstName}" placeholder="First Name">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">Last Name</label>
          <input type="text" id="editLastName" value="${userDetails.lastName}" placeholder="Last Name">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">Email</label>
          <input type="email" id="editEmail" value="${userDetails.email || ''}" placeholder="Email">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">Phone</label>
          <input type="tel" id="editPhone" value="${userDetails.phone}" placeholder="Phone">
        </div>
        <button class="save-btn-inline" id="saveProfileBtn">💾 Save Changes</button>
        <button class="cancel-btn-inline" id="cancelProfileBtn">Cancel</button>
      `;
      
      container.querySelector('#saveProfileBtn').addEventListener('click', () => {
        userDetails.firstName = container.querySelector('#editFirstName').value;
        userDetails.lastName = container.querySelector('#editLastName').value;
        userDetails.email = container.querySelector('#editEmail').value;
        userDetails.phone = container.querySelector('#editPhone').value;
        localStorage.setItem('vividUser_pro', JSON.stringify(userDetails));
        renderAccountPage(container);
        showToast("Profile updated successfully! ✅", "#4A6552");
      });
      
      container.querySelector('#cancelProfileBtn').addEventListener('click', () => {
        renderAccountPage(container);
      });
    });

    // Edit Address
    container.querySelector('#editAddressBtnEnhanced').addEventListener('click', () => {
      const addressInfoDisplay = container.querySelector('#addressInfoDisplay');
      addressInfoDisplay.innerHTML = `
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">Street Address</label>
          <input type="text" id="editAddress" value="${userDetails.address}" placeholder="Street Address">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">City</label>
          <input type="text" id="editCity" value="${userDetails.city}" placeholder="City">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">Pincode</label>
          <input type="text" id="editPincode" value="${userDetails.pincode}" placeholder="Pincode">
        </div>
        <div class="edit-input-group">
          <label style="font-size:0.8rem; color:#8a857a;">State</label>
          <select id="editState">
            <option ${userDetails.state === 'Maharashtra' ? 'selected' : ''}>Maharashtra</option>
            <option ${userDetails.state === 'Delhi' ? 'selected' : ''}>Delhi</option>
            <option ${userDetails.state === 'Karnataka' ? 'selected' : ''}>Karnataka</option>
            <option ${userDetails.state === 'Tamil Nadu' ? 'selected' : ''}>Tamil Nadu</option>
            <option ${userDetails.state === 'West Bengal' ? 'selected' : ''}>West Bengal</option>
            <option ${userDetails.state === 'Gujarat' ? 'selected' : ''}>Gujarat</option>
            <option ${userDetails.state === 'Andhra Pradesh' ? 'selected' : ''}>Andhra Pradesh</option>
            <option ${userDetails.state === 'Arunachal Pradesh' ? 'selected' : ''}>Arunachal Pradesh</option>
            <option ${userDetails.state === 'Assam' ? 'selected' : ''}>Assam</option>
            <option ${userDetails.state === 'Bihar' ? 'selected' : ''}>Bihar</option>
            <option ${userDetails.state === 'Chhattisgarh' ? 'selected' : ''}>Chhattisgarh</option>
            <option ${userDetails.state === 'Goa' ? 'selected' : ''}>Goa</option>
            <option ${userDetails.state === 'Haryana' ? 'selected' : ''}>Haryana</option>
            <option ${userDetails.state === 'Himachal Pradesh' ? 'selected' : ''}>Himachal Pradesh</option>
            <option ${userDetails.state === 'Jharkhand' ? 'selected' : ''}>Jharkhand</option>
            <option ${userDetails.state === 'Punjab' ? 'selected' : ''}>Punjab</option>
            <option ${userDetails.state === 'Rajasthan' ? 'selected' : ''}>Rajasthan</option>
            <option ${userDetails.state === 'Uttar Pradesh' ? 'selected' : ''}>Uttar Pradesh</option>
            <option ${userDetails.state === 'Uttarakhand' ? 'selected' : ''}>Uttarakhand</option>
          </select>
        </div>
        <button class="save-btn-inline" id="saveAddressBtn">💾 Save Address</button>
        <button class="cancel-btn-inline" id="cancelAddressBtn">Cancel</button>
      `;
      
      container.querySelector('#saveAddressBtn').addEventListener('click', () => {
        userDetails.address = container.querySelector('#editAddress').value;
        userDetails.city = container.querySelector('#editCity').value;
        userDetails.pincode = container.querySelector('#editPincode').value;
        userDetails.state = container.querySelector('#editState').value;
        localStorage.setItem('vividUser_pro', JSON.stringify(userDetails));
        renderAccountPage(container);
        showToast("Address updated successfully! ✅", "#4A6552");
      });
      
      container.querySelector('#cancelAddressBtn').addEventListener('click', () => {
        renderAccountPage(container);
      });
    });

    // Preference toggles
    ['prefEmail', 'prefSMS', 'prefNewsletter', 'prefPromo'].forEach(id => {
      const toggle = container.querySelector(`#${id}`);
      if (toggle) {
        toggle.addEventListener('change', (e) => {
          const prefName = id.replace('pref', '');
          const status = e.target.checked ? 'enabled' : 'disabled';
          showToast(`${prefName} notifications ${status}`, "#C17A5A");
        });
      }
    });

    // Quick action cards
    container.querySelector('#quickOrders')?.addEventListener('click', () => {
      showToast("Order history coming soon! 📦", "#C17A5A");
    });
    
    container.querySelector('#quickWishlist')?.addEventListener('click', () => {
      showToast("Wishlist feature coming soon! ❤️", "#C17A5A");
    });
    
    container.querySelector('#quickSupport')?.addEventListener('click', () => {
      showToast("Contact us at hello@khusidecors.com", "#C17A5A");
    });

    // Logout
    container.querySelector('#logoutAccEnhanced').addEventListener('click', () => {
      userDetails = null;
      localStorage.removeItem('vividUser_pro');
      showPage('mainPage');
      showToast("Logged out successfully 👋", "#4A6552");
    });

    // Continue Shopping
    container.querySelector('#backHomeAccEnhanced').addEventListener('click', () => showPage('mainPage'));

  } else {
    // ========== LOGIN/SIGNUP VIEW  ==========
    container.innerHTML = `
      <div class="auth-wrapper">
        <div class="auth-container">
          <div class="auth-left">
            <div class="auth-brand">
              <div class="auth-logo" style="font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 1rem;">Khusi Decors</div>
              <p style="font-size: 1.1rem; line-height: 1.6;">Join the Khusi Decors family and discover curated interiors for your dream home.</p>
            </div>
            <div class="auth-benefits" style="margin-top: 2rem;">
              <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                <i class="fas fa-truck"></i> Free Shipping on orders ₹2000+
              </div>
              <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                <i class="fas fa-undo-alt"></i> Easy 7-Day Returns
              </div>
              <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                <i class="fas fa-gift"></i> Exclusive Member Offers
              </div>
              <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                <i class="fas fa-heart"></i> Save to Wishlist
              </div>
            </div>
          </div>
          
          <div class="auth-right">
            <div class="auth-tabs-container">
              <button class="auth-tab-btn active" data-tab="signup">Create Account</button>
              <button class="auth-tab-btn" data-tab="login">Sign In</button>
            </div>
            
            <div id="signupContainer" class="auth-form-container active">
              <div class="input-group">
                <i class="fas fa-user"></i>
                <input type="text" id="signupName" placeholder="Full Name" required>
              </div>
              <div class="input-group">
                <i class="fas fa-envelope"></i>
                <input type="email" id="signupEmail" placeholder="Email Address" required>
              </div>
              <div class="input-group">
                <i class="fas fa-phone"></i>
                <input type="tel" id="signupPhone" placeholder="Phone Number" required>
              </div>
              <div class="input-group">
                <i class="fas fa-location-dot"></i>
                <input type="text" id="signupAddress" placeholder="Street Address" required>
              </div>
              <div class="row-2">
                <div class="input-group">
                  <i class="fas fa-city"></i>
                  <input type="text" id="signupCity" placeholder="City" required>
                </div>
                <div class="input-group">
                  <i class="fas fa-code"></i>
                  <input type="text" id="signupPincode" placeholder="Pincode" required>
                </div>
              </div>
              <div class="input-group">
                <i class="fas fa-map"></i>
                <select id="signupState" required>
                  <option value="">Select State</option>
                  <option>Maharashtra</option>
                  <option>Delhi</option>
                  <option>Karnataka</option>
                  <option>Tamil Nadu</option>
                  <option>West Bengal</option>
                  <option>Gujarat</option>
                </select>
              </div>
              <button type="button" class="auth-submit-btn" id="signupBtn">
                <i class="fas fa-user-plus"></i> Create Account
              </button>
            </div>
            
            <div id="loginContainer" class="auth-form-container">
              <div class="input-group">
                <i class="fas fa-envelope"></i>
                <input type="email" id="loginEmail" placeholder="Email Address" required>
              </div>
              <div class="input-group">
                <i class="fas fa-lock"></i>
                <input type="password" id="loginPassword" placeholder="Password">
              </div>
              <button type="button" class="auth-submit-btn" id="loginBtn">
                <i class="fas fa-sign-in-alt"></i> Sign In
              </button>
            </div>
            
            <button class="btn" id="skipAuth" style="width:100%; margin-top:1rem; background:transparent; border:1px solid #e0dbd0; color:#6c757d;">
              Continue as Guest
            </button>
          </div>
        </div>
      </div>
    `;

    // Tab switching
    container.querySelectorAll('.auth-tab-btn').forEach(b => b.addEventListener('click', (e) => {
      container.querySelectorAll('.auth-tab-btn').forEach(t => t.classList.remove('active'));
      e.target.classList.add('active');
      container.querySelectorAll('.auth-form-container').forEach(f => f.classList.remove('active'));
      container.querySelector('#' + e.target.dataset.tab + 'Container').classList.add('active');
    }));

    // Signup handler
    container.querySelector('#signupBtn').addEventListener('click', () => {
      const name = document.getElementById('signupName')?.value.trim();
      const email = document.getElementById('signupEmail')?.value.trim();
      const phone = document.getElementById('signupPhone')?.value.trim();
      const address = document.getElementById('signupAddress')?.value.trim();
      const city = document.getElementById('signupCity')?.value.trim();
      const pincode = document.getElementById('signupPincode')?.value.trim();
      const state = document.getElementById('signupState')?.value;

      if (!name || !email || !phone || !address || !city || !pincode || !state) {
        showToast("Please fill all fields", "#c7362b");
        return;
      }
      userDetails = {
        firstName: name.split(' ')[0] || "User",
        lastName: name.split(' ')[1] || "",
        email, phone, address, city, pincode, state
      };
      localStorage.setItem('vividUser_pro', JSON.stringify(userDetails));
      showToast("Account created successfully! 🎉", "#4A6552");
      showPage('mainPage');
    });

    // Login handler
    container.querySelector('#loginBtn').addEventListener('click', () => {
      const email = document.getElementById('loginEmail')?.value.trim();
      if (!email) {
        showToast("Please enter your email address", "#c7362b");
        return;
      }
      if (userDetails && userDetails.email === email) {
        showToast("Logged in successfully! ✅", "#4A6552");
        showPage('mainPage');
      } else {
        showToast("Email not found. Please sign up first.", "#c7362b");
        container.querySelector('.auth-tab-btn[data-tab="signup"]')?.click();
      }
    });

    container.querySelector('#skipAuth').addEventListener('click', () => showPage('mainPage'));
  }
}

      // ---------- INITIALIZE ALL EVENT LISTENERS ----------
      function init() {
        // Menu toggle
        document.getElementById('menuToggle').addEventListener('click', () => {
          document.getElementById('sidebar').classList.add('active');
          document.getElementById('overlay').classList.add('active');
        });
        
        // Close sidebar
        document.getElementById('closeSidebar').addEventListener('click', closeSidebar);
        document.getElementById('overlay').addEventListener('click', closeSidebar);
        
        // Logo home
        document.getElementById('logoHome').addEventListener('click', () => showPage('mainPage'));
        
        // Header icons
        document.getElementById('loginIcon').addEventListener('click', () => showPage('account'));
        document.getElementById('cartIcon').addEventListener('click', () => showPage('cart'));
        
        // Sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
          link.addEventListener('click', (e) => {
            const page = e.currentTarget.dataset.page;
            if (page) showPage(page);
          });
        });

        // Desktop navigation links
        document.querySelectorAll('.desktop-nav-link').forEach(link => {
          link.addEventListener('click', (e) => {
            const page = e.currentTarget.dataset.page;
            if (page) showPage(page);
          });
        });
        
        // Footer links
        document.querySelectorAll('.footer-link').forEach(link => {
          link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            if (page) showPage(page);
          });
        });
        
        // Catalog cards
        document.querySelectorAll('.catalog-card').forEach(card => {
          card.addEventListener('click', () => showPage(card.dataset.page));
        });
        
        // Scroll to catalog
        document.getElementById('scrollToCatalog')?.addEventListener('click', () => {
          document.getElementById('catalogSection').scrollIntoView({behavior:'smooth'});
        });
        
        // View all products
        document.getElementById('viewAllProductsBtn')?.addEventListener('click', () => showPage('allProducts'));
        
        // Explore buttons
        document.querySelectorAll('.explore-btn').forEach(btn => {
          btn.addEventListener('click', () => showPage('allProducts'));
        });
        
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const searchWrapper = document.querySelector('.search-dropdown');
        
        if(searchInput && searchWrapper) {
          searchInput.addEventListener('click', (e) => {
            e.stopPropagation();
            searchWrapper.classList.toggle('active');
          });
          
          document.querySelectorAll('.search-option').forEach(option => {
            option.addEventListener('click', (e) => {
              e.stopPropagation();
              const page = option.dataset.page;
              searchInput.value = option.innerText.trim();
              searchWrapper.classList.remove('active');
              if(page) showPage(page);
            });
          });
          
          document.addEventListener('click', (e) => {
            if (!searchWrapper.contains(e.target) && e.target !== searchInput) {
              searchWrapper.classList.remove('active');
            }
          });
        }
        
        // Newsletter
        const newsletterBtn = document.getElementById('newsletterBtn');
        const newsletterInput = document.getElementById('newsletterEmail');
        
        if(newsletterBtn && newsletterInput) {
          newsletterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const email = newsletterInput.value.trim();
            if(email) {
              showToast("Thanks! Please complete your profile →", "#C17A5A");
              showPage('account');
              newsletterInput.value = '';
            } else {
              showToast("Please enter your email", "#c7362b");
            }
          });
        }
        
        // Close modal
        document.getElementById('closeModalBtn')?.addEventListener('click', () => {
          document.getElementById('successModal').classList.remove('active');
          showPage('mainPage');
        });
        
        // Hero slider
        let slideIdx = 0;
        const slides = document.querySelectorAll('.slide');
        if(slides.length > 0) {
          setInterval(() => {
            slides[slideIdx].classList.remove('active-slide');
            slideIdx = (slideIdx + 1) % slides.length;
            slides[slideIdx].classList.add('active-slide');
          }, 4200);
        }

        // ---------- INTERACTIVE STYLE PLANNER SYSTEM ----------
        const plannerData = {
          wallDecor: {
            title: "Wall Art Collection",
            tip: "Combine rich textures like organic cotton macrame and boho tapestries with minimalist clocks to create an inviting, artistic focal wall.",
            img: "IMAGES/WD1.jpg",
            page: "wallDecor",
            items: [
              { name: "Macrame Wall Hanging", price: 899, img: "IMAGES/WD1.jpg" },
              { name: "Boho Tapestry", price: 749, img: "IMAGES/WD5.jpg" },
              { name: "Modern Minimalist", price: 1199, img: "IMAGES/CLCOK3.jpg" }
            ]
          },
          lamps: {
            title: "Cozy Lighting Collection",
            tip: "Layer warm glow effects using hand-woven rattan materials, street-style modern setups, and artistic table sconces to design cozy, comfortable rooms.",
            img: "IMAGES/LAMP2.jpg",
            page: "lamps",
            items: [
              { name: "Rattan Lamp", price: 2499, img: "IMAGES/LAMP2.jpg" },
              { name: "Street Lamp", price: 1799, img: "IMAGES/LAMP.jpg" },
              { name: "Ceramic Table Lamp", price: 2099, img: "IMAGES/LAMP5.jpg" }
            ]
          },
          vases: {
            title: "Vase & Vessel Collection",
            tip: "Accentuate shelves and dressers with handcrafted ribbed vessels, natural terracotta structures, and bud vase pairs to support fresh or dried botanicals.",
            img: "IMAGES/VASE3.jpg",
            page: "vases",
            items: [
              { name: "Terracotta Set", price: 1099, img: "IMAGES/VASE1.jpg" },
              { name: "Ribbed Vase", price: 1899, img: "IMAGES/VASE2.jpg" },
              { name: "Bud Vase Duo", price: 2399, img: "IMAGES/VASEFIVR.jpg" }
            ]
          }
        };

        let activeCollection = 'wallDecor';

        function updatePlannerDisplay() {
          const data = plannerData[activeCollection];
          if(!data) return;

          // Update image
          const imgEl = document.getElementById('visualizerImage');
          if(imgEl) {
            imgEl.style.backgroundImage = `url('${data.img}')`;
          }

          // Update text overlays
          const titleEl = document.getElementById('visualizerTitle');
          const tipEl = document.getElementById('visualizerStylingTip');
          if(titleEl) titleEl.innerText = data.title;
          if(tipEl) tipEl.innerHTML = `<strong>Styling Tip:</strong> ${data.tip}`;

          // Populate list of elements
          const listEl = document.getElementById('recommendationsList');
          if(listEl) {
            listEl.innerHTML = data.items.map(item => `
              <div class="rec-pill">
                <img src="${item.img}" alt="${item.name}">
                <div class="rec-info">
                  <h5>${item.name}</h5>
                  <p>₹${item.price}</p>
                </div>
                <button class="rec-action add-to-planner-cart" data-name="${item.name}" data-price="${item.price}" title="Add to Bag">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            `).join('');

            // Attach cart additions
            listEl.querySelectorAll('.add-to-planner-cart').forEach(btn => {
              btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const name = btn.dataset.name;
                const price = parseInt(btn.dataset.price);
                cart.push({name, price});
                saveCart();
                showToast(`${name} added ✨`, "#C17A5A");
              });
            });
          }

          // Hook redirection button
          const exploreBtn = document.getElementById('plannerExploreBtn');
          if(exploreBtn) {
            exploreBtn.onclick = () => showPage(data.page);
          }
        }

        // Bind planner collection selection buttons
        document.querySelectorAll('#collectionSelector .planner-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            document.querySelectorAll('#collectionSelector .planner-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeCollection = btn.dataset.collection;
            updatePlannerDisplay();
          });
        });

        // Initialize planner display state
        updatePlannerDisplay();

        // ---------- STATIC SECTIONS TRIGGERS ----------

        // Bestsellers cart addition bindings
        document.querySelectorAll('#mainPage .add-to-cart').forEach(btn => {
          btn.addEventListener('click', () => {
            const name = btn.dataset.name, price = parseInt(btn.dataset.price);
            cart.push({name, price});
            saveCart();
            showToast(`${name} added ✨`, "#C17A5A");
          });
        });

        document.querySelectorAll('#mainPage .buy-now').forEach(btn => {
          btn.addEventListener('click', () => {
            const name = btn.dataset.name, price = parseInt(btn.dataset.price);
            cart.push({name, price});
            saveCart();
            showPage('cart');
          });
        });

        // Bestsellers card redirects to details view
        document.querySelectorAll('#mainPage .featured-card').forEach(card => {
          const img = card.querySelector('img');
          const h4 = card.querySelector('h4');
          const name = h4?.innerText.trim();
          if (name) {
            [img, h4].forEach(el => {
              if (el) {
                el.style.cursor = 'pointer';
                el.addEventListener('click', () => {
                  showPage('productDetail', name);
                });
              }
            });
          }
        });

        // Consultation Form
        const consultForm = document.getElementById('consultationForm');
        if(consultForm) {
          consultForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('consultName')?.value.trim();
            const phone = document.getElementById('consultPhone')?.value.trim();
            if(name && phone) {
              showToast(`Thank you ${name}! Our styling designer will contact you shortly. 📞`, "#4A6552");
              consultForm.reset();
            } else {
              showToast("Please fill in all fields", "#c7362b");
            }
          });
        }

        // Initial setup
        updateCartCount();
        showPage('mainPage');
      }

      // ---------- PRODUCT DETAIL PAGE ----------
      function findProductByName(name) {
        for (const cat in products) {
          const found = products[cat].find(p => p.name === name);
          if (found) {
            return { ...found, category: cat };
          }
        }
        // Fallback for featured products not in specific lists
        const allTagged = [];
        Object.entries(products).forEach(([cat, items]) => {
          items.forEach(item => allTagged.push({ ...item, category: cat }));
        });
        const exact = allTagged.find(p => p.name === name);
        if (exact) return exact;
        
        // Return dummy default matching first item
        return { name: "Macrame Wall Hanging", price: 899, img: "IMAGES/WD1.jpg", category: "wallDecor" };
      }

      function getProductGalleryImages(product) {
        const list = [product.img];
        const cat = product.category;
        
        const categoryAlternates = {
          wallDecor: [
            "IMAGES/WD3.jpg",
            "IMAGES/WD5.jpg",
            "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?q=80&w=600&auto=format",
            "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?q=80&w=600&auto=format"
          ],
          artificialPlants: [
            "IMAGES/AP2.jpg",
            "IMAGES/AP4.jpg",
            "https://images.unsplash.com/photo-1545241047-6083a3684587?q=80&w=600&auto=format",
            "https://images.unsplash.com/photo-1485955900006-10f4d324d411?q=80&w=600&auto=format"
          ],
          lamps: [
            "IMAGES/LAMP1.jpg",
            "IMAGES/LAMP3.jpg",
            "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?q=80&w=600&auto=format",
            "https://images.unsplash.com/photo-1540518614846-7eded433c457?q=80&w=600&auto=format"
          ],
          vases: [
            "IMAGES/VASE1.jpg",
            "IMAGES/VASE4.jpg",
            "https://images.unsplash.com/photo-1612196808214-b8e1d6145a8c?q=80&w=600&auto=format",
            "https://images.unsplash.com/photo-1578500494198-246f612d3b3d?q=80&w=600&auto=format"
          ],
          clocks: [
            "IMAGES/CLOCK1.jpg",
            "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?q=80&w=600&auto=format",
            "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=600&auto=format"
          ]
        };

        const alternates = categoryAlternates[cat] || [
          "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=600&auto=format",
          "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=600&auto=format"
        ];

        alternates.forEach(url => {
          if (url !== product.img && list.length < 3) {
            list.push(url);
          }
        });

        return list;
      }

      function renderProductDetail(container, product) {
        if (typeof product === 'string') {
          product = findProductByName(product);
        }
        if (!product) {
          showPage('mainPage');
          return;
        }

        const imagesList = getProductGalleryImages(product);
        const catLabel = categoryMeta[product.category]?.label || product.category;
        
        const sameCatProducts = products[product.category] || [];
        const related = sameCatProducts
          .filter(p => p.name !== product.name)
          .slice(0, 4);

        container.innerHTML = `
          <div class="product-detail-wrapper">
            <div class="product-detail-grid">
              
              <!-- Left Column: Thumbnail Switcher Gallery -->
              <div class="product-gallery-container">
                <div class="product-gallery-thumbs">
                  ${imagesList.map((url, idx) => `
                    <img src="${url}" alt="Thumbnail ${idx+1}" class="gallery-thumb-item ${idx === 0 ? 'active' : ''}" data-idx="${idx}">
                  `).join('')}
                </div>
                <div class="product-gallery-main">
                  <img src="${imagesList[0]}" alt="${product.name}" id="mainProductImg">
                </div>
              </div>

              <!-- Right Column: Details & Actions -->
              <div class="product-info-panel">
                <span class="product-info-cat">${catLabel}</span>
                <h2 class="product-info-title">${product.name}</h2>
                
                <div class="product-info-rating">
                  <div class="stars">
                    <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
                  </div>
                  <span class="reviews-count">(18 Verified Reviews)</span>
                </div>

                <div class="product-info-price">₹${product.price.toLocaleString('en-IN')}</div>
                
                <p class="product-info-desc">
                  Artisan crafted from premium biodegradable materials. This statement masterpiece brings elegant styling accents and soft organic texture to bedrooms, hallways, or living spaces. Designed carefully to harmonize with modern minimalist and rich bohemian decors alike.
                </p>

                <div class="product-info-actions">
                  <div class="qty-control-wrapper">
                    <span class="qty-control-label">Quantity:</span>
                    <div class="quantity-selector">
                      <button id="detailQtyDec">-</button>
                      <span id="detailQtyVal">1</span>
                      <button id="detailQtyInc">+</button>
                    </div>
                  </div>
                  <div class="btn-group" style="justify-content: flex-start; margin-top: 1rem; gap: 1.25rem;">
                    <button class="btn btn-primary" id="detailAddToCart" style="padding: 0.9rem 2.5rem; font-size: 0.95rem; font-weight: 700; border-radius: 50px;">
                      <i class="fas fa-bag-shopping" style="margin-right: 8px;"></i> Add to Bag
                    </button>
                    <button class="btn btn-outline" id="detailBuyNow" style="padding: 0.9rem 2.5rem; font-size: 0.95rem; font-weight: 700; border-radius: 50px; border-width: 2px;">
                      Buy Now
                    </button>
                  </div>
                </div>

                <div class="product-detail-badges">
                  <div class="detail-badge-item"><i class="fas fa-truck"></i> Free Shipping on ₹2000+</div>
                  <div class="detail-badge-item"><i class="fas fa-rupee-sign"></i> Cash on Delivery</div>
                  <div class="detail-badge-item"><i class="fas fa-shield-halved"></i> 100% Handcrafted</div>
                  <div class="detail-badge-item"><i class="fas fa-seedling"></i> Eco-friendly Materials</div>
                </div>
              </div>

            </div>

            <!-- Long Description Accordion/Tabs -->
            <div class="product-description-tabs" style="margin-top: 3.5rem; border-top: 1px solid #f0ede8; padding-top: 3rem;">
              <div class="tabs-header" style="display:flex; gap: 2rem; border-bottom: 2.5px solid #f7f5f0; margin-bottom: 1.5rem;">
                <h3 class="tab-title active" style="font-family:'Playfair Display', serif; font-size:1.4rem; padding-bottom: 0.75rem; border-bottom: 2.5px solid var(--primary); margin-bottom: -2.5px; cursor:pointer; color: var(--dark-charcoal);">Detailed Craftsmanship & Styling Guidelines</h3>
              </div>
              <div class="tab-content" style="color:#5C5850; line-height: 1.8; font-size: 0.95rem; display: flex; flex-direction: column; gap: 1rem;">
                <p>
                  This hand-selected piece represents the pinnacle of sustainable luxury. Individually woven or structured by multi-generational Indian craftspeople, it features carefully processed natural raw materials (organic cotton fibers, seasoned teak wood, or hand-fired ceramic clay) sourced directly from local eco-farms.
                </p>
                <p>
                  <strong>Design Styling Recommendations:</strong> For the ultimate designer look, display this piece in high-visibility areas such as entryway consoles, bedroom nightstands, or central living space gallery walls. Pair it with soft warm-tone accent lighting and dry organic botanical sprigs to capture an inviting, cohesive, and magazine-worthy aesthetic.
                </p>
                <ul style="padding-left: 1.5rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.5rem; margin-top: 0.5rem; list-style-type: square; color: #5C5850;">
                  <li><strong>Materials:</strong> 100% natural organic cotton, seasoned pine support, clay components</li>
                  <li><strong>Dimensions:</strong> Standard Size: 32" H x 18" W x 2" D</li>
                  <li><strong>Origin:</strong> Proudly designed and hand-woven in Maharashtra, India</li>
                  <li><strong>Care:</strong> Gentle dry dusting or light vacuum clean; avoid direct exposure to moisture</li>
                </ul>
              </div>
            </div>

            <!-- Related Products Section -->
            ${related.length === 0 ? '' : `
              <div class="related-products-section">
                <h3 class="related-products-title">Complete the Styling Look</h3>
                <p class="related-products-subtitle">Handpicked masterworks to pair perfectly in your room spaces</p>
                
                <div class="related-grid">
                  ${related.map(item => `
                    <div class="shop-product-card related-product-card" data-name="${item.name}">
                      <div class="shop-card-img-wrap" style="cursor: pointer;">
                        <img src="${item.img}" alt="${item.name}" loading="lazy">
                        <span class="shop-card-cat-tag">${catLabel}</span>
                      </div>
                      <div class="shop-card-body">
                        <h4 class="shop-card-name" style="cursor: pointer;">${item.name}</h4>
                        <p class="shop-card-price">₹${item.price.toLocaleString('en-IN')}</p>
                        <div class="shop-card-actions">
                          <button class="btn add-to-cart" data-name="${item.name}" data-price="${item.price}">
                            <i class="fas fa-bag-shopping"></i> Add to Bag
                          </button>
                          <button class="btn btn-outline buy-now" data-name="${item.name}" data-price="${item.price}">
                            Buy Now
                          </button>
                        </div>
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            `}
          </div>
        `;

        // GALLERY SWITCHER EVENT LISTENERS
        const mainImg = container.querySelector('#mainProductImg');
        const thumbs = container.querySelectorAll('.gallery-thumb-item');
        thumbs.forEach(thumb => {
          thumb.addEventListener('click', () => {
            thumbs.forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
            const idx = parseInt(thumb.dataset.idx);
            if (mainImg) {
              mainImg.style.opacity = '0.3';
              setTimeout(() => {
                mainImg.src = imagesList[idx];
                mainImg.style.opacity = '1';
              }, 120);
            }
          });
        });

        // QUANTITY SELECTOR EVENT LISTENERS
        let quantity = 1;
        const qtyVal = container.querySelector('#detailQtyVal');
        container.querySelector('#detailQtyDec')?.addEventListener('click', () => {
          if (quantity > 1) {
            quantity--;
            if (qtyVal) qtyVal.innerText = quantity;
          }
        });
        container.querySelector('#detailQtyInc')?.addEventListener('click', () => {
          quantity++;
          if (qtyVal) qtyVal.innerText = quantity;
        });

        // ACTION BUTTONS EVENT LISTENERS
        container.querySelector('#detailAddToCart')?.addEventListener('click', () => {
          for (let i = 0; i < quantity; i++) {
            cart.push({ name: product.name, price: product.price });
          }
          saveCart();
          showToast(`${quantity}x ${product.name} added to Bag ✨`, "#C17A5A");
        });

        container.querySelector('#detailBuyNow')?.addEventListener('click', () => {
          for (let i = 0; i < quantity; i++) {
            cart.push({ name: product.name, price: product.price });
          }
          saveCart();
          showPage('cart');
        });

        // RELATED CARDS SELECTION BINDING
        container.querySelectorAll('.related-product-card').forEach(card => {
          const name = card.dataset.name;
          card.querySelectorAll('.shop-card-img-wrap, .shop-card-name').forEach(el => {
            el.addEventListener('click', () => {
              showPage('productDetail', name);
            });
          });

          card.querySelector('.add-to-cart')?.addEventListener('click', (e) => {
            e.stopPropagation();
            const btn = e.currentTarget;
            const n = btn.dataset.name;
            const p = parseInt(btn.dataset.price);
            cart.push({ name: n, price: p });
            saveCart();
            showToast(`${n} added ✨`, "#C17A5A");
          });

          card.querySelector('.buy-now')?.addEventListener('click', (e) => {
            e.stopPropagation();
            const btn = e.currentTarget;
            const n = btn.dataset.name;
            const p = parseInt(btn.dataset.price);
            cart.push({ name: n, price: p });
            saveCart();
            showPage('cart');
          });
        });
      }

      // ---------- ABOUT PAGE ----------
      function renderAboutPage(container) {
        container.innerHTML = `
          <div class="about-page-wrapper">
            <!-- Sleek Compact Banner -->
            <div class="page-banner" style="background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.55)), url('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=1600&auto=format');">
              <div class="banner-content">
                <h1>Our Story</h1>
                <p>Crafting luxury, preserving artisanal spirit</p>
              </div>
            </div>
            
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 1.5rem 4rem;">
              <div class="about-grid-decor">
                <div class="about-story-content">
                  <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; color: var(--primary);">Craftsmanship</span>
                  <h2 style="font-family: 'Playfair Display', serif; font-size: 2.2rem; margin: 0.5rem 0 1.25rem;">Designing Homes with Soul</h2>
                  <p style="color: #6E695F; line-height: 1.7; margin-bottom: 1rem;">
                    Founded with the dream of bridging traditional Indian artistry and contemporary interior design, Khusi Decors stands as a testament to ethical design and sustainable luxury. Each item in our gallery tells a rich, unique story of master dedication.
                  </p>
                  <p style="color: #6E695F; line-height: 1.7;">
                    We believe a home is a dynamic sanctuary that represents your milestones. We work directly with generational artisans, sourcing natural, biodegradable materials to bring timeless, warm elements into your daily life.
                  </p>
                </div>
                <div>
                  <img src="https://images.unsplash.com/photo-1616486038856-74749f7004d7?q=80&w=800&auto=format" alt="Artisan Crafting" style="width: 100%; border-radius: 28px; box-shadow: var(--shadow-hover); max-height: 380px; object-fit: cover;">
                </div>
              </div>
              
              <h3 style="text-align: center; font-size: 1.8rem; font-family: 'Playfair Display', serif; margin-top: 4rem; margin-bottom: 2rem;">Our Core Pillars</h3>
              <div class="about-features-panel">
                <div class="about-feature-card">
                  <i class="fas fa-hand-holding-heart"></i>
                  <h4>100% Handcrafted</h4>
                  <p>Preserving regional Indian craftsmanship with ethical wage practices.</p>
                </div>
                <div class="about-feature-card">
                  <i class="fas fa-seedling"></i>
                  <h4>Eco-Conscious</h4>
                  <p>Using natural materials like jute, organic cotton, wood, and organic clay.</p>
                </div>
                <div class="about-feature-card">
                  <i class="fas fa-gem"></i>
                  <h4>Premium Finish</h4>
                  <p>Carefully hand-checked quality ensures high durability and stunning aesthetics.</p>
                </div>
              </div>
            </div>
          </div>
        `;
      }

      // ---------- CONTACT PAGE ----------
      function renderContactPage(container) {
        container.innerHTML = `
          <div class="contact-page-wrapper">
            <!-- Sleek Compact Banner -->
            <div class="page-banner" style="background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.55)), url('https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?q=80&w=1600&auto=format');">
              <div class="banner-content">
                <h1>Get in Touch</h1>
                <p>Let's collaborate on styling your sanctuary</p>
              </div>
            </div>
            
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 1.5rem 4rem;">
              <div class="contact-content-grid">
                <div class="contact-card-premium">
                  <h3 style="font-family: 'Playfair Display', serif; font-size: 1.8rem; margin-bottom: 1rem;">Direct Channels</h3>
                  <p style="color: #6E695F; line-height: 1.6; margin-bottom: 2rem;">Have questions regarding a product custom size, bulk wholesale orders, or looking to schedule a return? Reach our design concierge team via any of these channels:</p>
                  
                  <div class="contact-channels">
                    <div class="channel-item">
                      <div class="channel-icon"><i class="fas fa-envelope"></i></div>
                      <div class="channel-details">
                        <h5>Email Us</h5>
                        <p>hello@khusidecors.com</p>
                      </div>
                    </div>
                    <div class="channel-item">
                      <div class="channel-icon"><i class="fas fa-phone-alt"></i></div>
                      <div class="channel-details">
                        <h5>Call/WhatsApp</h5>
                        <p>+91 98765 43210</p>
                      </div>
                    </div>
                    <div class="channel-item">
                      <div class="channel-icon"><i class="fas fa-map-marker-alt"></i></div>
                      <div class="channel-details">
                        <h5>Head Studio</h5>
                        <p>Level 4, High Street Phoenix, Senapati Bapat Marg, Mumbai, MH</p>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Google Map Iframe Embed -->
                  <div class="contact-map-wrapper" style="margin-top: 1.8rem; border-radius: 16px; overflow: hidden; box-shadow: var(--shadow-soft); border: 1px solid #f0ede8; height: 200px; width: 100%;">
                    <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3771.803730225134!2d72.82283997576595!3d18.995304382190367!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3be7cef706fcb665%3A0xe7c569f1a5c68f5c!2sHigh%20Street%20Phoenix!5e0!3m2!1sen!2sin!4v1716654000000!5m2!1sen!2sin" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
                  </div>
                </div>
                
                <form class="contact-form-premium" id="conciergeContactForm">
                  <h3>Drop Us a Message</h3>
                  <p style="color: #6E695F; font-size: 0.9rem; margin-bottom: 0.5rem;">Send a query and get a designer callback within 24 hours.</p>
                  
                  <div class="edit-input-group">
                    <input type="text" id="contactName" placeholder="Full Name" required style="border-radius: 12px; padding: 0.8rem 1rem;">
                  </div>
                  <div class="edit-input-group">
                    <input type="tel" id="contactPhone" placeholder="Phone Number" required style="border-radius: 12px; padding: 0.8rem 1rem;">
                  </div>
                  <div class="edit-input-group">
                    <textarea id="contactMsg" placeholder="Describe your design styling requirements..." required rows="5" style="width: 100%; border: 1px solid #e0dbd0; border-radius: 12px; padding: 0.8rem 1rem; font-family: inherit; font-size: 0.85rem; resize: none;"></textarea>
                  </div>
                  <button type="submit" class="place-order-btn-enhanced" style="margin-top: 0.5rem; font-size: 0.9rem; font-weight: 600;">
                    <i class="fas fa-paper-plane"></i> Send Concierge Message
                  </button>
                </form>
              </div>
            </div>
          </div>
        `;
        
        document.getElementById('conciergeContactForm')?.addEventListener('submit', (e) => {
          e.preventDefault();
          const name = document.getElementById('contactName').value;
          showToast(`Thank you ${name}! Callback registered successfully! 📨`, "#4A6552");
          e.target.reset();
        });
      }

      // Run initialization when DOM is fully loaded
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
      } else {
        init();
      }
    })();
