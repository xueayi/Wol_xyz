<script setup lang="ts">
import { NConfigProvider, NMessageProvider, zhCN, dateZhCN } from 'naive-ui'

const themeOverrides = {
  common: {
    borderRadius: '12px',
    borderRadiusSmall: '8px',
    primaryColor: '#007AFF',
    primaryColorHover: '#0A84FF',
    primaryColorPressed: '#0066D6',
    successColor: '#34C759',
    warningColor: '#FF9F0A',
    errorColor: '#FF3B30',
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif',
  },
  Button: {
    borderRadiusMedium: '10px',
    borderRadiusSmall: '8px',
    heightMedium: '36px',
  },
  Card: {
    borderRadius: '16px',
  },
  Input: {
    borderRadius: '10px',
    heightMedium: '40px',
  },
  Select: {
    borderRadius: '10px',
  },
  Tag: {
    borderRadius: '20px',
  },
  Modal: {
    borderRadius: '20px',
  },
}
</script>

<template>
  <NConfigProvider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <router-view />
    </NMessageProvider>
  </NConfigProvider>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f2f2f7;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1c1c1e;
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: transparent;
}

.n-modal-mask {
  backdrop-filter: blur(8px) saturate(120%);
  -webkit-backdrop-filter: blur(8px) saturate(120%);
}
</style>
