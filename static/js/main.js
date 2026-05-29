// ---------- GLOBAL FRONTEND LOGIC ----------
window.KhushiDecors = {
  // Retrieve cart from localStorage
  getCart: function() {
    return JSON.parse(localStorage.getItem('vividCart_pro')) || [];
  },

  // Save cart to localStorage and update header counts
  saveCart: function(cart) {
    localStorage.setItem('vividCart_pro', JSON.stringify(cart));
    this.updateCartCount();
  },

  // Sync header cart indicators
  updateCartCount: function() {
    const cart = this.getCart();
    const countEl = document.getElementById('cartCount');
    if (countEl) {
      countEl.innerText = cart.length;
    }
  },

  // Retrieve user details from localStorage
  getUser: function() {
    return JSON.parse(localStorage.getItem('vividUser_pro')) || null;
  },

  // Save user details to localStorage
  saveUser: function(user) {
    localStorage.setItem('vividUser_pro', JSON.stringify(user));
  },

  // Display a feedback toast message to user
  showToast: function(msg, bg = "#C17A5A") {
    let toast = document.createElement('div');
    toast.innerText = msg;
    toast.style.position = 'fixed';
    toast.style.bottom = '30px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.backgroundColor = bg;
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '60px';
    toast.style.zIndex = '9999';
    toast.style.fontWeight = '500';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.transition = 'all 0.3s ease';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 1800);
  },

  // Show order success modal
  showSuccessModal: function() {
    const modal = document.getElementById('successModal');
    if (modal) {
      modal.classList.add('active');
    }
  },

  // Hide order success modal
  hideSuccessModal: function() {
    const modal = document.getElementById('successModal');
    if (modal) {
      modal.classList.remove('active');
    }
  }
};

// Initialize common layout behaviors
document.addEventListener('DOMContentLoaded', () => {
  // Sync cart indicators immediately
  window.KhushiDecors.updateCartCount();

  // Mobile Menu Toggling
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  const closeSidebar = document.getElementById('closeSidebar');

  if (menuToggle && sidebar && overlay) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.add('active');
      overlay.classList.add('active');
    });
  }

  const hideMenu = () => {
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
  };

  if (closeSidebar) closeSidebar.addEventListener('click', hideMenu);
  if (overlay) overlay.addEventListener('click', hideMenu);

  // Search dropdown trigger
  const searchInput = document.getElementById('searchInput');
  const searchWrapper = document.querySelector('.search-dropdown');
  const searchOptions = document.querySelectorAll('.search-option');

  if (searchInput && searchWrapper) {
    searchInput.addEventListener('click', (e) => {
      e.stopPropagation();
      searchWrapper.classList.toggle('active');
    });

    searchOptions.forEach(option => {
      option.addEventListener('click', (e) => {
        e.stopPropagation();
        const page = option.dataset.page;
        searchInput.value = option.innerText.trim();
        searchWrapper.classList.remove('active');
        
        // Navigation: Go to shop page with selected category filter parameter
        if (page === 'allProducts') {
          window.location.href = '/shop';
        } else if (page) {
          window.location.href = `/shop?category=${page}`;
        }
      });
    });

    document.addEventListener('click', (e) => {
      if (!searchWrapper.contains(e.target) && e.target !== searchInput) {
        searchWrapper.classList.remove('active');
      }
    });
  }

  // Newsletter Subscriptions
  const newsletterBtn = document.getElementById('newsletterBtn');
  const newsletterInput = document.getElementById('newsletterEmail');

  if (newsletterBtn && newsletterInput) {
    newsletterBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const email = newsletterInput.value.trim();
      if (email) {
        window.KhushiDecors.showToast("Thanks! Please complete your profile →", "#C17A5A");
        setTimeout(() => {
          window.location.href = '/account';
        }, 1200);
        newsletterInput.value = '';
      } else {
        window.KhushiDecors.showToast("Please enter your email", "#c7362b");
      }
    });
  }

  // Close Success Modal Btn
  const closeModalBtn = document.getElementById('closeModalBtn');
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      window.KhushiDecors.hideSuccessModal();
      window.location.href = '/';
    });
  }
});
