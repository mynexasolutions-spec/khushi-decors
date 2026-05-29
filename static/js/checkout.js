// ---------- CHECKOUT PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  const container = document.querySelector('.confirm-order-wrapper');

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

  function renderCheckout() {
    const cart = KD.getCart();
    const userDetails = KD.getUser();
    const quantities = JSON.parse(localStorage.getItem('vividCart_qty_totals')) || cart.map(() => 1);

    if (cart.length === 0) {
      window.location.href = '/cart';
      return;
    }

    if (!userDetails || !userDetails.address) {
      KD.showToast("Please complete your profile details first", "#c7362b");
      setTimeout(() => {
        window.location.href = '/account';
      }, 1200);
      return;
    }

    // Calculate totals
    const total = cart.reduce((sum, item, idx) => sum + (item.price * (quantities[idx] || 1)), 0);
    const delivery = total >= 2000 ? 0 : 80;
    const finalTotal = total + delivery;
    const orderId = "DEC" + Math.floor(Math.random() * 1000000);

    container.innerHTML = `
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
          <div class="card-header">
            <i class="fas fa-bag-shopping"></i>
            <h3>Items in Order</h3>
          </div>
          <div class="checkout-summary-list">
            ${cart.map((item, idx) => {
              const qty = quantities[idx] || 1;
              const priceLabel = qty > 1 ? `₹${item.price} x ${qty}` : `₹${item.price}`;
              return `
                <div class="checkout-summary-item">
                  <img src="${getProductImage(item.name)}" alt="${item.name}" class="checkout-item-img">
                  <div class="checkout-item-name">${item.name} <span style="font-size: 0.8rem; color: #8a857a;">(${qty} item${qty > 1 ? 's' : ''})</span></div>
                  <div class="checkout-item-price">${priceLabel}</div>
                </div>
              `;
            }).join('')}
          </div>

          <div class="card-header" style="margin-top:2rem;">
            <i class="fas fa-map-marker-alt"></i>
            <h3>Delivery Address</h3>
          </div>
          <div class="address-card-premium">
            <p style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--dark-charcoal);">${userDetails.firstName} ${userDetails.lastName}</p>
            <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6; margin-bottom: 0.3rem;">
              <i class="fas fa-building" style="color: var(--primary); margin-right: 8px;"></i>${userDetails.address}
            </p>
            <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6; margin-bottom: 0.3rem;">
              <i class="fas fa-city" style="color: var(--primary); margin-right: 8px;"></i>${userDetails.city}, ${userDetails.pincode}
            </p>
            <p style="font-size: 0.95rem; color: #4a4a52; line-height: 1.6;">
              <i class="fas fa-phone-alt" style="color: var(--primary); margin-right: 8px;"></i>Phone: ${userDetails.phone}
            </p>
          </div>
        </div>
        <div class="order-card">
          <div class="card-header">
            <i class="fas fa-credit-card"></i>
            <h3>Payment</h3>
          </div>
          <div class="payment-option-card selected">
            <i class="fas fa-money-bill-wave"></i> Cash on Delivery
          </div>
          <div style="margin: 1.5rem 0; border-top: 1px solid #f0ede8; padding-top: 1rem;">
            <p style="display:flex; justify-content:space-between; margin-bottom:0.5rem; font-size:0.95rem; color:#6E695F;">
              <span>Subtotal:</span> <span>₹${total}</span>
            </p>
            <p style="display:flex; justify-content:space-between; margin-bottom:1rem; font-size:0.95rem; color:#6E695F;">
              <span>Shipping:</span> <span>${delivery === 0 ? 'FREE' : '₹' + delivery}</span>
            </p>
            <p style="display:flex; justify-content:space-between; font-size:1.2rem; font-weight:800; color:var(--dark-charcoal);">
              <span>Total:</span> <span>₹${finalTotal}</span>
            </p>
          </div>
          <button class="place-order-btn-enhanced" id="finalOrderBtn" style="margin-bottom:0.8rem; padding:1rem; font-size:0.95rem;">
            Place Order · ₹${finalTotal}
          </button>
          <button class="btn btn-outline" id="backToCartFromConfirm" style="width:100%; padding:0.9rem; font-size:0.85rem;">
            Back to Cart
          </button>
        </div>
      </div>
    `;

    // Bind back to cart button
    document.getElementById('backToCartFromConfirm')?.addEventListener('click', () => {
      window.location.href = '/cart';
    });

    // Place Order button handler
    document.getElementById('finalOrderBtn')?.addEventListener('click', () => {
      // Clear Cart Data
      KD.saveCart([]);
      localStorage.removeItem('vividCart_qty_totals');

      // Update Order count
      let orderCount = parseInt(localStorage.getItem('vividOrderCount') || '0');
      orderCount++;
      localStorage.setItem('vividOrderCount', orderCount.toString());

      // Show Success popup modal
      KD.showSuccessModal();
    });
  }

  // Run rendering
  renderCheckout();
});
