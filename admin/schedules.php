<?php
/**
 * AnandBus Admin — Schedule Management Page with Run Chart & RBAC
 */
require_once __DIR__ . '/check_access.php';

// Enforce access for Super Admin, Manager, and Conductor
require_access(['super_admin', 'manager', 'conductor']);

$user_role = $_SESSION['role'] ?? 'manager';
$user_data = get_current_user_data();

// Sample Schedule Data (In real app, fetched via PDO/MySQL query)
$schedules_data = [
    [
        'id' => 101,
        'bus_number' => 'GJ-23-AB-1001',
        'bus_type' => 'Electric AC Express',
        'route_code' => 'R-101',
        'start_location' => 'Anand Bus Stand',
        'end_location' => 'Vallabh Vidyanagar',
        'departure_time' => '08:00 AM',
        'arrival_time' => '08:25 AM',
        'duration_mins' => 25,
        'conductor_name' => 'Vikram Singh',
        'status' => 'On Time'
    ],
    [
        'id' => 102,
        'bus_number' => 'GJ-23-AB-1002',
        'bus_type' => 'Non-AC Deluxe',
        'route_code' => 'R-102',
        'start_location' => 'Anand Railway Station',
        'end_location' => 'Karamsad Town',
        'departure_time' => '09:15 AM',
        'arrival_time' => '09:45 AM',
        'duration_mins' => 30,
        'conductor_name' => 'Amit Sharma',
        'status' => 'Delayed'
    ],
    [
        'id' => 103,
        'bus_number' => 'GJ-23-AB-1003',
        'bus_type' => 'City Mini Bus',
        'route_code' => 'R-103',
        'start_location' => 'GIDC Phase 1',
        'end_location' => 'Boriavi Square',
        'departure_time' => '10:30 AM',
        'arrival_time' => '11:15 AM',
        'duration_mins' => 45,
        'conductor_name' => 'Vikram Singh',
        'status' => 'On Time'
    ],
    [
        'id' => 104,
        'bus_number' => 'GJ-23-AB-1004',
        'bus_type' => 'Express AC',
        'route_code' => 'R-101',
        'start_location' => 'Anand Bus Stand',
        'end_location' => 'Vallabh Vidyanagar',
        'departure_time' => '12:00 PM',
        'arrival_time' => '12:25 PM',
        'duration_mins' => 25,
        'conductor_name' => 'Suresh Kumar',
        'status' => 'Completed'
    ],
    [
        'id' => 105,
        'bus_number' => 'GJ-23-AB-1005',
        'bus_type' => 'Non-AC Deluxe',
        'route_code' => 'R-105',
        'start_location' => 'Vadtal Temple Gateway',
        'end_location' => 'Anand Bus Stand',
        'departure_time' => '02:00 PM',
        'arrival_time' => '02:50 PM',
        'duration_mins' => 50,
        'conductor_name' => 'Mahesh Chavda',
        'status' => 'Cancelled'
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schedules Management — AnandBus Admin</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <!-- Chart.js for Run Chart -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #F5F8FA; font-family: 'Inter', -apple-system, sans-serif; color: #1E293B; }
        .main-content { min-height: 100vh; }
        .card-custom { border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .badge-ontime { background-color: #DEF7EC; color: #03543F; font-weight: 600; }
        .badge-delayed { background-color: #FEF08A; color: #713F12; font-weight: 600; }
        .badge-completed { background-color: #E0E7FF; color: #3730A3; font-weight: 600; }
        .badge-cancelled { background-color: #FDE8E8; color: #9B1C1C; font-weight: 600; }
        .table th { background-color: #F8FAFC; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; color: #64748B; font-weight: 700; }
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
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-calendar-alt me-2 text-primary"></i>Daily Schedule Management</h4>
                <small class="text-muted">Manage bus routes, timings, driver assignments, and trip status.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <!-- VIEW WEBSITE SHORTCUT BUTTON -->
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>

                <?php if (has_role(['super_admin', 'manager'])): ?>
                <button class="btn btn-primary rounded-pill px-4 fw-semibold" data-bs-toggle="modal" data-bs-target="#addScheduleModal">
                    <i class="fas fa-plus me-2"></i>Add New Schedule
                </button>
                <?php endif; ?>
            </div>
        </div>

        <!-- 📈 RUN CHART SECTION (Replacing round pie chart with Run Chart as requested) -->
        <div class="row g-4 mb-4">
            <div class="col-lg-8">
                <div class="card card-custom p-4 bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <h6 class="fw-bold mb-0 text-dark"><i class="fas fa-chart-line me-2 text-primary"></i>Punctuality & Trip Run Chart</h6>
                            <small class="text-muted">Daily trend analysis of scheduled vs delayed vs completed bus trips</small>
                        </div>
                        <span class="badge bg-light text-dark border">Run Chart</span>
                    </div>
                    <div style="height: 240px;">
                        <canvas id="scheduleRunChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Quick Metrics Cards -->
            <div class="col-lg-4">
                <div class="row g-3">
                    <div class="col-6">
                        <div class="card card-custom p-3 bg-white text-center">
                            <i class="fas fa-bus fa-2x text-primary mb-2"></i>
                            <h3 class="fw-black mb-0">24</h3>
                            <small class="text-muted">Active Trips Today</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="card card-custom p-3 bg-white text-center">
                            <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                            <h3 class="fw-black mb-0">92%</h3>
                            <small class="text-muted">On-Time Rate</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="card card-custom p-3 bg-white text-center">
                            <i class="fas fa-clock fa-2x text-warning mb-2"></i>
                            <h3 class="fw-black mb-0">2</h3>
                            <small class="text-muted">Delayed Trips</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="card card-custom p-3 bg-white text-center">
                            <i class="fas fa-user-check fa-2x text-info mb-2"></i>
                            <h3 class="fw-black mb-0">18</h3>
                            <small class="text-muted">Drivers On Duty</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search & Filter Controls -->
        <div class="card card-custom p-4 bg-white mb-4">
            <div class="row g-3 align-items-center">
                <div class="col-md-5">
                    <div class="input-group">
                        <span class="input-group-text bg-light border-end-0"><i class="fas fa-search text-muted"></i></span>
                        <input type="text" id="scheduleSearch" class="form-control bg-light border-start-0" placeholder="Search by Bus Number, Route Code, or Location...">
                    </div>
                </div>
                <div class="col-md-4">
                    <select id="statusFilter" class="form-select bg-light">
                        <option value="">All Statuses</option>
                        <option value="On Time">On Time</option>
                        <option value="Delayed">Delayed</option>
                        <option value="Completed">Completed</option>
                        <option value="Cancelled">Cancelled</option>
                    </select>
                </div>
                <div class="col-md-3 text-md-end">
                    <button class="btn btn-outline-secondary w-100" onclick="resetFilters()">
                        <i class="fas fa-redo me-1"></i>Reset Filters
                    </button>
                </div>
            </div>
        </div>

        <!-- Schedules Data Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover" id="schedulesTable">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Bus Number</th>
                            <th>Route Details</th>
                            <th>Departure</th>
                            <th>Arrival</th>
                            <th>Duration</th>
                            <th>Assigned Driver/Staff</th>
                            <th>Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($schedules_data as $sch): ?>
                        <tr data-status="<?php echo htmlspecialchars($sch['status']); ?>">
                            <td class="fw-bold">#<?php echo $sch['id']; ?></td>
                            <td>
                                <div class="fw-bold text-dark"><?php echo htmlspecialchars($sch['bus_number']); ?></div>
                                <small class="text-muted"><?php echo htmlspecialchars($sch['bus_type']); ?></small>
                            </td>
                            <td>
                                <span class="badge bg-light text-dark me-1"><?php echo htmlspecialchars($sch['route_code']); ?></span>
                                <span class="fw-semibold text-dark"><?php echo htmlspecialchars($sch['start_location']); ?></span>
                                <i class="fas fa-arrow-right text-muted mx-1"></i>
                                <span class="fw-semibold text-dark"><?php echo htmlspecialchars($sch['end_location']); ?></span>
                            </td>
                            <td class="fw-bold text-primary"><?php echo $sch['departure_time']; ?></td>
                            <td class="fw-bold text-secondary"><?php echo $sch['arrival_time']; ?></td>
                            <td><i class="far fa-clock me-1 text-muted"></i><?php echo $sch['duration_mins']; ?> mins</td>
                            <td><i class="fas fa-user-circle me-1 text-muted"></i><?php echo htmlspecialchars($sch['conductor_name']); ?></td>
                            <td>
                                <?php
                                $badge_class = 'badge-ontime';
                                if ($sch['status'] === 'Delayed') $badge_class = 'badge-delayed';
                                if ($sch['status'] === 'Completed') $badge_class = 'badge-completed';
                                if ($sch['status'] === 'Cancelled') $badge_class = 'badge-cancelled';
                                ?>
                                <span class="badge <?php echo $badge_class; ?> px-3 py-2 rounded-pill"><?php echo $sch['status']; ?></span>
                            </td>
                            <td class="text-end">
                                <div class="btn-group">
                                    <?php if (has_role(['super_admin', 'manager'])): ?>
                                        <button class="btn btn-sm btn-outline-primary" title="Edit Schedule" onclick="editSchedule(<?php echo $sch['id']; ?>)">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" title="Cancel Trip" onclick="cancelSchedule(<?php echo $sch['id']; ?>)">
                                            <i class="fas fa-ban"></i>
                                        </button>
                                    <?php endif; ?>
                                    <button class="btn btn-sm btn-outline-info" title="View Bookings" onclick="viewBookings(<?php echo $sch['id']; ?>)">
                                        <i class="fas fa-ticket-alt"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<!-- Modal: Edit Schedule -->
<div class="modal fade" id="editScheduleModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-edit me-2 text-primary"></i>Edit Schedule</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
                <form id="editScheduleForm">
                    <input type="hidden" id="edit_schedule_id">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Departure Time</label>
                        <input type="time" class="form-control" id="edit_departure" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Arrival Time</label>
                        <input type="time" class="form-control" id="edit_arrival" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Trip Status</label>
                        <select class="form-select" id="edit_status">
                            <option value="On Time">On Time</option>
                            <option value="Delayed">Delayed</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Save Changes</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Bootstrap 5 Bundle JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>

<!-- RUN CHART JS IMPLEMENTATION -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 📈 RUN CHART (Trend Analysis of Punctuality over Time)
    const ctx = document.getElementById('scheduleRunChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['06:00 AM', '08:00 AM', '10:00 AM', '12:00 PM', '02:00 PM', '04:00 PM', '06:00 PM', '08:00 PM'],
            datasets: [
                {
                    label: 'On Time Trips',
                    data: [4, 8, 12, 10, 14, 11, 15, 9],
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                },
                {
                    label: 'Delayed Trips',
                    data: [0, 1, 2, 1, 3, 1, 2, 0],
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
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

    // Real-time table filter
    const searchInput = document.getElementById('scheduleSearch');
    const statusSelect = document.getElementById('statusFilter');
    const rows = document.querySelectorAll('#schedulesTable tbody tr');

    function filterTable() {
        const query = searchInput.value.toLowerCase();
        const status = statusSelect.value;

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const rowStatus = row.getAttribute('data-status');

            const matchesSearch = text.includes(query);
            const matchesStatus = !status || rowStatus === status;

            if (matchesSearch && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchInput.addEventListener('input', filterTable);
    statusSelect.addEventListener('change', filterTable);
});

function resetFilters() {
    document.getElementById('scheduleSearch').value = '';
    document.getElementById('statusFilter').value = '';
    document.querySelectorAll('#schedulesTable tbody tr').forEach(r => r.style.display = '');
}

function editSchedule(id) {
    document.getElementById('edit_schedule_id').value = id;
    new bootstrap.Modal(document.getElementById('editScheduleModal')).show();
}

function cancelSchedule(id) {
    if (confirm('Are you sure you want to cancel Schedule #' + id + '?')) {
        alert('Schedule #' + id + ' has been marked as Cancelled.');
    }
}

function viewBookings(id) {
    alert('Navigating to Bookings for Schedule #' + id);
}
</script>

</body>
</html>
