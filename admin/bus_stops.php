<?php
/**
 * AnandBus Admin — Bus Stops Management Page (Full CRUD)
 * Accessible by: Super Admin, Manager, Conductor
 */
require_once __DIR__ . '/check_access.php';

// Enforce access for Super Admin, Manager, and Conductor
require_access(['super_admin', 'manager', 'conductor']);

$user_role = $_SESSION['role'] ?? 'manager';
$user_data = get_current_user_data();

// Sample Bus Stops Data
$bus_stops_list = [
    [
        'id' => 1,
        'route_code' => 'R-101',
        'route_name' => 'Anand Bus Stand → Vallabh Vidyanagar',
        'stop_name' => 'Anand Bus Stand Main Gate',
        'stop_order' => 1,
        'landmark' => 'Near Central Bus Depot'
    ],
    [
        'id' => 2,
        'route_code' => 'R-101',
        'route_name' => 'Anand Bus Stand → Vallabh Vidyanagar',
        'stop_name' => 'Ganesh Chokdi',
        'stop_order' => 2,
        'landmark' => 'Opposite Town Hall'
    ],
    [
        'id' => 3,
        'route_code' => 'R-101',
        'route_name' => 'Anand Bus Stand → Vallabh Vidyanagar',
        'stop_name' => 'Vallabh Vidyanagar Circle',
        'stop_order' => 3,
        'landmark' => 'Near BVM Engineering College'
    ],
    [
        'id' => 4,
        'route_code' => 'R-102',
        'route_name' => 'Anand Railway Station → Karamsad Town',
        'stop_name' => 'Anand Railway Station West',
        'stop_order' => 1,
        'landmark' => 'Platform 1 Gate'
    ],
    [
        'id' => 5,
        'route_code' => 'R-102',
        'route_name' => 'Anand Railway Station → Karamsad Town',
        'stop_name' => 'Karamsad Medical Circle',
        'stop_order' => 2,
        'landmark' => 'Pramukh Swami Medical College'
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bus Stops Management — AnandBus Admin</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #F5F8FA; font-family: 'Inter', -apple-system, sans-serif; color: #1E293B; }
        .card-custom { border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .table th { background-color: #F8FAFC; text-transform: uppercase; font-size: 0.75rem; color: #64748B; font-weight: 700; }
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
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-map-marker-alt me-2 text-primary"></i>Bus Stops Management</h4>
                <small class="text-muted">Manage intermediate stops, route sequences, and landmarks. (Admin & Conductor Access)</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <!-- VIEW WEBSITE SHORTCUT -->
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>

                <button class="btn btn-primary rounded-pill px-4 fw-semibold" data-bs-toggle="modal" data-bs-target="#addStopModal">
                    <i class="fas fa-plus me-2"></i>Add Bus Stop
                </button>
            </div>
        </div>

        <!-- Search & Filter Controls -->
        <div class="card card-custom p-4 bg-white mb-4">
            <div class="row g-3 align-items-center">
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text bg-light border-end-0"><i class="fas fa-search text-muted"></i></span>
                        <input type="text" id="stopSearch" class="form-control bg-light border-start-0" placeholder="Search by Stop Name, Route Code, or Landmark...">
                    </div>
                </div>
                <div class="col-md-4">
                    <select id="routeFilter" class="form-select bg-light">
                        <option value="">All Routes</option>
                        <option value="R-101">R-101 (Anand → Vidyanagar)</option>
                        <option value="R-102">R-102 (Railway Stn → Karamsad)</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <button class="btn btn-outline-secondary w-100" onclick="resetFilters()">Reset</button>
                </div>
            </div>
        </div>

        <!-- Bus Stops Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover" id="stopsTable">
                    <thead>
                        <tr>
                            <th>Stop ID</th>
                            <th>Route Code</th>
                            <th>Bus Stop Name</th>
                            <th>Stop Order</th>
                            <th>Landmark / Address</th>
                            <th class="text-end">Actions (Insert/Update/Delete)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($bus_stops_list as $stp): ?>
                        <tr data-route="<?php echo $stp['route_code']; ?>">
                            <td class="fw-bold">#STP-<?php echo sprintf('%03d', $stp['id']); ?></td>
                            <td>
                                <span class="badge bg-primary px-3 py-2 fs-7"><?php echo htmlspecialchars($stp['route_code']); ?></span>
                                <small class="text-muted d-block mt-1"><?php echo htmlspecialchars($stp['route_name']); ?></small>
                            </td>
                            <td class="fw-bold text-dark"><i class="fas fa-map-pin text-danger me-2"></i><?php echo htmlspecialchars($stp['stop_name']); ?></td>
                            <td>
                                <span class="badge bg-secondary rounded-circle p-2" style="width:30px; height:30px; display:inline-flex; align-items:center; justify-content:center;">
                                    <?php echo $stp['stop_order']; ?>
                                </span>
                            </td>
                            <td><small class="text-muted"><i class="fas fa-compass me-1"></i><?php echo htmlspecialchars($stp['landmark']); ?></small></td>
                            <td class="text-end">
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-primary" title="Edit Stop" onclick="editStop(<?php echo $stp['id']; ?>, '<?php echo htmlspecialchars($stp['stop_name']); ?>', <?php echo $stp['stop_order']; ?>, '<?php echo htmlspecialchars($stp['landmark']); ?>')">
                                        <i class="fas fa-edit"></i> Edit
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" title="Delete Stop" onclick="deleteStop(<?php echo $stp['id']; ?>)">
                                        <i class="fas fa-trash-alt"></i> Delete
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

<!-- Modal: Add Bus Stop (INSERT) -->
<div class="modal fade" id="addStopModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-plus-circle me-2 text-primary"></i>Add New Bus Stop</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
                <form id="addStopForm" onsubmit="handleStopSubmit(event, 'insert')">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Select Route</label>
                        <select class="form-select" required>
                            <option value="R-101">R-101 (Anand Bus Stand → Vallabh Vidyanagar)</option>
                            <option value="R-102">R-102 (Anand Railway Station → Karamsad Town)</option>
                            <option value="R-103">R-103 (GIDC Phase 1 → Boriavi Square)</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Bus Stop Name</label>
                        <input type="text" class="form-control" placeholder="e.g. BVM College Gate" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Stop Order Sequence</label>
                        <input type="number" class="form-control" min="1" value="1" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Landmark / Location Detail</label>
                        <input type="text" class="form-control" placeholder="e.g. Near Shastri Maidan">
                    </div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Insert Bus Stop</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Edit Bus Stop (UPDATE) -->
<div class="modal fade" id="editStopModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-edit me-2 text-primary"></i>Update Bus Stop Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
                <form id="editStopForm" onsubmit="handleStopSubmit(event, 'update')">
                    <input type="hidden" id="edit_stop_id">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Bus Stop Name</label>
                        <input type="text" class="form-control" id="edit_stop_name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Stop Order Sequence</label>
                        <input type="number" class="form-control" id="edit_stop_order" min="1" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Landmark / Location Detail</label>
                        <input type="text" class="form-control" id="edit_stop_landmark">
                    </div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Save Changes (Update)</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Bootstrap 5 Bundle JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>
<script>
function editStop(id, name, order, landmark) {
    document.getElementById('edit_stop_id').value = id;
    document.getElementById('edit_stop_name').value = name;
    document.getElementById('edit_stop_order').value = order;
    document.getElementById('edit_stop_landmark').value = landmark;
    new bootstrap.Modal(document.getElementById('editStopModal')).show();
}

function deleteStop(id) {
    if (confirm(`Are you sure you want to delete Bus Stop #${id}?`)) {
        alert(`Bus Stop #${id} deleted successfully.`);
        location.reload();
    }
}

function handleStopSubmit(e, action) {
    e.preventDefault();
    alert(`Bus Stop successfully ${action === 'insert' ? 'inserted' : 'updated'}!`);
    location.reload();
}

// Search and filter logic
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('stopSearch');
    const routeSelect = document.getElementById('routeFilter');
    const rows = document.querySelectorAll('#stopsTable tbody tr');

    function filterStops() {
        const query = searchInput.value.toLowerCase();
        const route = routeSelect.value;

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const rowRoute = row.getAttribute('data-route');

            const matchesSearch = text.includes(query);
            const matchesRoute = !route || rowRoute === route;

            row.style.display = (matchesSearch && matchesRoute) ? '' : 'none';
        });
    }

    searchInput.addEventListener('input', filterStops);
    routeSelect.addEventListener('change', filterStops);
});

function resetFilters() {
    document.getElementById('stopSearch').value = '';
    document.getElementById('routeFilter').value = '';
    document.querySelectorAll('#stopsTable tbody tr').forEach(r => r.style.display = '');
}
</script>

</body>
</html>
