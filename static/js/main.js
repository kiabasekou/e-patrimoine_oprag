
// main.js - Fonctions communes pour l'application de gestion de patrimoine

document.addEventListener('DOMContentLoaded', function() {
    // Gestion des messages flash
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                message.remove();
            }
        }, 5000); // Les messages disparaissent après 5 secondes
    });

    // Confirmation de suppression générique
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.')) {
                e.preventDefault();
            }
        });
    });

    // Activation des tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Pour les formulaires avec champs requis, ajouter une indication visuelle
    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
    requiredFields.forEach(function(field) {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label && !label.querySelector('.required-indicator')) {
            const indicator = document.createElement('span');
            indicator.classList.add('required-indicator', 'text-danger', 'ms-1');
            indicator.textContent = '*';
            label.appendChild(indicator);
        }
    });

    // Ajouter la classe active au menu correspondant à la page actuelle
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
        } else if (currentPath === '/' && href === '/') {
            link.classList.add('active');
        }
    });

    // Gestion des alertes personnalisées
    window.showAlert = function(message, type = 'info') {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertContainer.setAttribute('role', 'alert');
        alertContainer.style.zIndex = '9999';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertContainer);
        
        setTimeout(function() {
            const closeButton = alertContainer.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alertContainer.remove();
            }
        }, 5000);
    };

    // Formatter les valeurs monétaires
    document.querySelectorAll('.format-currency').forEach(function(element) {
        const value = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
        if (!isNaN(value)) {
            element.textContent = new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'XAF',
                minimumFractionDigits: 0
            }).format(value);
        }
    });

    // Pour les tableaux filtrables
    const tableFilter = document.getElementById('tableFilter');
    if (tableFilter) {
        tableFilter.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const table = document.querySelector(this.dataset.table);
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filterValue) ? '' : 'none';
            });
        });
    }

    // Recherche dynamique dans les selects
    document.querySelectorAll('.select-search').forEach(function(select) {
        // Ici, vous pourriez ajouter une bibliothèque comme select2 pour améliorer l'expérience
        select.addEventListener('focus', function() {
            console.log('Améliorer cette expérience avec select2 ou similaire');
        });
    });

    // Pour les charts responsives
    window.addEventListener('resize', function() {
        if (window.resizeCharts && typeof window.resizeCharts === 'function') {
            window.resizeCharts();
        }
    });
});

// Pour l'ajout de profil technique
function setupProfilTechniqueForm() {
    // Implémenté dans chaque page où c'est nécessaire via une balise script spécifique
    console.log('Form setup function loaded');
}

// Fonctions d'aide pour les formats de date
const formatUtils = {
    formatDate: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('fr-FR');
    },
    
    parseDate: function(dateString) {
        if (!dateString) return null;
        const parts = dateString.split('/');
        if (parts.length !== 3) return null;
        return new Date(parts[2], parts[1] - 1, parts[0]);
    },
    
    calculateAge: function(dateString) {
        const birthDate = this.parseDate(dateString);
        if (!birthDate) return null;
        
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        
        return age;
    }
};

// Gestion des formulaires d'ajout dynamiques
function setupDynamicFormFields() {
    const addFieldButtons = document.querySelectorAll('.add-field-btn');
    
    addFieldButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const fieldContainer = document.getElementById(this.dataset.container);
            const template = document.getElementById(this.dataset.template);
            const clone = template.content.cloneNode(true);
            
            // Mettre à jour les IDs et attributs pour éviter les doublons
            const newIndex = fieldContainer.querySelectorAll('.dynamic-form-row').length;
            const inputs = clone.querySelectorAll('input, select, textarea');
            
            inputs.forEach(function(input) {
                const name = input.getAttribute('name');
                if (name) {
                    const newName = name.replace('__prefix__', newIndex);
                    input.setAttribute('name', newName);
                    input.setAttribute('id', `id_${newName}`);
                }
            });
            
            // Ajouter le nouveau champ
            fieldContainer.appendChild(clone);
            
            // Ajouter un bouton de suppression
            const rowElement = fieldContainer.lastElementChild;
            const deleteButton = rowElement.querySelector('.delete-field-btn');
            
            if (deleteButton) {
                deleteButton.addEventListener('click', function() {
                    rowElement.remove();
                });
            }
        });
    });
}

// Gestion des filtres avancés
function setupAdvancedFilters() {
    const showFiltersBtn = document.getElementById('show-advanced-filters');
    const filtersContainer = document.getElementById('advanced-filters-container');
    
    if (showFiltersBtn && filtersContainer) {
        showFiltersBtn.addEventListener('click', function() {
            filtersContainer.classList.toggle('d-none');
            this.innerHTML = filtersContainer.classList.contains('d-none') 
                ? '<i class="fas fa-filter me-2"></i>Afficher les filtres avancés'
                : '<i class="fas fa-times me-2"></i>Masquer les filtres avancés';
        });
    }
}

// Formatter les nombres en format monétaire FCFA
function formatMoney(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'decimal',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount) + ' FCFA';
}

// Initialiser les graphiques
function initCharts() {
    // Cette fonction sera définie dans chaque page nécessitant des graphiques
    console.log('Charts initialization placeholder');
}

// Gestion de la sélection de commune pour les adresses
function setupLocationSelectors() {
    const provinceSelect = document.getElementById('id_province');
    const departementSelect = document.getElementById('id_departement');
    const communeSelect = document.getElementById('id_commune');
    
    if (provinceSelect && departementSelect) {
        provinceSelect.addEventListener('change', function() {
            const provinceId = this.value;
            
            if (provinceId) {
                // Requête AJAX pour charger les départements
                fetch(`/api/departements/?province=${provinceId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Réinitialiser les options
                        departementSelect.innerHTML = '<option value="">Sélectionnez un département</option>';
                        
                        // Ajouter les nouvelles options
                        data.forEach(dept => {
                            const option = document.createElement('option');
                            option.value = dept.id;
                            option.textContent = dept.nom;
                            departementSelect.appendChild(option);
                        });
                        
                        // Réinitialiser les communes
                        if (communeSelect) {
                            communeSelect.innerHTML = '<option value="">Sélectionnez une commune</option>';
                        }
                    });
            }
        });
    }
    
    if (departementSelect && communeSelect) {
        departementSelect.addEventListener('change', function() {
            const departementId = this.value;
            
            if (departementId) {
                // Requête AJAX pour charger les communes
                fetch(`/api/communes/?departement=${departementId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Réinitialiser les options
                        communeSelect.innerHTML = '<option value="">Sélectionnez une commune</option>';
                        
                        // Ajouter les nouvelles options
                        data.forEach(commune => {
                            const option = document.createElement('option');
                            option.value = commune.id;
                            option.textContent = commune.nom;
                            communeSelect.appendChild(option);
                        });
                    });
            }
        });
    }
}

// Export de données vers Excel/CSV
function setupExportButtons() {
    const exportButtons = document.querySelectorAll('.export-btn');
    
    exportButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const url = new URL(this.href);
            const filterForm = document.getElementById(this.dataset.filterForm);
            
            if (filterForm) {
                // Ajouter les filtres à l'URL d'export
                const formData = new FormData(filterForm);
                for (const [key, value] of formData.entries()) {
                    if (value) {
                        url.searchParams.append(key, value);
                    }
                }
            }
            
            // Ajouter format=excel ou format=csv
            url.searchParams.append('format', this.dataset.format || 'excel');
            
            // Rediriger vers l'URL d'export avec les filtres
            window.location.href = url.toString();
        });
    });
}

// Gestionnaire de fichiers justificatifs
function setupFileHandlers() {
    const fileInputs = document.querySelectorAll('.custom-file-input');
    
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Aucun fichier sélectionné';
            const label = this.nextElementSibling;
            
            if (label) {
                label.textContent = fileName;
            }
            
            // Vérifier la taille du fichier
            const maxSize = parseInt(this.dataset.maxSize || 5) * 1024 * 1024; // en Mo
            
            if (this.files[0] && this.files[0].size > maxSize) {
                window.showAlert(`Le fichier est trop volumineux. Taille maximale: ${this.dataset.maxSize || 5}Mo`, 'danger');
                this.value = ''; // Effacer la sélection
                if (label) {
                    label.textContent = 'Aucun fichier sélectionné';
                }
            }
            
            // Vérifier le type de fichier
            const allowedTypes = this.dataset.acceptedTypes?.split(',') || ['.pdf', '.jpg', '.png', '.doc', '.docx'];
            const fileExtension = '.' + this.files[0]?.name.split('.').pop().toLowerCase();
            
            if (this.files[0] && !allowedTypes.includes(fileExtension)) {
                window.showAlert(`Type de fichier non autorisé. Types acceptés: ${allowedTypes.join(', ')}`, 'danger');
                this.value = ''; // Effacer la sélection
                if (label) {
                    label.textContent = 'Aucun fichier sélectionné';
                }
            }
        });
    });
}

// Initialiser tous les composants interactifs
function initComponents() {
    setupDynamicFormFields();
    setupAdvancedFilters();
    setupLocationSelectors();
    setupExportButtons();
    setupFileHandlers();
}

// Appeler l'initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', initComponents);