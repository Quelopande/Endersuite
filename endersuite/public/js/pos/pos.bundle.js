import { createApp } from 'vue';
import POS from './POS.vue';

function setup_vue(wrapper) {
    const app = createApp(POS);
    app.mount(wrapper.get(0));
    return app;
}

frappe.ui.setup_vue = setup_vue;
export default setup_vue;
