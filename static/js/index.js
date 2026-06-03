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
  const plannerData = {
    wallDecor: {
      title: "Wall Art Collection",
      tip: "Combine rich textures like organic cotton macrame and boho tapestries with minimalist clocks to create an inviting, artistic focal wall.",
      img: "/static/images/WD1.jpg",
      page: "wallDecor",
      items: [
        { name: "Macrame Wall Hanging", price: 899, img: "/static/images/WD1.jpg" },
        { name: "Boho Tapestry", price: 749, img: "/static/images/WD5.jpg" },
        { name: "Modern Minimalist", price: 1199, img: "/static/images/CLCOK3.jpg" }
      ]
    },
    lamps: {
      title: "Cozy Lighting Collection",
      tip: "Layer warm glow effects using hand-woven rattan materials, street-style modern setups, and artistic table sconces to design cozy, comfortable rooms.",
      img: "/static/images/LAMP2.jpg",
      page: "lamps",
      items: [
        { name: "Rattan Lamp", price: 2499, img: "/static/images/LAMP2.jpg" },
        { name: "Street Lamp", price: 1799, img: "/static/images/LAMP.jpg" },
        { name: "Ceramic Table Lamp", price: 2099, img: "/static/images/LAMP5.jpg" }
      ]
    },
    vases: {
      title: "Vase & Vessel Collection",
      tip: "Accentuate shelves and dressers with handcrafted ribbed vessels, natural terracotta structures, and bud vase pairs to support fresh or dried botanicals.",
      img: "/static/images/VASE3.jpg",
      page: "vases",
      items: [
        { name: "Terracotta Set", price: 1099, img: "/static/images/VASE1.jpg" },
        { name: "Ribbed Vase", price: 1899, img: "/static/images/VASE2.jpg" },
        { name: "Bud Vase Duo", price: 2399, img: "/static/images/VASEFIVR.jpg" }
      ]
    }
  };

  let activeCollection = 'wallDecor';

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

      // Bind add-to-cart clicks for the recommendation pills
      listEl.querySelectorAll('.add-to-planner-cart').forEach(btn => {
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
      if (name && phone) {
        KD.showToast(`Thank you ${name}! Our styling designer will contact you shortly. 📞`, "#4A6552");
        consultForm.reset();
      } else {
        KD.showToast("Please fill in all fields", "#c7362b");
      }
    });
  }
});
