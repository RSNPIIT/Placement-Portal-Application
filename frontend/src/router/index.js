import { createRouter, createWebHistory } from "vue-router"

import Welcome from "../views/welcome.vue"
import Login from "../views/login.vue"
import Register from "../views/register.vue"
import AdminDashboard from "../views/AdminDashboard.vue"
import StudentDashboard from "../views/StudentDashboard.vue"
import CompanyDashboard from "../views/CompanyDashboard.vue"

const routes = [
  { path: "/", component: Welcome },

  { path: "/login", component: Login },
  { path: "/register", component: Register },

  {
    path: "/admin-dashboard",
    component: AdminDashboard,
    meta: { requiresAuth: true, role: "admin" }
  },
  {
    path: "/student-dashboard",
    component: StudentDashboard,
    meta: { requiresAuth: true, role: "student" }
  },
  {
    path: "/company-dashboard",
    component: CompanyDashboard,
    meta: { requiresAuth: true, role: "company" }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

//Added a Route Guard to prevent unauthorized access
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token")
  const role = localStorage.getItem("role")

  if (to.meta.requiresAuth) {

    // Not logged in
    if (!token) {
      return next("/login")
    }

    // Logged in but wrong role
    if (to.meta.role !== role) {
      return next("/")   // or redirect to their own dashboard
    }
  }

  next()
})

export default router