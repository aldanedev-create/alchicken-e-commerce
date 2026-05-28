document.querySelectorAll('.account-menu li').forEach(menuItem => {
    menuItem.addEventListener('click', function() {
        const tabId = this.dataset.tab;
        
        // Update active menu item
        document.querySelectorAll('.account-menu li').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
    });
});




