// ---------- PRODUCT DETAIL PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;

  // 1. Thumbnail Image Swapping
  const mainProductImg = document.getElementById('mainProductImg');
  const thumbs = document.querySelectorAll('.gallery-thumb-item');

  thumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      // Remove active states
      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');

      const src = thumb.src;
      if (mainProductImg) {
        mainProductImg.style.opacity = '0.3';
        setTimeout(() => {
          mainProductImg.src = src;
          mainProductImg.style.opacity = '1';
        }, 120);
      }
    });
  });

  // 2. Quantity Selectors Counter
  let quantity = 1;
  const qtyVal = document.getElementById('detailQtyVal');
  const qtyDecBtn = document.getElementById('detailQtyDec');
  const qtyIncBtn = document.getElementById('detailQtyInc');

  if (qtyDecBtn && qtyIncBtn && qtyVal) {
    qtyDecBtn.addEventListener('click', () => {
      if (quantity > 1) {
        quantity--;
        qtyVal.innerText = quantity;
      }
    });

    qtyIncBtn.addEventListener('click', () => {
      quantity++;
      qtyVal.innerText = quantity;
    });
  }

  // 3. Add to Bag / Buy Now buttons action
  const detailAddToCart = document.getElementById('detailAddToCart');
  const detailBuyNow = document.getElementById('detailBuyNow');

  if (detailAddToCart) {
    detailAddToCart.addEventListener('click', () => {
      const name = detailAddToCart.dataset.name;
      const price = parseInt(detailAddToCart.dataset.price);
      const cart = KD.getCart();

      // Append selected quantity
      for (let i = 0; i < quantity; i++) {
        cart.push({ name, price });
      }

      KD.saveCart(cart);
      KD.showToast(`${quantity}x ${name} added to Bag ✨`, "#C17A5A");
    });
  }

  if (detailBuyNow) {
    detailBuyNow.addEventListener('click', () => {
      const name = detailBuyNow.dataset.name;
      const price = parseInt(detailBuyNow.dataset.price);
      const cart = KD.getCart();

      for (let i = 0; i < quantity; i++) {
        cart.push({ name, price });
      }

      KD.saveCart(cart);
      window.location.href = '/cart';
    });
  }

  // 4. Related Products bindings
  const relatedCards = document.querySelectorAll('.related-product-card');
  relatedCards.forEach(card => {
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

    // Related cards detail pages redirect
    card.querySelectorAll('.shop-card-img-wrap, .shop-card-name').forEach(el => {
      el.addEventListener('click', () => {
        const name = card.dataset.name;
        if (name) {
          window.location.href = `/product/${encodeURIComponent(name)}`;
        }
      });
    });
  });
});
