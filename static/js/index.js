// ---------- HOMEPAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;

  // 1. Hero banner auto slider transitions
  let slideIdx = 0;
  const slides = document.querySelectorAll('.slide');
  if (slides.length > 0) {
    setInterval(() => {
      slides[slideIdx].classList.remove('active-slide');
      slideIdx = (slideIdx + 1) % slides.length;
      slides[slideIdx].classList.add('active-slide');
    }, 4200);
  }

  // Scroll to catalog section action
  const scrollToCatalog = document.getElementById('scrollToCatalog');
  const catalogSection = document.getElementById('catalogSection');
  if (scrollToCatalog && catalogSection) {
    scrollToCatalog.addEventListener('click', () => {
      catalogSection.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // 2. Curated Bestsellers cart bindings
  const featuredCards = document.querySelectorAll('.featured-card');
  featuredCards.forEach(card => {
    // Add to bag button click
    const addBtn = card.querySelector('.add-to-cart');
    const buyBtn = card.querySelector('.buy-now');

    if (addBtn) {
      addBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = addBtn.dataset.name;
        const price = parseInt(addBtn.dataset.price);
        const cart = KD.getCart();
        cart.push({ name, price });
        KD.saveCart(cart);
        KD.showToast(`${name} added ✨`, "#C17A5A");
      });
    }

    if (buyBtn) {
      buyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = buyBtn.dataset.name;
        const price = parseInt(buyBtn.dataset.price);
        const cart = KD.getCart();
        cart.push({ name, price });
        KD.saveCart(cart);
        window.location.href = '/cart';
      });
    }

    // Card thumbnail clicks -> navigate to product detail
    const img = card.querySelector('img');
    const title = card.querySelector('h4');
    const pId = card.dataset.id;
    const preselect = card.dataset.preselect;

    if (pId) {
      [img, title].forEach(el => {
        if (el) {
          el.style.cursor = 'pointer';
          el.addEventListener('click', () => {
            let url = `/product/${pId}`;
            if (preselect) {
              url += `?preselect=${encodeURIComponent(preselect)}`;
            }
            window.location.href = url;
          });
        }
      });
    }
  });

  // Category navigation cards clicks -> redirect to shop category
  const catalogCards = document.querySelectorAll('.catalog-card');
  catalogCards.forEach(card => {
    card.addEventListener('click', () => {
      const cat = card.dataset.page;
      if (cat === 'allProducts') {
        window.location.href = '/shop';
      } else if (cat) {
        window.location.href = `/shop?category=${cat}`;
      }
    });
  });

  // View entire catalogue button redirect
  const viewAllBtn = document.getElementById('viewAllProductsBtn');
  if (viewAllBtn) {
    viewAllBtn.addEventListener('click', () => {
      window.location.href = '/shop';
    });
  }

  // 3. Interactive Style Planner System
  const plannerData = window.PLANNER_DATA || {};

  let activeCollection = 'wallArt';

  function updatePlannerDisplay() {
    const data = plannerData[activeCollection];
    if (!data) return;

    // Update Image background
    const imgEl = document.getElementById('visualizerImage');
    if (imgEl) {
      imgEl.style.backgroundImage = `url('${data.img}')`;
    }

    // Update Text overlays
    const titleEl = document.getElementById('visualizerTitle');
    const tipEl = document.getElementById('visualizerStylingTip');
    if (titleEl) titleEl.innerText = data.title;
    if (tipEl) tipEl.innerHTML = `<strong>Styling Tip:</strong> ${data.tip}`;

    // Populate recommendation pills list
    const listEl = document.getElementById('recommendationsList');
    if (listEl) {
      listEl.innerHTML = (data.items || []).map(item => `
        <div class="rec-pill">
          <img src="${item.image_url}" alt="${item.name}">
          <div class="rec-info">
            <h5>${item.name}</h5>
            <p>₹${item.price}</p>
          </div>
          <button class="rec-action add-to-planner-cart" data-name="${item.name}" data-price="${item.price}" data-sku="${item.sku || ''}" title="Add to Bag">
            <i class="fas fa-plus"></i>
          </button>
        </div>
      `).join('');

      // Bind add-to-cart clicks for the recommendation pills
      listEl.querySelectorAll('.add-to-planner-cart').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const name = btn.dataset.name;
          const price = parseInt(btn.dataset.price);
          const sku = btn.dataset.sku || '';
          const cart = KD.getCart();
          cart.push({ name, price, sku });
          KD.saveCart(cart);
          KD.showToast(`${name} added ✨`, "#C17A5A");
        });
      });
    }

    // Bind styling collection explore redirects
    const exploreBtn = document.getElementById('plannerExploreBtn');
    if (exploreBtn) {
      exploreBtn.onclick = () => {
        window.location.href = `/shop?category=${data.page}`;
      };
    }
  }

  // Swapping collection buttons
  const plannerBtns = document.querySelectorAll('#collectionSelector .planner-btn');
  plannerBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      plannerBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCollection = btn.dataset.collection;
      updatePlannerDisplay();
    });
  });

  // Initial planner rendering call
  if (plannerBtns.length > 0) {
    updatePlannerDisplay();
  }

  // 4. Consultation Virtual Appointment Form Submit
  const consultForm = document.getElementById('consultationForm');
  if (consultForm) {
    consultForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('consultName').value.trim();
      const phone = document.getElementById('consultPhone').value.trim();
      const csrfToken = document.getElementById('consultCsrf').value;

      if (!name || !phone) {
        KD.showToast("Please fill in all fields", "#c7362b");
        return;
      }

      const formData = new FormData();
      formData.append('name', name);
      formData.append('email', 'consultation@khushidecors.com');
      formData.append('phone', phone);
      formData.append('message', 'Virtual Styling Consultation Request');
      formData.append('csrf_token', csrfToken);

      fetch('/contact', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          KD.showToast(`Thank you ${name}! Our styling designer will contact you shortly. 📞`, "#4A6552");
          consultForm.reset();
        } else {
          KD.showToast(data.error || "Submission failed", "#c7362b");
        }
      })
      .catch(err => {
        KD.showToast("Connection error, please try again", "#c7362b");
      });
    });
  }
});
