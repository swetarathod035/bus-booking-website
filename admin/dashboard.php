<?php
/**
 * AnandBus Admin — Dashboard Overview Page with Run Chart & RBAC
 */
require_once __DIR__ . '/check_access.php';

require_access(['super_admin', 'manager', 'conductor']);

$user_role = $_SESSION['role'] ?? 'super_admin';
$user_data = get_current_user_data();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard — AnandBus</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <!-- Chart.js for Run Chart -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #F5F8FA; font-family: 'Inter', -apple-system, sans-serif; color: #1E293B; }
        .card-custom { border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
    </style>
</head>
<body>

<div class="d-flex">
    <!-- Dynamic Sidebar Component -->
    <?php include __DIR__ . '/sidebar.php'; ?>

    <!-- Main Content Area -->
    <div class="main-content flex-grow-1 p-4">
        
        <!-- Top Header Bar -->
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm">
            <div>
                <h4 class="fw-bold mb-0 text-dark">Welcome back, <?php echo htmlspecialchars($user_data['name']); ?> 👋</h4>
                <small class="text-muted">Role: <span class="badge bg-primary"><?php echo $user_data['role_title']; ?></span></small>
            </div>
            
            <div class="d-flex align-items-center gap-3">
                <!-- 🌐 VIEW WEBSITE OPTION IN ADMIN PANEL -->
                <a href="/" target="_blank" class="btn btn-warning text-dark fw-bold rounded-pill px-4 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe fs-5"></i>
                    <span>View Website</span>
                    <i class="fas fa-external-link-alt fs-8"></i>
                </a>
            </div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="row g-4 mb-4">
            <div class="col-xl-3 col-md-6">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Daily Bookings</small>
                            <h2 class="fw-black mb-0 mt-1">1,248</h2>
                            <small class="text-success fw-semibold"><i class="fas fa-arrow-up me-1"></i>+14% today</small>
                        </div>
                        <div class="stat-icon bg-primary text-white"><i class="fas fa-ticket-alt"></i></div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-md-6">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Active Buses</small>
                            <h2 class="fw-black mb-0 mt-1">42 / 48</h2>
                            <small class="text-muted fw-semibold">6 under maintenance</small>
                        </div>
                        <div class="stat-icon bg-info text-white"><i class="fas fa-bus"></i></div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-md-6">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Active Student Passes</small>
                            <h2 class="fw-black mb-0 mt-1">3,850</h2>
                            <small class="text-warning fw-semibold"><i class="fas fa-clock me-1"></i>12 Pending approval</small>
                        </div>
                        <div class="stat-icon bg-warning text-white"><i class="fas fa-id-card"></i></div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-md-6">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Today's Revenue</small>
                            <h2 class="fw-black mb-0 mt-1">₹48,920</h2>
                            <small class="text-success fw-semibold"><i class="fas fa-arrow-up me-1"></i>+8.2% vs avg</small>
                        </div>
                        <div class="stat-icon bg-success text-white"><i class="fas fa-rupee-sign"></i></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 📈 RUN CHART SECTION (Replacing round pie graph with Run Chart line trend) -->
        <div class="row g-4 mb-4">
            <div class="col-lg-8">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <h6 class="fw-bold mb-0 text-dark"><i class="fas fa-chart-line me-2 text-primary"></i>Hourly Passenger Density Run Chart</h6>
                            <small class="text-muted">Passenger volume and bus load factor over time</small>
                        </div>
                        <span class="badge bg-primary-subtle text-primary fw-bold px-3 py-2">Run Chart Analysis</span>
                    </div>
                    <div style="height: 280px;">
                        <canvas id="passengerRunChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Quick Access Modules Grid -->
            <div class="col-lg-4">
                <div class="card card-custom p-4 bg-white h-100">
                    <h6 class="fw-bold mb-3 text-dark"><i class="fas fa-rocket me-2 text-warning"></i>Quick Management Modules</h6>
                    <div class="d-grid gap-2">
                        <a href="schedules.php" class="btn btn-outline-primary text-start d-flex justify-content-between align-items-center p-3 rounded-3">
                            <div>
                                <div class="fw-bold">Manage Schedules</div>
                                <small class="text-muted">Daily departures & conductor assignments</small>
                            </div>
                            <i class="fas fa-chevron-right"></i>
                        </a>
                        <a href="student_passes.php" class="btn btn-outline-warning text-dark text-start d-flex justify-content-between align-items-center p-3 rounded-3">
                            <div>
                                <div class="fw-bold">Student Pass Verification</div>
                                <small class="text-muted">Approve pending applications & QR hash</small>
                            </div>
                            <i class="fas fa-chevron-right"></i>
                        </a>
                        <a href="buses.php" class="btn btn-outline-info text-start d-flex justify-content-between align-items-center p-3 rounded-3">
                            <div>
                                <div class="fw-bold">Bus Fleet Status</div>
                                <small class="text-muted">Capacity & maintenance tracking</small>
                            </div>
                            <i class="fas fa-chevron-right"></i>
                        </a>
                        <a href="/" target="_blank" class="btn btn-warning fw-bold text-dark text-start d-flex justify-content-between align-items-center p-3 rounded-3 shadow-sm">
                            <div>
                                <div class="fw-bold"><i class="fas fa-globe me-2"></i>Open Public Website</div>
                                <small class="text-dark opacity-75">View live passenger booking portal</small>
                            </div>
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>

<!-- Bootstrap 5 Bundle JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>

<!-- RUN CHART JS IMPLEMENTATION -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('passengerRunChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['06 AM', '08 AM', '10 AM', '12 PM', '02 PM', '04 PM', '06 PM', '08 PM', '10 PM'],
            datasets: [
                {
                    label: 'Passenger Count (Peak Trend)',
                    data: [120, 480, 320, 210, 260, 510, 640, 380, 150],
                    borderColor: '#1E3A5F',
                    backgroundColor: 'rgba(30, 58, 95, 0.12)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointBackgroundColor: '#FF6B35',
                    pointRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            }
        }
    });
});
</script>
</body>
</html>
