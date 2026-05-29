// ---------- ACCOUNT PAGE FRONTEND LOGIC ----------
document.addEventListener('DOMContentLoaded', () => {
  const KD = window.KhushiDecors;
  const container = document.querySelector('.account-dashboard-wrapper');

  if (!container) return;

  function renderAccount() {
    const userDetails = KD.getUser();
    const cart = KD.getCart();

    if (userDetails && userDetails.firstName && userDetails.address) {
      // ==========================================
      // ---------- LOGGED IN DASHBOARD ----------
      // ==========================================
      const memberSince = new Date().getFullYear();
      const orderCount = JSON.parse(localStorage.getItem('vividOrderCount') || '0');

      container.innerHTML = `
        <div class="account-dashboard">
          <!-- Hero Section -->
          <div class="account-hero">
            <div class="account-avatar-large">
              <i class="fas fa-user-circle"></i>
            </div>
            <div class="account-info">
              <h2>Welcome back, ${userDetails.firstName}! 👋</h2>
              <p>Member since ${memberSince} · ${userDetails.email || 'Email not set'}</p>
              <div class="account-stats-row">
                <div class="stat-badge">
                  <div class="stat-num">${cart.length}</div>
                  <div class="stat-lbl">Cart Items</div>
                </div>
                <div class="stat-badge">
                  <div class="stat-num">${orderCount}</div>
                  <div class="stat-lbl">Orders</div>
                </div>
                <div class="stat-badge">
                  <div class="stat-num">0</div>
                  <div class="stat-lbl">Wishlist</div>
                </div>
                <div class="stat-badge">
                  <div class="stat-num">₹0</div>
                  <div class="stat-lbl">Saved</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="quick-actions-grid">
            <div class="quick-action-card" id="quickCart">
              <i class="fas fa-shopping-bag"></i>
              <span>My Cart</span>
            </div>
            <div class="quick-action-card" id="quickOrders">
              <i class="fas fa-box"></i>
              <span>My Orders</span>
            </div>
            <div class="quick-action-card" id="quickWishlist">
              <i class="fas fa-heart"></i>
              <span>Wishlist</span>
            </div>
            <div class="quick-action-card" id="quickSupport">
              <i class="fas fa-headset"></i>
              <span>Support</span>
            </div>
          </div>

          <!-- Main Grid -->
          <div class="account-grid-enhanced">
            <!-- Profile Card -->
            <div class="enhanced-card" id="profileCard">
              <div class="card-header-enhanced">
                <h3><i class="fas fa-id-card"></i> Personal Information</h3>
                <button class="edit-btn-icon" id="editProfileBtnEnhanced" title="Edit Profile">
                  <i class="fas fa-pen"></i>
                </button>
              </div>
              <div class="info-grid" id="profileInfoDisplay">
                <div class="info-item">
                  <span class="info-label">Full Name</span>
                  <span class="info-value">${userDetails.firstName} ${userDetails.lastName}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Email</span>
                  <span class="info-value">${userDetails.email || 'Not provided'}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Phone</span>
                  <span class="info-value">${userDetails.phone || 'Not provided'}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Member Since</span>
                  <span class="info-value">${memberSince}</span>
                </div>
              </div>
            </div>

            <!-- Address Card -->
            <div class="enhanced-card" id="addressCard">
              <div class="card-header-enhanced">
                <h3><i class="fas fa-map-marker-alt"></i> Delivery Address</h3>
                <button class="edit-btn-icon" id="editAddressBtnEnhanced" title="Edit Address">
                  <i class="fas fa-pen"></i>
                </button>
              </div>
              <div class="address-display" id="addressInfoDisplay">
                <div class="address-line">
                  <i class="fas fa-building"></i>
                  <span>${userDetails.address}</span>
                </div>
                <div class="address-line">
                  <i class="fas fa-city"></i>
                  <span>${userDetails.city}, ${userDetails.pincode}</span>
                </div>
                <div class="address-line">
                  <i class="fas fa-map"></i>
                  <span>${userDetails.state || 'Maharashtra'}, India</span>
                </div>
                <div class="address-line">
                  <i class="fas fa-phone-alt"></i>
                  <span>${userDetails.phone}</span>
                </div>
              </div>
            </div>

            <!-- Preferences Card -->
            <div class="enhanced-card">
              <div class="card-header-enhanced">
                <h3><i class="fas fa-sliders-h"></i> Preferences</h3>
              </div>
              <div class="preference-list">
                <div class="preference-row">
                  <span><i class="fas fa-envelope" style="margin-right: 8px; color: #C17A5A;"></i> Email Notifications</span>
                  <label class="switch">
                    <input type="checkbox" checked id="prefEmail">
                    <span class="slider"></span>
                  </label>
                </div>
                <div class="preference-row">
                  <span><i class="fas fa-sms" style="margin-right: 8px; color: #C17A5A;"></i> SMS Alerts</span>
                  <label class="switch">
                    <input type="checkbox" id="prefSMS">
                    <span class="slider"></span>
                  </label>
                </div>
                <div class="preference-row">
                  <span><i class="fas fa-newspaper" style="margin-right: 8px; color: #C17A5A;"></i> Newsletter</span>
                  <label class="switch">
                    <input type="checkbox" checked id="prefNewsletter">
                    <span class="slider"></span>
                  </label>
                </div>
                <div class="preference-row">
                  <span><i class="fas fa-tag" style="margin-right: 8px; color: #C17A5A;"></i> Promo Offers</span>
                  <label class="switch">
                    <input type="checkbox" checked id="prefPromo">
                    <span class="slider"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="account-actions-row">
            <button class="btn-logout" id="logoutAccEnhanced">
              <i class="fas fa-sign-out-alt"></i> Logout
            </button>
            <button class="btn-shopping" id="backHomeAccEnhanced">
              <i class="fas fa-shopping-bag"></i> Continue Shopping
            </button>
          </div>
        </div>
      `;

      // ---------- EVENT BINDINGS FOR LOGGED IN VIEW ----------
      
      // Edit Profile handler
      container.querySelector('#editProfileBtnEnhanced').addEventListener('click', () => {
        const profileInfoDisplay = container.querySelector('#profileInfoDisplay');
        profileInfoDisplay.innerHTML = `
          <div class="edit-input-group">
            <label>First Name</label>
            <input type="text" id="editFirstName" value="${userDetails.firstName}">
          </div>
          <div class="edit-input-group">
            <label>Last Name</label>
            <input type="text" id="editLastName" value="${userDetails.lastName}">
          </div>
          <div class="edit-input-group">
            <label>Email</label>
            <input type="email" id="editEmail" value="${userDetails.email || ''}">
          </div>
          <div class="edit-input-group">
            <label>Phone</label>
            <input type="tel" id="editPhone" value="${userDetails.phone}">
          </div>
          <button class="save-btn-inline" id="saveProfileBtn">💾 Save Changes</button>
          <button class="cancel-btn-inline" id="cancelProfileBtn">Cancel</button>
        `;

        container.querySelector('#saveProfileBtn').addEventListener('click', () => {
          userDetails.firstName = container.querySelector('#editFirstName').value.trim();
          userDetails.lastName = container.querySelector('#editLastName').value.trim();
          userDetails.email = container.querySelector('#editEmail').value.trim();
          userDetails.phone = container.querySelector('#editPhone').value.trim();
          
          KD.saveUser(userDetails);
          renderAccount();
          KD.showToast("Profile updated successfully! ✅", "#4A6552");
        });

        container.querySelector('#cancelProfileBtn').addEventListener('click', () => {
          renderAccount();
        });
      });

      // Edit Address handler
      container.querySelector('#editAddressBtnEnhanced').addEventListener('click', () => {
        const addressInfoDisplay = container.querySelector('#addressInfoDisplay');
        addressInfoDisplay.innerHTML = `
          <div class="edit-input-group">
            <label>Street Address</label>
            <input type="text" id="editAddress" value="${userDetails.address}">
          </div>
          <div class="edit-input-group">
            <label>City</label>
            <input type="text" id="editCity" value="${userDetails.city}">
          </div>
          <div class="edit-input-group">
            <label>Pincode</label>
            <input type="text" id="editPincode" value="${userDetails.pincode}">
          </div>
          <div class="edit-input-group">
            <label>State</label>
            <select id="editState">
              <option ${userDetails.state === 'Maharashtra' ? 'selected' : ''}>Maharashtra</option>
              <option ${userDetails.state === 'Delhi' ? 'selected' : ''}>Delhi</option>
              <option ${userDetails.state === 'Karnataka' ? 'selected' : ''}>Karnataka</option>
              <option ${userDetails.state === 'Tamil Nadu' ? 'selected' : ''}>Tamil Nadu</option>
              <option ${userDetails.state === 'West Bengal' ? 'selected' : ''}>West Bengal</option>
              <option ${userDetails.state === 'Gujarat' ? 'selected' : ''}>Gujarat</option>
            </select>
          </div>
          <button class="save-btn-inline" id="saveAddressBtn">💾 Save Address</button>
          <button class="cancel-btn-inline" id="cancelAddressBtn">Cancel</button>
        `;

        container.querySelector('#saveAddressBtn').addEventListener('click', () => {
          userDetails.address = container.querySelector('#editAddress').value.trim();
          userDetails.city = container.querySelector('#editCity').value.trim();
          userDetails.pincode = container.querySelector('#editPincode').value.trim();
          userDetails.state = container.querySelector('#editState').value;

          KD.saveUser(userDetails);
          renderAccount();
          KD.showToast("Address updated successfully! ✅", "#4A6552");
        });

        container.querySelector('#cancelAddressBtn').addEventListener('click', () => {
          renderAccount();
        });
      });

      // Preference toggles logic
      ['prefEmail', 'prefSMS', 'prefNewsletter', 'prefPromo'].forEach(id => {
        const toggle = container.querySelector(`#${id}`);
        if (toggle) {
          toggle.addEventListener('change', (e) => {
            const prefName = id.replace('pref', '');
            const status = e.target.checked ? 'enabled' : 'disabled';
            KD.showToast(`${prefName} notifications ${status}`, "#C17A5A");
          });
        }
      });

      // Quick actions links
      container.querySelector('#quickCart')?.addEventListener('click', () => {
        window.location.href = '/cart';
      });

      container.querySelector('#quickOrders')?.addEventListener('click', () => {
        KD.showToast("Order history coming soon! 📦", "#C17A5A");
      });

      container.querySelector('#quickWishlist')?.addEventListener('click', () => {
        KD.showToast("Wishlist feature coming soon! ❤️", "#C17A5A");
      });

      container.querySelector('#quickSupport')?.addEventListener('click', () => {
        KD.showToast("Contact us at hello@khusidecors.com", "#C17A5A");
      });

      // Logout handler
      container.querySelector('#logoutAccEnhanced').addEventListener('click', () => {
        localStorage.removeItem('vividUser_pro');
        KD.showToast("Logged out successfully 👋", "#4A6552");
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
      });

      // Continue Shopping
      container.querySelector('#backHomeAccEnhanced').addEventListener('click', () => {
        window.location.href = '/shop';
      });

    } else {
      // ============================================
      // ---------- LOGIN/SIGNUP FORM VIEW ----------
      // ============================================
      container.innerHTML = `
        <div class="auth-wrapper">
          <div class="auth-container">
            <div class="auth-left">
              <div class="auth-brand">
                <div class="auth-logo" style="font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 1rem;">Khushi Decors</div>
                <p style="font-size: 1.1rem; line-height: 1.6;">Join the Khushi Decors family and discover curated interiors for your dream home.</p>
              </div>
              <div class="auth-benefits" style="margin-top: 2rem;">
                <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                  <i class="fas fa-truck"></i> Free Shipping on orders ₹2000+
                </div>
                <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                  <i class="fas fa-undo-alt"></i> Easy 7-Day Returns
                </div>
                <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                  <i class="fas fa-gift"></i> Exclusive Member Offers
                </div>
                <div class="benefit-item" style="display:flex; align-items:center; gap:1rem; padding:0.8rem 0;">
                  <i class="fas fa-heart"></i> Save to Wishlist
                </div>
              </div>
            </div>
            
            <div class="auth-right">
              <div class="auth-tabs-container">
                <button class="auth-tab-btn active" data-tab="signup">Create Account</button>
                <button class="auth-tab-btn" data-tab="login">Sign In</button>
              </div>
              
              <div id="signupContainer" class="auth-form-container active">
                <div class="input-group">
                  <i class="fas fa-user"></i>
                  <input type="text" id="signupName" placeholder="Full Name" required>
                </div>
                <div class="input-group">
                  <i class="fas fa-envelope"></i>
                  <input type="email" id="signupEmail" placeholder="Email Address" required>
                </div>
                <div class="input-group">
                  <i class="fas fa-phone"></i>
                  <input type="tel" id="signupPhone" placeholder="Phone Number" required>
                </div>
                <div class="input-group">
                  <i class="fas fa-location-dot"></i>
                  <input type="text" id="signupAddress" placeholder="Street Address" required>
                </div>
                <div class="row-2">
                  <div class="input-group">
                    <i class="fas fa-city"></i>
                    <input type="text" id="signupCity" placeholder="City" required>
                  </div>
                  <div class="input-group">
                    <i class="fas fa-barcode"></i>
                    <input type="text" id="signupPincode" placeholder="Pincode" required>
                  </div>
                </div>
                <div class="input-group">
                  <i class="fas fa-map"></i>
                  <select id="signupState" required>
                    <option value="">Select State</option>
                    <option>Maharashtra</option>
                    <option>Delhi</option>
                    <option>Karnataka</option>
                    <option>Tamil Nadu</option>
                    <option>West Bengal</option>
                    <option>Gujarat</option>
                  </select>
                </div>
                <button type="button" class="auth-submit-btn" id="signupBtn">
                  <i class="fas fa-user-plus"></i> Create Account
                </button>
              </div>
              
              <div id="loginContainer" class="auth-form-container">
                <div class="input-group">
                  <i class="fas fa-envelope"></i>
                  <input type="email" id="loginEmail" placeholder="Email Address" required>
                </div>
                <div class="input-group">
                  <i class="fas fa-lock"></i>
                  <input type="password" id="loginPassword" placeholder="Password">
                </div>
                <button type="button" class="auth-submit-btn" id="loginBtn">
                  <i class="fas fa-sign-in-alt"></i> Sign In
                </button>
              </div>
              
              <button class="btn" id="skipAuth" style="width:100%; margin-top:1rem; background:transparent; border:1px solid #e0dbd0; color:#6c757d;">
                Continue as Guest
              </button>
            </div>
          </div>
        </div>
      `;

      // Tab Swapping
      container.querySelectorAll('.auth-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          container.querySelectorAll('.auth-tab-btn').forEach(t => t.classList.remove('active'));
          e.target.classList.add('active');
          container.querySelectorAll('.auth-form-container').forEach(f => f.classList.remove('active'));
          container.querySelector('#' + e.target.dataset.tab + 'Container').classList.add('active');
        });
      });

      // Signup form submit handler
      container.querySelector('#signupBtn').addEventListener('click', () => {
        const name = document.getElementById('signupName').value.trim();
        const email = document.getElementById('signupEmail').value.trim();
        const phone = document.getElementById('signupPhone').value.trim();
        const address = document.getElementById('signupAddress').value.trim();
        const city = document.getElementById('signupCity').value.trim();
        const pincode = document.getElementById('signupPincode').value.trim();
        const state = document.getElementById('signupState').value;

        if (!name || !email || !phone || !address || !city || !pincode || !state) {
          KD.showToast("Please fill all fields", "#c7362b");
          return;
        }

        const newUser = {
          firstName: name.split(' ')[0] || "User",
          lastName: name.split(' ').slice(1).join(' ') || "",
          email,
          phone,
          address,
          city,
          pincode,
          state
        };

        KD.saveUser(newUser);
        KD.showToast("Account created successfully! 🎉", "#4A6552");
        renderAccount();
      });

      // Login form submit handler
      container.querySelector('#loginBtn').addEventListener('click', () => {
        const email = document.getElementById('loginEmail').value.trim();
        if (!email) {
          KD.showToast("Please enter your email address", "#c7362b");
          return;
        }

        // Mock sign in - check if email matches saved email, or search in localStorage
        const stored = KD.getUser();
        if (stored && stored.email === email) {
          KD.showToast("Logged in successfully! ✅", "#4A6552");
          renderAccount();
        } else {
          KD.showToast("Email not found. Please sign up first.", "#c7362b");
          container.querySelector('.auth-tab-btn[data-tab="signup"]').click();
        }
      });

      // Skip Auth click handler
      container.querySelector('#skipAuth').addEventListener('click', () => {
        window.location.href = '/shop';
      });
    }
  }

  // Run rendering
  renderAccount();
});
