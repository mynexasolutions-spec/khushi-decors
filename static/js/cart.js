// ---------- CART PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  const container = document.querySelector('.cart-wrapper');

  if (!container) return;

  const productsImages = {
    "Macrame Wall Hanging": "/static/images/WD1.jpg",
    "Abstract Canvas": "/static/images/WD2.jpg",
    "Jute Wall Art": "/static/images/WD3.jpg",
    "Floating Set": "/static/images/WD4.jpg",
    "Boho Tapestry": "/static/images/WD5.jpg",
    "Mirror Decor": "https://images.unsplash.com/photo-1618220179428-22790b461013?w=400&auto=format",
    "Fiddle lavender Leaf": "/static/images/AP.jpg",
    "Succulent Trio": "/static/images/AP1.jpg",
    "Hanging Ivy": "/static/images/AP2.jpg",
    "Monstera Plant": "/static/images/AP3.jpg",
    "Orchid Stem": "/static/images/AP4.jpg",
    "Pink Tree": "/static/images/APFIVE.jpg",
    "Street Lamp": "/static/images/LAMP.jpg",
    "Table Lamp": "/static/images/LAMP1.jpg",
    "Rattan Lamp": "/static/images/LAMP2.jpg",
    "Wall Sconce Pair": "/static/images/LAMP3.jpg",
    "Arc Floor Lamp": "/static/images/LAMP4.jpg",
    "Ceramic Table Lamp": "/static/images/LAMP5.jpg",
    "Terracotta Set": "/static/images/VASE1.jpg",
    "Ribbed Vase": "/static/images/VASE2.jpg",
    "Handcrafted Ceramic": "/static/images/VASE3.jpg",
    "Minimalist Marble": "/static/images/VASE4.jpg",
    "Bud Vase Duo": "/static/images/VASEFIVR.jpg",
    "Ceramic Vase": "https://images.unsplash.com/photo-1612196808214-b8e1d6145a8c?w=400&auto=format",
    "LongMountainic Clock": "/static/images/CLOCK1.jpg",
    "Vintage Wall Clock": "/static/images/CLCOK2.jpg",
    "Modern Minimalist": "/static/images/CLCOK3.jpg",
    "Digital Smart Clock": "/static/images/CLCOK4.jpg"
  };

  function getProductImage(name) {
    return productsImages[name] || "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=300&auto=format";
  }

  function renderCart() {
    const cart = KD.getCart();
    
    // Clear and build grid
    container.innerHTML = '';

    if (cart.length === 0) {
      container.innerHTML = `
        <h1 style="margin-bottom:1.5rem;"><i class="fas fa-shopping-bag"></i> Your Shopping Bag (0)</h1>
        <p style="text-align:center; padding: 4rem 1rem; color:#8a857a; font-size:1.1rem;">
          Your bag is empty.<br><br>
          <button class="btn btn-primary" id="startShopping" style="padding:0.9rem 2.2rem; font-size:0.9rem;">Start Shopping</button>
        </p>
      `;
      document.getElementById('startShopping')?.addEventListener('click', () => {
        window.location.href = '/shop';
      });
      return;
    }

    const total = cart.reduce((s, i) => s + i.price, 0);
    const delivery = total >= 2000 ? 0 : 80;
    const finalTotal = total + delivery;

    container.innerHTML = `
      <h1 style="margin-bottom:1.5rem;"><i class="fas fa-shopping-bag"></i> Your Shopping Bag (${cart.length})</h1>
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
          <p style="display:flex; justify-content:space-between; margin-bottom: 0.8rem; font-size:0.95rem;">
            <span>Subtotal:</span> <span>₹<span id="summarySubtotal">${total}</span></span>
          </p>
          <p style="display:flex; justify-content:space-between; margin-bottom: 1.2rem; border-bottom: 1px solid #f0ede8; padding-bottom: 0.8rem; font-size:0.95rem;">
            <span>Shipping:</span> <span id="summaryShipping">${delivery === 0 ? '<strong style="color:var(--secondary)">FREE</strong>' : '₹' + delivery}</span>
          </p>
          <h4 style="display:flex; justify-content:space-between; font-size:1.25rem; margin-bottom: 1.5rem; font-weight:800; color:var(--dark-charcoal);">
            <span>Total:</span> <span>₹<span id="summaryTotal">${finalTotal}</span></span>
          </h4>
          <button class="checkout-btn" id="proceedCheckout" style="margin-bottom:0.8rem; padding:1rem; font-size:0.95rem;">Proceed to Checkout</button>
          <button class="btn btn-outline" id="continueShopping" style="width:100%; padding:0.9rem; font-size:0.85rem;">Continue Shopping</button>
        </div>
      </div>
    `;

    // Local state for quantities
    let quantities = cart.map(() => 1);

    function updateTotals() {
      const activeCart = KD.getCart();
      let newTotal = activeCart.reduce((s, item, i) => s + (item.price * quantities[i]), 0);
      let newDelivery = newTotal >= 2000 ? 0 : 80;
      
      const subtotalEl = document.getElementById('summarySubtotal');
      const shippingEl = document.getElementById('summaryShipping');
      const totalEl = document.getElementById('summaryTotal');

      if (subtotalEl) subtotalEl.innerText = newTotal;
      if (shippingEl) {
        shippingEl.innerHTML = newDelivery === 0 ? '<strong style="color:var(--secondary)">FREE</strong>' : '₹' + newDelivery;
      }
      if (totalEl) totalEl.innerText = newTotal + newDelivery;

      // Save quantities back to local storage by duplicating cart items if quantities > 1, 
      // or we can just save subtotal totals for checkout.
      // Wait, in order confirmation, it reads cart from local storage. To sync quantities properly, 
      // let's update the checkout-summary totals.
      localStorage.setItem('vividCart_qty_totals', JSON.stringify(quantities));
    }

    // Bind item increments
    container.querySelectorAll('.qty-inc').forEach(b => b.addEventListener('click', (e) => {
      const idx = e.target.dataset.idx; 
      quantities[idx]++; 
      document.getElementById('qty-' + idx).innerText = quantities[idx];
      document.getElementById('item-total-' + idx).innerText = '₹' + (cart[idx].price * quantities[idx]);
      updateTotals();
    }));

    // Bind item decrements
    container.querySelectorAll('.qty-dec').forEach(b => b.addEventListener('click', (e) => {
      const idx = e.target.dataset.idx; 
      if (quantities[idx] > 1) {
        quantities[idx]--;
        document.getElementById('qty-' + idx).innerText = quantities[idx];
        document.getElementById('item-total-' + idx).innerText = '₹' + (cart[idx].price * quantities[idx]);
        updateTotals();
      }
    }));

    // Bind item removals
    container.querySelectorAll('.remove-item').forEach(b => b.addEventListener('click', (e) => {
      const idx = e.target.closest('button').dataset.idx; 
      const currentCart = KD.getCart();
      currentCart.splice(idx, 1);
      KD.saveCart(currentCart);
      
      // Update quantities array
      quantities.splice(idx, 1);
      localStorage.setItem('vividCart_qty_totals', JSON.stringify(quantities));
      
      renderCart();
    }));

    // Continue Shopping btn redirect
    document.getElementById('continueShopping')?.addEventListener('click', () => {
      window.location.href = '/shop';
    });

    // Proceed to Checkout btn redirect
    document.getElementById('proceedCheckout')?.addEventListener('click', () => {
      const user = KD.getUser();
      if (!user || !user.address) {
        KD.showToast("Please complete your profile to continue", "#c7362b");
        setTimeout(() => {
          window.location.href = '/account';
        }, 1200);
      } else {
        window.location.href = '/checkout';
      }
    });

    // Save initial quantities mapping
    localStorage.setItem('vividCart_qty_totals', JSON.stringify(quantities));
  }

  // Run rendering
  renderCart();
});
