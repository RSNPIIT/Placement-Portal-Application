<template>
  <div class="login-page">
    <div class="card">
      <h1>Login Page</h1>

      <form @submit.prevent="loginUser">
        <input
          type="email"
          placeholder="Email"
          v-model="email"
          required
        />

        <input
          type="password"
          placeholder="Password"
          v-model="password"
          required
        />

        <button type="submit" class="login-btn">
          Login
        </button>
      </form>

      <p class="signup-text">
        No account?
        <router-link to="/register">Sign Up</router-link>
      </p>

      <router-link to="/">
        <button class="back-btn">
          Go Back
        </button>
      </router-link>

      <p v-if="message" class="error">
        {{ message }}
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios"

export default {
  data() {
    return {
      email: "",
      password: "",
      message: ""
    }
  },
  methods: {
    async loginUser() {
      try {
        const res = await axios.post("http://127.0.0.1:5000/login", {
          email: this.email,
          password: this.password
        })

        localStorage.setItem("access_token", res.data.access_token)
        localStorage.setItem("role", res.data.role)
        localStorage.setItem("name", res.data.name)
        localStorage.setItem("user_id", res.data.user_id)
        localStorage.setItem("user_id", res.data.user_id);  

        axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;

        if (res.data.role === "admin") {
          this.$router.push("/admin-dashboard")
        } else if (res.data.role === "student") {
          this.$router.push("/student-dashboard")
        } else {
          this.$router.push("/company-dashboard")
        }

      } catch (err) {
        this.message = err.response?.data?.msg || "Login Failed"
      }
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(to right, #1976d2, #26c6da);
  display: flex;
  justify-content: center;
  align-items: center;
}

.card {
  background: #e0e0e0;
  padding: 40px;
  width: 420px;
  text-align: center;
  border-radius: 10px;
}

h1 {
  margin-bottom: 25px;
}

input {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
}

button {
  width: 100%;
  padding: 10px;
  margin-top: 10px;
  cursor: pointer;
  border: none;
}

.login-btn {
  background-color: #1976d2;
  color: white;
}

.back-btn {
  background-color: #555;
  color: white;
}

.signup-text {
  margin-top: 15px;
  font-size: 14px;
}

.signup-text a {
  color: #1976d2;
  text-decoration: none;
  font-weight: bold;
}

.error {
  margin-top: 15px;
  color: red;
}
</style>