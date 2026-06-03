// ---------- PRODUCT DETAIL PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  if (!KD) return;

  // Cache default product gallery elements on load for fallback
  const mainProductImg = document.getElementById('mainProductImg');
  const galleryThumbsContainer = document.getElementById('productGalleryThumbs');
  let defaultThumbsHtml = galleryThumbsContainer ? galleryThumbsContainer.innerHTML : '';
  let defaultMainImgSrc = mainProductImg ? mainProductImg.src : '';

  let activeImageIndex = 0;

  function setActiveImage(index) {
    const thumbs = document.querySelectorAll('.gallery-thumb-item');
    if (!thumbs.length) return;

    // Index wrapping check
    if (index < 0) {
      index = thumbs.length - 1;
    } else if (index >= thumbs.length) {
      index = 0;
    }

    activeImageIndex = index;

    // Sync active classes on thumbnails
    thumbs.forEach((t, i) => {
      if (i === activeImageIndex) {
        t.classList.add('active');
        // Ensure selected thumbnail is scrolled horizontally/vertically into view inside thumbs list
        t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      } else {
        t.classList.remove('active');
      }
    });

    // Animate source update on main image
    if (mainProductImg && thumbs[activeImageIndex]) {
      const src = thumbs[activeImageIndex].src;
      mainProductImg.style.opacity = '0.3';
      setTimeout(() => {
        mainProductImg.src = src;
        mainProductImg.style.opacity = '1';
      }, 120);
    }
  }

  // 1. Thumbnail Image Swapping helper
  function setupThumbnailListeners() {
    const thumbs = document.querySelectorAll('.gallery-thumb-item');
    thumbs.forEach((thumb, i) => {
      // Clear or bind standard index-based set active event listener
      thumb.addEventListener('click', () => {
        setActiveImage(i);
      });
    });
  }
  setupThumbnailListeners();

  // Navigation Arrows click listeners
  const galleryPrevBtn = document.getElementById('galleryPrevBtn');
  const galleryNextBtn = document.getElementById('galleryNextBtn');

  if (galleryPrevBtn) {
    galleryPrevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      setActiveImage(activeImageIndex - 1);
    });
  }

  if (galleryNextBtn) {
    galleryNextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      setActiveImage(activeImageIndex + 1);
    });
  }

  // Touch Swipe Gesture support for mobile screens
  const mainGalleryContainer = document.querySelector('.product-gallery-main');
  if (mainGalleryContainer) {
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;

    mainGalleryContainer.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    mainGalleryContainer.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      handleSwipeGesture();
    }, { passive: true });

    function handleSwipeGesture() {
      const diffX = touchEndX - touchStartX;
      const diffY = touchEndY - touchStartY;

      // Trigger swipe if primary gesture was horizontal & exceeds threshold (50px)
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          // Swiped right -> go to previous image
          setActiveImage(activeImageIndex - 1);
        } else {
          // Swiped left -> go to next image
          setActiveImage(activeImageIndex + 1);
        }
      }
    }
  }

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

  // 3. Tab Switching Logic
  const tabBtnDesc = document.getElementById('tabBtnDesc');
  const tabBtnSpecs = document.getElementById('tabBtnSpecs');
  const tabContentDesc = document.getElementById('tabContentDesc');
  const tabContentSpecs = document.getElementById('tabContentSpecs');

  if (tabBtnDesc && tabBtnSpecs && tabContentDesc && tabContentSpecs) {
    tabBtnDesc.addEventListener('click', () => {
      tabBtnDesc.classList.add('active');
      tabBtnDesc.style.borderBottom = '2.5px solid var(--primary)';
      tabBtnDesc.style.color = 'var(--dark-charcoal)';

      tabBtnSpecs.classList.remove('active');
      tabBtnSpecs.style.borderBottom = '2.5px solid transparent';
      tabBtnSpecs.style.color = '#8a857a';

      tabContentDesc.style.display = 'flex';
      tabContentSpecs.style.display = 'none';
    });

    tabBtnSpecs.addEventListener('click', () => {
      tabBtnSpecs.classList.add('active');
      tabBtnSpecs.style.borderBottom = '2.5px solid var(--primary)';
      tabBtnSpecs.style.color = 'var(--dark-charcoal)';

      tabBtnDesc.classList.remove('active');
      tabBtnDesc.style.borderBottom = '2.5px solid transparent';
      tabBtnDesc.style.color = '#8a857a';

      tabContentSpecs.style.display = 'block';
      tabContentDesc.style.display = 'none';
    });
  }

  // 4. Interactive Review Form Star Rating Selection
  const starsContainer = document.querySelector('.interactive-star-selector');
  const ratingInput = document.getElementById('reviewFormRatingInput');

  if (starsContainer && ratingInput) {
    const starIcons = starsContainer.querySelectorAll('.star-select-icon');
    starIcons.forEach(icon => {
      icon.addEventListener('click', () => {
        const rating = parseInt(icon.dataset.rating);
        ratingInput.value = rating;
        
        starIcons.forEach(s => {
          const r = parseInt(s.dataset.rating);
          if (r <= rating) {
            s.className = 'fas fa-star star-select-icon';
            s.style.color = '#E6A15C';
          } else {
            s.className = 'far fa-star star-select-icon';
            s.style.color = '#dcd8d0';
          }
        });
      });

      // Hover feedback effect
      icon.addEventListener('mouseover', () => {
        const rating = parseInt(icon.dataset.rating);
        starIcons.forEach(s => {
          const r = parseInt(s.dataset.rating);
          if (r <= rating) {
            s.style.color = '#E6A15C';
          } else {
            s.style.color = '#dcd8d0';
          }
        });
      });

      icon.addEventListener('mouseout', () => {
        const rating = parseInt(ratingInput.value || 0);
        starIcons.forEach(s => {
          const r = parseInt(s.dataset.rating);
          if (r <= rating) {
            s.style.color = '#E6A15C';
            s.className = 'fas fa-star star-select-icon';
          } else {
            s.style.color = '#dcd8d0';
            s.className = 'far fa-star star-select-icon';
          }
        });
      });
    });
  }

  // Review Form Collapsible Toggle
  const toggleReviewFormBtn = document.getElementById('toggleReviewFormBtn');
  const cancelReviewFormBtn = document.getElementById('cancelReviewFormBtn');
  const reviewFormWrapper = document.getElementById('reviewFormWrapper');

  if (toggleReviewFormBtn && reviewFormWrapper) {
    toggleReviewFormBtn.addEventListener('click', () => {
      reviewFormWrapper.style.display = 'block';
      reviewFormWrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }

  if (cancelReviewFormBtn && reviewFormWrapper) {
    cancelReviewFormBtn.addEventListener('click', () => {
      reviewFormWrapper.style.display = 'none';
    });
  }

  // 5. Premium Variation State Engine
  const variations = window.PRODUCT_VARIATIONS || [];
  const attributesData = window.PRODUCT_ATTRIBUTES || null;

  if (attributesData && variations.length > 0) {
    const swatchBtns = document.querySelectorAll('.swatch-btn');
    const varSelects = document.querySelectorAll('.variation-select');

    const detailProductPrice = document.getElementById('detailProductPrice');
    const detailProductSku = document.getElementById('detailProductSku');
    const detailProductStock = document.getElementById('detailProductStock');
    const detailProductTitle = document.getElementById('detailProductTitle');
    const detailProductShortDesc = document.getElementById('detailProductShortDesc');

    const addToBagBtn = document.getElementById('detailAddToCart');
    const buyNowBtn = document.getElementById('detailBuyNow');

    // Store base title and description for fallback
    const parentProductName = detailProductTitle ? detailProductTitle.innerText : '';
    const parentProductDesc = detailProductShortDesc ? detailProductShortDesc.innerText : '';

    // Handle Swatch Clicks
    swatchBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const parentGroup = btn.closest('.variation-group');
        const slug = parentGroup.dataset.attrSlug;
        const valLabel = document.getElementById(`label-${slug}`);

        // Update active class
        parentGroup.querySelectorAll('.swatch-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update value text
        if (valLabel) valLabel.innerText = btn.dataset.value;

        // Recalculate State
        syncVariationState();
      });
    });

    // Handle Dropdown changes
    varSelects.forEach(select => {
      select.addEventListener('change', () => {
        syncVariationState();
      });
    });

    // Main Variation Syncing function
    function syncVariationState() {
      // 1. Gather all active selections
      const selections = {};
      
      // Read swatch groups
      document.querySelectorAll('.variation-group').forEach(group => {
        const attrId = group.dataset.attrId;
        const swatchActive = group.querySelector('.swatch-btn.active');
        if (swatchActive) {
          selections[attrId] = swatchActive.dataset.valueId;
        }

        const dropdown = group.querySelector('.variation-select');
        if (dropdown) {
          const selectedOption = dropdown.options[dropdown.selectedIndex];
          selections[attrId] = selectedOption.dataset.valueId;
        }
      });

      // 2. Find matching variation
      let matchedVariation = null;
      for (const v of variations) {
        let isMatch = true;
        // Check if all selected attributes match this variation's value IDs
        for (const attrId in selections) {
          const valId = selections[attrId];
          const hasVal = v.values.some(valObj => valObj.attribute_id === attrId && valObj.value_id === valId);
          if (!hasVal) {
            isMatch = false;
            break;
          }
        }
        if (isMatch) {
          matchedVariation = v;
          break;
        }
      }

      // 3. Render matched variation details
      if (matchedVariation) {
        // Price Updates
        if (detailProductPrice) {
          if (matchedVariation.sale_price && matchedVariation.sale_price < matchedVariation.price) {
            detailProductPrice.innerHTML = `
              <span class="original-price" style="text-decoration: line-through; color: #8a857a; font-size: 1.1rem; margin-right: 10px;">₹${Math.round(matchedVariation.price)}</span>
              <span class="current-price" style="color: var(--primary); font-weight: 800;">₹${Math.round(matchedVariation.sale_price)}</span>
            `;
          } else {
            detailProductPrice.innerHTML = `
              <span class="current-price" style="color: var(--dark-charcoal); font-weight: 800;">₹${Math.round(matchedVariation.price)}</span>
            `;
          }
        }

        // SKU
        if (detailProductSku) {
          detailProductSku.innerText = `SKU: ${matchedVariation.sku || 'N/A'}`;
        }

        // Title and descriptions update
        if (detailProductTitle && matchedVariation.name) {
          detailProductTitle.innerText = matchedVariation.name;
        }
        if (detailProductShortDesc && matchedVariation.short_description) {
          detailProductShortDesc.innerText = matchedVariation.short_description;
        }

        // Stock Updates & Action Buttons state
        if (detailProductStock) {
          detailProductStock.className = 'stock-badge in-stock';
          if (matchedVariation.stock_status === 'out_of_stock' || matchedVariation.stock_quantity <= 0) {
            detailProductStock.className = 'stock-badge out-of-stock';
            detailProductStock.innerText = 'Out of Stock';
            detailProductStock.style.backgroundColor = '#fae9e8';
            detailProductStock.style.color = '#c7362b';

            if (addToBagBtn) {
              addToBagBtn.disabled = true;
              addToBagBtn.innerHTML = 'Out of Stock';
            }
            if (buyNowBtn) {
              buyNowBtn.disabled = true;
              buyNowBtn.innerHTML = 'Unavailable';
            }
          } else {
            detailProductStock.style.backgroundColor = '#e8f6ed';
            detailProductStock.style.color = '#1f8546';
            if (matchedVariation.stock_quantity <= 5) {
              detailProductStock.innerText = `In Stock (Only ${matchedVariation.stock_quantity} left!)`;
            } else {
              detailProductStock.innerText = 'In Stock';
            }

            if (addToBagBtn) {
              addToBagBtn.disabled = false;
              addToBagBtn.innerHTML = '<i class="fas fa-bag-shopping" style="margin-right: 8px;"></i> Add to Bag';
            }
            if (buyNowBtn) {
              buyNowBtn.disabled = false;
              buyNowBtn.innerHTML = 'Buy Now';
            }
          }
        }

        // Gallery Images Swap
        if (matchedVariation.images && matchedVariation.images.length > 0) {
          activeImageIndex = 0; // Reset index to 0 for new set of variation images
          if (galleryThumbsContainer) {
            galleryThumbsContainer.innerHTML = matchedVariation.images.map((imgUrl, i) => `
              <img src="${imgUrl}" alt="Thumbnail ${i + 1}" class="gallery-thumb-item ${i === 0 ? 'active' : ''}" data-idx="${i}">
            `).join('');
          }
          if (mainProductImg) {
            mainProductImg.src = matchedVariation.images[0];
          }
          setupThumbnailListeners();
        } else {
          // Revert to parent defaults if variation has no specific images
          activeImageIndex = 0; // Reset index to 0 for parent defaults
          if (galleryThumbsContainer) {
            galleryThumbsContainer.innerHTML = defaultThumbsHtml;
          }
          if (mainProductImg) {
            mainProductImg.src = defaultMainImgSrc;
          }
          setupThumbnailListeners();
        }

        // Add to Bag / Buy Now buttons datasets alignment
        const activeName = matchedVariation.name || `${parentProductName} - Variation`;
        const activePrice = Math.round(matchedVariation.sale_price || matchedVariation.price);
        
        if (addToBagBtn) {
          addToBagBtn.dataset.name = activeName;
          addToBagBtn.dataset.price = activePrice;
          addToBagBtn.dataset.sku = matchedVariation.sku || '';
          addToBagBtn.dataset.variationId = matchedVariation.id;
        }
        if (buyNowBtn) {
          buyNowBtn.dataset.name = activeName;
          buyNowBtn.dataset.price = activePrice;
          buyNowBtn.dataset.sku = matchedVariation.sku || '';
          buyNowBtn.dataset.variationId = matchedVariation.id;
        }

      } else {
        // Unavailable State (Safety fallback)
        if (detailProductStock) {
          detailProductStock.className = 'stock-badge out-of-stock';
          detailProductStock.innerText = 'Unavailable';
        }
        if (addToBagBtn) {
          addToBagBtn.disabled = true;
          addToBagBtn.innerText = 'Unavailable';
        }
        if (buyNowBtn) {
          buyNowBtn.disabled = true;
          buyNowBtn.innerText = 'Unavailable';
        }
      }
    }

    // Auto Preselect Behavior
    function autoPreselect() {
      const preselectVal = window.PRESELECT_VALUE || '';
      const preselectParts = preselectVal.split(',').map(p => p.trim().toLowerCase());

      // Preselect shape swatches
      let shapeMatched = false;
      document.querySelectorAll('.variation-group[data-attr-slug="shape"] .swatch-btn').forEach(btn => {
        const btnVal = btn.dataset.value.toLowerCase();
        if (preselectParts.includes(btnVal) || btnVal === preselectParts[0]) {
          btn.click();
          shapeMatched = true;
        }
      });

      if (!shapeMatched) {
        // Fallback: click the first swatch
        const firstSwatch = document.querySelector('.swatch-btn');
        if (firstSwatch) firstSwatch.click();
      }

      // Preselect size select options
      document.querySelectorAll('.variation-group[data-attr-slug="size"] .variation-select').forEach(select => {
        let sizeMatched = false;
        for (let i = 0; i < select.options.length; i++) {
          const optVal = select.options[i].value.toLowerCase();
          if (preselectParts.includes(optVal) || optVal === preselectParts[0] || optVal === preselectParts[1]) {
            select.selectedIndex = i;
            sizeMatched = true;
            break;
          }
        }
        if (!sizeMatched) {
          select.selectedIndex = 0;
        }
      });

      // Synchronize overall state
      syncVariationState();
    }

    // Trigger pre-selection
    autoPreselect();
  }

  // 6. Add to Bag & Buy Now trigger bindings
  const detailAddToCart = document.getElementById('detailAddToCart');
  const detailBuyNow = document.getElementById('detailBuyNow');

  if (detailAddToCart) {
    detailAddToCart.addEventListener('click', () => {
      const name = detailAddToCart.dataset.name;
      const price = parseInt(detailAddToCart.dataset.price);
      const sku = detailAddToCart.dataset.sku || '';
      const varId = detailAddToCart.dataset.variationId || '';
      const cart = KD.getCart();

      // Append selected quantity
      for (let i = 0; i < quantity; i++) {
        cart.push({ name, price, sku, variation_id: varId });
      }

      KD.saveCart(cart);
      KD.showToast(`${quantity}x ${name} added to Bag ✨`, "#C17A5A");
    });
  }

  if (detailBuyNow) {
    detailBuyNow.addEventListener('click', () => {
      const name = detailBuyNow.dataset.name;
      const price = parseInt(detailBuyNow.dataset.price);
      const sku = detailBuyNow.dataset.sku || '';
      const varId = detailBuyNow.dataset.variationId || '';
      const cart = KD.getCart();

      for (let i = 0; i < quantity; i++) {
        cart.push({ name, price, sku, variation_id: varId });
      }

      KD.saveCart(cart);
      window.location.href = '/cart';
    });
  }

  // Related Products bindings
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
  });
});
