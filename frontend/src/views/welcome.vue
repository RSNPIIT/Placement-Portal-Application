<template>
  <div class="welcome-page">
    <div class="card">
      <h1>Welcome to Placement Portal</h1>

      <p class="subtitle">
        Your gateway to opportunities
      </p>

      <router-link to="/login">
        <button class="login-btn">
          Login
        </button>
      </router-link>

      <router-link to="/register">
        <button class="register-btn">
          Register
        </button>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.welcome-page {
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
  margin-bottom: 15px;
}

.subtitle {
  margin-bottom: 25px;
  color: #555;
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

.register-btn {
  background-color: #2e7d32;
  color: white;
}
</style>