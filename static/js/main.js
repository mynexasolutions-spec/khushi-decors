// ---------- GLOBAL FRONTEND LOGIC ----------
window.KhushiDecors = {
  // Retrieve cart (fallback to empty)
  getCart: function() {
    return [];
  },

  // Save cart (fallback mock)
  saveCart: function(cart) {
    // Session cart handles persistence on the backend
  },

  // Sync header cart indicators
  updateCartCount: function() {
    // Do not overwrite cartCount as it is rendered by Flask session on page load
  },

  // Add to cart via AJAX (Flask session)
  addToCartAjax: function(productId, variationId, qty, selectedOptions, callback) {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const tokenVal = csrfMeta ? csrfMeta.getAttribute('content') : '';
    
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('variation_id', variationId || '');
    formData.append('selected_options', selectedOptions || '');
    formData.append('qty', qty || 1);
    
    fetch('/cart/add', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': tokenVal
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const countEl = document.getElementById('cartCount');
        if (countEl) countEl.innerText = data.cart_count;
        if (callback) callback(null, data);
      } else {
        if (callback) callback(data.message || 'Error adding to cart', null);
      }
    })
    .catch(err => {
      console.error('Error in addToCartAjax:', err);
      if (callback) callback(err, null);
    });
  },

  // Update cart quantity via AJAX (Flask session)
  updateCartQtyAjax: function(key, delta, callback) {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const tokenVal = csrfMeta ? csrfMeta.getAttribute('content') : '';
    
    const formData = new FormData();
    formData.append('key', key);
    formData.append('delta', delta);
    
    fetch('/cart/ajax_update', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': tokenVal
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        if (callback) callback(null, data);
      } else {
        if (callback) callback(data.error || 'Error updating cart', null);
      }
    })
    .catch(err => {
      console.error('Error in updateCartQtyAjax:', err);
      if (callback) callback(err, null);
    });
  },

  // Remove cart item via AJAX (Flask session)
  removeCartItemAjax: function(key, callback) {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const tokenVal = csrfMeta ? csrfMeta.getAttribute('content') : '';
    
    const formData = new FormData();
    formData.append('key', key);
    
    fetch('/cart/ajax_remove', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': tokenVal
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        if (callback) callback(null, data);
      } else {
        if (callback) callback(data.error || 'Error removing item', null);
      }
    })
    .catch(err => {
      console.error('Error in removeCartItemAjax:', err);
      if (callback) callback(err, null);
    });
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
