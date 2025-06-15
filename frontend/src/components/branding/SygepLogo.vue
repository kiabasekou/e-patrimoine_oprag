<!-- frontend/src/components/branding/SygepLogo.vue -->
<template>
  <div class="sygep-logo" :class="[sizeClass, variantClass]">
    <div class="logo-container">
      <!-- Logo SVG -->
      <svg
        v-if="!imageOnly"
        viewBox="0 0 200 60"
        xmlns="http://www.w3.org/2000/svg"
        class="logo-svg"
      >
        <!-- Icône stylisée port/patrimoine -->
        <g class="logo-icon">
          <!-- Vagues représentant la mer/port -->
          <path
            d="M10 35 Q 20 30, 30 35 T 50 35"
            stroke="#0066CC"
            stroke-width="2"
            fill="none"
          />
          <path
            d="M10 40 Q 20 35, 30 40 T 50 40"
            stroke="#003366"
            stroke-width="2"
            fill="none"
          />
          
          <!-- Bâtiment/Grue portuaire stylisée -->
          <rect x="25" y="15" width="10" height="20" fill="#003366" />
          <path
            d="M20 15 L40 15 L30 5 Z"
            fill="#FF6B35"
          />
          <line x1="30" y1="5" x2="30" y2="0" stroke="#003366" stroke-width="2" />
          
          <!-- Conteneur -->
          <rect x="35" y="25" width="12" height="8" fill="#0066CC" rx="1" />
        </g>
        
        <!-- Texte SYGEP -->
        <text x="60" y="30" class="logo-text-primary">
          SYGEP
        </text>
        
        <!-- Séparateur -->
        <line
          v-if="showFullName"
          x1="60"
          y1="35"
          x2="140"
          y2="35"
          stroke="#003366"
          stroke-width="1"
          opacity="0.3"
        />
        
        <!-- Texte OPRAG -->
        <text
          v-if="showFullName"
          x="60"
          y="48"
          class="logo-text-secondary"
        >
          OPRAG
        </text>
      </svg>
      
      <!-- Alternative image -->
      <img
        v-else
        :src="logoSrc"
        :alt="altText"
        class="logo-image"
      >
    </div>
    
    <!-- Tagline optionnelle -->
    <div v-if="showTagline" class="logo-tagline">
      Système de Gestion du Patrimoine
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'small' | 'medium' | 'large' | 'xl'
  variant?: 'default' | 'white' | 'dark' | 'colored'
  showFullName?: boolean
  showTagline?: boolean
  imageOnly?: boolean
  customSrc?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  variant: 'default',
  showFullName: true,
  showTagline: false,
  imageOnly: false,
  customSrc: ''
})

const sizeClass = computed(() => `logo-${props.size}`)
const variantClass = computed(() => `logo-${props.variant}`)

const logoSrc = computed(() => {
  return props.customSrc || `/static/img/logo-sygep-${props.variant}.png`
})

const altText = computed(() => {
  return props.showFullName ? 'SYGEP-OPRAG Logo' : 'SYGEP Logo'
})
</script>

<style scoped lang="scss">
.sygep-logo {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
  
  // Tailles
  &.logo-small {
    .logo-svg {
      height: 30px;
    }
    .logo-image {
      height: 30px;
    }
    .logo-tagline {
      font-size: 0.7rem;
    }
  }
  
  &.logo-medium {
    .logo-svg {
      height: 40px;
    }
    .logo-image {
      height: 40px;
    }
    .logo-tagline {
      font-size: 0.8rem;
    }
  }
  
  &.logo-large {
    .logo-svg {
      height: 60px;
    }
    .logo-image {
      height: 60px;
    }
    .logo-tagline {
      font-size: 0.9rem;
    }
  }
  
  &.logo-xl {
    .logo-svg {
      height: 80px;
    }
    .logo-image {
      height: 80px;
    }
    .logo-tagline {
      font-size: 1rem;
    }
  }
  
  // Variantes de couleur
  &.logo-default {
    .logo-text-primary {
      fill: #003366;
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 24px;
    }
    
    .logo-text-secondary {
      fill: #0066CC;
      font-family: 'Montserrat', sans-serif;
      font-weight: 500;
      font-size: 14px;
    }
    
    .logo-tagline {
      color: #666;
    }
  }
  
  &.logo-white {
    .logo-icon path,
    .logo-icon rect,
    .logo-icon line {
      stroke: white !important;
      fill: white !important;
    }
    
    .logo-text-primary,
    .logo-text-secondary {
      fill: white;
    }
    
    .logo-tagline {
      color: white;
    }
  }
  
  &.logo-dark {
    .logo-icon path,
    .logo-icon rect,
    .logo-icon line {
      stroke: #1a1a1a !important;
      fill: #1a1a1a !important;
    }
    
    .logo-text-primary,
    .logo-text-secondary {
      fill: #1a1a1a;
    }
    
    .logo-tagline {
      color: #1a1a1a;
    }
  }
  
  &.logo-colored {
    // Garde les couleurs originales définies dans le SVG
  }
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo-svg {
  width: auto;
  display: block;
}

.logo-image {
  width: auto;
  display: block;
  object-fit: contain;
}

.logo-tagline {
  margin-top: 0.5rem;
  font-family: 'Open Sans', sans-serif;
  font-weight: 400;
  text-align: center;
  opacity: 0.8;
}

// Animation au hover
.sygep-logo {
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
  }
}

// Mode sombre
@media (prefers-color-scheme: dark) {
  .logo-default {
    filter: brightness(0.9);
  }
}
</style>