<template>
  <div class="dashboard">
    <div class="top-bar">
      <div class="branding">
        <h1>Welcome, {{ name }}</h1>
        <p class="subtitle">Student Placement Portal</p>
      </div>
      
      <div class="header-actions">
        <button class="btn-report" @click="exportReport">📤 Export Report</button>
        <button class="btn-report" @click="downloadReport">📥 Download Report</button>

        <template v-if="view === 'applications'">
          <button class="btn-outline" @click="exportData">📤 Export CSV</button>
          <button v-if="exportReady" class="btn-success" @click="downloadCSV">💾 Download</button>
        </template>
        
        <button class="btn-primary" @click="view = 'profile'">Edit Profile</button>
        <button class="btn-danger" @click="logout">Logout</button>
      </div>
    </div>

    <div class="navigation-menu">
      <button :class="{ active: view === 'jobs' }" @click="view = 'jobs'">Browse Jobs</button>
      <button :class="{ active: view === 'applications' }" @click="view = 'applications'">My Applications</button>
      <button :class="{ active: view === 'profile' }" @click="view = 'profile'">My Profile</button>
    </div>

    <div v-if="view === 'jobs'" class="view-container">
      <div class="search-section">
        <input v-model="searchQuery" placeholder="🔍 Search by title, skills, or company..." class="main-search" />
      </div>

      <div class="section-header">
        <h2>Available Opportunities</h2>
      </div>
      
      <div v-for="job in filteredJobs" :key="job.id" class="job-card">
        <div class="job-info">
          <h3>{{ job.title }}</h3>
          <p class="description">{{ job.description }}</p>
          <p class="skills-tag"><b>Required:</b> {{ job.skills }}</p>
        </div>
        <button 
          @click="apply(job.id)" 
          :class="['apply-btn', { applied: job.applied }]"
          :disabled="job.applied"
        >
          {{ job.applied ? "Applied" : "Apply Now" }}
        </button>
      </div>
    </div>

    <div v-if="view === 'applications'" class="view-container">
      <div class="section-header">
        <h2>My Applications</h2>
      </div>

      <div v-for="app in applications" :key="app.id" class="app-card">
        <div class="app-header">
          <h3>{{ app.job_title }}</h3>
          <span :class="['status-badge', app.status]">{{ app.status.toUpperCase() }}</span>
        </div>

        <div class="app-body">
          <p v-if="app.interview_date">📅 Interview: {{ app.interview_date }}</p>
          <p v-if="app.feedback">💬 Feedback: {{ app.feedback }}</p>
          <a v-if="app.offer_letter && app.status === 'selected'" :href="app.offer_letter" target="_blank" class="offer-link">
            📄 Download Offer Letter
          </a>
        </div>
      </div>
    </div>

    <div v-if="view === 'profile'" class="view-container">
      <div class="profile-card">
        <div class="form-section">
          <h2 class="form-heading">Personal Information</h2>
          <div class="form-grid">
            <div class="field">
              <label>Full Name</label>
              <input v-model="profile.name" placeholder="Full Name" />
            </div>
            <div class="field">
              <label>Email Address</label>
              <input v-model="profile.email" placeholder="Email" />
            </div>
            <div class="field">
              <label>Department</label>
              <input v-model="profile.department" placeholder="e.g. Computer Science" />
            </div>
            <div class="field">
              <label>Current CGPA</label>
              <input v-model="profile.cgpa" placeholder="0.00" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h2 class="form-heading">Academic & Professional</h2>
          <div class="vertical-fields">
            <div class="field">
              <label>Education</label>
              <input v-model="profile.education" placeholder="Degree, University" />
            </div>
            <div class="field">
              <label>Technical Skills</label>
              <input v-model="profile.skills" placeholder="Java, Python, Vue, etc." />
            </div>
            <div class="field">
              <label>Work/Project Experience</label>
              <textarea v-model="profile.experience" placeholder="Describe your experience..."></textarea>
            </div>
            <div class="field">
              <label>Resume Link</label>
              <input v-model="profile.resume" placeholder="Public Link (Google Drive/GitHub)" />
            </div>
          </div>
        </div>

        <button class="btn-save" @click="updateProfile">Save Profile Changes</button>
      </div>
    </div>
  </div>
</template>

<script>
  import axios from "../axios";

  export default {
    data() {
      return {
        name: localStorage.getItem("name"),
        view: "jobs",
        searchQuery: "",
        reportReady: false,
        exportReady: false,
        jobs: [],
        reportFile: null,
        appliedJobs: new Set(),
        applications: [],
        profile: {
          name: "",
          email: "",
          password: "",
          education: "",
          skills: "",
          experience: "",
          department: "",
          cgpa: "",
          resume: ""
        }
      };
    },
    computed: {
      filteredJobs() {
        return this.jobs.filter(job =>
          job.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          job.skills?.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          job.company_name?.toLowerCase().includes(this.searchQuery.toLowerCase())
        );
      }
    },

    mounted() {
      this.fetchJobs();
      this.fetchApplications();
      this.fetchProfile();

      this.interval = setInterval(() => {
        if (this.view === "applications") {
          this.fetchApplications();
        }
      }, 5000);
    },

    beforeUnmount() {
      clearInterval(this.interval);
    },

    methods: {
     async fetchJobs() {
        const token = localStorage.getItem("access_token");

        const res = await axios.get("http://127.0.0.1:5000/student/jobs", {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.jobs = res.data;
      },

      async exportReport() {
        try 
        {
          await fetch("http://127.0.0.1:5000/admin/generate-report");

          this.reportReady = true;
          alert("Report generated successfully!");
        } 
        catch (err) 
        {
          alert("Failed to generate report");
        }
      },

      downloadReport() 
      {
          if (!this.reportReady)
           {
              alert("Generate report first");
              return;
            }
        window.open(
          "http://127.0.0.1:5000/admin/download-report/placement_report_latest.pdf"
        );
      },

      async apply(jobId) {
        const token = localStorage.getItem("access_token");
        if (!this.profile.cgpa) {
          alert("Please fill your CGPA before applying");
          this.view = "profile";
          return;
        }
        try {
          const res = await axios.post(
            `http://127.0.0.1:5000/student/apply/${jobId}`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
          );

            alert(res.data.msg || "Applied successfully");

            const job = this.jobs.find(j => j.id === jobId);
            if (job) job.applied = true;

          } catch (err) {
            alert(err.response?.data?.msg || "Apply failed");
          }

          await this.fetchApplications();
          await this.fetchJobs();
          
      },
      async exportData() {
        const token = localStorage.getItem("access_token");
        try {
          await axios.post(
            "http://127.0.0.1:5000/student/export",
            {},
            { headers: { Authorization: `Bearer ${token}` } }
          );

        this.exportReady = true;
        alert("Export started!");

        } 
        catch (err) {
          alert("Export failed");
        }
      },
      async downloadCSV() {
        if (!this.exportReady) {
          alert("Please click Export first");
          return;
        }

        const token = localStorage.getItem("access_token");
        const user_id = localStorage.getItem("user_id");

        try {
          alert("Downloading...");

          const response = await fetch(
            `http://127.0.0.1:5000/student/download/export_${user_id}.csv`,
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          );

          if (!response.ok) {
            throw new Error("Download failed");
          }

          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);

          const a = document.createElement("a");
          a.href = url;
          a.download = `export_${user_id}.csv`;
          a.click();

          window.URL.revokeObjectURL(url);
        } 
        catch (err) {
          console.error(err);
          alert("Download failed");
        }
      },
      async fetchApplications() {
        const token = localStorage.getItem("access_token");
        const res = await axios.get("http://127.0.0.1:5000/student/applications", {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.applications = res.data;
        this.appliedJobs = new Set(res.data.map(a => a.job_id));
      },

      async fetchProfile() {
        const token = localStorage.getItem("access_token");
        const res = await axios.get("http://127.0.0.1:5000/student/profile", {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.profile = res.data;
      },

      async updateProfile() {
        const token = localStorage.getItem("access_token");

        try {
          await axios.put(
            "http://127.0.0.1:5000/student/profile",
            this.profile,
            { headers: { Authorization: `Bearer ${token}` } }
          );

          await this.fetchProfile();
          localStorage.setItem("name", this.profile.name);
          this.name = this.profile.name;

          alert("Profile updated");

        } catch (err) {
          alert(err.response?.data?.msg || "Update failed");
        }
      },

      logout() {
        localStorage.clear();
        this.$router.push("/login");
      }
    },
    watch: {
      view(newVal) {
        if (newVal === "applications") this.fetchApplications();
        if (newVal === "jobs") this.fetchJobs();
        if (newVal === "profile") this.fetchProfile();
      }
    }
  };
</script>

<style scoped>

.btn-report {
  background: #4f46e5; 
  color: white;
}

.btn-report:hover {
  background: #4338ca;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap; 
  justify-content: flex-end;
}

.dashboard {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #2d3748;
  background-color: #f7fafc;
  min-height: 100vh;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.branding h1 { margin: 0; font-size: 1.8rem; color: #1a202c; }
.subtitle { margin: 4px 0 0; color: #718096; font-size: 0.9rem; }

.header-actions { display: flex; gap: 10px; }

button {
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary { background: #3182ce; color: white; }
.btn-primary:hover { background: #2b6cb0; }
.btn-outline { background: white; border: 1px solid #cbd5e0; color: #4a5568; }
.btn-success { background: #38a169; color: white; }
.btn-danger { background: #fff5f5; color: #e53e3e; border: 1px solid #feb2b2; }

.navigation-menu {
  display: flex;
  background: white;
  padding: 8px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.navigation-menu button {
  flex: 1;
  background: transparent;
  color: #718096;
}

.navigation-menu button.active {
  background: #3182ce;
  color: white;
}

.view-container { animation: fadeIn 0.3s ease-in; }
.main-search {
  width: 100%;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 1rem;
  margin-bottom: 25px;
  box-sizing: border-box;
}

.job-card, .app-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-card { flex-direction: column; align-items: flex-start; }

.status-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: bold;
}
.status-badge.applied { background: #ebf8ff; color: #2b6cb0; }
.status-badge.selected { background: #f0fff4; color: #2f855a; }
.status-badge.rejected { background: #fff5f5; color: #c53030; }

.profile-card {
  background: white;
  padding: 40px;
  border-radius: 15px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.form-section { margin-bottom: 35px; }
.form-heading {
  font-size: 1.2rem;
  margin-bottom: 20px;
  color: #2d3748;
  border-left: 4px solid #3182ce;
  padding-left: 15px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.vertical-fields {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field { display: flex; flex-direction: column; gap: 8px; }
.field label { font-size: 0.85rem; font-weight: 700; color: #4a5568; }

input, textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  font-size: 0.95rem;
  box-sizing: border-box; 
}
textarea { min-height: 100px; resize: vertical; }

.btn-save {
  width: 100%;
  padding: 15px;
  background: #2d3748;
  color: white;
  font-size: 1rem;
  margin-top: 10px;
}

.btn-save:hover { background: #1a202c; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
  .top-bar { flex-direction: column; align-items: flex-start; gap: 15px; }
  .job-card { flex-direction: column; align-items: flex-start; gap: 15px; }
}

</style>