<template>
  <div class="register-page">
    <div class="card">
      <h1>Register Page</h1>

      <form @submit.prevent="registerUser">
        <input
          type="text"
          placeholder="Full Name"
          v-model="name"
          required
        />

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

        <select v-model="role" required>
          <option disabled value="">Select Role</option>
          <option value="student">Student</option>
          <option value="company">Company</option>
        </select>

        <button type="submit" class="register-btn">
          Register
        </button>
      </form>

      <p class="login-text">
        Already have an account?
        <router-link to="/login">Login</router-link>
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
import axios from "../axios";

export default {
  data() {
    return {
      name: "",
      email: "",
      password: "",
      role: "",
      message: ""
    }
  },
  methods: {
    async registerUser() {
      try {
        await axios.post("http://127.0.0.1:5000/req", {
          name: this.name,
          email: this.email,
          password: this.password,
          role: this.role
        })

        this.$router.push("/login")

      } catch (err) {
        this.message = err.response?.data?.msg || "Registration Failed"
      }
    }
  }
}
</script>

<style scoped>
.register-page {
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

input,
select {
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

.register-btn {
  background-color: #2e7d32;
  color: white;
}

.back-btn {
  background-color: #555;
  color: white;
}

.login-text {
  margin-top: 15px;
  font-size: 14px;
}

.login-text a {
  color: #1976d2;
  text-decoration: none;
  font-weight: bold;
}

.error {
  margin-top: 15px;
  color: red;
}
</style>