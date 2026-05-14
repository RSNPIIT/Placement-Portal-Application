<template>
  <div class="dashboard">
    <nav class="navbar">
      <h1>Admin Control Panel</h1>
      <div class="nav-right">
        <span>Logged in as: Admin</span>
        <button class="logout-btn" @click="logout">Logout</button>
      </div>
    </nav>
    
    <div class="container">
      <div class="search-wrapper">
        <input 
          v-model="searchQuery" 
          :placeholder="'Search ' + currentView + '...'" 
          class="search-input"
        />
      </div>

      <div class="stats-grid">
        <div class="stat-card" :class="{ 'active-card': currentView === 'students' }">
          <h3>Students</h3>
          <p class="number">{{ stats.total_students }}</p>
          <button @click="currentView = 'students'" class="view-btn">View Students</button>
        </div>

        <div class="stat-card" :class="{ 'active-card': currentView === 'companies' }">
          <h3>Companies</h3>
          <p class="number">{{ stats.total_companies }}</p>
          <button @click="currentView = 'companies'" class="view-btn">View Companies</button>
        </div>

        <div class="stat-card" :class="{ 'active-card': currentView === 'jobs' }">
          <h3>Jobs</h3>
          <p class="number">{{ stats.total_jobs }}</p>
          <button @click="currentView = 'jobs'; loadJobs()" class="view-btn">View Jobs</button>
        </div>

        <div class="stat-card" :class="{ 'active-card': currentView === 'applications' }">
          <h3>Applications</h3>
          <p class="number">{{ stats.total_applications }}</p>
          <button @click="currentView = 'applications'; showApplications()" class="view-btn">View Applications</button>
        </div>
      </div>

      <div v-if="currentView === 'students' || currentView === 'companies'" class="table-container">
        <h2>List of {{ currentView === 'students' ? 'Students' : 'Companies' }}</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.ids">
              <td>{{ user.ids }}</td>
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span :class="user.is_approved ? 'text-success' : 'text-danger'">
                  {{ user.is_approved ? 'Approved' : 'Pending/Blacklisted' }}
                </span>
              </td>
              <td>
                <button 
                  v-if="!user.is_approved" 
                  @click="toggleApproval(user.ids)" 
                  class="approve-btn">
                  Approve
                </button>
                <button 
                  v-else 
                  @click="toggleApproval(user.ids)" 
                  class="blacklist-btn">
                  Blacklist
                </button>
              </td>
            </tr>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="5" class="no-data">No results found for "{{ searchQuery }}"</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="currentView === 'jobs'" class="table-container">
        <h2>All Job Listings</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Company</th>
              <th>Location</th>
              <th>Salary</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs.filter(j => j.title.toLowerCase().includes(searchQuery.toLowerCase()) || j.company_name.toLowerCase().includes(searchQuery.toLowerCase()))" :key="job.id">
              <td>{{ job.id }}</td>
              <td>{{ job.title }}</td>
              <td>{{ job.company_name }}</td>
              <td>{{ job.location }}</td>
              <td>{{ job.salary }}</td>
              <td>
                <span :class="job.status === 'active' ? 'text-success' : 'text-danger'">
                  {{ job.status }}
                </span>
              </td>
              <td>
                <button class="blacklist-btn" @click="deleteJob(job.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="currentView === 'applications'" class="table-container">
        <h2>All Applications</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Student</th>
              <th>Email</th>
              <th>Job</th>
              <th>Company</th>
              <th>Status</th>
              <th>Interview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in applications.filter(a => a.student_name.toLowerCase().includes(searchQuery.toLowerCase()) || a.job_title.toLowerCase().includes(searchQuery.toLowerCase()))" :key="app.application_id">
              <td>{{ app.application_id }}</td>
              <td>{{ app.student_name }}</td>
              <td>{{ app.student_email }}</td>
              <td>{{ app.job_title }}</td>
              <td>{{ app.company_name }}</td>
              <td>
                <span :class="{
                  'text-success': app.status === 'selected',
                  'text-danger': app.status === 'rejected',
                  'text-warning': app.status === 'shortlisted'
                }">{{ app.status }}</span>
              </td>
              <td>
                <div v-if="app.interview_date">
                  {{ app.interview_date }}<br>
                  <a :href="app.interview_link" target="_blank" class="join-link">Join</a>
                </div>
                <span v-else>—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "../axios";

export default {
  data() {
    return {
      students: [],
      companies: [],
      currentView: 'companies',
      stats: {
      total_students: 0,
      total_companies: 0,
      total_jobs: 0,
      total_applications: 0
      },
      applications: [],
      jobs: [],
      searchQuery: ""
    }
  },
  computed: {
    filteredUsers() {
      const list = this.currentView === 'students' ? this.students : this.companies;

      return list.filter(u =>
        u.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        u.email.toLowerCase().includes(this.searchQuery.toLowerCase())
      );
    }
  },
  methods: {
    async loadData() {
      try {
        const token = localStorage.getItem('access_token');
        const res = await axios.get('http://127.0.0.1:5000/admin/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.students = res.data.students || [];
        this.companies = res.data.companies || [];

        this.stats.total_students = res.data.total_students;
        this.stats.total_companies = res.data.total_companies;
        this.stats.total_jobs = res.data.total_jobs;
        this.stats.total_applications = res.data.total_applications;
      } catch (err) {
        console.error("Failed to load DB data:", err);
      }
    },
    showJobs() { 
      this.currentView = 'jobs'; 
      this.loadJobs(); 
    },
    async loadJobs() {
      try {
        const token = localStorage.getItem('access_token');
        const res = await axios.get(
          'http://127.0.0.1:5000/admin/jobs',
          { headers: { Authorization: `Bearer ${token}` } }
        );
        this.jobs = res.data;

      } catch (err) {
        console.error("Failed to load jobs:", err);
      }
    },
    async loadApplications() {
      try {
        const token = localStorage.getItem('access_token');

        const res = await axios.get(
          'http://127.0.0.1:5000/admin/applications',
          { headers: { Authorization: `Bearer ${token}` } }
        );

        this.applications = res.data;

      } catch (err) {
        console.error("Failed to load applications:", err);
      }
    },
    async deleteJob(jobId) {
      const token = localStorage.getItem('access_token');

      if (!confirm("Delete this job?")) return;

      try {
        const res = await axios.delete(
          `http://127.0.0.1:5000/admin/jobs/${jobId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        alert(res.data.msg || "Job deleted successfully");  

        await this.loadJobs();
        await this.loadData();

      } 
      catch (err) {
        alert(err.response?.data?.msg || "Delete failed");
      }
    },
    async toggleApproval(userId) {
      try {
        const token = localStorage.getItem('access_token');

        await axios.post(
          `http://127.0.0.1:5000/admin/toggle/${userId}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );

        this.loadData(); // refresh UI

      } catch (err) {
        alert(err.response?.data?.msg || "Action failed");
      }
    },
    logout() {
      localStorage.clear();
      this.$router.push("/login");
    },
    showApplications() {
      this.currentView = 'applications';
      this.loadApplications();
    }
  },
  mounted() {
    this.loadData(); 
  }
}
</script>

<style scoped>

.dashboard {
  background: #f4f7f6;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
}

.navbar {
  background: #007bff;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.container {
  padding: 2rem;
  max-width: 1200px;
  margin: auto;
}

.search-wrapper {
  margin-bottom: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 12px 20px;
  border-radius: 25px;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  outline: none;
  transition: 0.3s;
  text-align: center;
}

.search-input:focus {
  border-color: #007bff;
  box-shadow: 0 2px 15px rgba(0, 123, 255, 0.2);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.active-card {
  border-color: #007bff;
  background: #f0f7ff;
  transform: scale(1.02);
}

.number {
  font-size: 2.8rem;
  font-weight: bold;
  color: #007bff;
  margin: 10px 0;
}

h3 {
  color: #555;
  margin: 0;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.table-container {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th {
  text-align: left;
  padding: 15px;
  background: #f8f9fa;
  color: #666;
  font-weight: 600;
  border-bottom: 2px solid #eee;
}

td {
  padding: 15px;
  border-bottom: 1px solid #eee;
  color: #333;
  font-size: 0.95rem;
}

.no-data {
  text-align: center;
  padding: 30px;
  color: #999;
  font-style: italic;
}

.view-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 10px;
  transition: 0.3s;
}

.view-btn:hover {
  background: #495057;
}

.approve-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.blacklist-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.logout-btn {
  background: #ff4d4d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.text-success {
  color: #28a745;
  font-weight: bold;
}

.text-danger {
  color: #dc3545;
  font-weight: bold;
}

.text-warning {
  color: #f39c12;
  font-weight: bold;
}

.join-link {
  color: #007bff;
  font-weight: bold;
  text-decoration: none;
}
</style>