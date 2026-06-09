// ---------- CHECKOUT PAGE FRONTEND LOGIC (DATABASE INTEGRATED) ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  if (!KD) return;

  const form = document.getElementById('checkoutForm');
  if (!form) return;

  const checkoutData = window.CHECKOUT_DATA || {};
  let currentSubtotal = checkoutData.subtotal || 0;
  let currentTotal = checkoutData.total || 0;
  let activeCoupon = '';

  // 1. Handle Saved Address Radio Selection Toggle
  const savedAddressRadios = document.querySelectorAll('input[name="saved_address_id"]');
  const newAddressContainer = document.getElementById('newAddressContainer');
  
  const requiredInputs = [
    document.getElementById('newAddrFirst'),
    document.getElementById('newAddrLast'),
    document.getElementById('newAddrPhone'),
    document.getElementById('newAddrLine1'),
    document.getElementById('newAddrCity'),
    document.getElementById('newAddrState'),
    document.getElementById('newAddrPin')
  ];

  function toggleNewAddressFields() {
    const selectedRadio = document.querySelector('input[name="saved_address_id"]:checked');
    const isNewAddress = !selectedRadio || selectedRadio.value === "";
    
    if (newAddressContainer) {
      newAddressContainer.style.display = isNewAddress ? "block" : "none";
    }
    
    // Set required flags on inputs only if a new address is selected
    requiredInputs.forEach(input => {
      if (input) {
        input.required = isNewAddress;
      }
    });
  }

  savedAddressRadios.forEach(radio => {
    radio.addEventListener('change', toggleNewAddressFields);
  });
  
  // Run toggler on load
  toggleNewAddressFields();

  // 2. Styling Toggle for Selected Payment Methods
  const paymentRadios = document.querySelectorAll('input[name="payment_method"]');
  function updatePaymentStyles() {
    paymentRadios.forEach(radio => {
      const card = radio.closest('.payment-option-card') || radio.closest('.payment-option-label');
      if (card) {
        if (radio.checked) {
          card.classList.add('selected');
          card.style.borderColor = 'var(--primary)';
          card.style.background = '#faf9f6';
        } else {
          card.classList.remove('selected');
          card.style.borderColor = '#dcd8d0';
          card.style.background = '#ffffff';
        }
      }
    });
  }
  paymentRadios.forEach(radio => {
    radio.addEventListener('change', updatePaymentStyles);
  });
  updatePaymentStyles();

  // 3. Handle Coupon Code Validation (AJAX)
  const applyCouponBtn = document.getElementById('applyCouponBtn');
  const couponInput = document.getElementById('couponInput');
  const couponFeedback = document.getElementById('couponFeedback');
  const discountRow = document.getElementById('discountRow');
  const discountVal = document.getElementById('discountVal');
  const summaryTotal = document.getElementById('summaryTotal');
  const btnTotal = document.getElementById('btnTotal');

  if (applyCouponBtn && couponInput) {
    applyCouponBtn.addEventListener('click', () => {
      const code = couponInput.value.trim();
      if (!code) {
        if (couponFeedback) {
          couponFeedback.style.display = 'block';
          couponFeedback.style.color = '#c7362b';
          couponFeedback.innerText = 'Please enter a coupon code.';
        }
        return;
      }

      applyCouponBtn.disabled = true;
      
      fetch('/apply_coupon', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          coupon_code: code,
          subtotal: currentSubtotal
        })
      })
      .then(res => res.json())
      .then(data => {
        applyCouponBtn.disabled = false;
        if (couponFeedback) couponFeedback.style.display = 'block';
        
        if (data.valid) {
          activeCoupon = code.toUpperCase();
          if (couponFeedback) {
            couponFeedback.style.color = '#166534';
            couponFeedback.innerText = data.message;
          }
          if (discountRow && discountVal) {
            discountRow.style.display = 'flex';
            discountVal.innerText = Math.round(data.discount_amount);
          }
          currentTotal = data.new_total;
          if (summaryTotal) summaryTotal.innerText = Math.round(data.new_total);
          if (btnTotal) btnTotal.innerText = Math.round(data.new_total);
          
          KD.showToast("Coupon applied successfully!", "#166534");
        } else {
          activeCoupon = '';
          if (couponFeedback) {
            couponFeedback.style.color = '#c7362b';
            couponFeedback.innerText = data.error;
          }
          if (discountRow) discountRow.style.display = 'none';
          if (summaryTotal) summaryTotal.innerText = Math.round(checkoutData.total);
          if (btnTotal) btnTotal.innerText = Math.round(checkoutData.total);
          
          KD.showToast(data.error, "#c7362b");
        }
      })
      .catch(err => {
        applyCouponBtn.disabled = false;
        console.error('Error applying coupon:', err);
        KD.showToast('Error validating coupon', '#c7362b');
      });
    });
  }

  // 4. Handle Razorpay Payments Integration or Cash on Delivery Submit
  form.addEventListener('submit', (e) => {
    const selectedPayment = document.querySelector('input[name="payment_method"]:checked')?.value;
    
    if (selectedPayment === 'razorpay' && checkoutData.online_enabled) {
      e.preventDefault(); // Stop normal form POST
      
      const submitBtn = document.getElementById('finalOrderBtn');
      if (submitBtn) submitBtn.disabled = true;

      KD.showToast("Initializing payment secure connection...", "#C17A5A");

      // Request Razorpay order ID from Flask backend
      fetch('/razorpay/create_order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          coupon_code: activeCoupon
        })
      })
      .then(res => res.json())
      .then(resData => {
        if (!resData.success) {
          if (submitBtn) submitBtn.disabled = false;
          KD.showToast(resData.message || "Failed to initiate online transaction.", "#c7362b");
          return;
        }

        const rzpOrder = resData.order;

        // Open Razorpay Standard Checkout overlay
        const options = {
          key: checkoutData.razorpay_key_id,
          amount: rzpOrder.amount,
          currency: rzpOrder.currency,
          name: "Khushi Decors",
          description: "Premium Home Decor & Lighting Order",
          order_id: rzpOrder.id,
          handler: function (response) {
            // Success callback: populate hidden inputs and submit form to backend
            document.getElementById('rzpPaymentId').value = response.razorpay_payment_id;
            document.getElementById('rzpOrderId').value = response.razorpay_order_id;
            document.getElementById('rzpSignature').value = response.razorpay_signature;

            KD.showToast("Payment verified. Creating your order...", "#166534");
            
            // Submit form to /checkout POST endpoint
            form.submit();
          },
          prefill: {
            name: checkoutData.user_name,
            email: checkoutData.user_email,
            contact: checkoutData.user_phone
          },
          theme: {
            color: "#C17A5A"
          },
          modal: {
            ondismiss: function () {
              if (submitBtn) submitBtn.disabled = false;
              KD.showToast("Payment window closed. Order was not placed.", "#c7362b");
            }
          }
        };

        const rzp = new Razorpay(options);
        rzp.open();
      })
      .catch(err => {
        if (submitBtn) submitBtn.disabled = false;
        console.error('Error creating Razorpay order:', err);
        KD.showToast("Online payment initialization error", "#c7362b");
      });
    } else {
      // For COD, let the form submit normally
      KD.showToast("Processing Cash on Delivery order...", "#C17A5A");
    }
  });
});
