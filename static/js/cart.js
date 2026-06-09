// ---------- CART PAGE FRONTEND LOGIC (AJAX CONNECTED) ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  if (!KD) return;

  const container = document.querySelector('.cart-wrapper');
  if (!container) return;

  // Update summary totals on summary card
  function updateSummaryCard(subtotal, shipping, total) {
    const subtotalEl = document.getElementById('summarySubtotal');
    const shippingEl = document.getElementById('summaryShipping');
    const totalEl = document.getElementById('summaryTotal');

    if (subtotalEl) subtotalEl.innerText = Math.round(subtotal);
    if (shippingEl) {
      shippingEl.innerHTML = shipping === 0 ? '<strong style="color:var(--secondary)">FREE</strong>' : '₹' + Math.round(shipping);
    }
    if (totalEl) totalEl.innerText = Math.round(total);
  }

  // Bind decrement clicks
  container.querySelectorAll('.qty-dec').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const key = btn.dataset.key;
      const qtySpan = document.getElementById('qty-' + key);
      const currentQty = parseInt(qtySpan.innerText);
      if (currentQty > 1) {
        btn.disabled = true;
        KD.updateCartQtyAjax(key, -1, (err, data) => {
          btn.disabled = false;
          if (err) {
            KD.showToast(err, "#c7362b");
          } else {
            qtySpan.innerText = data.qty;
            const itemTotalEl = document.getElementById('item-total-' + key);
            if (itemTotalEl) itemTotalEl.innerText = '₹' + Math.round(data.item_total);
            updateSummaryCard(data.subtotal, data.shipping, data.total);
          }
        });
      }
    });
  });

  // Bind increment clicks
  container.querySelectorAll('.qty-inc').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const key = btn.dataset.key;
      const qtySpan = document.getElementById('qty-' + key);
      btn.disabled = true;
      KD.updateCartQtyAjax(key, 1, (err, data) => {
        btn.disabled = false;
        if (err) {
          KD.showToast(err, "#c7362b");
        } else {
          qtySpan.innerText = data.qty;
          const itemTotalEl = document.getElementById('item-total-' + key);
          if (itemTotalEl) itemTotalEl.innerText = '₹' + Math.round(data.item_total);
          updateSummaryCard(data.subtotal, data.shipping, data.total);
        }
      });
    });
  });

  // Bind removals
  container.querySelectorAll('.remove-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const key = btn.dataset.key;
      btn.disabled = true;
      KD.removeCartItemAjax(key, (err, data) => {
        btn.disabled = false;
        if (err) {
          KD.showToast(err, "#c7362b");
        } else {
          // Remove item card from DOM
          const itemCard = container.querySelector(`.cart-item-card[data-key="${key}"]`);
          if (itemCard) {
            itemCard.remove();
          }
          
          // If cart empty, reload page to display empty cart message
          if (data.cart_empty) {
            window.location.reload();
          } else {
            updateSummaryCard(data.subtotal, data.shipping, data.total);
            
            // Update page header cart count dynamically
            const headerCount = document.getElementById('cartCount');
            if (headerCount) {
              const currentVal = parseInt(headerCount.innerText) || 0;
              headerCount.innerText = Math.max(0, currentVal - 1);
            }
          }
          KD.showToast("Item removed from Bag", "#C17A5A");
        }
      });
    });
  });

  // Bind Proceed to Checkout
  document.getElementById('proceedCheckout')?.addEventListener('click', () => {
    window.location.href = '/checkout';
  });
});
