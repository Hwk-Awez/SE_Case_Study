/**
 * Software Component Cataloguing System
 * Vanilla JavaScript for interaction & modals
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mark as Reused Modal Handling
  const reuseModal = document.getElementById('reuseModal');
  const openReuseBtn = document.getElementById('openReuseModalBtn');
  const closeReuseBtn = document.getElementById('closeReuseModalBtn');
  const cancelReuseBtn = document.getElementById('cancelReuseBtn');

  if (openReuseBtn && reuseModal) {
    openReuseBtn.addEventListener('click', function () {
      reuseModal.classList.add('active');
    });
  }

  function closeReuseModal() {
    if (reuseModal) {
      reuseModal.classList.remove('active');
    }
  }

  if (closeReuseBtn) closeReuseBtn.addEventListener('click', closeReuseModal);
  if (cancelReuseBtn) cancelReuseBtn.addEventListener('click', closeReuseModal);

  // Close modal when clicking on background backdrop
  if (reuseModal) {
    reuseModal.addEventListener('click', function (e) {
      if (e.target === reuseModal) {
        closeReuseModal();
      }
    });
  }

  // 2. Dynamic Subcategory filter in Component Form
  const categorySelect = document.getElementById('id_category');
  const subcategorySelect = document.getElementById('id_subcategory');

  if (categorySelect && subcategorySelect) {
    // Store all subcategory options initially
    const subOptions = Array.from(subcategorySelect.querySelectorAll('option'));

    function filterSubcategories() {
      const selectedParentId = categorySelect.value;
      const currentSelectedVal = subcategorySelect.value;

      // Clear existing options
      subcategorySelect.innerHTML = '';

      // Default blank option
      const blankOption = document.createElement('option');
      blankOption.value = '';
      blankOption.textContent = '-- Select Subcategory (Optional) --';
      subcategorySelect.appendChild(blankOption);

      if (!selectedParentId) return;

      // Add options whose data-parent matches selected category
      let matchedCount = 0;
      subOptions.forEach(opt => {
        if (opt.value && opt.dataset.parent === selectedParentId) {
          const clone = opt.cloneNode(true);
          if (clone.value === currentSelectedVal) {
            clone.selected = true;
          }
          subcategorySelect.appendChild(clone);
          matchedCount++;
        }
      });
    }

    categorySelect.addEventListener('change', filterSubcategories);
  }

  // 3. Print Report Trigger
  const printBtn = document.getElementById('printReportBtn');
  if (printBtn) {
    printBtn.addEventListener('click', function () {
      window.print();
    });
  }
});
