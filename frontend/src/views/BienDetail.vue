<!-- frontend/src/views/BienDetail.vue -->
<template>
  <div class="bien-detail" v-if="bien">
    <!-- Header avec actions -->
    <div class="header-section">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
              <li class="breadcrumb-item">
                <router-link to="/dashboard">Dashboard</router-link>
              </li>
              <li class="breadcrumb-item">
                <router-link to="/biens">Inventaire</router-link>
              </li>
              <li class="breadcrumb-item active">{{ bien.code_patrimoine }}</li>
            </ol>
          </nav>
          <h1 class="h2 mb-3">
            {{ bien.nom }}
            <span class="badge" :class="getStatutClass(bien.statut)">
              {{ bien.statut_display }}
            </span>
          </h1>
          <div class="text-muted">
            <i class="bi bi-tag me-2"></i>{{ bien.categorie.nom }} - {{ bien.sous_categorie.nom }}
            <span class="mx-2">|</span>
            <i class="bi bi-building me-2"></i>{{ bien.entite.nom }}
          </div>
        </div>
        
        <div class="btn-group">
          <button
            class="btn btn-outline-primary"
            @click="showEditModal = true"
            v-if="canEdit"
          >
            <i class="bi bi-pencil me-2"></i>Modifier
          </button>
          <button
            class="btn btn-outline-primary dropdown-toggle dropdown-toggle-split"
            data-bs-toggle="dropdown"
          >
            <span class="visually-hidden">Actions</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end">
            <li>
              <a class="dropdown-item" @click="showTransferModal = true">
                <i class="bi bi-arrow-left-right me-2"></i>Transférer
              </a>
            </li>
            <li>
              <a class="dropdown-item" @click="showMaintenanceModal = true">
                <i class="bi bi-tools me-2"></i>Planifier maintenance
              </a>
            </li>
            <li>
              <a class="dropdown-item" @click="showResponsableModal = true">
                <i class="bi bi-person-badge me-2"></i>Assigner responsable
              </a>
            </li>
            <li><hr class="dropdown-divider"></li>
            <li>
              <a class="dropdown-item" @click="genererQRCode">
                <i class="bi bi-qr-code me-2"></i>Générer QR Code
              </a>
            </li>
            <li>
              <a class="dropdown-item" @click="exporterFiche">
                <i class="bi bi-file-pdf me-2"></i>Exporter fiche
              </a>
            </li>
            <li v-if="canReform"><hr class="dropdown-divider"></li>
            <li v-if="canReform">
              <a class="dropdown-item text-danger" @click="showReformModal = true">
                <i class="bi bi-x-circle me-2"></i>Réformer
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Alertes et notifications -->
    <div class="alerts-section mt-4" v-if="alertes.length > 0">
      <div
        v-for="alerte in alertes"
        :key="alerte.id"
        class="alert alert-dismissible fade show"
        :class="`alert-${alerte.type}`"
      >
        <i :class="getAlertIcon(alerte.type)" class="me-2"></i>
        {{ alerte.message }}
        <button
          type="button"
          class="btn-close"
          @click="dismissAlert(alerte.id)"
        ></button>
      </div>
    </div>

    <!-- Contenu principal en tabs -->
    <div class="content-section mt-4">
      <ul class="nav nav-tabs" role="tablist">
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'informations' }"
            @click="activeTab = 'informations'"
          >
            <i class="bi bi-info-circle me-2"></i>Informations
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'technique' }"
            @click="activeTab = 'technique'"
          >
            <i class="bi bi-gear me-2"></i>Fiche technique
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'valeurs' }"
            @click="activeTab = 'valeurs'"
          >
            <i class="bi bi-graph-up me-2"></i>Valeurs
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'historique' }"
            @click="activeTab = 'historique'"
          >
            <i class="bi bi-clock-history me-2"></i>Historique
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'documents' }"
            @click="activeTab = 'documents'"
          >
            <i class="bi bi-folder me-2"></i>Documents
            <span class="badge bg-secondary ms-1">{{ documentsCount }}</span>
          </button>
        </li>
      </ul>

      <div class="tab-content mt-4">
        <!-- Tab Informations -->
        <div v-show="activeTab === 'informations'" class="tab-pane fade show active">
          <div class="row">
            <div class="col-md-8">
              <div class="card">
                <div class="card-body">
                  <h5 class="card-title mb-4">Informations générales</h5>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Code patrimoine</div>
                    <div class="col-sm-8">
                      <code>{{ bien.code_patrimoine }}</code>
                      <button
                        class="btn btn-sm btn-link"
                        @click="copierCode"
                      >
                        <i class="bi bi-clipboard"></i>
                      </button>
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Description</div>
                    <div class="col-sm-8">
                      {{ bien.description || 'Aucune description' }}
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">État physique</div>
                    <div class="col-sm-8">
                      <span class="badge" :class="getEtatClass(bien.etat_physique)">
                        {{ bien.etat_physique_display }}
                      </span>
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Localisation</div>
                    <div class="col-sm-8">
                      <i class="bi bi-geo-alt me-1"></i>
                      {{ bien.commune?.nom || 'Non spécifiée' }}
                      <span v-if="bien.localisation_precise">
                        - {{ bien.localisation_precise }}
                      </span>
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Date d'acquisition</div>
                    <div class="col-sm-8">
                      {{ formatDate(bien.date_acquisition) }}
                      <span class="text-muted ms-2">
                        ({{ getAge(bien.date_acquisition) }})
                      </span>
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Fournisseur</div>
                    <div class="col-sm-8">
                      {{ bien.fournisseur || 'Non spécifié' }}
                    </div>
                  </div>
                  
                  <div class="row mb-3" v-if="bien.tags?.length > 0">
                    <div class="col-sm-4 text-muted">Tags</div>
                    <div class="col-sm-8">
                      <span
                        v-for="tag in bien.tags"
                        :key="tag"
                        class="badge bg-secondary me-1"
                      >
                        {{ tag }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Responsable actuel -->
              <div class="card mt-3">
                <div class="card-body">
                  <h5 class="card-title mb-4">
                    Responsable actuel
                    <button
                      class="btn btn-sm btn-outline-primary float-end"
                      @click="showResponsableModal = true"
                    >
                      <i class="bi bi-person-plus"></i>
                    </button>
                  </h5>
                  
                  <div v-if="responsableActuel" class="d-flex align-items-center">
                    <div class="avatar me-3">
                      <img
                        :src="responsableActuel.avatar || '/img/default-avatar.png'"
                        class="rounded-circle"
                        width="48"
                        height="48"
                        :alt="responsableActuel.nom"
                      >
                    </div>
                    <div>
                      <h6 class="mb-0">{{ responsableActuel.nom }}</h6>
                      <div class="text-muted small">
                        {{ responsableActuel.fonction }} - {{ responsableActuel.entite }}
                      </div>
                      <div class="text-muted small">
                        Depuis le {{ formatDate(responsableActuel.date_affectation) }}
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-muted">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Aucun responsable assigné
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Sidebar -->
            <div class="col-md-4">
              <!-- Carte de valeur -->
              <div class="card bg-primary text-white">
                <div class="card-body">
                  <h5 class="card-title">Valeur actuelle</h5>
                  <h2 class="display-6 mb-0">
                    {{ formatCurrency(bien.valeur_actuelle) }}
                  </h2>
                  <div class="mt-2">
                    <small>Valeur d'acquisition: {{ formatCurrency(bien.valeur_acquisition) }}</small>
                  </div>
                  <div class="progress mt-3" style="height: 8px;">
                    <div
                      class="progress-bar bg-white"
                      :style="{ width: `${100 - bien.taux_amortissement}%` }"
                    ></div>
                  </div>
                  <small class="d-block mt-1">
                    Amortissement: {{ bien.taux_amortissement }}%
                  </small>
                </div>
              </div>
              
              <!-- Actions rapides -->
              <div class="card mt-3">
                <div class="card-body">
                  <h6 class="card-title">Actions rapides</h6>
                  <div class="d-grid gap-2">
                    <button
                      class="btn btn-outline-primary btn-sm"
                      @click="showHistoriqueValeurModal = true"
                    >
                      <i class="bi bi-plus-circle me-2"></i>Ajouter une valeur
                    </button>
                    <button
                      class="btn btn-outline-primary btn-sm"
                      @click="showDocumentModal = true"
                    >
                      <i class="bi bi-file-earmark-plus me-2"></i>Ajouter document
                    </button>
                    <button
                      class="btn btn-outline-primary btn-sm"
                      @click="showPhotoModal = true"
                    >
                      <i class="bi bi-camera me-2"></i>Ajouter photo
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Prochaine maintenance -->
              <div class="card mt-3" v-if="bien.prochaine_maintenance">
                <div class="card-body">
                  <h6 class="card-title">Prochaine maintenance</h6>
                  <div class="d-flex align-items-center">
                    <i class="bi bi-calendar-event text-warning fs-3 me-3"></i>
                    <div>
                      <div class="fw-bold">{{ formatDate(bien.prochaine_maintenance) }}</div>
                      <small class="text-muted">
                        Dans {{ getDaysUntil(bien.prochaine_maintenance) }} jours
                      </small>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Garantie -->
              <div class="card mt-3" v-if="bien.date_fin_garantie">
                <div class="card-body">
                  <h6 class="card-title">Garantie</h6>
                  <div class="d-flex align-items-center">
                    <i
                      class="bi fs-3 me-3"
                      :class="[
                        isGarantieActive ? 'bi-shield-check text-success' : 'bi-shield-x text-danger'
                      ]"
                    ></i>
                    <div>
                      <div class="fw-bold">
                        {{ isGarantieActive ? 'Active' : 'Expirée' }}
                      </div>
                      <small class="text-muted">
                        {{ isGarantieActive ? 'Jusqu\'au' : 'Expirée le' }}
                        {{ formatDate(bien.date_fin_garantie) }}
                      </small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab Fiche technique -->
        <div v-show="activeTab === 'technique'" class="tab-pane">
          <ProfilTechnique
            :bien="bien"
            :profil="profilTechnique"
            :editable="canEdit"
            @update="updateProfilTechnique"
          />
        </div>

        <!-- Tab Valeurs -->
        <div v-show="activeTab === 'valeurs'" class="tab-pane">
          <div class="row">
            <div class="col-md-8">
              <div class="card">
                <div class="card-body">
                  <h5 class="card-title">Évolution de la valeur</h5>
                  <canvas ref="chartValeur" height="100"></canvas>
                </div>
              </div>
              
              <div class="card mt-3">
                <div class="card-body">
                  <h5 class="card-title">
                    Historique des valeurs
                    <button
                      class="btn btn-sm btn-outline-primary float-end"
                      @click="showHistoriqueValeurModal = true"
                    >
                      <i class="bi bi-plus"></i>
                    </button>
                  </h5>
                  <div class="table-responsive">
                    <table class="table table-sm">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Valeur</th>
                          <th>Type</th>
                          <th>Motif</th>
                          <th>Évaluateur</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="valeur in historiqueValeurs" :key="valeur.id">
                          <td>{{ formatDate(valeur.date) }}</td>
                          <td>{{ formatCurrency(valeur.valeur) }}</td>
                          <td>
                            <span class="badge bg-secondary">
                              {{ valeur.type_evaluation_display }}
                            </span>
                          </td>
                          <td>{{ valeur.motif }}</td>
                          <td>{{ valeur.evaluateur }}</td>
                          <td>
                            <button
                              v-if="valeur.document_justificatif"
                              class="btn btn-sm btn-link"
                              @click="telechargerDocument(valeur.document_justificatif)"
                            >
                              <i class="bi bi-download"></i>
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="col-md-4">
              <div class="card">
                <div class="card-body">
                  <h5 class="card-title">Calcul d'amortissement</h5>
                  <dl class="row">
                    <dt class="col-6">Méthode</dt>
                    <dd class="col-6">{{ amortissement.methode }}</dd>
                    
                    <dt class="col-6">Base amortissable</dt>
                    <dd class="col-6">{{ formatCurrency(amortissement.base_amortissable) }}</dd>
                    
                    <dt class="col-6">Durée</dt>
                    <dd class="col-6">{{ bien.duree_amortissement }} mois</dd>
                    
                    <dt class="col-6">Dotation mensuelle</dt>
                    <dd class="col-6">{{ formatCurrency(amortissement.dotation_mensuelle) }}</dd>
                    
                    <dt class="col-6">Cumulé</dt>
                    <dd class="col-6">{{ formatCurrency(amortissement.amortissement_cumule) }}</dd>
                    
                    <dt class="col-6">Mois restants</dt>
                    <dd class="col-6">{{ amortissement.mois_restants }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab Historique -->
        <div v-show="activeTab === 'historique'" class="tab-pane">
          <Timeline :bien-id="bien.id" />
        </div>

        <!-- Tab Documents -->
        <div v-show="activeTab === 'documents'" class="tab-pane">
          <DocumentsManager
            :bien-id="bien.id"
            :documents="documents"
            @upload="handleDocumentUpload"
            @delete="handleDocumentDelete"
          />
        </div>
      </div>
    </div>

    <!-- Modals -->
    <EditBienModal
      v-if="showEditModal"
      :bien="bien"
      @close="showEditModal = false"
      @saved="handleBienUpdated"
    />
    
    <TransferBienModal
      v-if="showTransferModal"
      :bien="bien"
      @close="showTransferModal = false"
      @transferred="handleBienTransferred"
    />
    
    <MaintenanceModal
      v-if="showMaintenanceModal"
      :bien="bien"
      @close="showMaintenanceModal = false"
      @scheduled="handleMaintenanceScheduled"
    />
    
    <ResponsableModal
      v-if="showResponsableModal"
      :bien="bien"
      @close="showResponsableModal = false"
      @assigned="handleResponsableAssigned"
    />
    
    <HistoriqueValeurModal
      v-if="showHistoriqueValeurModal"
      :bien="bien"
      @close="showHistoriqueValeurModal = false"
      @added="handleValeurAdded"
    />
    
    <ReformModal
      v-if="showReformModal"
      :bien="bien"
      @close="showReformModal = false"
      @reformed="handleBienReformed"
    />
  </div>
  
  <div v-else-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Chargement...</span>
    </div>
  </div>
  
  <div v-else-if="error" class="alert alert-danger">
    <i class="bi bi-exclamation-triangle me-2"></i>
    {{ error }}
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import Chart from 'chart.js/auto'
import { format, formatDistance, differenceInDays, parseISO } from 'date-fns'
import { fr } from 'date-fns/locale'

// Stores
import { useBienStore } from '@/stores/bien'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

// Components
import ProfilTechnique from '@/components/biens/ProfilTechnique.vue'
import Timeline from '@/components/biens/Timeline.vue'
import DocumentsManager from '@/components/biens/DocumentsManager.vue'
import EditBienModal from '@/components/modals/EditBienModal.vue'
import TransferBienModal from '@/components/modals/TransferBienModal.vue'
import MaintenanceModal from '@/components/modals/MaintenanceModal.vue'
import ResponsableModal from '@/components/modals/ResponsableModal.vue'
import HistoriqueValeurModal from '@/components/modals/HistoriqueValeurModal.vue'
import ReformModal from '@/components/modals/ReformModal.vue'

// Types
import type { Bien, HistoriqueValeur, Document } from '@/types'

// Composables
import { usePermissions } from '@/composables/usePermissions'
import { useCurrency } from '@/composables/useCurrency'

const route = useRoute()
const router = useRouter()
const bienStore = useBienStore()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const { hasPermission } = usePermissions()
const { formatCurrency } = useCurrency()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref('informations')
const chartValeur = ref<HTMLCanvasElement>()
const chartInstance = ref<Chart | null>(null)

// Modals
const showEditModal = ref(false)
const showTransferModal = ref(false)
const showMaintenanceModal = ref(false)
const showResponsableModal = ref(false)
const showHistoriqueValeurModal = ref(false)
const showReformModal = ref(false)
const showDocumentModal = ref(false)
const showPhotoModal = ref(false)

// Data
const bien = ref<Bien | null>(null)
const profilTechnique = ref<any>(null)
const historiqueValeurs = ref<HistoriqueValeur[]>([])
const documents = ref<Document[]>([])
const amortissement = ref<any>({})
const alertes = ref<any[]>([])

// Computed
const { user } = storeToRefs(authStore)

const canEdit = computed(() => {
  return hasPermission('patrimoine.change_bien') && 
         bien.value?.statut !== 'REFORME'
})

const canReform = computed(() => {
  return hasPermission('patrimoine.can_reform_bien')
})

const responsableActuel = computed(() => {
  return bien.value?.responsable_actuel
})

const isGarantieActive = computed(() => {
  if (!bien.value?.date_fin_garantie) return false
  return new Date(bien.value.date_fin_garantie) > new Date()
})

const documentsCount = computed(() => {
  let count = documents.value.length
  if (bien.value?.facture) count++
  if (bien.value?.photo_principale) count++
  return count
})

// Methods
const loadBien = async () => {
  try {
    loading.value = true
    error.value = null
    
    const bienId = route.params.id as string
    const data = await bienStore.fetchBien(bienId)
    
    bien.value = data.bien
    profilTechnique.value = data.profil_technique
    historiqueValeurs.value = data.historique_valeurs
    documents.value = data.documents
    amortissement.value = data.amortissement
    
    // Charger les alertes
    checkAlertes()
    
    // Initialiser le graphique
    if (activeTab.value === 'valeurs') {
      initChart()
    }
  } catch (err) {
    error.value = "Erreur lors du chargement du bien"
    console.error(err)
  } finally {
    loading.value = false
  }
}

const checkAlertes = () => {
  alertes.value = []
  
  if (!bien.value) return
  
  // Maintenance en retard
  if (bien.value.prochaine_maintenance) {
    const jours = differenceInDays(
      new Date(bien.value.prochaine_maintenance),
      new Date()
    )
    if (jours < 0) {
      alertes.value.push({
        id: 'maintenance',
        type: 'warning',
        message: `Maintenance en retard de ${Math.abs(jours)} jours`
      })
    }
  }
  
  // Garantie expirée
  if (bien.value.date_fin_garantie) {
    const garantieExpired = new Date(bien.value.date_fin_garantie) < new Date()
    if (garantieExpired) {
      const mois = Math.abs(differenceInDays(
        new Date(bien.value.date_fin_garantie),
        new Date()
      )) / 30
      if (mois < 3) {
        alertes.value.push({
          id: 'garantie',
          type: 'info',
          message: 'Garantie expirée récemment'
        })
      }
    }
  }
  
  // Sans responsable
  if (!bien.value.responsable_actuel) {
    alertes.value.push({
      id: 'responsable',
      type: 'danger',
      message: 'Aucun responsable assigné'
    })
  }
  
  // État critique
  if (['MAUVAIS', 'HORS_USAGE'].includes(bien.value.etat_physique)) {
    alertes.value.push({
      id: 'etat',
      type: 'danger',
      message: 'État physique critique'
    })
  }
}

const initChart = () => {
  if (!chartValeur.value || !historiqueValeurs.value.length) return
  
  const ctx = chartValeur.value.getContext('2d')
  if (!ctx) return
  
  // Détruire le graphique existant
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }
  
  const data = historiqueValeurs.value
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map(h => ({
      x: h.date,
      y: h.valeur
    }))
  
  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Valeur',
        data: data,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              return formatCurrency(context.parsed.y)
            }
          }
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'month',
            displayFormats: {
              month: 'MMM yyyy'
            }
          }
        },
        y: {
          ticks: {
            callback: (value) => {
              return formatCurrency(value as number)
            }
          }
        }
      }
    }
  })
}

// Formatters
const formatDate = (date: string) => {
  return format(parseISO(date), 'dd MMMM yyyy', { locale: fr })
}

const getAge = (date: string) => {
  return formatDistance(parseISO(date), new Date(), {
    locale: fr,
    addSuffix: true
  })
}

const getDaysUntil = (date: string) => {
  return differenceInDays(parseISO(date), new Date())
}

// Helpers
const getStatutClass = (statut: string) => {
  const classes: Record<string, string> = {
    'ACTIF': 'bg-success',
    'INACTIF': 'bg-secondary',
    'MAINTENANCE': 'bg-warning',
    'REFORME': 'bg-danger',
    'CEDE': 'bg-info'
  }
  return classes[statut] || 'bg-secondary'
}

const getEtatClass = (etat: string) => {
  const classes: Record<string, string> = {
    'NEUF': 'bg-success',
    'EXCELLENT': 'bg-success',
    'BON': 'bg-primary',
    'MOYEN': 'bg-warning',
    'MAUVAIS': 'bg-danger',
    'HORS_USAGE': 'bg-dark'
  }
  return classes[etat] || 'bg-secondary'
}

const getAlertIcon = (type: string) => {
  const icons: Record<string, string> = {
    'danger': 'bi-exclamation-triangle-fill',
    'warning': 'bi-exclamation-circle-fill',
    'info': 'bi-info-circle-fill',
    'success': 'bi-check-circle-fill'
  }
  return icons[type] || 'bi-info-circle-fill'
}

// Actions
const copierCode = () => {
  if (!bien.value) return
  navigator.clipboard.writeText(bien.value.code_patrimoine)
  notificationStore.success('Code copié dans le presse-papier')
}

const genererQRCode = async () => {
  if (!bien.value) return
  try {
    const blob = await bienStore.genererQRCode(bien.value.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `QR_${bien.value.code_patrimoine}.png`
    a.click()
    URL.revokeObjectURL(url)
    notificationStore.success('QR Code généré')
  } catch (error) {
    notificationStore.error('Erreur lors de la génération du QR Code')
  }
}

const exporterFiche = async () => {
  if (!bien.value) return
  try {
    const blob = await bienStore.exporterFiche(bien.value.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Fiche_${bien.value.code_patrimoine}.pdf`
    a.click()
    URL.revokeObjectURL(url)
    notificationStore.success('Fiche exportée')
  } catch (error) {
    notificationStore.error('Erreur lors de l\'export')
  }
}

const dismissAlert = (id: string) => {
  alertes.value = alertes.value.filter(a => a.id !== id)
}

// Event handlers
const handleBienUpdated = (updatedBien: Bien) => {
  bien.value = updatedBien
  showEditModal.value = false
  notificationStore.success('Bien mis à jour')
  checkAlertes()
}

const handleBienTransferred = () => {
  showTransferModal.value = false
  notificationStore.success('Transfert effectué')
  loadBien()
}

const handleMaintenanceScheduled = () => {
  showMaintenanceModal.value = false
  notificationStore.success('Maintenance planifiée')
  loadBien()
}

const handleResponsableAssigned = () => {
  showResponsableModal.value = false
  notificationStore.success('Responsable assigné')
  loadBien()
}

const handleValeurAdded = () => {
  showHistoriqueValeurModal.value = false
  notificationStore.success('Valeur ajoutée')
  loadBien()
}

const handleBienReformed = () => {
  showReformModal.value = false
  notificationStore.success('Bien réformé')
  router.push('/biens')
}

const handleDocumentUpload = async (files: File[]) => {
  // Implémenter l'upload de documents
}

const handleDocumentDelete = async (documentId: string) => {
  // Implémenter la suppression de document
}

const updateProfilTechnique = async (data: any) => {
  // Implémenter la mise à jour du profil technique
}

const telechargerDocument = (url: string) => {
  window.open(url, '_blank')
}

// Lifecycle
onMounted(() => {
  loadBien()
})

// Watchers
watch(activeTab, (newTab) => {
  if (newTab === 'valeurs' && historiqueValeurs.value.length > 0) {
    setTimeout(() => initChart(), 100)
  }
})
</script>

<style scoped lang="scss">
.bien-detail {
  .header-section {
    background-color: var(--bs-gray-100);
    padding: 2rem 0;
    margin: -2rem -2rem 0;
    padding-left: 2rem;
    padding-right: 2rem;
  }
  
  .avatar {
    img {
      border: 3px solid var(--bs-gray-300);
    }
  }
  
  .nav-tabs {
    .nav-link {
      color: var(--bs-gray-600);
      
      &.active {
        color: var(--bs-primary);
        font-weight: 500;
      }
      
      &:hover:not(.active) {
        color: var(--bs-gray-800);
      }
    }
  }
  
  .progress {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  code {
    padding: 0.2rem 0.4rem;
    background-color: var(--bs-gray-200);
    border-radius: 0.25rem;
  }
}
</style>