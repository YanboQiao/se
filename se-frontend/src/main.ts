import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

import './style.css';   // 若使用 Tailwind，这里确保已引入

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
